from models.infra_model import RouteTable, Route


class RTExtractor:

    def __init__(self, session):
        self.ec2_client = session.get_client('ec2')

    def extract_route_tables(self) -> list[RouteTable]:
        paginator = self.ec2_client.get_paginator('describe_route_tables')
        rts = []

        for page in paginator.paginate():
            for rt_data in page["RouteTables"]:
                tags = {tag["Key"]: tag["Value"] for tag in rt_data.get("Tags", [])}

                routes = []
                for route_data in rt_data.get("Routes", []):
                    target = (
                        route_data.get("GatewayId") or
                        route_data.get("NatGatewayId") or
                        route_data.get("TransitGatewayId") or
                        route_data.get("VpcPeeringConnectionId") or
                        route_data.get("NetworkInterfaceId") or
                        ""
                    )
                    route = Route(
                        destination=route_data.get("DestinationCidrBlock") or route_data.get("DestinationPrefixListId", ""),
                        target=target,
                        state=route_data.get("State", ""),
                    )
                    routes.append(route)

                subnet_associations = []
                is_main = False
                for assoc in rt_data.get("Associations", []):
                    if assoc.get("Main"):
                        is_main = True
                    elif assoc.get("SubnetId"):
                        subnet_associations.append(assoc["SubnetId"])

                rt = RouteTable(
                    resource_id=rt_data["RouteTableId"],
                    name=tags.get("Name"),
                    tags=tags,
                    vpc_id=rt_data.get("VpcId", ""),
                    subnet_associations=subnet_associations,
                    routes=routes,
                    is_main=is_main,
                )
                rts.append(rt)

        return rts
