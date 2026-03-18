import boto3
from models.infra_model import Instance


class EC2Extractor:

    def __init__(self, region_name: str = "us-east-1"):
        self.ec2_client = boto3.client('ec2', region_name=region_name)

    def extract_instances(self) -> list[Instance]:
        response = self.ec2_client.describe_instances()
        instances = []

        for reservation in response["Reservations"]:
            for instance_data in reservation["Instances"]:
                tags = {tag["Key"]: tag["Value"] for tag in instance_data.get("Tags", [])}

                instance = Instance(
                    resource_id=instance_data["InstanceId"],
                    name=tags.get("Name"),
                    tags=tags,
                    instance_type=instance_data.get("InstanceType", ""),
                    state=instance_data.get("State", {}).get("Name", ""),
                    vpc_id=instance_data.get("VpcId", ""),
                    subnet_id=instance_data.get("SubnetId", ""),
                    security_groups=[sg["GroupId"] for sg in instance_data.get("SecurityGroups", [])],
                    public_ip=instance_data.get("PublicIpAddress"),
                    private_ip=instance_data.get("PrivateIpAddress"),
                )
                instances.append(instance)

        return instances
