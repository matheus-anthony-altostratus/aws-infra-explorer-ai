import xml.etree.ElementTree as ET
from models.infra_model import InfrastructureData

STYLES = {
    "vpc":            "points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=12;fontStyle=1;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_vpc2;strokeColor=#8C4FFF;fillColor=none;verticalAlign=top;align=left;spacingLeft=30;fontColor=#232F3E;dashed=0;",
    "subnet_public":  "points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=11;fontStyle=0;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_security_group;strokeColor=#7AA116;fillColor=#F6FFED;verticalAlign=top;align=left;spacingLeft=30;fontColor=#232F3E;dashed=0;",
    "subnet_private": "points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=11;fontStyle=0;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_security_group;strokeColor=#00A4A6;fillColor=#E6FFFE;verticalAlign=top;align=left;spacingLeft=30;fontColor=#232F3E;dashed=0;",
    "az":             "fillColor=#F0F7FF;strokeColor=#147EBA;dashed=1;verticalAlign=top;fontStyle=1;fontColor=#147EBA;whiteSpace=wrap;html=1;",
    "ec2":            "outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor=#ED7100;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.instance2;",
    "rds":            "outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor=#C925D1;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.rds;",
    "dynamodb":       "outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor=#C925D1;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.dynamodb;",
    "igw":            "outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor=#8C4FFF;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.internet_gateway;",
    "natgw":          "outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor=#8C4FFF;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.nat_gateway;",
    "elb":            "outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor=#8C4FFF;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.elastic_load_balancing;",
    "tgw":            "outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor=#8C4FFF;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.transit_gateway;",
    "vpn_gw":         "outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor=#8C4FFF;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.vpn_gateway;",
    "customer_gw":    "outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor=#8C4FFF;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.customer_gateway;",
    "ecs":            "outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor=#ED7100;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.ecs;",
    "eks":            "outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor=#ED7100;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.eks;",
    "efs":            "outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor=#7AA116;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.efs;",
    "dx":             "outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor=#8C4FFF;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.direct_connect;",
    "eip":            "outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor=#8C4FFF;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.elastic_ip_address;",
    "peering":        "outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor=#8C4FFF;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.peering_connection;",
    "sg":             "outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor=#DD344C;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.security_group;",
    "arrow":          "rounded=1;orthogonalLoop=1;jettySize=auto;exitX=0.5;exitY=0;exitDx=0;exitDy=0;entryX=0.5;entryY=1;entryDx=0;entryDy=0;edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#6B7280;strokeWidth=1.5;fillColor=#6B7280;fontColor=#374151;fontSize=10;",
    "arrow_loose":    "rounded=1;orthogonalLoop=1;jettySize=auto;edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#6B7280;strokeWidth=1.5;fillColor=#6B7280;fontColor=#374151;fontSize=10;exitX=1;exitY=0.5;exitDx=0;exitDy=0;",
    "label_title":    "text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacingLeft=4;fontSize=15;fontStyle=1;fontColor=#111827;",
    "label_section":  "text;html=1;strokeColor=none;fillColor=#EEF2FF;align=left;verticalAlign=middle;spacingLeft=10;fontSize=12;fontStyle=1;fontColor=#4338CA;rounded=1;",
    "summary_header": "rounded=1;whiteSpace=wrap;html=1;fillColor=#1E3A5F;strokeColor=none;fontColor=#FFFFFF;fontSize=12;fontStyle=1;",
    "summary_cell":   "rounded=1;whiteSpace=wrap;html=1;fillColor=#F9FAFB;strokeColor=#D1D5DB;fontSize=12;fontColor=#111827;",
    "summary_count":  "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#8C4FFF;fontSize=18;fontStyle=1;fontColor=#8C4FFF;",
    "placeholder_box":"rounded=1;whiteSpace=wrap;html=1;fillColor=#F9FAFB;strokeColor=#D1D5DB;dashed=1;fontSize=13;fontColor=#6B7280;verticalAlign=middle;",
    "sg_box":         "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFF5F5;strokeColor=#DD344C;fontSize=11;fontColor=#111827;verticalAlign=top;align=left;spacingLeft=8;spacingTop=6;",
}

ICON_SIZE        = 48
ICON_LABEL_H     = 40
ICON_SLOT_W      = 120   # ancho reservado por icono (icono + label lateral)
ICON_SLOT_H      = ICON_SIZE + ICON_LABEL_H
SUBNET_PADDING   = 24
SUBNET_INNER_GAP = 32
AZ_PADDING       = 24
VPC_PADDING      = 32
VPC_GAP          = 48
SECTION_GAP      = 80
ICONS_PER_ROW    = 6


class _Page:
    """Contexto aislado de IDs y celdas para una sola pestaña."""

    def __init__(self):
        self._counter = 2
        self.cells: list = []
        self.node_map: dict = {}

    def next_id(self) -> str:
        self._counter += 1
        return str(self._counter)

    def add_container(self, parent: str, label: str, style: str,
                      x: int, y: int, w: int, h: int) -> str:
        cid = self.next_id()
        self.cells.append({"id": cid, "value": label, "style": style,
                           "vertex": "1", "parent": parent,
                           "x": x, "y": y, "width": w, "height": h})
        return cid

    def add_icon(self, parent: str, label: str, style: str, x: int, y: int) -> str:
        cid = self.next_id()
        self.cells.append({"id": cid, "value": label, "style": style,
                           "vertex": "1", "parent": parent,
                           "x": x, "y": y, "width": ICON_SIZE, "height": ICON_SIZE})
        return cid

    def add_edge(self, parent: str, source: str, target: str,
                 label: str = "", loose: bool = False) -> str:
        cid = self.next_id()
        self.cells.append({"id": cid, "value": label,
                           "style": STYLES["arrow_loose"] if loose else STYLES["arrow"],
                           "edge": "1", "parent": parent,
                           "source": source, "target": target})
        return cid

    def to_xml_element(self, name: str) -> ET.Element:
        diagram = ET.Element("diagram", name=name)
        model   = ET.SubElement(diagram, "mxGraphModel")
        root    = ET.SubElement(model, "root")
        ET.SubElement(root, "mxCell", id="0")
        ET.SubElement(root, "mxCell", id="1", parent="0")
        for c in self.cells:
            attrs = {"id": c["id"], "value": c.get("value", ""),
                     "style": c.get("style", "")}
            if "vertex" in c: attrs["vertex"] = c["vertex"]
            if "edge"   in c: attrs["edge"]   = c["edge"]
            if "parent" in c: attrs["parent"] = c["parent"]
            if "source" in c: attrs["source"] = c["source"]
            if "target" in c: attrs["target"] = c["target"]
            el = ET.SubElement(root, "mxCell", **attrs)
            if "x" in c:
                ET.SubElement(el, "mxGeometry",
                              x=str(c["x"]), y=str(c["y"]),
                              width=str(c["width"]), height=str(c["height"]),
                              **{"as": "geometry"})
            elif "edge" in c:
                ET.SubElement(el, "mxGeometry", relative="1", **{"as": "geometry"})
        return diagram


class DrawioGenerator:

    # ── Helpers compartidos ───────────────────────────────────────────────────

    def _prepare_subnet_icons(self, infra: InfrastructureData) -> dict:
        subnet_icons: dict = {}
        for inst in infra.instances:
            if inst.subnet_id:
                label = f"{inst.name or inst.resource_id}<br/>{inst.instance_type}"
                subnet_icons.setdefault(inst.subnet_id, []).append(
                    {"resource_id": inst.resource_id, "label": label, "style": STYLES["ec2"]})
        for natgw in infra.nat_gateways:
            if natgw.subnet_id:
                label = f"NAT GW<br/>{natgw.name or natgw.resource_id}"
                subnet_icons.setdefault(natgw.subnet_id, []).append(
                    {"resource_id": natgw.resource_id, "label": label, "style": STYLES["natgw"]})
        return subnet_icons

    def _prepare_subnet_icons_compute_only(self, infra: InfrastructureData) -> dict:
        """Solo EC2 — sin NAT GW — para la pestaña Compute."""
        subnet_icons: dict = {}
        for inst in infra.instances:
            if inst.subnet_id:
                label = f"{inst.name or inst.resource_id}<br/>{inst.instance_type}"
                subnet_icons.setdefault(inst.subnet_id, []).append(
                    {"resource_id": inst.resource_id, "label": label, "style": STYLES["ec2"]})
        return subnet_icons

    def _subnets_by_az(self, vpc, subnet_icons: dict) -> dict:
        result: dict = {}
        for subnet in vpc.subnets:
            result.setdefault(subnet.availability_zone, []).append({
                "resource_id": subnet.resource_id,
                "name":        subnet.name,
                "cidr_block":  subnet.cidr_block,
                "is_public":   subnet.is_public,
                "_icons":      subnet_icons.get(subnet.resource_id, []),
            })
        return result

    def _build_subnet(self, page: _Page, parent: str, subnet_data: dict,
                      x: int, y: int) -> tuple:
        is_public = subnet_data["is_public"]
        label     = f"{subnet_data['name'] or subnet_data['resource_id']}<br/>{subnet_data['cidr_block']}"
        style     = STYLES["subnet_public"] if is_public else STYLES["subnet_private"]
        icons     = subnet_data.get("_icons", [])
        count     = max(len(icons), 1)
        w         = max(SUBNET_PADDING * 2 + count * ICON_SIZE + (count - 1) * SUBNET_INNER_GAP, 220)
        h         = ICON_SLOT_H + SUBNET_PADDING * 2
        cid       = page.add_container(parent, label, style, x, y, w, h)
        page.node_map[subnet_data["resource_id"]] = cid
        ix = SUBNET_PADDING
        for icon in icons:
            iid = page.add_icon(cid, icon["label"], icon["style"], ix, SUBNET_PADDING + 20)
            page.node_map[icon["resource_id"]] = iid
            ix += ICON_SIZE + SUBNET_INNER_GAP
        return cid, w, h

    def _build_az(self, page: _Page, parent: str, az_name: str,
                  subnets: list, x: int, y: int) -> tuple:
        az_id = page.add_container(parent, az_name, STYLES["az"], x, y, 100, 100)
        sx, sy, max_w = AZ_PADDING, AZ_PADDING + 20, 0
        for s in subnets:
            _, sw, sh = self._build_subnet(page, az_id, s, sx, sy)
            max_w = max(max_w, sw)
            sy += sh + 12
        az_w = max_w + AZ_PADDING * 2
        az_h = sy + AZ_PADDING - 12
        for c in page.cells:
            if c["id"] == az_id:
                c["width"], c["height"] = az_w, az_h
                break
        return az_id, az_w, az_h

    def _build_vpc(self, page: _Page, parent: str, vpc,
                   subnets_by_az: dict, x: int, y: int) -> tuple:
        label  = f"{vpc.name or vpc.resource_id}  ·  {vpc.cidr_block}"
        vpc_id = page.add_container(parent, label, STYLES["vpc"], x, y, 100, 100)
        page.node_map[vpc.resource_id] = vpc_id
        ax, ay, max_h = VPC_PADDING, VPC_PADDING + 28, 0
        for az_name, subnets in subnets_by_az.items():
            _, aw, ah = self._build_az(page, vpc_id, az_name, subnets, ax, ay)
            ax += aw + 16
            max_h = max(max_h, ah)
        vpc_w = ax + VPC_PADDING - 16
        vpc_h = max_h + VPC_PADDING * 2 + 28
        for c in page.cells:
            if c["id"] == vpc_id:
                c["width"], c["height"] = vpc_w, vpc_h
                break
        return vpc_id, vpc_w, vpc_h

    def _section_header(self, page: _Page, label: str, x: int, y: int, w: int = 400) -> None:
        page.add_container("1", label, STYLES["label_section"], x, y, w, 28)

    # ── Página 1: Resumen ─────────────────────────────────────────────────────

    def _build_page_summary(self, infra: InfrastructureData) -> _Page:
        page = _Page()
        page.add_container("1", f"☁️  Resumen de infraestructura — {infra.region}",
                           STYLES["label_title"], 20, 20, 700, 36)
        counts = [
            ("VPCs",             len(infra.vpcs)),
            ("Subnets",          sum(len(v.subnets) for v in infra.vpcs)),
            ("EC2 Instances",    len(infra.instances)),
            ("RDS Instances",    len(infra.rds_instances)),
            ("DynamoDB Tables",  len(getattr(infra, "dynamodb_tables", []))),
            ("Load Balancers",   len(infra.load_balancers)),
            ("ECS Clusters",     len(infra.ecs_clusters)),
            ("EKS Clusters",     len(infra.eks_clusters)),
            ("EFS File Systems", len(infra.efs_file_systems)),
            ("Internet GWs",     len(infra.internet_gateways)),
            ("NAT Gateways",     len(infra.nat_gateways)),
            ("Transit GWs",      len(infra.transit_gateways)),
            ("VPN Connections",  len(infra.vpn_connections)),
            ("Direct Connect",   len(infra.direct_connect_connections)),
            ("VPC Peerings",     len(infra.vpc_peerings)),
            ("Elastic IPs",      len(infra.elastic_ips)),
            ("Security Groups",  len(infra.security_groups)),
        ]
        col_w, row_h, cols = 200, 56, 4
        sx, sy = 20, 76
        headers = ["Recurso", "Total", "Recurso", "Total"]
        for ci, h in enumerate(headers):
            page.add_container("1", h, STYLES["summary_header"],
                               sx + ci * col_w, sy, col_w - 4, 28)
        for i, (label, count) in enumerate(counts):
            row = i // 2
            col = (i % 2) * 2
            rx  = sx + col * col_w
            ry  = sy + 32 + row * (row_h + 4)
            page.add_container("1", label,      STYLES["summary_cell"],  rx,          ry, col_w - 4, row_h)
            page.add_container("1", str(count), STYLES["summary_count"], rx + col_w,  ry, col_w - 4, row_h)
        return page

    # ── Página 2: Networking ──────────────────────────────────────────────────

    def _build_page_networking(self, infra: InfrastructureData) -> _Page:
        page         = _Page()
        p            = "1"
        subnet_icons = self._prepare_subnet_icons(infra)

        # IGWs y EIPs en la franja superior
        self._section_header(page, "Internet Gateways & Elastic IPs", 40, 20)
        ix = 40
        for igw in infra.internet_gateways:
            iid = page.add_icon(p, igw.name or igw.resource_id, STYLES["igw"], ix, 60)
            page.node_map[igw.resource_id] = iid
            ix += ICON_SLOT_W
        for eip in infra.elastic_ips:
            iid = page.add_icon(p, f"EIP\n{eip.public_ip}", STYLES["eip"], ix, 60)
            page.node_map[eip.resource_id] = iid
            ix += ICON_SLOT_W

        # VPCs
        vy = 60 + ICON_SLOT_H + 32
        for vpc in infra.vpcs:
            saz = self._subnets_by_az(vpc, subnet_icons)
            if not saz:
                continue
            _, _, vpc_h = self._build_vpc(page, p, vpc, saz, 40, vy)
            vy += vpc_h + VPC_GAP

        # VPC Peerings debajo de las VPCs
        if infra.vpc_peerings:
            self._section_header(page, "VPC Peerings", 40, vy)
            vy += 36
            px = 40
            for peering in infra.vpc_peerings:
                label = f"{peering.resource_id}<br/>{peering.state}"
                iid   = page.add_icon(p, label, STYLES["peering"], px, vy)
                page.node_map[peering.resource_id] = iid
                req = page.node_map.get(peering.requester_vpc_id)
                acc = page.node_map.get(peering.accepter_vpc_id)
                if req: page.add_edge(p, req, iid, "requester", loose=True)
                if acc: page.add_edge(p, acc, iid, "accepter",  loose=True)
                px += ICON_SLOT_W

        # Conexiones IGW → VPC
        for igw in infra.internet_gateways:
            igw_n = page.node_map.get(igw.resource_id)
            vpc_n = page.node_map.get(igw.vpc_id)
            if igw_n and vpc_n:
                page.add_edge(p, igw_n, vpc_n, loose=True)

        return page

    # ── Página 3: Compute ─────────────────────────────────────────────────────

    def _build_page_compute(self, infra: InfrastructureData) -> _Page:
        page         = _Page()
        p            = "1"
        subnet_icons = self._prepare_subnet_icons_compute_only(infra)
        vy           = 20

        # EC2 agrupadas dentro de su VPC/AZ/Subnet
        if infra.instances:
            self._section_header(page, "EC2 Instances", 40, vy)
            vy += 36
            for vpc in infra.vpcs:
                saz = self._subnets_by_az(vpc, subnet_icons)
                saz_filtered = {
                    az: [s for s in subnets if s["_icons"]]
                    for az, subnets in saz.items()
                }
                saz_filtered = {az: s for az, s in saz_filtered.items() if s}
                if not saz_filtered:
                    continue
                _, _, vpc_h = self._build_vpc(page, p, vpc, saz_filtered, 40, vy)
                vy += vpc_h + VPC_GAP

        # ECS
        if infra.ecs_clusters:
            vy += 16
            self._section_header(page, "ECS Clusters", 40, vy)
            vy += 36
            x = 40
            for cluster in infra.ecs_clusters:
                label = f"{cluster.name or cluster.resource_id}<br/>Servicios: {len(cluster.services)}<br/>{cluster.status}"
                page.add_icon(p, label, STYLES["ecs"], x, vy)
                x += ICON_SLOT_W
                if x > 900:
                    x = 40
                    vy += ICON_SLOT_H + 60

        # EKS
        if infra.eks_clusters:
            vy += 16
            self._section_header(page, "EKS Clusters", 40, vy)
            vy += 36
            x = 40
            for cluster in infra.eks_clusters:
                label = f"{cluster.name or cluster.resource_id}<br/>v{cluster.version}<br/>{cluster.status}"
                page.add_icon(p, label, STYLES["eks"], x, vy)
                x += ICON_SLOT_W
                if x > 900:
                    x = 40
                    vy += ICON_SLOT_H + 60

        return page

    # ── Página 4: Database & Storage ─────────────────────────────────────────

    def _build_page_database(self, infra: InfrastructureData) -> _Page:
        page = _Page()
        p    = "1"
        vy   = 20

        # RDS
        if infra.rds_instances:
            self._section_header(page, "RDS Instances", 40, vy)
            vy += 36
            x = 40
            for rds in infra.rds_instances:
                multi = "Multi-AZ" if rds.multi_az else "Single-AZ"
                label = f"{rds.name or rds.resource_id}<br/>{rds.engine} {rds.engine_version}<br/>{multi}"
                page.add_icon(p, label, STYLES["rds"], x, vy)
                x += ICON_SLOT_W
                if x > 900:
                    x = 40
                    vy += ICON_SLOT_H + 60
            vy += ICON_SLOT_H + SECTION_GAP

        # DynamoDB
        dynamodb_tables = getattr(infra, "dynamodb_tables", [])
        if dynamodb_tables:
            self._section_header(page, "DynamoDB Tables", 40, vy)
            vy += 36
            x = 40
            for table in dynamodb_tables:
                label = f"{table.name or table.resource_id}<br/>{table.billing_mode}<br/>{table.status}"
                page.add_icon(p, label, STYLES["dynamodb"], x, vy)
                x += ICON_SLOT_W
                if x > 900:
                    x = 40
                    vy += ICON_SLOT_H + 60
            vy += ICON_SLOT_H + SECTION_GAP

        # EFS
        if infra.efs_file_systems:
            self._section_header(page, "EFS File Systems", 40, vy)
            vy += 36
            x = 40
            for efs in infra.efs_file_systems:
                enc   = "Encrypted" if efs.encrypted else "Not encrypted"
                label = f"{efs.name or efs.resource_id}<br/>{efs.performance_mode}<br/>{enc}"
                page.add_icon(p, label, STYLES["efs"], x, vy)
                x += ICON_SLOT_W
                if x > 900:
                    x = 40
                    vy += ICON_SLOT_H + 60
            vy += ICON_SLOT_H + SECTION_GAP

        # Load Balancers
        if infra.load_balancers:
            self._section_header(page, "Load Balancers", 40, vy)
            vy += 36
            x = 40
            for lb in infra.load_balancers:
                dns   = lb.dns_name[:28] + "…" if len(lb.dns_name) > 28 else lb.dns_name
                label = f"{lb.name or lb.resource_id}<br/>{lb.type} · {lb.scheme}<br/>{dns}"
                page.add_icon(p, label, STYLES["elb"], x, vy)
                x += ICON_SLOT_W
                if x > 900:
                    x = 40
                    vy += ICON_SLOT_H + 60

        return page

    # ── Página 5: Connectivity ────────────────────────────────────────────────

    def _build_page_connectivity(self, infra: InfrastructureData) -> _Page:
        page = _Page()
        p    = "1"
        vy   = 20

        # Transit Gateways
        if infra.transit_gateways:
            self._section_header(page, "Transit Gateways", 40, vy)
            vy += 36
            x = 40
            for tgw in infra.transit_gateways:
                label = f"{tgw.name or tgw.resource_id}<br/>ASN: {tgw.amazon_asn}<br/>{tgw.state}"
                tgw_id = page.add_icon(p, label, STYLES["tgw"], x, vy)
                page.node_map[tgw.resource_id] = tgw_id
                x += ICON_SLOT_W
            vy += ICON_SLOT_H + SECTION_GAP

        # VPN
        if infra.vpn_gateways or infra.customer_gateways:
            self._section_header(page, "VPN", 40, vy)
            vy += 36
            x = 40
            for vgw in infra.vpn_gateways:
                label = f"VPN GW<br/>{vgw.name or vgw.resource_id}<br/>{vgw.state}"
                iid   = page.add_icon(p, label, STYLES["vpn_gw"], x, vy)
                page.node_map[vgw.resource_id] = iid
                x += ICON_SLOT_W
            for cgw in infra.customer_gateways:
                label = f"Customer GW<br/>{cgw.ip_address}<br/>ASN: {cgw.bgp_asn}"
                iid   = page.add_icon(p, label, STYLES["customer_gw"], x, vy)
                page.node_map[cgw.resource_id] = iid
                x += ICON_SLOT_W
            # Flechas VPN connections
            for vpn in infra.vpn_connections:
                vgw_n = page.node_map.get(vpn.vpn_gateway_id)
                cgw_n = page.node_map.get(vpn.customer_gateway_id)
                tgw_n = page.node_map.get(vpn.transit_gateway_id)
                if vgw_n and cgw_n:
                    page.add_edge(p, vgw_n, cgw_n, vpn.state, loose=True)
                if tgw_n and cgw_n:
                    page.add_edge(p, tgw_n, cgw_n, vpn.state, loose=True)
            vy += ICON_SLOT_H + SECTION_GAP

        # Direct Connect
        if infra.direct_connect_connections:
            self._section_header(page, "Direct Connect", 40, vy)
            vy += 36
            x = 40
            for dx in infra.direct_connect_connections:
                label = f"{dx.name or dx.resource_id}<br/>{dx.bandwidth}<br/>{dx.state}"
                page.add_icon(p, label, STYLES["dx"], x, vy)
                x += ICON_SLOT_W

        return page

    # ── Página 6: Security ────────────────────────────────────────────────────

    def _build_page_security(self, infra: InfrastructureData) -> _Page:
        page = _Page()
        p    = "1"
        vy   = 20

        if not infra.security_groups:
            page.add_container(p, "No se encontraron Security Groups.",
                               STYLES["label_title"], 40, 40, 400, 30)
            return page

        self._section_header(page, "Security Groups", 40, vy)
        vy += 36

        # Cada SG como caja con nombre + conteo de reglas — sin descripción ni fecha
        SG_W, SG_H, SG_GAP_X, SG_GAP_Y = 200, 72, 16, 16
        cols = 5
        for i, sg in enumerate(infra.security_groups):
            col = i % cols
            row = i // cols
            x   = 40 + col * (SG_W + SG_GAP_X)
            y   = vy + row * (SG_H + SG_GAP_Y)
            name  = (sg.name or sg.resource_id)[:28]
            label = f"<b>{name}</b><br/>Ingress: {len(sg.ingress_rules)}  ·  Egress: {len(sg.egress_rules)}"
            page.add_container(p, label, STYLES["sg_box"], x, y, SG_W, SG_H)

        return page

    # ── Página 7: Gestión & Usuarios ─────────────────────────────────────────

    def _build_page_iam(self, infra: InfrastructureData) -> _Page:
        page = _Page()
        page.add_container("1", "Gestión & Usuarios", STYLES["label_title"], 20, 20, 500, 36)
        placeholder = (
            "⚠️  Datos de gestión de identidad no disponibles aún.<br/><br/>"
            "Esta pestaña está reservada para:<br/>"
            "· IAM — usuarios, roles y políticas<br/>"
            "· AWS IAM Identity Center (SSO)<br/>"
            "· AWS Organizations — estructura de cuentas<br/><br/>"
            "La extracción de estos recursos se incorporará en una próxima fase."
        )
        page.add_container("1", placeholder, STYLES["placeholder_box"], 20, 80, 560, 200)
        return page

    # ── Punto de entrada ──────────────────────────────────────────────────────

    def generate(self, infra: InfrastructureData) -> str:
        pages = [
            ("Resumen",            self._build_page_summary(infra)),
            ("Networking",         self._build_page_networking(infra)),
            ("Compute",            self._build_page_compute(infra)),
            ("Database & Storage", self._build_page_database(infra)),
            ("Connectivity",       self._build_page_connectivity(infra)),
            ("Security",           self._build_page_security(infra)),
            ("Gestión & Usuarios", self._build_page_iam(infra)),
        ]
        mxfile = ET.Element("mxfile")
        for name, page in pages:
            mxfile.append(page.to_xml_element(name))
        ET.indent(mxfile, space="  ")
        return ET.tostring(mxfile, encoding="unicode", xml_declaration=True)
