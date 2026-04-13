from models.infra_model import NATGateway


class NATGWExtractor:

    def __init__(self, session):
        self.ec2_client = session.get_client('ec2')

    def extract_natgws(self) -> list[NATGateway]:
        paginator = self.ec2_client.get_paginator('describe_nat_gateways')
        natgws = []

        for page in paginator.paginate():
            for natgw_data in page["NatGateways"]:
                tags = {tag["Key"]: tag["Value"] for tag in natgw_data.get("Tags", [])}
                public_ip = ""
                for addr in natgw_data.get("NatGatewayAddresses", []):
                    if addr.get("PublicIp"):
                        public_ip = addr["PublicIp"]
                        break

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
