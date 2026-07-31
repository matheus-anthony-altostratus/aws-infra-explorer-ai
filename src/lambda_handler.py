import base64
import json
import os
import uuid
import boto3
from boto3.dynamodb.conditions import Attr
from core.session_manager import SessionManager
from core.orchestrator import InfraOrchestrator
from generators.bedrock_generator import BedrockGenerator

s3_client      = boto3.client("s3")
lambda_client  = boto3.client("lambda")
dynamodb       = boto3.resource("dynamodb")
secrets_client = boto3.client("secretsmanager")

OUTPUTS_BUCKET = os.environ["OUTPUTS_BUCKET"]
FUNCTION_NAME  = os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "")
ACCOUNTS_TABLE = os.environ.get("ACCOUNTS_TABLE", "infra-explorer-accounts")
HISTORY_TABLE  = os.environ.get("HISTORY_TABLE",  "infra-explorer-history")
NOTION_TOKEN        = os.environ.get("NOTION_TOKEN", "")
NOTION_SECRET_NAME  = os.environ.get("NOTION_SECRET_NAME", "infra-explorer/notion-token")
_notion_token_cache = None
COGNITO_USER_POOL_ID = os.environ.get("COGNITO_USER_POOL_ID", "")
cognito_client       = boto3.client("cognito-idp")

# ─── Router ──────────────────────────────────────────────────────────────────

def handler(event, context):
    if "async_analyze" in event:
        return _run_analysis(event["async_analyze"])
    if "async_multi" in event:
        return _run_multi_analysis(event["async_multi"])

    route_key = event.get("routeKey", "")

    if route_key == "POST /analyze":
        return _handle_analyze(event)
    elif route_key.startswith("GET /status/"):
        return _handle_status(event)
    elif route_key.startswith("GET /download/"):
        return _handle_download(event)
    elif route_key == "GET /history":
        return _handle_history(event)
    elif route_key == "GET /accounts":
        return _handle_accounts_list(event)
    elif route_key == "POST /accounts":
        return _handle_accounts_create(event)
    elif route_key.startswith("PUT /accounts/"):
        return _handle_accounts_update(event)
    elif route_key.startswith("DELETE /accounts/"):
        return _handle_accounts_delete(event)
    elif route_key == "GET /profiles/{group_id}":
        return _handle_profile_get(event)
    elif route_key == "PUT /profiles/{group_id}":
        return _handle_profile_put(event)
    elif route_key == "POST /notion/{s3_prefix}":
        return _handle_notion(event)
    elif route_key == "GET /dashboard":
        return _handle_dashboard(event)
    elif route_key == "GET /alerts":
        return _handle_alerts(event)
    elif route_key == "GET /users":
        return _handle_users_list(event)
    elif route_key == "GET /users/log":
        return _handle_users_log(event)
    elif route_key == "POST /users":
        return _handle_users_create(event)
    elif route_key == "DELETE /users/{email}":
        return _handle_users_delete(event)
    elif route_key == "POST /users/{email}/reset":
        return _handle_users_reset(event)
    else:
        return _response(404, {"error": "Not found"})


# ─── Analyze ─────────────────────────────────────────────────────────────────

def _handle_analyze(event):
    try:
        body       = json.loads(event.get("body", "{}"))

        # Fase 26 — si el body trae una lista account_ids, es un análisis multicuenta
        if isinstance(body.get("account_ids"), list) and body["account_ids"]:
            return _handle_analyze_multi(event, body)

        account_id = body.get("account_id", "").strip()
        region     = body.get("region", "eu-west-1").strip()

        if not account_id or not account_id.isdigit() or len(account_id) != 12:
            return _response(400, {"error": "account_id debe ser un número de 12 dígitos"})

        account_name, group_name, color = _get_account_info(account_id)
        body_email  = body.get("user_email", "").strip()
        user_email  = body_email or _get_user_email(event)
        analysis_id = str(uuid.uuid4())[:8]

        # La carpeta S3 usa account_id + region para sobreescribir siempre
        s3_prefix = f"{account_id}_{region}"

        _save_status(s3_prefix, {"status": "processing", "region": region})

        lambda_client.invoke(
            FunctionName=FUNCTION_NAME,
            InvocationType="Event",
            Payload=json.dumps({
                "async_analyze": {
                    "analysis_id": analysis_id,
                    "s3_prefix":   s3_prefix,
                    "account_id":  account_id,
                    "account_name": account_name,
                    "group_name":  group_name,
                    "color":       color,
                    "region":      region,
                    "user_email":  user_email,
                }
            }),
        )

        return _response(202, {"analysis_id": s3_prefix, "status": "processing"})

    except Exception as e:
        return _response(500, {"error": str(e)})


def _run_analysis(params):
    analysis_id  = params["analysis_id"]
    s3_prefix    = params["s3_prefix"]
    account_id   = params["account_id"]
    account_name = params.get("account_name", account_id)
    group_name   = params.get("group_name", "")
    color        = params.get("color", "#0166ff")
    region       = params["region"]
    user_email   = params.get("user_email", "")

    def step(label):
        _save_status(s3_prefix, {"status": "processing", "region": region, "step": label})

    try:
        step("🔐 Conectando con la cuenta AWS...")
        role_arn     = f"arn:aws:iam::{account_id}:role/infra-explorer-read-only"
        session      = SessionManager(region_name=region, role_arn=role_arn)
        orchestrator = InfraOrchestrator(session=session)

        step("🔍 Extrayendo infraestructura (VPCs, EC2, RDS, ECS, EKS...)...")
        infra      = orchestrator.collect()
        infra_json = orchestrator.export_to_json(infra, output_dir="/tmp")

        # Fase 17 — leer el inventario anterior desde S3 (antes de sobreescribirlo) y calcular el diff
        previous_infra = _get_previous_infra(s3_prefix, region)
        changes        = _compute_infra_diff(previous_infra, infra)

        step("📝 Generando documentación técnica con IA...")
        prompts_dir  = os.path.join(os.path.dirname(__file__), "prompts")
        bedrock      = BedrockGenerator(region_name=region, prompts_dir=prompts_dir)
        report       = bedrock.generate_report(infra)
        report_paths = bedrock.export_report(report, region, output_dir="/tmp")

        step("🏗️ Generando diagrama de arquitectura draw.io...")
        drawio_path = orchestrator.generate_drawio(infra, output_dir="/tmp")

        step("☁️ Subiendo archivos a S3...")
        files = {
            f"infra_{region}.json":       infra_json,
            f"documentation_{region}.md": report_paths["documentation"],
            f"suggestions_{region}.md":   report_paths["suggestions"],
            f"diagram_{region}.drawio":   drawio_path,
        }

        download_urls = {}
        for filename, filepath in files.items():
            s3_key = f"{s3_prefix}/{filename}"
            s3_client.upload_file(filepath, OUTPUTS_BUCKET, s3_key)
            download_urls[filename] = _generate_presigned_url(s3_key)

        health  = _calculate_health_score(infra)
        diagram = _build_diagram_summary(infra)

        _save_status(s3_prefix, {
            "status":        "completed",
            "account_id":    account_id,
            "account_name":  account_name,
            "group_name":    group_name,
            "color":         color,
            "region":        region,
            "user_email":    user_email,
            "documentation": report.documentation,
            "suggestions":   report.suggestions,
            "downloads":     download_urls,
            "health_score":  health,
            "changes":       changes,
            "diagram":       diagram,
            "timestamp":     _now_iso(),
        })

        _save_history({
            "analysis_id":  analysis_id,
            "s3_prefix":    s3_prefix,
            "timestamp":    _now_iso(),
            "account_id":   account_id,
            "account_name": account_name,
            "group_name":   group_name,
            "color":        color,
            "region":       region,
            "user_email":   user_email,
            "status":       "completed",
        })

    except Exception as e:
        _save_status(s3_prefix, {"status": "error", "error": str(e)})


# ─── Fase 26 — Análisis multicuenta ──────────────────────────────────────────

def _handle_analyze_multi(event, body):
    try:
        account_ids = [str(a).strip() for a in body.get("account_ids", [])]
        account_ids = [a for a in account_ids if a.isdigit() and len(a) == 12]
        region      = body.get("region", "eu-west-1").strip()

        if len(account_ids) < 2:
            return _response(400, {"error": "Selecciona al menos 2 cuentas válidas (12 dígitos)"})

        accounts = []
        for aid in account_ids:
            name, group, color = _get_account_info(aid)
            accounts.append({"account_id": aid, "account_name": name, "group_name": group, "color": color})

        user_email = body.get("user_email", "").strip() or _get_user_email(event)
        multi_id   = f"multi_{str(uuid.uuid4())[:8]}"

        _save_status(multi_id, {"status": "processing", "type": "multi", "region": region})

        lambda_client.invoke(
            FunctionName=FUNCTION_NAME,
            InvocationType="Event",
            Payload=json.dumps({
                "async_multi": {
                    "multi_id":   multi_id,
                    "region":     region,
                    "accounts":   accounts,
                    "user_email": user_email,
                }
            }),
        )

        return _response(202, {"analysis_id": multi_id, "status": "processing"})
    except Exception as e:
        return _response(500, {"error": str(e)})


def _run_multi_analysis(params):
    multi_id   = params["multi_id"]
    region     = params["region"]
    accounts   = params["accounts"]
    user_email = params.get("user_email", "")

    def step(label):
        _save_status(multi_id, {"status": "processing", "type": "multi", "region": region, "step": label})

    try:
        collected = []   # [{account_id, account_name, color, infra, error}]
        for acc in accounts:
            aid = acc["account_id"]
            step(f"🔍 Extrayendo {acc['account_name']} ({aid})...")
            try:
                role_arn = f"arn:aws:iam::{aid}:role/infra-explorer-read-only"
                session  = SessionManager(region_name=region, role_arn=role_arn)
                infra    = InfraOrchestrator(session=session).collect()
                collected.append({**acc, "infra": infra, "error": None})
            except Exception as e:
                collected.append({**acc, "infra": None, "error": str(e)})

        step("🔗 Correlacionando conexiones entre cuentas...")
        connections = _correlate_accounts(collected)

        step("📝 Generando explicación con IA...")
        narrative = _multi_narrative(region, collected, connections)

        accounts_summary = []
        for c in collected:
            entry = {"account_id": c["account_id"], "account_name": c["account_name"], "color": c["color"]}
            if c["error"]:
                entry["error"] = c["error"]
            else:
                infra = c["infra"]
                entry["summary"] = {
                    "vpcs":             len(infra.vpcs),
                    "transit_gateways": len(infra.transit_gateways),
                    "vpc_peerings":     len(infra.vpc_peerings),
                    "vpn_connections":  len(infra.vpn_connections),
                    "direct_connect":   len(infra.direct_connect_connections),
                }
            accounts_summary.append(entry)

        _save_status(multi_id, {
            "status":      "completed",
            "type":        "multi",
            "region":      region,
            "accounts":    accounts_summary,
            "connections": connections,
            "narrative":   narrative,
            "timestamp":   _now_iso(),
        })

        _save_history({
            "analysis_id":  multi_id,
            "s3_prefix":    multi_id,
            "timestamp":    _now_iso(),
            "type":         "multi",
            "account_id":   ",".join(a["account_id"] for a in accounts),
            "account_name": " + ".join(a["account_name"] for a in accounts),
            "region":       region,
            "user_email":   user_email,
            "status":       "completed",
        })
    except Exception as e:
        _save_status(multi_id, {"status": "error", "type": "multi", "error": str(e)})


def _correlate_accounts(collected):
    """Detecta conexiones entre cuentas cruzando IDs de recursos (sin IA)."""
    vpc_owner    = {}    # vpc_id -> account_id
    tgw_accounts = {}    # tgw_id -> set(account_id)
    for c in collected:
        if not c["infra"]:
            continue
        aid = c["account_id"]
        for vpc in c["infra"].vpcs:
            vpc_owner[vpc.resource_id] = aid
        for tgw in c["infra"].transit_gateways:
            tgw_accounts.setdefault(tgw.resource_id, set()).add(aid)

    name_of     = {c["account_id"]: c["account_name"] for c in collected}
    connections = []
    seen        = set()

    def add(a, b, ctype, detail):
        if a == b:
            return
        key = tuple(sorted([a, b]) + [ctype, detail])
        if key in seen:
            return
        seen.add(key)
        connections.append({
            "type": ctype,
            "from": a, "from_name": name_of.get(a, a),
            "to":   b, "to_name":   name_of.get(b, b),
            "detail": detail,
        })

    for c in collected:
        if not c["infra"]:
            continue
        aid = c["account_id"]

        # VPC Peering: si la VPC del otro lado pertenece a otra cuenta del set
        for p in c["infra"].vpc_peerings:
            for other_vpc in (p.requester_vpc_id, p.accepter_vpc_id):
                owner = vpc_owner.get(other_vpc)
                if owner and owner != aid:
                    add(aid, owner, "VPC Peering", f"{p.requester_vpc_id} ↔ {p.accepter_vpc_id}")

        # TGW: attachments que apuntan a VPCs de otra cuenta
        for tgw in c["infra"].transit_gateways:
            for att in tgw.attachments:
                owner = vpc_owner.get(att.resource_id_ref)
                if owner and owner != aid:
                    add(aid, owner, "Transit Gateway", f"TGW {tgw.resource_id} ↔ {att.resource_id_ref}")

    # TGW compartido: el mismo tgw_id aparece en varias cuentas
    for tgw_id, accs in tgw_accounts.items():
        accs = list(accs)
        for i in range(len(accs)):
            for j in range(i + 1, len(accs)):
                add(accs[i], accs[j], "Transit Gateway", f"TGW compartido {tgw_id}")

    return connections


def _multi_narrative(region, collected, connections):
    """Pide a Bedrock una explicación en lenguaje natural de la topología."""
    summary = {
        "region": region,
        "accounts": [
            {
                "account_id":       c["account_id"],
                "account_name":     c["account_name"],
                "error":            c["error"],
                "vpcs":             [{"id": v.resource_id, "name": v.name, "cidr": v.cidr_block} for v in c["infra"].vpcs] if c["infra"] else [],
                "transit_gateways": [t.resource_id for t in c["infra"].transit_gateways] if c["infra"] else [],
                "vpn_connections":  len(c["infra"].vpn_connections) if c["infra"] else 0,
                "direct_connect":   len(c["infra"].direct_connect_connections) if c["infra"] else 0,
            }
            for c in collected
        ],
        "connections": connections,
    }
    prompt = (
        "Eres un arquitecto de redes AWS. A partir de este JSON con varias cuentas de un cliente y las "
        "conexiones detectadas entre ellas, explica en español, de forma clara y para un ingeniero de operaciones, "
        "cómo están interconectadas. Usa Markdown. Incluye: (1) qué hay en cada cuenta a nivel de red, "
        "(2) cómo se conectan entre sí (peering, transit gateway, etc.) citando los IDs, y (3) puntos de atención "
        "para diagnosticar problemas de conectividad. Si una cuenta tiene 'error', indícalo. No inventes recursos "
        "ni conexiones que no estén en el JSON.\n\n"
        f"```json\n{json.dumps(summary, indent=2, default=str)}\n```"
    )
    try:
        prompts_dir = os.path.join(os.path.dirname(__file__), "prompts")
        return BedrockGenerator(region_name=region, prompts_dir=prompts_dir)._invoke(prompt)
    except Exception as e:
        return f"No se pudo generar la explicación con IA: {e}"


# ─── Status & Download ───────────────────────────────────────────────────────

def _handle_status(event):
    try:
        analysis_id = event.get("pathParameters", {}).get("analysis_id")
        if not analysis_id:
            return _response(400, {"error": "analysis_id requerido"})
        status = _get_status(analysis_id)
        if not status:
            return _response(404, {"error": "Análisis no encontrado"})
        return _response(200, status)
    except Exception as e:
        return _response(500, {"error": str(e)})


def _handle_download(event):
    try:
        params      = event.get("pathParameters", {})
        analysis_id = params.get("analysis_id")
        filename    = params.get("filename")
        if not analysis_id or not filename:
            return _response(400, {"error": "Parámetros inválidos"})
        url = _generate_presigned_url(f"{analysis_id}/{filename}")
        return _response(302, {}, headers={"Location": url})
    except Exception as e:
        return _response(500, {"error": str(e)})


# ─── History ─────────────────────────────────────────────────────────────────

def _handle_history(event):
    try:
        table    = dynamodb.Table(HISTORY_TABLE)
        response = table.scan()
        items    = response.get("Items", [])
        while "LastEvaluatedKey" in response:
            response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
            items.extend(response.get("Items", []))

        # Agrupar por account_id + region
        groups = {}
        for item in items:
            key = f"{item['account_id']}_{item['region']}"
            if key not in groups:
                groups[key] = {
                    "account_id":   item["account_id"],
                    "account_name": item.get("account_name", item["account_id"]),
                    "group_name":   item.get("group_name", ""),
                    "color":        item.get("color", "#0166ff"),
                    "region":       item["region"],
                    "s3_prefix":    item.get("s3_prefix", key),
                    "analyses":     [],
                }
            groups[key]["analyses"].append({
                "analysis_id": item["analysis_id"],
                "timestamp":   item.get("timestamp", ""),
                "user_email":  item.get("user_email", ""),
                "status":      item.get("status", ""),
            })

        # Ordenar análisis dentro de cada grupo por timestamp desc
        result = []
        for g in groups.values():
            g["analyses"].sort(key=lambda x: x["timestamp"], reverse=True)
            result.append(g)

        # Ordenar grupos por el timestamp del análisis más reciente
        result.sort(key=lambda x: x["analyses"][0]["timestamp"] if x["analyses"] else "", reverse=True)

        return _response(200, {"groups": result})
    except Exception as e:
        return _response(500, {"error": str(e)})


def _save_history(entry):
    dynamodb.Table(HISTORY_TABLE).put_item(Item=entry)


# ─── Accounts ────────────────────────────────────────────────────────────────

def _handle_accounts_list(event):
    try:
        table    = dynamodb.Table(ACCOUNTS_TABLE)
        response = table.scan()
        items    = response.get("Items", [])
        while "LastEvaluatedKey" in response:
            response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
            items.extend(response.get("Items", []))

        groups = {}
        for item in items:
            gid = item["group_id"]
            if gid not in groups:
                groups[gid] = {
                    "group_id":   gid,
                    "group_name": item.get("group_name", ""),
                    "accounts":   [],
                }
            groups[gid]["accounts"].append({
                "account_id":     item["account_id"],
                "account_name":   item.get("account_name", ""),
                "alias":          item.get("alias", ""),
                "default_region": item.get("default_region", "eu-west-1"),
                "color":          item.get("color", "#0166ff"),
            })

        result = sorted(groups.values(), key=lambda x: x["group_name"])
        return _response(200, {"groups": result})
    except Exception as e:
        return _response(500, {"error": str(e)})


def _handle_accounts_create(event):
    try:
        body           = json.loads(event.get("body", "{}"))
        group_id       = body.get("group_id") or str(uuid.uuid4())[:8]
        group_name     = body.get("group_name", "").strip()
        account_id     = body.get("account_id", "").strip()
        account_name   = body.get("account_name", "").strip()
        alias          = body.get("alias", "").strip()
        default_region = body.get("default_region", "eu-west-1").strip()
        color          = body.get("color", "#0166ff").strip()

        if not group_name or not account_id or not account_name:
            return _response(400, {"error": "group_name, account_id y account_name son requeridos"})
        if not account_id.isdigit() or len(account_id) != 12:
            return _response(400, {"error": "account_id debe ser un número de 12 dígitos"})

        dynamodb.Table(ACCOUNTS_TABLE).put_item(Item={
            "group_id":       group_id,
            "group_name":     group_name,
            "account_id":     account_id,
            "account_name":   account_name,
            "alias":          alias,
            "default_region": default_region,
            "color":          color,
            "created_at":     _now_iso(),
        })

        return _response(201, {"group_id": group_id, "account_id": account_id})
    except Exception as e:
        return _response(500, {"error": str(e)})


def _handle_accounts_update(event):
    try:
        params     = event.get("pathParameters", {})
        group_id   = params.get("group_id")
        account_id = params.get("account_id")
        body       = json.loads(event.get("body", "{}"))

        if not group_id or not account_id:
            return _response(400, {"error": "group_id y account_id requeridos"})

        dynamodb.Table(ACCOUNTS_TABLE).update_item(
            Key={"group_id": group_id, "account_id": account_id},
            UpdateExpression="SET group_name=:gn, account_name=:an, alias=:al, default_region=:dr, color=:co",
            ExpressionAttributeValues={
                ":gn": body.get("group_name", ""),
                ":an": body.get("account_name", ""),
                ":al": body.get("alias", ""),
                ":dr": body.get("default_region", "eu-west-1"),
                ":co": body.get("color", "#0166ff"),
            },
        )
        return _response(200, {"updated": True})
    except Exception as e:
        return _response(500, {"error": str(e)})


def _handle_accounts_delete(event):
    try:
        params     = event.get("pathParameters", {})
        group_id   = params.get("group_id")
        account_id = params.get("account_id")

        if not group_id or not account_id:
            return _response(400, {"error": "group_id y account_id requeridos"})

        dynamodb.Table(ACCOUNTS_TABLE).delete_item(
            Key={"group_id": group_id, "account_id": account_id}
        )
        return _response(200, {"deleted": True})
    except Exception as e:
        return _response(500, {"error": str(e)})


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _get_account_info(account_id):
    try:
        table    = dynamodb.Table(ACCOUNTS_TABLE)
        response = table.scan(FilterExpression=Attr("account_id").eq(account_id))
        items    = response.get("Items", [])
        if items:
            return (
                items[0].get("account_name", account_id),
                items[0].get("group_name", ""),
                items[0].get("color", "#0166ff"),
            )
    except Exception:
        pass
    return account_id, "", "#0166ff"


def _save_status(s3_prefix, data):
    s3_client.put_object(
        Bucket=OUTPUTS_BUCKET,
        Key=f"{s3_prefix}/status.json",
        Body=json.dumps(data),
        ContentType="application/json",
    )


def _get_status(s3_prefix):
    try:
        response = s3_client.get_object(Bucket=OUTPUTS_BUCKET, Key=f"{s3_prefix}/status.json")
        return json.loads(response["Body"].read())
    except Exception:
        return None


def _get_user_email(event):
    """Email del usuario que realiza la petición (el 'quién' del registro de actividad).

    Orden de resolución:
      1. Claims del authorizer JWT de API Gateway — fuente fiable, requiere que la
         ruta tenga el authorizer Cognito asociado.
      2. Payload del id_token recibido en 'Authorization: Bearer ...'.
      3. Campo 'user_email' del body.
      4. Parámetro 'user_email' del query string.
    """
    try:
        claims = (event.get("requestContext", {})
                       .get("authorizer", {})
                       .get("jwt", {})
                       .get("claims", {})) or {}
        if claims.get("email"):
            return str(claims["email"]).strip().lower()
    except Exception:
        pass

    email = _email_from_bearer(event)
    if email:
        return email

    try:
        body = json.loads(event.get("body") or "{}")
        if isinstance(body, dict) and body.get("user_email"):
            return str(body["user_email"]).strip().lower()
    except Exception:
        pass

    qs = event.get("queryStringParameters") or {}
    if qs.get("user_email"):
        return str(qs["user_email"]).strip().lower()

    return ""


def _email_from_bearer(event):
    """Lee el claim 'email' del JWT que llega en el header Authorization.

    Solo se usa para atribuir acciones en el registro de actividad. La validación
    criptográfica del token corresponde al authorizer JWT de API Gateway; aquí
    únicamente se decodifica el payload.
    """
    try:
        headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
        auth    = headers.get("authorization", "")
        if not auth.lower().startswith("bearer "):
            return ""
        parts = auth.split(" ", 1)[1].strip().split(".")
        if len(parts) < 2:
            return ""
        payload_b64 = parts[1] + "=" * (-len(parts[1]) % 4)
        payload     = json.loads(base64.urlsafe_b64decode(payload_b64))
        return str(payload.get("email", "")).strip().lower()
    except Exception:
        return ""


def _now_iso():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _generate_presigned_url(s3_key):
    return s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": OUTPUTS_BUCKET, "Key": s3_key},
        ExpiresIn=3600,
    )


def _handle_profile_get(event):
    try:
        group_id = event.get("pathParameters", {}).get("group_id")
        if not group_id:
            return _response(400, {"error": "group_id requerido"})
        item = dynamodb.Table(ACCOUNTS_TABLE).get_item(
            Key={"group_id": group_id, "account_id": "PROFILE"}
        ).get("Item")
        if not item:
            return _response(200, {"profile": {}})
        return _response(200, {"profile": {
            "cmc_level":      item.get("cmc_level", ""),
            "identity":       item.get("identity", ""),
            "cicd":           item.get("cicd", []),
            "containers":     item.get("containers", []),
            "observability":  item.get("observability", []),
            "runbook":        item.get("runbook", ""),
            "notion_page_id": item.get("notion_page_id", ""),
        }})
    except Exception as e:
        return _response(500, {"error": str(e)})


def _handle_profile_put(event):
    try:
        group_id = event.get("pathParameters", {}).get("group_id")
        if not group_id:
            return _response(400, {"error": "group_id requerido"})
        body = json.loads(event.get("body", "{}"))
        dynamodb.Table(ACCOUNTS_TABLE).put_item(Item={
            "group_id":       group_id,
            "account_id":     "PROFILE",
            "cmc_level":      body.get("cmc_level", ""),
            "identity":       body.get("identity", ""),
            "cicd":           body.get("cicd", []),
            "containers":     body.get("containers", []),
            "observability":  body.get("observability", []),
            "runbook":        body.get("runbook", ""),
            "notion_page_id": body.get("notion_page_id", ""),
            "updated_at":     _now_iso(),
        })
        return _response(200, {"saved": True})
    except Exception as e:
        return _response(500, {"error": str(e)})

# ─── Users ───────────────────────────────────────────────────────────────────

def _handle_users_list(event):
    try:
        if not COGNITO_USER_POOL_ID:
            return _response(503, {"error": "COGNITO_USER_POOL_ID no configurado"})
        users = []
        kwargs = {"UserPoolId": COGNITO_USER_POOL_ID, "Limit": 60}
        response = cognito_client.list_users(**kwargs)
        while True:
            for u in response.get("Users", []):
                attrs = {a["Name"]: a["Value"] for a in u.get("Attributes", [])}
                users.append({
                    "email":      attrs.get("email", u["Username"]),
                    "status":     u["UserStatus"],
                    "enabled":    u["Enabled"],
                    "created_at": u["UserCreateDate"].strftime("%Y-%m-%dT%H:%M:%SZ"),
                })
            token = response.get("PaginationToken")
            if not token:
                break
            response = cognito_client.list_users(**kwargs, PaginationToken=token)
        return _response(200, {"users": users})
    except Exception as e:
        return _response(500, {"error": str(e)})


def _handle_users_create(event):
    try:
        if not COGNITO_USER_POOL_ID:
            return _response(503, {"error": "COGNITO_USER_POOL_ID no configurado"})
        body  = json.loads(event.get("body", "{}"))
        email = body.get("email", "").strip().lower()
        if not email or not email.endswith("@altostratus.es"):
            return _response(400, {"error": "El email debe ser @altostratus.es"})
        cognito_client.admin_create_user(
            UserPoolId=COGNITO_USER_POOL_ID,
            Username=email,
            UserAttributes=[{"Name": "email", "Value": email},
                            {"Name": "email_verified", "Value": "true"}],
            DesiredDeliveryMediums=["EMAIL"],
        )
        created_by = _get_user_email(event)
        _save_history({
            "analysis_id": f"USER_ACTION#{uuid.uuid4()}",
            "timestamp":   _now_iso(),
            "action":      "CREATE",
            "target":      email,
            "user_email":  created_by,
        })
        return _response(201, {"created": email})
    except cognito_client.exceptions.UsernameExistsException:
        return _response(409, {"error": "Este usuario ya existe"})
    except Exception as e:
        return _response(500, {"error": str(e)})


def _handle_users_delete(event):
    try:
        if not COGNITO_USER_POOL_ID:
            return _response(503, {"error": "COGNITO_USER_POOL_ID no configurado"})
        email      = event.get("pathParameters", {}).get("email", "").strip()
        deleted_by = _get_user_email(event)
        if not email:
            return _response(400, {"error": "email requerido"})
        if email.lower() == deleted_by.lower() and deleted_by:
            return _response(400, {"error": "No puedes eliminar tu propia cuenta"})
        cognito_client.admin_delete_user(
            UserPoolId=COGNITO_USER_POOL_ID, Username=email,
        )
        _save_history({
            "analysis_id": f"USER_ACTION#{uuid.uuid4()}",
            "timestamp":   _now_iso(),
            "action":      "DELETE",
            "target":      email,
            "user_email":  deleted_by,
        })
        return _response(200, {"deleted": email})
    except cognito_client.exceptions.UserNotFoundException:
        return _response(404, {"error": "Usuario no encontrado"})
    except Exception as e:
        return _response(500, {"error": str(e)})

def _get_cognito_user_status(email):
    """Estado del usuario en Cognito (FORCE_CHANGE_PASSWORD, CONFIRMED, ...).

    Se usa ListUsers con filtro por email en lugar de AdminGetUser para no
    necesitar permisos IAM adicionales.
    """
    try:
        resp = cognito_client.list_users(
            UserPoolId=COGNITO_USER_POOL_ID,
            Filter=f'email = "{email}"',
            Limit=1,
        )
        users = resp.get("Users", [])
        return users[0]["UserStatus"] if users else ""
    except Exception:
        return ""


def _handle_users_reset(event):
    try:
        if not COGNITO_USER_POOL_ID:
            return _response(503, {"error": "COGNITO_USER_POOL_ID no configurado"})
        email    = event.get("pathParameters", {}).get("email", "").strip()
        reset_by = _get_user_email(event)
        if not email:
            return _response(400, {"error": "email requerido"})

        if _get_cognito_user_status(email) == "FORCE_CHANGE_PASSWORD":
            # El usuario nunca ha entrado. Un reset normal le enviaría un simple
            # código de verificación, sin explicar nada. Reenviamos la invitación
            # completa: nueva contraseña temporal + instrucciones para crear la suya.
            cognito_client.admin_create_user(
                UserPoolId=COGNITO_USER_POOL_ID,
                Username=email,
                MessageAction="RESEND",
                DesiredDeliveryMediums=["EMAIL"],
            )
            action = "RESEND_INVITE"
        else:
            cognito_client.admin_reset_user_password(
                UserPoolId=COGNITO_USER_POOL_ID, Username=email,
            )
            action = "RESET_PASSWORD"

        _save_history({
            "analysis_id": f"USER_ACTION#{uuid.uuid4()}",
            "timestamp":   _now_iso(),
            "action":      action,
            "target":      email,
            "user_email":  reset_by,
        })
        return _response(200, {"reset": email, "action": action})
    except cognito_client.exceptions.UserNotFoundException:
        return _response(404, {"error": "Usuario no encontrado"})
    except Exception as e:
        return _response(500, {"error": str(e)})

def _handle_users_log(event):
    try:
        table    = dynamodb.Table(HISTORY_TABLE)
        response = table.scan(
            FilterExpression=Attr("analysis_id").begins_with("USER_ACTION#")
        )
        items = response.get("Items", [])
        while "LastEvaluatedKey" in response:
            response = table.scan(
                FilterExpression=Attr("analysis_id").begins_with("USER_ACTION#"),
                ExclusiveStartKey=response["LastEvaluatedKey"],
            )
            items.extend(response.get("Items", []))
        items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return _response(200, {"logs": items[:300]})
    except Exception as e:
        return _response(500, {"error": str(e)})


def _get_notion_token():
    global _notion_token_cache
    if _notion_token_cache:
        return _notion_token_cache
    if NOTION_TOKEN:                       # override por env var si existe
        _notion_token_cache = NOTION_TOKEN
        return _notion_token_cache
    try:
        resp = secrets_client.get_secret_value(SecretId=NOTION_SECRET_NAME)
        _notion_token_cache = resp.get("SecretString", "")
    except Exception as e:
        print(f"No se pudo leer el secreto de Notion: {e}")
        _notion_token_cache = ""
    return _notion_token_cache


def _handle_notion(event):
    try:
        notion_token = _get_notion_token()
        if not notion_token:
            return _response(503, {"error": "Notion no está configurado. Falta el secreto en Secrets Manager."})

        s3_prefix = event.get("pathParameters", {}).get("s3_prefix")
        if not s3_prefix:
            return _response(400, {"error": "s3_prefix requerido"})

        body            = json.loads(event.get("body", "{}"))
        notion_page_id  = body.get("notion_page_id", "").strip()
        if not notion_page_id:
            return _response(400, {"error": "notion_page_id requerido — configúralo en el Service Profile del cliente"})

        # Leer el análisis de S3
        status = _get_status(s3_prefix)
        if not status or status.get("status") != "completed":
            return _response(400, {"error": "El análisis no está completado o no existe"})

        # Generar URL pública temporal del SVG si existe (24h)
        diagram_url = None
        svg_key     = f"{s3_prefix}/diagram_summary.svg"
        try:
            s3_client.head_object(Bucket=OUTPUTS_BUCKET, Key=svg_key)
            diagram_url = s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": OUTPUTS_BUCKET, "Key": svg_key},
                ExpiresIn=86400,
            )
        except Exception:
            pass

        from generators.notion_generator import NotionGenerator
        notion   = NotionGenerator(notion_token)
        page_url = notion.create_analysis_page(
            parent_page_id = notion_page_id,
            group_name     = status.get("group_name", ""),
            account_name   = status.get("account_name", s3_prefix),
            account_id     = status.get("account_id", ""),
            region         = status.get("region", ""),
            user_email     = status.get("user_email", "") or _get_user_email(event),
            documentation  = status.get("documentation", ""),
            suggestions    = status.get("suggestions", ""),
            diagram_url    = diagram_url,
        )

        return _response(200, {"url": page_url})

    except Exception as e:
        return _response(500, {"error": str(e)})

# ─── Health Score & Alerts ───────────────────────────────────────────────────

def _generate_security_alerts(infra):
    """Genera alertas de seguridad a partir de la infraestructura."""
    alerts = []

    critical_ports = {22, 3389}
    sensitive_ports = {3306, 5432, 1433, 27017, 6379, 9200}
    for sg in infra.security_groups:
        sg_name = sg.name or sg.resource_id
        for rule in sg.ingress_rules:
            for cidr in rule.cidr_blocks:
                if cidr in ("0.0.0.0/0", "::/0"):
                    if rule.from_port == 0 and rule.to_port == 65535:
                        alerts.append({"severity": "critical", "resource": sg_name, "type": "SG", "msg": "Todos los puertos abiertos al mundo"})
                    elif rule.from_port in critical_ports:
                        alerts.append({"severity": "critical", "resource": sg_name, "type": "SG", "msg": f"Puerto {rule.from_port} abierto al mundo (SSH/RDP)"})
                    elif rule.from_port in sensitive_ports:
                        alerts.append({"severity": "high", "resource": sg_name, "type": "SG", "msg": f"Puerto {rule.from_port} (base de datos) abierto al mundo"})
                    elif rule.to_port - rule.from_port > 100:
                        alerts.append({"severity": "medium", "resource": sg_name, "type": "SG", "msg": f"Rango amplio de puertos abierto ({rule.from_port}-{rule.to_port})"})
                    else:
                        alerts.append({"severity": "high", "resource": sg_name, "type": "SG", "msg": f"Puerto {rule.from_port} abierto al mundo"})

    for rds in infra.rds_instances:
        rds_name = rds.name or rds.resource_id
        if rds.publicly_accessible:
            alerts.append({"severity": "critical", "resource": rds_name, "type": "RDS", "msg": "Acceso publico habilitado"})
        if not rds.multi_az:
            alerts.append({"severity": "high", "resource": rds_name, "type": "RDS", "msg": "Sin Multi-AZ (sin alta disponibilidad)"})

    for vpc in infra.vpcs:
        vpc_name = vpc.name or vpc.resource_id
        vpc_nats = [n for n in infra.nat_gateways if n.vpc_id == vpc.resource_id]
        if 0 < len(vpc_nats) < 2:
            alerts.append({"severity": "medium", "resource": vpc_name, "type": "VPC", "msg": "Un solo NAT Gateway (sin redundancia AZ)"})

    for eip in infra.elastic_ips:
        if not eip.association_id:
            alerts.append({"severity": "low", "resource": eip.public_ip, "type": "EIP", "msg": "EIP sin asociar (coste innecesario)"})

    for ec2 in infra.instances:
        ec2_name = ec2.name or ec2.resource_id
        if ec2.state == "stopped":
            alerts.append({"severity": "medium", "resource": ec2_name, "type": "EC2", "msg": "Instancia detenida"})

    if infra.iam_summary:
        for user in getattr(infra.iam_summary, "users", []):
            if not user.mfa_active:
                alerts.append({"severity": "high", "resource": user.username, "type": "IAM", "msg": "Usuario sin MFA habilitado"})

    no_name_count = sum(1 for ec2 in infra.instances if not ec2.name)
    if no_name_count > 0:
        alerts.append({"severity": "info", "resource": f"{no_name_count} instancias", "type": "EC2", "msg": "Instancias sin tag Name"})

    return alerts


# ─── Fase 17 — Diff entre análisis ───────────────────────────────────────────

def _get_previous_infra(s3_prefix, region):
    """Lee el infra_{region}.json existente en S3 (el del análisis anterior)."""
    try:
        resp = s3_client.get_object(Bucket=OUTPUTS_BUCKET, Key=f"{s3_prefix}/infra_{region}.json")
        return json.loads(resp["Body"].read())
    except Exception:
        return None


_DIFF_CATEGORIES = {
    "vpcs": "VPC", "internet_gateways": "Internet Gateway", "nat_gateways": "NAT Gateway",
    "security_groups": "Security Group", "instances": "EC2", "rds_instances": "RDS",
    "route_tables": "Route Table", "load_balancers": "Load Balancer", "target_groups": "Target Group",
    "transit_gateways": "Transit Gateway", "vpn_gateways": "VPN Gateway",
    "customer_gateways": "Customer Gateway", "vpn_connections": "VPN Connection",
    "elastic_ips": "Elastic IP", "vpc_peerings": "VPC Peering",
    "direct_connect_connections": "Direct Connect", "ecs_clusters": "ECS Cluster",
    "efs_file_systems": "EFS", "eks_clusters": "EKS Cluster", "dynamodb_tables": "DynamoDB Table",
}


def _diff_fields(before, after):
    """Compara campos escalares de dos recursos y devuelve los que cambiaron."""
    changes = []
    for field, new_val in after.items():
        if isinstance(new_val, (list, dict)):
            continue  # ignoramos estructuras anidadas para evitar ruido
        old_val = before.get(field)
        if old_val != new_val:
            changes.append({"field": field, "before": old_val, "after": new_val})
    return changes


def _compute_infra_diff(previous, infra):
    """Compara el inventario anterior (dict de S3) con el actual (dataclass)."""
    from dataclasses import asdict
    iam_backup = infra.iam_summary
    infra.iam_summary = None
    current = asdict(infra)
    infra.iam_summary = iam_backup

    diff = {"is_first": previous is None, "added": [], "removed": [], "modified": []}

    for key, label in _DIFF_CATEGORIES.items():
        prev_list = previous.get(key) if previous else []
        if not isinstance(prev_list, list):
            prev_list = []   # en el JSON los vacíos se guardan como texto ("No se encontraron...")
        curr_list = current.get(key) or []
        if not isinstance(curr_list, list):
            curr_list = []

        prev_by_id = {r.get("resource_id"): r for r in prev_list if isinstance(r, dict)}
        curr_by_id = {r.get("resource_id"): r for r in curr_list if isinstance(r, dict)}

        for rid, r in curr_by_id.items():
            if rid not in prev_by_id:
                diff["added"].append({"category": label, "resource_id": rid, "name": r.get("name") or rid})
            else:
                field_changes = _diff_fields(prev_by_id[rid], r)
                if field_changes:
                    diff["modified"].append({"category": label, "resource_id": rid,
                                             "name": r.get("name") or rid, "changes": field_changes})

        for rid, r in prev_by_id.items():
            if rid not in curr_by_id:
                diff["removed"].append({"category": label, "resource_id": rid, "name": r.get("name") or rid})

    diff["has_changes"] = bool(diff["added"] or diff["removed"] or diff["modified"])
    return diff


def _calculate_health_score(infra):
    """Score determinista 0-100. Cada TIPO de problema penaliza una sola vez,
    sin importar cuántos recursos lo presenten (8 usuarios sin MFA = un único
    problema, no ocho). Las severidades menores (low/info) no pueden restar más
    de 10 puntos en conjunto, para que el ruido no hunda el score."""
    alerts = _generate_security_alerts(infra)
    penalties = {"critical": 15, "high": 10, "medium": 5, "low": 3, "info": 2}

    seen = set()
    score = 100
    minor_total = 0
    for alert in alerts:
        key = (alert["type"], alert["msg"])
        if key in seen:
            continue
        seen.add(key)
        severity = alert["severity"]
        pts = penalties.get(severity, 0)
        if severity in ("low", "info"):
            minor_total = min(10, minor_total + pts)
        else:
            score -= pts
    score -= minor_total

    return {"score": max(0, score), "alerts": alerts}


def _build_diagram_summary(infra):
    """Resumen compacto de red para dibujar el diagrama en el navegador."""
    vpcs = []
    for vpc in infra.vpcs:
        vid = vpc.resource_id
        vpcs.append({
            "id":      vid,
            "name":    vpc.name or vid,
            "cidr":    vpc.cidr_block,
            "subnets": len(vpc.subnets),
            "ec2":     sum(1 for i in infra.instances     if i.vpc_id == vid),
            "rds":     sum(1 for r in infra.rds_instances  if r.vpc_id == vid),
            "elb":     sum(1 for l in infra.load_balancers if l.vpc_id == vid),
            "nat":     sum(1 for n in infra.nat_gateways   if n.vpc_id == vid),
        })
    peerings  = [{"a": p.requester_vpc_id, "b": p.accepter_vpc_id} for p in infra.vpc_peerings]
    tgw_links = []
    for t in infra.transit_gateways:
        for att in t.attachments:
            if att.resource_id_ref:
                tgw_links.append({"tgw": t.resource_id, "vpc": att.resource_id_ref})
    return {
        "region":    infra.region,
        "vpcs":      vpcs,
        "peerings":  peerings,
        "tgws":      [t.resource_id for t in infra.transit_gateways],
        "tgw_links": tgw_links,
        "igw":       len(infra.internet_gateways) > 0,
        "vpn":       len(infra.vpn_connections) > 0,
        "dx":        len(infra.direct_connect_connections) > 0,
    }


def _handle_alerts(event):

    """Devuelve todas las alertas activas de todas las cuentas."""
    try:
        table = dynamodb.Table(ACCOUNTS_TABLE)
        response = table.scan()
        items = response.get("Items", [])
        while "LastEvaluatedKey" in response:
            response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
            items.extend(response.get("Items", []))

        all_alerts = []
        for item in items:
            if item["account_id"] == "PROFILE":
                continue
            s3_prefix = f"{item['account_id']}_{item.get('default_region', 'eu-west-1')}"
            status = _get_status(s3_prefix)
            if status and status.get("status") == "completed":
                for alert in status.get("health_score", {}).get("alerts", []):
                    all_alerts.append({
                        **alert,
                        "account_id": item["account_id"],
                        "account_name": item.get("account_name", ""),
                        "group_name": item.get("group_name", ""),
                        "color": item.get("color", "#0166ff"),
                        "region": item.get("default_region", "eu-west-1"),
                    })

        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        all_alerts.sort(key=lambda x: severity_order.get(x.get("severity"), 5))
        return _response(200, {"alerts": all_alerts})
    except Exception as e:
        return _response(500, {"error": str(e)})


def _latest_analysis_by_account():
    """Devuelve {account_id: {s3_prefix, region, timestamp}} con el análisis más reciente de cada cuenta (desde history)."""
    result = {}
    try:
        table = dynamodb.Table(HISTORY_TABLE)
        response = table.scan()
        items = response.get("Items", [])
        while "LastEvaluatedKey" in response:
            response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
            items.extend(response.get("Items", []))
        for it in items:
            aid = it.get("account_id")
            if not aid or str(it.get("analysis_id", "")).startswith("USER_ACTION#"):
                continue
            ts = it.get("timestamp", "")
            if aid not in result or ts > result[aid]["timestamp"]:
                result[aid] = {
                    "s3_prefix": it.get("s3_prefix", f"{aid}_{it.get('region', 'eu-west-1')}"),
                    "region":    it.get("region", "eu-west-1"),
                    "timestamp": ts,
                }
    except Exception:
        pass
    return result

def _handle_dashboard(event):
    try:
        # Leer todas las cuentas
        table = dynamodb.Table(ACCOUNTS_TABLE)
        response = table.scan()
        items = response.get("Items", [])
        while "LastEvaluatedKey" in response:
            response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
            items.extend(response.get("Items", []))

        # Último análisis real de cada cuenta (prefijo y región exactos usados)
        latest_by_account = _latest_analysis_by_account()

        groups = {}
        for item in items:
            if item["account_id"] == "PROFILE":
                continue
            gid = item["group_id"]
            if gid not in groups:
                groups[gid] = {"group_id": gid, "group_name": item.get("group_name", ""), "accounts": []}
            groups[gid]["accounts"].append({
                "account_id": item["account_id"],
                "account_name": item.get("account_name", ""),
                "color": item.get("color", "#0166ff"),
                "default_region": item.get("default_region", "eu-west-1"),
            })

        # Para cada cuenta, leer su último status.json
        clients = []
        total_alerts = 0
        scores = []
        for g in groups.values():
            for acc in g["accounts"]:
                latest    = latest_by_account.get(acc["account_id"])
                s3_prefix = latest["s3_prefix"] if latest else f"{acc['account_id']}_{acc['default_region']}"
                region    = latest["region"]    if latest else acc["default_region"]
                status = _get_status(s3_prefix)
                entry = {
                    "group_name": g["group_name"],
                    "account_name": acc["account_name"],
                    "account_id": acc["account_id"],
                    "color": acc["color"],
                    "region": region,
                }
                if status and status.get("status") == "completed":
                    entry["score"] = status.get("health_score", {}).get("score")
                    entry["alerts"] = len(status.get("health_score", {}).get("alerts", []))
                    entry["last_analysis"] = status.get("timestamp", "")
                    if entry["score"] is not None:
                        scores.append(entry["score"])
                        total_alerts += entry["alerts"]
                else:
                    entry["score"] = None
                    entry["alerts"] = 0
                    entry["last_analysis"] = None
                clients.append(entry)

        avg_score = round(sum(scores) / len(scores)) if scores else None
        return _response(200, {
            "total_clients": len(groups),
            "total_accounts": sum(len(g["accounts"]) for g in groups.values()),
            "total_alerts": total_alerts,
            "avg_score": avg_score,
            "clients": clients,
        })
    except Exception as e:
        return _response(500, {"error": str(e)})

def _response(status_code, body, headers=None):
    return {
        "statusCode": status_code,
        "headers":    {"Content-Type": "application/json", **(headers or {})},
        "body":       json.dumps(body),
    }
