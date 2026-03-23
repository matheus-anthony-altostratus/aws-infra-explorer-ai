import boto3
from models.infra_model import VPCPeering


class PeeringExtractor:

    def __init__(self, region_name: str = "us-east-1"):
        self.ec2_client = boto3.client('ec2', region_name=region_name)

    def extract_vpc_peerings(self) -> list[VPCPeering]:
        response = self.ec2_client.describe_vpc_peering_connections()
        peerings = []

        for peer_data in response["VpcPeeringConnections"]:
            tags = {tag["Key"]: tag["Value"] for tag in peer_data.get("Tags", [])}

            requester = peer_data.get("RequesterVpcInfo", {})
            accepter = peer_data.get("AccepterVpcInfo", {})

            peering = VPCPeering(
                resource_id=peer_data["VpcPeeringConnectionId"],
                name=tags.get("Name"),
                tags=tags,
                requester_vpc_id=requester.get("VpcId", ""),
                requester_cidr=requester.get("CidrBlock", ""),
                accepter_vpc_id=accepter.get("VpcId", ""),
                accepter_cidr=accepter.get("CidrBlock", ""),
                state=peer_data.get("Status", {}).get("Code", ""),
            )
            peerings.append(peering)

        return peerings
