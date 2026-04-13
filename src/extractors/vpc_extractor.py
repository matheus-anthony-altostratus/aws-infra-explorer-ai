from models.infra_model import VPC, Subnet


class VPCExtractor:

    def __init__(self, session):
        self.ec2_client = session.get_client('ec2')

    def extract_vpcs(self) -> list[VPC]:
        paginator = self.ec2_client.get_paginator('describe_vpcs')
        subnet_paginator = self.ec2_client.get_paginator('describe_subnets')

        vpcs = {}
        for page in paginator.paginate():
            for vpc_data in page["Vpcs"]:
                tags = {tag["Key"]: tag["Value"] for tag in vpc_data.get("Tags", [])}
                vpc = VPC(
                    resource_id=vpc_data["VpcId"],
                    cidr_block=vpc_data["CidrBlock"],
                    name=tags.get("Name"),
                    tags=tags,
                    subnets=[],
                )
                vpcs[vpc.resource_id] = vpc

        for page in subnet_paginator.paginate():
            for subnet_data in page["Subnets"]:
                subnet_tags = {tag["Key"]: tag["Value"] for tag in subnet_data.get("Tags", [])}
                subnet = Subnet(
                    resource_id=subnet_data["SubnetId"],
                    cidr_block=subnet_data["CidrBlock"],
                    availability_zone=subnet_data["AvailabilityZone"],
                    name=subnet_tags.get("Name"),
                    tags=subnet_tags,
                )
                vpc_id = subnet_data["VpcId"]
                if vpc_id in vpcs:
                    vpcs[vpc_id].subnets.append(subnet)

        return list(vpcs.values())
