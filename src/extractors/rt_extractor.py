import boto3
from models.infra_model import RouteTable, Route


class RTExtractor:

    def __init__(self, region_name: str = "us-east-1"):
        self.ec2_client = boto3.client('ec2', region_name=region_name)

    def extract_route_tables(self) -> list[RouteTable]:
        response = self.ec2_client.describe_route_tables()
        route_tables = []

        for rt_data in response["RouteTables"]:
            tags = {tag["Key"]: tag["Value"] for tag in rt_data.get("Tags", [])}

            routes = []
            for route_data in rt_data.get("Routes", []):
                target = (
                    route_data.get("GatewayId") or
                    route_data.get("NatGatewayId") or
                    route_data.get("TransitGatewayId") or
                    route_data.get("VpcPeeringConnectionId") or
                    route_data.get("NetworkInterfaceId") or
                    "local"
                )
                route = Route(
                    destination=route_data.get("DestinationCidrBlock", route_data.get("DestinationPrefixListId", "")),
                    target=target,
                    state=route_data.get("State", ""),
                )
                routes.append(route)

            subnet_associations = []
            is_main = False
            for assoc in rt_data.get("Associations", []):
                if assoc.get("Main", False):
                    is_main = True
                elif assoc.get("SubnetId"):
                    subnet_associations.append(assoc["SubnetId"])

            rt = RouteTable(
                resource_id=rt_data["RouteTableId"],
                name=tags.get("Name"),
                tags=tags,
                vpc_id=rt_data.get("VpcId", ""),
                routes=routes,
                subnet_associations=subnet_associations,
                is_main=is_main,
            )
            route_tables.append(rt)

        return route_tables
