import boto3
from models.infra_model import InternetGateway


class IGWExtractor:

    def __init__(self, region_name: str = "us-east-1"):
        self.ec2_client = boto3.client('ec2', region_name=region_name)

    def extract_igws(self) -> list[InternetGateway]:
        response = self.ec2_client.describe_internet_gateways()
        igws = []

        for igw_data in response["InternetGateways"]:
            tags = {tag["Key"]: tag["Value"] for tag in igw_data.get("Tags", [])}

            # Un IGW puede estar attached a una VPC o no
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
