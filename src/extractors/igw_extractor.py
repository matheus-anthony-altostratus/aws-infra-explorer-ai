from models.infra_model import InternetGateway


class IGWExtractor:

    def __init__(self, session):
        self.ec2_client = session.get_client('ec2')

    def extract_igws(self) -> list[InternetGateway]:
        paginator = self.ec2_client.get_paginator('describe_internet_gateways')
        igws = []

        for page in paginator.paginate():
            for igw_data in page["InternetGateways"]:
                tags = {tag["Key"]: tag["Value"] for tag in igw_data.get("Tags", [])}
                attachments = igw_data.get("Attachments", [])
                vpc_id = attachments[0]["VpcId"] if attachments else ""

                igw = InternetGateway(
                    resource_id=igw_data["InternetGatewayId"],
                    name=tags.get("Name"),
                    tags=tags,
                    vpc_id=vpc_id,
                )
                igws.append(igw)

        return igws
