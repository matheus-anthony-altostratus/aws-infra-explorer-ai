from models.infra_model import LoadBalancer, Listener, TargetGroup


class ELBExtractor:

    def __init__(self, session):
        self.elbv2_client = session.get_client('elbv2')

    def extract_load_balancers(self) -> list[LoadBalancer]:
        paginator = self.elbv2_client.get_paginator('describe_load_balancers')
        lbs = []

        for page in paginator.paginate():
            for lb_data in page["LoadBalancers"]:
                lb_arn = lb_data["LoadBalancerArn"]

                listeners = []
                try:
                    listener_paginator = self.elbv2_client.get_paginator('describe_listeners')
                    for listener_page in listener_paginator.paginate(LoadBalancerArn=lb_arn):
                        for listener_data in listener_page["Listeners"]:
                            target_group_arn = ""
                            for action in listener_data.get("DefaultActions", []):
                                if action.get("TargetGroupArn"):
                                    target_group_arn = action["TargetGroupArn"]
                                    break

                            listener = Listener(
                                port=listener_data.get("Port", 0),
                                protocol=listener_data.get("Protocol", ""),
                                target_group_arn=target_group_arn,
                            )
                            listeners.append(listener)
                except Exception:
                    pass

                lb = LoadBalancer(
                    resource_id=lb_arn,
                    name=lb_data.get("LoadBalancerName"),
                    type=lb_data.get("Type", ""),
                    scheme=lb_data.get("Scheme", ""),
                    dns_name=lb_data.get("DNSName", ""),
                    vpc_id=lb_data.get("VpcId", ""),
                    availability_zones=[az["ZoneName"] for az in lb_data.get("AvailabilityZones", [])],
                    security_groups=lb_data.get("SecurityGroups", []),
                    listeners=listeners,
                )
                lbs.append(lb)

        return lbs

    def extract_target_groups(self) -> list[TargetGroup]:
        paginator = self.elbv2_client.get_paginator('describe_target_groups')
        tgs = []

        for page in paginator.paginate():
            for tg_data in page["TargetGroups"]:
                tg_arn = tg_data["TargetGroupArn"]

                targets = []
                try:
                    health_response = self.elbv2_client.describe_target_health(TargetGroupArn=tg_arn)
                    for target in health_response["TargetHealthDescriptions"]:
                        targets.append(target["Target"]["Id"])
                except Exception:
                    pass

                tg = TargetGroup(
                    resource_id=tg_arn,
                    name=tg_data.get("TargetGroupName"),
                    port=tg_data.get("Port", 0),
                    protocol=tg_data.get("Protocol", ""),
                    vpc_id=tg_data.get("VpcId", ""),
                    target_type=tg_data.get("TargetType", ""),
                    targets=targets,
                )
                tgs.append(tg)

        return tgs
