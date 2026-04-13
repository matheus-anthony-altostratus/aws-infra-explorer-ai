from models.infra_model import TransitGateway, TGWAttachment, TGWRouteTable, TGWRoute


class TGWExtractor:

    def __init__(self, session):
        self.ec2_client = session.get_client('ec2')

    def _extract_attachments(self, tgw_id: str) -> list[TGWAttachment]:
        paginator = self.ec2_client.get_paginator('describe_transit_gateway_attachments')
        attachments = []

        for page in paginator.paginate(Filters=[{"Name": "transit-gateway-id", "Values": [tgw_id]}]):
            for att_data in page["TransitGatewayAttachments"]:
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
        paginator = self.ec2_client.get_paginator('describe_transit_gateway_route_tables')
        route_tables = []

        for page in paginator.paginate(Filters=[{"Name": "transit-gateway-id", "Values": [tgw_id]}]):
            for rt_data in page["TransitGatewayRouteTables"]:
                tags = {tag["Key"]: tag["Value"] for tag in rt_data.get("Tags", [])}
                rt_id = rt_data["TransitGatewayRouteTableId"]

                routes = []
                try:
                    routes_response = self.ec2_client.search_transit_gateway_routes(
                        TransitGatewayRouteTableId=rt_id,
                        Filters=[{"Name": "state", "Values": ["active", "blackhole"]}],
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
        paginator = self.ec2_client.get_paginator('describe_transit_gateways')
        tgws = []

        for page in paginator.paginate():
            for tgw_data in page["TransitGateways"]:
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
