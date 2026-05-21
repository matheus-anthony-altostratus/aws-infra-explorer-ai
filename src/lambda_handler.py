import json
import os
import uuid
import boto3
from boto3.dynamodb.conditions import Attr
from core.session_manager import SessionManager
from core.orchestrator import InfraOrchestrator
from generators.bedrock_generator import BedrockGenerator

s3_client     = boto3.client("s3")
lambda_client = boto3.client("lambda")
dynamodb      = boto3.resource("dynamodb")

OUTPUTS_BUCKET = os.environ["OUTPUTS_BUCKET"]
FUNCTION_NAME  = os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "")
ACCOUNTS_TABLE = os.environ.get("ACCOUNTS_TABLE", "infra-explorer-accounts")
HISTORY_TABLE  = os.environ.get("HISTORY_TABLE",  "infra-explorer-history")


# ─── Router ──────────────────────────────────────────────────────────────────

def handler(event, context):
    if "async_analyze" in event:
        return _run_analysis(event["async_analyze"])

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
    else:
        return _response(404, {"error": "Not found"})


# ─── Analyze ─────────────────────────────────────────────────────────────────

def _handle_analyze(event):
    try:
        body       = json.loads(event.get("body", "{}"))
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

        _save_status(s3_prefix, {
            "status":        "completed",
            "account_id":    account_id,
            "account_name":  account_name,
            "group_name":    group_name,
            "color":         color,
            "region":        region,
            "documentation": report.documentation,
            "suggestions":   report.suggestions,
            "downloads":     download_urls,
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
    try:
        claims = event.get("requestContext", {}).get("authorizer", {}).get("jwt", {}).get("claims", {})
        return claims.get("email", "")
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
            "cmc_level":       item.get("cmc_level", ""),
            "identity":        item.get("identity", ""),
            "cicd":            item.get("cicd", []),
            "containers":      item.get("containers", []),
            "observability":   item.get("observability", []),
            "runbook":         item.get("runbook", ""),
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
            "group_id":      group_id,
            "account_id":    "PROFILE",
            "cmc_level":     body.get("cmc_level", ""),
            "identity":      body.get("identity", ""),
            "cicd":          body.get("cicd", []),
            "containers":    body.get("containers", []),
            "observability": body.get("observability", []),
            "runbook":       body.get("runbook", ""),
            "updated_at":    _now_iso(),
        })
        return _response(200, {"saved": True})
    except Exception as e:
        return _response(500, {"error": str(e)})


def _response(status_code, body, headers=None):
    return {
        "statusCode": status_code,
        "headers":    {"Content-Type": "application/json", **(headers or {})},
        "body":       json.dumps(body),
    }
