import sys
import os
import json
import markdown

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

from core.session_manager import SessionManager
from core.orchestrator import InfraOrchestrator

app = FastAPI(title="AWS Infra Explorer AI")

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.post("/analyze", response_class=HTMLResponse)
async def analyze(
    request: Request,
    auth_mode: str = Form(...),
    aws_access_key_id: str = Form(""),
    aws_secret_access_key: str = Form(""),
    account_id: str = Form(""),
    region: str = Form(...),
):
    try:
        if auth_mode == "assume_role":
            if not account_id or not account_id.strip().isdigit() or len(account_id.strip()) != 12:
                raise ValueError("El Account ID debe ser un número de 12 dígitos.")
            role_arn = f"arn:aws:iam::{account_id.strip()}:role/cct_role_read_only"
            session = SessionManager(region_name=region, role_arn=role_arn)
        else:
            if not aws_access_key_id or not aws_secret_access_key:
                raise ValueError("Access Key ID y Secret Access Key son obligatorios.")
            session = SessionManager(
                region_name=region,
                aws_access_key_id=aws_access_key_id.strip(),
                aws_secret_access_key=aws_secret_access_key.strip(),
            )

        orchestrator = InfraOrchestrator(session=session)

        # Extracción
        infra = orchestrator.collect()
        infra_path = orchestrator.export_to_json(infra, output_dir=os.path.join(PROJECT_ROOT, "outputs"))

        # Conteo de recursos
        resource_summary = _build_summary(infra)

        # Reportes Bedrock
        generator_bedrock = __import__("generators.bedrock_generator", fromlist=["BedrockGenerator"])
        bedrock = generator_bedrock.BedrockGenerator(region_name=region, prompts_dir=os.path.join(PROJECT_ROOT, "prompts"))

        report = bedrock.generate_report(infra)
        report_paths = bedrock.export_report(report, region, output_dir=os.path.join(PROJECT_ROOT, "outputs"))

        # Diagrama draw.io
        drawio_path = orchestrator.generate_drawio(infra, output_dir=os.path.join(PROJECT_ROOT, "outputs"))

        # Convertir markdown a HTML
        doc_html = markdown.markdown(report.documentation, extensions=["tables", "fenced_code"])
        sug_html = markdown.markdown(report.suggestions, extensions=["tables", "fenced_code"])

        return templates.TemplateResponse(request, "results.html", {
            "region": region,
            "summary": resource_summary,
            "documentation_html": doc_html,
            "suggestions_html": sug_html,
            "infra_path": infra_path,
            "doc_path": report_paths["documentation"],
            "sug_path": report_paths["suggestions"],
            "drawio_path": drawio_path,
        })

    except Exception as e:
        return templates.TemplateResponse(request, "index.html", {
            "error": str(e),
        })


def _build_summary(infra) -> str:
    parts = []
    counts = [
        ("VPCs", len(infra.vpcs)),
        ("Subnets", sum(len(v.subnets) for v in infra.vpcs)),
        ("EC2", len(infra.instances)),
        ("RDS", len(infra.rds_instances)),
        ("Security Groups", len(infra.security_groups)),
        ("Load Balancers", len(infra.load_balancers)),
        ("ECS Clusters", len(infra.ecs_clusters)),
        ("EKS Clusters", len(infra.eks_clusters)),
    ]
    for name, count in counts:
        if count > 0:
            parts.append(f"{count} {name}")
    return ", ".join(parts) if parts else "No se encontraron recursos"


@app.get("/download/{filename}")
async def download(filename: str):
    filepath = os.path.join(PROJECT_ROOT, "outputs", filename)
    if os.path.exists(filepath):
        return FileResponse(filepath, filename=filename)
    return HTMLResponse("Archivo no encontrado", status_code=404)
