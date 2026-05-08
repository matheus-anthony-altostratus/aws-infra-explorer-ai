import json
import os
import uuid
import boto3
from core.session_manager import SessionManager
from core.orchestrator import InfraOrchestrator
from generators.bedrock_generator import BedrockGenerator

s3_client = boto3.client("s3")
lambda_client = boto3.client("lambda")
OUTPUTS_BUCKET = os.environ["OUTPUTS_BUCKET"]
FUNCTION_NAME = os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "")


def handler(event, context):
    # Invocación asíncrona (viene sin routeKey)
    if "async_analyze" in event:
        return _run_analysis(event["async_analyze"])

    route_key = event.get("routeKey", "")

    if route_key == "POST /analyze":
        return _handle_analyze(event)
    elif route_key.startswith("GET /status/"):
        return _handle_status(event)
    elif route_key.startswith("GET /download/"):
        return _handle_download(event)
    else:
        return _response(404, {"error": "Not found"})


def _handle_analyze(event):
    try:
        body = json.loads(event.get("body", "{}"))
        account_id = body.get("account_id", "").strip()
        region = body.get("region", "eu-west-1").strip()

        if not account_id or not account_id.isdigit() or len(account_id) != 12:
            return _response(400, {"error": "account_id debe ser un número de 12 dígitos"})

        analysis_id = str(uuid.uuid4())[:8]

        # Guardar estado inicial en S3
        _save_status(analysis_id, {"status": "processing", "region": region})

        # Auto-invocación asíncrona
        lambda_client.invoke(
            FunctionName=FUNCTION_NAME,
            InvocationType="Event",
            Payload=json.dumps({
                "async_analyze": {
                    "analysis_id": analysis_id,
                    "account_id": account_id,
                    "region": region,
                }
            }),
        )

        return _response(202, {
            "analysis_id": analysis_id,
            "status": "processing",
        })

    except Exception as e:
        return _response(500, {"error": str(e)})


def _run_analysis(params):
    analysis_id = params["analysis_id"]
    account_id = params["account_id"]
    region = params["region"]

    try:
        role_arn = f"arn:aws:iam::{account_id}:role/infra-explorer-read-only"
        session = SessionManager(region_name=region, role_arn=role_arn)
        orchestrator = InfraOrchestrator(session=session)

        # Extracción
        infra = orchestrator.collect()
        infra_json = orchestrator.export_to_json(infra, output_dir="/tmp")

        # Reportes Bedrock
        prompts_dir = os.path.join(os.path.dirname(__file__), "prompts")
        bedrock = BedrockGenerator(region_name=region, prompts_dir=prompts_dir)
        report = bedrock.generate_report(infra)
        report_paths = bedrock.export_report(report, region, output_dir="/tmp")

        # Diagrama draw.io
        drawio_path = orchestrator.generate_drawio(infra, output_dir="/tmp")

        # Subir archivos a S3
        files = {
            f"infra_{region}.json": infra_json,
            f"documentation_{region}.md": report_paths["documentation"],
            f"suggestions_{region}.md": report_paths["suggestions"],
            f"diagram_{region}.drawio": drawio_path,
        }

        download_urls = {}
        for filename, filepath in files.items():
            s3_key = f"{analysis_id}/{filename}"
            s3_client.upload_file(filepath, OUTPUTS_BUCKET, s3_key)
            download_urls[filename] = _generate_presigned_url(s3_key)

        # Guardar estado completado
        _save_status(analysis_id, {
            "status": "completed",
            "region": region,
            "documentation": report.documentation,
            "suggestions": report.suggestions,
            "downloads": download_urls,
        })

    except Exception as e:
        _save_status(analysis_id, {
            "status": "error",
            "error": str(e),
        })


def _handle_status(event):
    try:
        params = event.get("pathParameters", {})
        analysis_id = params.get("analysis_id")

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
        params = event.get("pathParameters", {})
        analysis_id = params.get("analysis_id")
        filename = params.get("filename")

        if not analysis_id or not filename:
            return _response(400, {"error": "Parámetros inválidos"})

        s3_key = f"{analysis_id}/{filename}"
        url = _generate_presigned_url(s3_key)
        return _response(302, {}, headers={"Location": url})

    except Exception as e:
        return _response(500, {"error": str(e)})


def _save_status(analysis_id, data):
    s3_client.put_object(
        Bucket=OUTPUTS_BUCKET,
        Key=f"{analysis_id}/status.json",
        Body=json.dumps(data),
        ContentType="application/json",
    )


def _get_status(analysis_id):
    try:
        response = s3_client.get_object(
            Bucket=OUTPUTS_BUCKET,
            Key=f"{analysis_id}/status.json",
        )
        return json.loads(response["Body"].read())
    except s3_client.exceptions.NoSuchKey:
        return None


def _generate_presigned_url(s3_key):
    return s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": OUTPUTS_BUCKET, "Key": s3_key},
        ExpiresIn=3600,
    )


def _response(status_code, body, headers=None):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json", **(headers or {})},
        "body": json.dumps(body),
    }
