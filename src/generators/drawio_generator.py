import xml.etree.ElementTree as ET
from models.infra_model import InfrastructureData


# Estilos AWS para draw.io
STYLES = {
    "vpc": "points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=12;fontStyle=1;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_vpc2;strokeColor=#8C4FFF;fillColor=none;verticalAlign=top;align=left;spacingLeft=30;fontColor=#AAB7B8;dashed=0;",
    "subnet_public": "points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=12;fontStyle=1;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_security_group;strokeColor=#7AA116;fillColor=none;verticalAlign=top;align=left;spacingLeft=30;fontColor=#AAB7B8;dashed=0;",
    "subnet_private": "points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=12;fontStyle=1;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_security_group;strokeColor=#00A4A6;fillColor=none;verticalAlign=top;align=left;spacingLeft=30;fontColor=#AAB7B8;dashed=0;",
    "az": "fillColor=none;strokeColor=#147EBA;dashed=1;verticalAlign=top;fontStyle=1;fontColor=#147EBA;whiteSpace=wrap;html=1;",
    "ec2": "outlineConnect=0;fontColor=#FFFFFF;gradientColor=none;fillColor=#ED7100;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.instance2;",
    "rds": "outlineConnect=0;fontColor=#FFFFFF;gradientColor=none;fillColor=#C925D1;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.rds;",
    "igw": "outlineConnect=0;fontColor=#FFFFFF;gradientColor=none;fillColor=#8C4FFF;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.internet_gateway;",
    "natgw": "outlineConnect=0;fontColor=#FFFFFF;gradientColor=none;fillColor=#8C4FFF;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.nat_gateway;",
    "elb": "outlineConnect=0;fontColor=#FFFFFF;gradientColor=none;fillColor=#8C4FFF;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.elastic_load_balancing;",
    "tgw": "outlineConnect=0;fontColor=#FFFFFF;gradientColor=none;fillColor=#8C4FFF;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.transit_gateway;",
    "vpn_gw": "outlineConnect=0;fontColor=#FFFFFF;gradientColor=none;fillColor=#8C4FFF;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.vpn_gateway;",
    "customer_gw": "outlineConnect=0;fontColor=#FFFFFF;gradientColor=none;fillColor=#8C4FFF;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.customer_gateway;",
    "ecs": "outlineConnect=0;fontColor=#FFFFFF;gradientColor=none;fillColor=#ED7100;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.ecs;",
    "eks": "outlineConnect=0;fontColor=#FFFFFF;gradientColor=none;fillColor=#ED7100;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.eks;",
    "efs": "outlineConnect=0;fontColor=#FFFFFF;gradientColor=none;fillColor=#7AA116;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.efs;",
    "dx": "outlineConnect=0;fontColor=#FFFFFF;gradientColor=none;fillColor=#8C4FFF;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.direct_connect;",
    "eip": "outlineConnect=0;fontColor=#FFFFFF;gradientColor=none;fillColor=#8C4FFF;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.elastic_ip_address;",
    "peering": "outlineConnect=0;fontColor=#FFFFFF;gradientColor=none;fillColor=#8C4FFF;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.peering_connection;",
    "arrow": "edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#232F3E;strokeWidth=2;",
}

# Dimensiones
ICON_SIZE = 48
SUBNET_PADDING = 30
SUBNET_INNER_GAP = 20
AZ_PADDING = 30
VPC_PADDING = 40
VPC_GAP = 60
RESOURCE_GAP = 80


class DrawioGenerator:

    def __init__(self):
        self._id_counter = 1
        self._cells = []
        self._node_id_map = {}

    def _next_id(self) -> str:
        self._id_counter += 1
        return str(self._id_counter)

    def _add_container(self, parent_id: str, label: str, style: str, x: int, y: int, w: int, h: int) -> str:
        cell_id = self._next_id()
        self._cells.append({
            "id": cell_id, "value": label, "style": style,
            "vertex": "1", "parent": parent_id,
            "x": x, "y": y, "width": w, "height": h,
        })
        return cell_id

    def _add_icon(self, parent_id: str, label: str, style: str, x: int, y: int) -> str:
        cell_id = self._next_id()
        self._cells.append({
            "id": cell_id, "value": label, "style": style,
            "vertex": "1", "parent": parent_id,
            "x": x, "y": y, "width": ICON_SIZE, "height": ICON_SIZE,
        })
        return cell_id

    def _add_edge(self, parent_id: str, source_id: str, target_id: str, label: str = "") -> str:
        cell_id = self._next_id()
        self._cells.append({
            "id": cell_id, "value": label, "style": STYLES["arrow"],
            "edge": "1", "parent": parent_id,
            "source": source_id, "target": target_id,
        })
        return cell_id

    def _build_subnet(self, parent_id: str, subnet_data: dict, x: int, y: int) -> tuple[str, int, int]:
        subnet_id = subnet_data["resource_id"]
        is_public = subnet_data["is_public"]
        label = f"{subnet_data['name'] or subnet_id}<br/>{subnet_data['cidr_block']}"
        style = STYLES["subnet_public"] if is_public else STYLES["subnet_private"]

        icons_in_subnet = subnet_data.get("_icons", [])
        icon_count = max(len(icons_in_subnet), 1)

        w = SUBNET_PADDING * 2 + icon_count * ICON_SIZE + (icon_count - 1) * SUBNET_INNER_GAP
        w = max(w, 200)
        h = ICON_SIZE + SUBNET_PADDING * 2 + 20

        container_id = self._add_container(parent_id, label, style, x, y, w, h)
        self._node_id_map[subnet_id] = container_id

        ix = SUBNET_PADDING
        for icon_info in icons_in_subnet:
            icon_cell_id = self._add_icon(container_id, icon_info["label"], icon_info["style"], ix, SUBNET_PADDING + 20)
            self._node_id_map[icon_info["resource_id"]] = icon_cell_id
            ix += ICON_SIZE + SUBNET_INNER_GAP

        return container_id, w, h

    def _build_az(self, parent_id: str, az_name: str, subnets: list, x: int, y: int) -> tuple[str, int, int]:
        az_id = self._add_container(parent_id, az_name, STYLES["az"], x, y, 100, 100)

        sx, sy = AZ_PADDING, AZ_PADDING + 20
        max_w = 0
        for subnet_data in subnets:
            _, sw, sh = self._build_subnet(az_id, subnet_data, sx, sy)
            max_w = max(max_w, sw)
            sy += sh + 15

        az_w = max_w + AZ_PADDING * 2
        az_h = sy + AZ_PADDING - 15

        for cell in self._cells:
            if cell["id"] == az_id:
                cell["width"] = az_w
                cell["height"] = az_h
                break

        return az_id, az_w, az_h

    def _prepare_subnet_icons(self, infra: InfrastructureData):
        subnet_icons = {}

        for inst in infra.instances:
            if inst.subnet_id:
                subnet_icons.setdefault(inst.subnet_id, [])
                label = f"{inst.name or inst.resource_id}<br/>{inst.instance_type}<br/>{inst.state}"
                subnet_icons[inst.subnet_id].append({
                    "resource_id": inst.resource_id, "label": label, "style": STYLES["ec2"],
                })

        for natgw in infra.nat_gateways:
            if natgw.subnet_id:
                subnet_icons.setdefault(natgw.subnet_id, [])
                label = f"NAT GW<br/>{natgw.name or natgw.resource_id}<br/>{natgw.public_ip or ''}"
                subnet_icons[natgw.subnet_id].append({
                    "resource_id": natgw.resource_id, "label": label, "style": STYLES["natgw"],
                })

        return subnet_icons

    def _build_vpc(self, parent_id: str, vpc, subnets_by_az: dict, x: int, y: int) -> tuple[str, int, int]:
        label = f"{vpc.name or vpc.resource_id}<br/>{vpc.cidr_block}"
        vpc_cell_id = self._add_container(parent_id, label, STYLES["vpc"], x, y, 100, 100)
        self._node_id_map[vpc.resource_id] = vpc_cell_id

        ax, ay = VPC_PADDING, VPC_PADDING + 25
        max_h = 0
        for az_name, subnets in subnets_by_az.items():
            _, aw, ah = self._build_az(vpc_cell_id, az_name, subnets, ax, ay)
            ax += aw + 20
            max_h = max(max_h, ah)

        vpc_w = ax + VPC_PADDING - 20
        vpc_h = max_h + VPC_PADDING * 2 + 25

        for cell in self._cells:
            if cell["id"] == vpc_cell_id:
                cell["width"] = vpc_w
                cell["height"] = vpc_h
                break

        return vpc_cell_id, vpc_w, vpc_h

    def _build_igws(self, parent_id: str, infra: InfrastructureData, x: int, y: int) -> int:
        for igw in infra.internet_gateways:
            label = f"IGW<br/>{igw.name or igw.resource_id}"
            icon_id = self._add_icon(parent_id, label, STYLES["igw"], x, y)
            self._node_id_map[igw.resource_id] = icon_id
            x += RESOURCE_GAP
        return x

    def _build_external_resources(self, parent_id: str, infra: InfrastructureData, x: int, y: int) -> int:
        for cgw in infra.customer_gateways:
            label = f"Customer GW<br/>{cgw.ip_address}<br/>ASN: {cgw.bgp_asn}"
            icon_id = self._add_icon(parent_id, label, STYLES["customer_gw"], x, y)
            self._node_id_map[cgw.resource_id] = icon_id
            x += RESOURCE_GAP

        for dx in infra.direct_connect_connections:
            label = f"Direct Connect<br/>{dx.name or dx.resource_id}<br/>{dx.bandwidth}"
            icon_id = self._add_icon(parent_id, label, STYLES["dx"], x, y)
            self._node_id_map[dx.resource_id] = icon_id
            x += RESOURCE_GAP

        return x

    def _build_connections(self, parent_id: str, infra: InfrastructureData):
        for igw in infra.internet_gateways:
            igw_node = self._node_id_map.get(igw.resource_id)
            vpc_node = self._node_id_map.get(igw.vpc_id)
            if igw_node and vpc_node:
                self._add_edge(parent_id, igw_node, vpc_node)

        for natgw in infra.nat_gateways:
            natgw_node = self._node_id_map.get(natgw.resource_id)
            igw_for_vpc = next((i for i in infra.internet_gateways if i.vpc_id == natgw.vpc_id), None)
            if natgw_node and igw_for_vpc:
                igw_node = self._node_id_map.get(igw_for_vpc.resource_id)
                if igw_node:
                    self._add_edge(parent_id, natgw_node, igw_node)

        for vpn in infra.vpn_connections:
            vpn_gw_node = self._node_id_map.get(vpn.vpn_gateway_id)
            cgw_node = self._node_id_map.get(vpn.customer_gateway_id)
            if vpn_gw_node and cgw_node:
                self._add_edge(parent_id, vpn_gw_node, cgw_node)

        for peering in infra.vpc_peerings:
            req_node = self._node_id_map.get(peering.requester_vpc_id)
            acc_node = self._node_id_map.get(peering.accepter_vpc_id)
            if req_node and acc_node:
                self._add_edge(parent_id, req_node, acc_node, "Peering")

    def generate(self, infra: InfrastructureData) -> str:
        root_id = "1"
        subnet_icons = self._prepare_subnet_icons(infra)

        for vpc in infra.vpcs:
            for subnet in vpc.subnets:
                subnet._icons = subnet_icons.get(subnet.resource_id, [])

        igw_x = self._build_igws(root_id, infra, 40, 20)
        self._build_external_resources(root_id, infra, igw_x + 40, 20)

        vx, vy = 40, 120
        for vpc in infra.vpcs:
            subnets_by_az = {}
            for subnet in vpc.subnets:
                az = subnet.availability_zone
                subnets_by_az.setdefault(az, [])
                subnet_data = {
                    "resource_id": subnet.resource_id,
                    "name": subnet.name,
                    "cidr_block": subnet.cidr_block,
                    "is_public": subnet.is_public,
                    "_icons": getattr(subnet, "_icons", []),
                }
                subnets_by_az[az].append(subnet_data)

            _, vpc_w, vpc_h = self._build_vpc(root_id, vpc, subnets_by_az, vx, vy)
            vy += vpc_h + VPC_GAP

        self._build_connections(root_id, infra)

        return self._to_xml()

    def _to_xml(self) -> str:
        mxfile = ET.Element("mxfile")
        diagram = ET.SubElement(mxfile, "diagram", name="AWS Architecture")
        model = ET.SubElement(diagram, "mxGraphModel")
        root = ET.SubElement(model, "root")

        ET.SubElement(root, "mxCell", id="0")
        ET.SubElement(root, "mxCell", id="1", parent="0")

        for cell in self._cells:
            attrs = {"id": cell["id"], "value": cell.get("value", ""), "style": cell.get("style", "")}

            if "vertex" in cell:
                attrs["vertex"] = cell["vertex"]
            if "edge" in cell:
                attrs["edge"] = cell["edge"]
            if "parent" in cell:
                attrs["parent"] = cell["parent"]
            if "source" in cell:
                attrs["source"] = cell["source"]
            if "target" in cell:
                attrs["target"] = cell["target"]

            mx_cell = ET.SubElement(root, "mxCell", **attrs)

            if "x" in cell:
                ET.SubElement(mx_cell, "mxGeometry",
                    x=str(cell["x"]), y=str(cell["y"]),
                    width=str(cell["width"]), height=str(cell["height"]),
                    **{"as": "geometry"})
            elif "edge" in cell:
                ET.SubElement(mx_cell, "mxGeometry", relative="1", **{"as": "geometry"})

        ET.indent(mxfile, space="  ")
        return ET.tostring(mxfile, encoding="unicode", xml_declaration=True)
