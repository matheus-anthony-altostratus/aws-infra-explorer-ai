"""
VPC Extractor

Este módulo se encarga de extraer información de red desde AWS.

Responsabilidades:
1. Consultar AWS usando boto3.
2. Obtener VPCs y Subnets.
3. Convertir los datos de AWS en modelos del sistema.
"""

import boto3
from models.infra_model import VPC, Subnet

class VPCExtractor:
    """ Extractor responsable de recuperar la infraestructura relacionada con la VPC de AWS y convertirla en modelos internos."""

    def __init__(self, region_name: str = "us-east-1"):

        """Initialize the extractor with an EC2 client."""

        self.region_name = region_name
        self.ec2_client = boto3.client('ec2', region_name=region_name)



    def extract_vpcs(self) -> list[VPC]:

        """    Retrieves all VPCs and attaches their subnets.    """

        response = self.ec2_client.describe_vpcs()
        subnet_response = self.ec2_client.describe_subnets()

        vpcs = {}

        for vpc_data in response["Vpcs"]:
            tags = {tag["Key"]: tag["Value"] for tag in vpc_data.get("Tags", [])}
            name = tags.get("Name")
            vpc = VPC(
            resource_id=vpc_data["VpcId"],
            cidr_block=vpc_data["CidrBlock"],
            name=name,
            tags=tags,
            subnets=[]
        )
        vpcs[vpc.resource_id] = vpc

        for subnet_data in subnet_response["Subnets"]:
            subnet = Subnet(
            resource_id=subnet_data["SubnetId"],
            cidr_block=subnet_data["CidrBlock"],
            availability_zone=subnet_data["AvailabilityZone"],
        )
            vpc_id = subnet_data["VpcId"]
            if vpc_id in vpcs:
                vpcs[vpc_id].subnets.append(subnet)

        return list(vpcs.values())


    def extract_subnets(self, vpc_id: str) -> list[Subnet]:

        """Retrieves all subnets from AWS and converts them into Subnet models."""

        response = self.ec2_client.describe_subnets()
        subnets = []
        for subnet_data in response["Subnets"]:
            subnet = Subnet(
            resource_id=subnet_data["SubnetId"],
            cidr_block=subnet_data["CidrBlock"],
            availability_zone=subnet_data["AvailabilityZone"],
        )
        subnets.append(subnet)
        return subnets