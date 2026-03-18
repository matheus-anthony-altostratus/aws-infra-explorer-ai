import json
import os
from dataclasses import asdict

from extractors.vpc_extractor import VPCExtractor
from extractors.igw_extractor import IGWExtractor
from extractors.natgw_extractor import NATGWExtractor
from extractors.sg_extractor import SGExtractor
from extractors.ec2_extractor import EC2Extractor
from extractors.rds_extractor import RDSExtractor
from models.infra_model import InfrastructureData


class InfraOrchestrator:

    def __init__(self, region_name: str):
        self.region_name = region_name

    def collect(self) -> InfrastructureData:
        vpc_extractor = VPCExtractor(region_name=self.region_name)
        igw_extractor = IGWExtractor(region_name=self.region_name)
        natgw_extractor = NATGWExtractor(region_name=self.region_name)
        sg_extractor = SGExtractor(region_name=self.region_name)
        ec2_extractor = EC2Extractor(region_name=self.region_name)
        rds_extractor = RDSExtractor(region_name=self.region_name)

        return InfrastructureData(
            region=self.region_name,
            vpcs=vpc_extractor.extract_vpcs(),
            internet_gateways=igw_extractor.extract_igws(),
            nat_gateways=natgw_extractor.extract_natgws(),
            security_groups=sg_extractor.extract_security_groups(),
            instances=ec2_extractor.extract_instances(),
            rds_instances=rds_extractor.extract_rds_instances(),
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

