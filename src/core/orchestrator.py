import json
import os
from dataclasses import asdict

from extractors.vpc_extractor import VPCExtractor
from extractors.igw_extractor import IGWExtractor
from extractors.natgw_extractor import NATGWExtractor
from extractors.sg_extractor import SGExtractor
from extractors.ec2_extractor import EC2Extractor
from extractors.rds_extractor import RDSExtractor
from generators.bedrock_generator import BedrockGenerator
from models.infra_model import InfrastructureData


class InfraOrchestrator:

    def __init__(self, region_name: str):
        self.region_name = region_name

    def collect(self) -> InfrastructureData:
        extractors = {
            "VPCs": lambda: VPCExtractor(self.region_name).extract_vpcs(),
            "Internet Gateways": lambda: IGWExtractor(self.region_name).extract_igws(),
            "NAT Gateways": lambda: NATGWExtractor(self.region_name).extract_natgws(),
            "Security Groups": lambda: SGExtractor(self.region_name).extract_security_groups(),
            "EC2 Instances": lambda: EC2Extractor(self.region_name).extract_instances(),
            "RDS Instances": lambda: RDSExtractor(self.region_name).extract_rds_instances(),
        }

        results = {}
        for name, extract_fn in extractors.items():
            try:
                results[name] = extract_fn()
            except Exception as e:
                print(f"  Advertencia: No se pudo extraer {name}: {e}")
                results[name] = []

        return InfrastructureData(
            region=self.region_name,
            vpcs=results["VPCs"],
            internet_gateways=results["Internet Gateways"],
            nat_gateways=results["NAT Gateways"],
            security_groups=results["Security Groups"],
            instances=results["EC2 Instances"],
            rds_instances=results["RDS Instances"],
        )

    def export_to_json(self, infra: InfrastructureData, output_dir: str = "outputs") -> str:
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"infra_{infra.region}.json")

        data = asdict(infra)

        resource_labels = {
            "vpcs": "VPCs",
            "internet_gateways": "Internet Gateways",
            "nat_gateways": "NAT Gateways",
            "security_groups": "Security Groups",
            "instances": "EC2 Instances",
            "rds_instances": "RDS Instances",
        }

        for key, label in resource_labels.items():
            if not data[key]:
                data[key] = f"No se encontraron recursos de {label}."

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

        return output_path

    def generate_reports(self, infra: InfrastructureData) -> dict:
        generator = BedrockGenerator(region_name=self.region_name)
        report = generator.generate_report(infra)
        paths = generator.export_report(report, infra.region)
        return paths

    def run(self, output_dir: str = "outputs") -> dict:
        print(f"\nExtrayendo infraestructura de la región {self.region_name}...")
        infra = self.collect()
        infra_path = self.export_to_json(infra, output_dir)

        print("Generando reportes con Amazon Bedrock...")
        report_paths = self.generate_reports(infra)

        return {
            "infra_json": infra_path,
            **report_paths,
        }
