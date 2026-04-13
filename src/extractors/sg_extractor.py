from models.infra_model import SecurityGroup, SecurityGroupRule


class SGExtractor:

    def __init__(self, session):
        self.ec2_client = session.get_client('ec2')

    def extract_security_groups(self) -> list[SecurityGroup]:
        paginator = self.ec2_client.get_paginator('describe_security_groups')
        sgs = []

        for page in paginator.paginate():
            for sg_data in page["SecurityGroups"]:
                tags = {tag["Key"]: tag["Value"] for tag in sg_data.get("Tags", [])}

                ingress_rules = []
                for rule in sg_data.get("IpPermissions", []):
                    ingress_rules.append(SecurityGroupRule(
                        protocol=rule.get("IpProtocol", ""),
                        from_port=rule.get("FromPort", -1),
                        to_port=rule.get("ToPort", -1),
                        cidr_blocks=[r["CidrIp"] for r in rule.get("IpRanges", [])],
                    ))

                egress_rules = []
                for rule in sg_data.get("IpPermissionsEgress", []):
                    egress_rules.append(SecurityGroupRule(
                        protocol=rule.get("IpProtocol", ""),
                        from_port=rule.get("FromPort", -1),
                        to_port=rule.get("ToPort", -1),
                        cidr_blocks=[r["CidrIp"] for r in rule.get("IpRanges", [])],
                    ))

                sg = SecurityGroup(
                    resource_id=sg_data["GroupId"],
                    name=sg_data.get("GroupName"),
                    tags=tags,
                    description=sg_data.get("Description"),
                    ingress_rules=ingress_rules,
                    egress_rules=egress_rules,
                )
                sgs.append(sg)

        return sgs
