from models.infra_model import Instance


class EC2Extractor:

    def __init__(self, session):
        self.ec2_client = session.get_client('ec2')

    def extract_instances(self) -> list[Instance]:
        paginator = self.ec2_client.get_paginator('describe_instances')
        instances = []

        for page in paginator.paginate():
            for reservation in page["Reservations"]:
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
