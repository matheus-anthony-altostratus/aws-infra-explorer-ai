import boto3
from models.infra_model import SecurityGroup, SecurityGroupRule


class SGExtractor:

    def __init__(self, region_name: str = "us-east-1"):
        self.ec2_client = boto3.client('ec2', region_name=region_name)

    def _parse_rules(self, rules_data: list) -> list[SecurityGroupRule]:
        rules = []
        for rule in rules_data:
            sg_rule = SecurityGroupRule(
                protocol=rule.get("IpProtocol", ""),
                from_port=rule.get("FromPort", -1),
                to_port=rule.get("ToPort", -1),
                cidr_blocks=[ip["CidrIp"] for ip in rule.get("IpRanges", [])],
            )
            rules.append(sg_rule)
        return rules

    def extract_security_groups(self) -> list[SecurityGroup]:
        response = self.ec2_client.describe_security_groups()
        sgs = []

        for sg_data in response["SecurityGroups"]:
            tags = {tag["Key"]: tag["Value"] for tag in sg_data.get("Tags", [])}

            sg = SecurityGroup(
                resource_id=sg_data["GroupId"],
                name=tags.get("Name", sg_data.get("GroupName", "")),
                tags=tags,
                description=sg_data.get("Description"),
                ingress_rules=self._parse_rules(sg_data.get("IpPermissions", [])),
                egress_rules=self._parse_rules(sg_data.get("IpPermissionsEgress", [])),
            )
            sgs.append(sg)

        return sgs
