from models.infra_model import VPCPeering


class PeeringExtractor:

    def __init__(self, session):
        self.ec2_client = session.get_client('ec2')

    def extract_vpc_peerings(self) -> list[VPCPeering]:
        paginator = self.ec2_client.get_paginator('describe_vpc_peering_connections')
        peerings = []

        for page in paginator.paginate():
            for peer_data in page["VpcPeeringConnections"]:
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
