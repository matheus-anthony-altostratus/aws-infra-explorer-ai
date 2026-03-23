import boto3
from models.infra_model import TransitGateway, TGWAttachment, TGWRouteTable, TGWRoute


class TGWExtractor:

    def __init__(self, region_name: str = "us-east-1"):
        self.ec2_client = boto3.client('ec2', region_name=region_name)

    def _extract_attachments(self, tgw_id: str) -> list[TGWAttachment]:
        response = self.ec2_client.describe_transit_gateway_attachments(
            Filters=[{"Name": "transit-gateway-id", "Values": [tgw_id]}]
        )
        attachments = []

        for att_data in response["TransitGatewayAttachments"]:
            tags = {tag["Key"]: tag["Value"] for tag in att_data.get("Tags", [])}
            att = TGWAttachment(
                resource_id=att_data["TransitGatewayAttachmentId"],
                name=tags.get("Name"),
                tags=tags,
                tgw_id=tgw_id,
                resource_type=att_data.get("ResourceType", ""),
                resource_id_ref=att_data.get("ResourceId", ""),
                state=att_data.get("State", ""),
            )
            attachments.append(att)

        return attachments

    def _extract_route_tables(self, tgw_id: str) -> list[TGWRouteTable]:
        response = self.ec2_client.describe_transit_gateway_route_tables(
            Filters=[{"Name": "transit-gateway-id", "Values": [tgw_id]}]
        )
        route_tables = []

        for rt_data in response["TransitGatewayRouteTables"]:
            tags = {tag["Key"]: tag["Value"] for tag in rt_data.get("Tags", [])}
            rt_id = rt_data["TransitGatewayRouteTableId"]

            routes = []
            try:
                routes_response = self.ec2_client.search_transit_gateway_routes(
                    TransitGatewayRouteTableId=rt_id,
                    Filters=[{"Name": "state", "Values": ["active", "blackhole"]}]
                )
                for route_data in routes_response.get("Routes", []):
                    attachments = route_data.get("TransitGatewayAttachments", [])
                    target_id = attachments[0]["TransitGatewayAttachmentId"] if attachments else ""

                    route = TGWRoute(
                        destination=route_data.get("DestinationCidrBlock", ""),
                        target_attachment_id=target_id,
                        state=route_data.get("State", ""),
                        route_type=route_data.get("Type", ""),
                    )
                    routes.append(route)
            except Exception:
                pass

            rt = TGWRouteTable(
                resource_id=rt_id,
                name=tags.get("Name"),
                tags=tags,
                tgw_id=tgw_id,
                routes=routes,
            )
            route_tables.append(rt)

        return route_tables

    def extract_transit_gateways(self) -> list[TransitGateway]:
        response = self.ec2_client.describe_transit_gateways()
        tgws = []

        for tgw_data in response["TransitGateways"]:
            tags = {tag["Key"]: tag["Value"] for tag in tgw_data.get("Tags", [])}
            tgw_id = tgw_data["TransitGatewayId"]

            tgw = TransitGateway(
                resource_id=tgw_id,
                name=tags.get("Name"),
                tags=tags,
                amazon_asn=tgw_data.get("Options", {}).get("AmazonSideAsn", 0),
                state=tgw_data.get("State", ""),
                attachments=self._extract_attachments(tgw_id),
                route_tables=self._extract_route_tables(tgw_id),
            )
            tgws.append(tgw)

        return tgws
