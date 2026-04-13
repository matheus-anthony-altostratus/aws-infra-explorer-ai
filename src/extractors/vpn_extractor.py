from models.infra_model import VPNGateway, CustomerGateway, VPNConnection


class VPNExtractor:

    def __init__(self, session):
        self.ec2_client = session.get_client('ec2')

    def extract_vpn_gateways(self) -> list[VPNGateway]:
        response = self.ec2_client.describe_vpn_gateways()
        vgws = []

        for vgw_data in response["VpnGateways"]:
            tags = {tag["Key"]: tag["Value"] for tag in vgw_data.get("Tags", [])}

            vpc_id = ""
            for att in vgw_data.get("VpcAttachments", []):
                if att.get("State") == "attached":
                    vpc_id = att["VpcId"]
                    break

            vgw = VPNGateway(
                resource_id=vgw_data["VpnGatewayId"],
                name=tags.get("Name"),
                tags=tags,
                vpc_id=vpc_id,
                state=vgw_data.get("State", ""),
                amazon_asn=vgw_data.get("AmazonSideAsn", 0),
            )
            vgws.append(vgw)

        return vgws

    def extract_customer_gateways(self) -> list[CustomerGateway]:
        response = self.ec2_client.describe_customer_gateways()
        cgws = []

        for cgw_data in response["CustomerGateways"]:
            tags = {tag["Key"]: tag["Value"] for tag in cgw_data.get("Tags", [])}

            cgw = CustomerGateway(
                resource_id=cgw_data["CustomerGatewayId"],
                name=tags.get("Name"),
                tags=tags,
                ip_address=cgw_data.get("IpAddress", ""),
                bgp_asn=cgw_data.get("BgpAsn", ""),
                type=cgw_data.get("Type", ""),
                state=cgw_data.get("State", ""),
            )
            cgws.append(cgw)

        return cgws

    def extract_vpn_connections(self) -> list[VPNConnection]:
        response = self.ec2_client.describe_vpn_connections()
        vpns = []

        for vpn_data in response["VpnConnections"]:
            tags = {tag["Key"]: tag["Value"] for tag in vpn_data.get("Tags", [])}

            vpn = VPNConnection(
                resource_id=vpn_data["VpnConnectionId"],
                name=tags.get("Name"),
                tags=tags,
                vpn_gateway_id=vpn_data.get("VpnGatewayId", ""),
                customer_gateway_id=vpn_data.get("CustomerGatewayId", ""),
                transit_gateway_id=vpn_data.get("TransitGatewayId", ""),
                type=vpn_data.get("Type", ""),
                state=vpn_data.get("State", ""),
                static_routes_only=vpn_data.get("Options", {}).get("StaticRoutesOnly", False),
            )
            vpns.append(vpn)

        return vpns
