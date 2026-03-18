import boto3
from models.infra_model import NATGateway


class NATGWExtractor:

    def __init__(self, region_name: str = "us-east-1"):
        self.ec2_client = boto3.client('ec2', region_name=region_name)

    def extract_natgws(self) -> list[NATGateway]:
        response = self.ec2_client.describe_nat_gateways()
        natgws = []

        for natgw_data in response["NatGateways"]:
            tags = {tag["Key"]: tag["Value"] for tag in natgw_data.get("Tags", [])}

            # La IP pública está dentro de NatGatewayAddresses
            addresses = natgw_data.get("NatGatewayAddresses", [])
            public_ip = addresses[0].get("PublicIp") if addresses else None

            natgw = NATGateway(
                resource_id=natgw_data["NatGatewayId"],
                name=tags.get("Name"),
                tags=tags,
                vpc_id=natgw_data.get("VpcId", ""),
                subnet_id=natgw_data.get("SubnetId", ""),
                public_ip=public_ip,
                state=natgw_data.get("State", ""),
            )
            natgws.append(natgw)

        return natgws
