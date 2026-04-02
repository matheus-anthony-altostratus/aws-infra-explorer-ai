import json
import os
import boto3
from dataclasses import asdict
from models.infra_model import InfrastructureData, GeneratedReport


class BedrockGenerator:

    def __init__(self, region_name: str = "eu-west-1", prompts_dir: str = "prompts"):
        self.bedrock_client = boto3.client("bedrock-runtime", region_name=region_name)
        self.model_id = "eu.anthropic.claude-sonnet-4-20250514-v1:0"
        self.prompts_dir = prompts_dir

    def _invoke(self, prompt: str) -> str:
        response = self.bedrock_client.invoke_model(
            modelId=self.model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 16384,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            }),
        )

        result = json.loads(response["body"].read())
        return result["content"][0]["text"]

    def _load_prompt(self, filename: str, infra: InfrastructureData) -> str:
        prompt_path = os.path.join(self.prompts_dir, filename)
        with open(prompt_path, "r") as f:
            template = f.read()

        infra_json = json.dumps(asdict(infra), indent=2, default=str)
        return template.replace("{infrastructure_json}", infra_json)

    def generate_report(self, infra: InfrastructureData) -> GeneratedReport:
        report = GeneratedReport()

        tasks = {
            "documentation": ("Generando documentación técnica...", "documentation_prompt.txt"),
            "suggestions": ("Generando sugerencias de mejora...", "suggestions_prompt.txt"),
        }

        for field, (message, prompt_file) in tasks.items():
            try:
                print(message)
                result = self._invoke(self._load_prompt(prompt_file, infra))
                setattr(report, field, result)
            except Exception as e:
                print(f"  Error al generar {field}: {e}")
                setattr(report, field, f"Error: No se pudo generar este reporte. Detalle: {e}")

        return report

    def export_report(self, report: GeneratedReport, region: str, output_dir: str = "outputs") -> dict:
        os.makedirs(output_dir, exist_ok=True)
        paths = {}

        doc_path = os.path.join(output_dir, f"documentation_{region}.md")
        with open(doc_path, "w") as f:
            f.write(report.documentation)
        paths["documentation"] = doc_path

        suggestions_path = os.path.join(output_dir, f"suggestions_{region}.md")
        with open(suggestions_path, "w") as f:
            f.write(report.suggestions)
        paths["suggestions"] = suggestions_path

        return paths
