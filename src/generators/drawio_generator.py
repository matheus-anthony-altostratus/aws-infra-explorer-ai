import xml.etree.ElementTree as ET
from models.infra_model import InfrastructureData

STYLES = {
    "vpc":            "points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=12;fontStyle=1;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_vpc2;strokeColor=#8C4FFF;fillColor=none;verticalAlign=top;align=left;spacingLeft=30;fontColor=#1a1a2e;dashed=0;",
    "subnet_public":  "points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=11;fontStyle=1;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_security_group;strokeColor=#5a8a00;fillColor=#f0fff0;verticalAlign=top;align=left;spacingLeft=30;fontColor=#2d5a00;dashed=0;",
    "subnet_private": "points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=11;fontStyle=1;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_security_group;strokeColor=#007a7c;fillColor=#e6fffe;verticalAlign=top;align=left;spacingLeft=30;fontColor=#004d4e;dashed=0;",
    "az":             "fillColor=#e8f4fd;strokeColor=#1a6fa8;dashed=1;verticalAlign=top;fontStyle=1;fontColor=#1a6fa8;whiteSpace=wrap;html=1;",
    "ec2":            "outlineConnect=0;fontColor=#111827;gradientColor=none;fillColor=#ED7100;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.instance2;",
    "rds":            "outlineConnect=0;fontColor=#111827;gradientColor=none;fillColor=#C925D1;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.rds;",
    "dynamodb":       "outlineConnect=0;fontColor=#111827;gradientColor=none;fillColor=#C925D1;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.dynamodb;",
    "igw":            "outlineConnect=0;fontColor=#111827;gradientColor=none;fillColor=#8C4FFF;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.internet_gateway;",
    "natgw":          "outlineConnect=0;fontColor=#111827;gradientColor=none;fillColor=#8C4FFF;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.nat_gateway;",
    "elb":            "outlineConnect=0;fontColor=#111827;gradientColor=none;fillColor=#8C4FFF;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.elastic_load_balancing;",
    "tgw":            "outlineConnect=0;fontColor=#111827;gradientColor=none;fillColor=#8C4FFF;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.transit_gateway;",
    "vpn_gw":         "outlineConnect=0;fontColor=#111827;gradientColor=none;fillColor=#8C4FFF;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.vpn_gateway;",
    "customer_gw":    "outlineConnect=0;fontColor=#111827;gradientColor=none;fillColor=#8C4FFF;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.customer_gateway;",
    "ecs":            "outlineConnect=0;fontColor=#111827;gradientColor=none;fillColor=#ED7100;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.ecs;",
    "eks":            "outlineConnect=0;fontColor=#111827;gradientColor=none;fillColor=#ED7100;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.eks;",
    "efs":            "outlineConnect=0;fontColor=#111827;gradientColor=none;fillColor=#7AA116;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.efs;",
    "dx":             "outlineConnect=0;fontColor=#111827;gradientColor=none;fillColor=#8C4FFF;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.direct_connect;",
    "eip":            "outlineConnect=0;fontColor=#111827;gradientColor=none;fillColor=#8C4FFF;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.elastic_ip_address;",
    "peering":        "outlineConnect=0;fontColor=#111827;gradientColor=none;fillColor=#8C4FFF;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.peering_connection;",
    "sg":             "outlineConnect=0;fontColor=#111827;gradientColor=none;fillColor=#DD344C;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.security_group;",
    "iam_role":       "outlineConnect=0;fontColor=#111827;gradientColor=none;fillColor=#DD344C;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.role;",
    "arrow":          "rounded=1;orthogonalLoop=1;jettySize=auto;exitX=0.5;exitY=0;exitDx=0;exitDy=0;entryX=0.5;entryY=1;entryDx=0;entryDy=0;edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#6B7280;strokeWidth=1.5;fillColor=#6B7280;fontColor=#374151;fontSize=10;",
    "arrow_loose":    "rounded=1;orthogonalLoop=1;jettySize=auto;edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#6B7280;strokeWidth=1.5;fillColor=#6B7280;fontColor=#374151;fontSize=10;exitX=1;exitY=0.5;exitDx=0;exitDy=0;",
    "label_title":    "text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacingLeft=4;fontSize=15;fontStyle=1;fontColor=#111827;",
    "label_section":  "text;html=1;strokeColor=none;fillColor=#EEF2FF;align=left;verticalAlign=middle;spacingLeft=10;fontSize=12;fontStyle=1;fontColor=#4338CA;rounded=1;",
    "summary_header": "rounded=1;whiteSpace=wrap;html=1;fillColor=#1E3A5F;strokeColor=none;fontColor=#FFFFFF;fontSize=12;fontStyle=1;",
    "summary_cell":   "rounded=1;whiteSpace=wrap;html=1;fillColor=#F9FAFB;strokeColor=#D1D5DB;fontSize=12;fontColor=#111827;",
    "summary_count":  "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#8C4FFF;fontSize=18;fontStyle=1;fontColor=#8C4FFF;",
    "placeholder_box":"rounded=1;whiteSpace=wrap;html=1;fillColor=#F9FAFB;strokeColor=#D1D5DB;dashed=1;fontSize=13;fontColor=#6B7280;verticalAlign=middle;",
    "sg_box":         "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFF5F5;strokeColor=#DD344C;fontSize=11;fontColor=#111827;verticalAlign=top;align=left;spacingLeft=8;spacingTop=6;",
    "iam_box":        "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFF0F0;strokeColor=#DD344C;fontSize=11;fontColor=#111827;verticalAlign=top;align=left;spacingLeft=8;spacingTop=6;",
    "cover_meta":     "rounded=1;whiteSpace=wrap;html=1;fillColor=#EEF2FF;strokeColor=#C7D2FE;fontSize=12;fontColor=#3730a3;align=left;spacingLeft=12;verticalAlign=middle;",
    "cover_alert":    "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFF7ED;strokeColor=#FED7AA;fontSize=12;fontColor=#92400e;align=left;spacingLeft=12;verticalAlign=middle;",
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
        from datetime import datetime, timezone
        page = _Page()
        p    = "1"

        # ── Título principal ──────────────────────────────────────────────────
        page.add_container(p, f"☁️  AWS Infra Explorer — Análisis de {infra.region}",
                           STYLES["label_title"], 20, 20, 760, 40)

        # ── Bloque de metadatos ───────────────────────────────────────────────
        now_str = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
        meta_lines = [
            f"🌍  Región analizada:  {infra.region}",
            f"📅  Fecha del análisis:  {now_str}",
            f"🔒  Acceso via:  STS AssumeRole — infra-explorer-read-only (solo lectura)",
        ]
        my = 72
        for line in meta_lines:
            page.add_container(p, line, STYLES["cover_meta"], 20, my, 760, 32)
            my += 36

        # ── Totales destacados ────────────────────────────────────────────────
        highlights = [
            ("VPCs",           len(infra.vpcs),            "#8C4FFF"),
            ("Subnets",        sum(len(v.subnets) for v in infra.vpcs), "#147EBA"),
            ("EC2",            len(infra.instances),       "#ED7100"),
            ("RDS",            len(infra.rds_instances),   "#C925D1"),
            ("Load Balancers", len(infra.load_balancers),  "#8C4FFF"),
            ("Security Groups",len(infra.security_groups), "#DD344C"),
            ("NAT Gateways",   len(infra.nat_gateways),    "#8C4FFF"),
            ("Elastic IPs",    len(infra.elastic_ips),     "#8C4FFF"),
        ]
        hx, hy = 20, my + 24
        card_w, card_h = 180, 70
        gap = 12
        for i, (label, count, color) in enumerate(highlights):
            col = i % 4
            row = i // 4
            x   = hx + col * (card_w + gap)
            y   = hy + row * (card_h + gap)
            page.add_container(p,
                f"<b style='font-size:24px;color:{color};'>{count}</b><br/>{label}",
                f"rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor={color}44;"
                f"fontSize=12;fontColor=#374151;verticalAlign=middle;align=center;",
                x, y, card_w, card_h)

        # ── Nota de navegación ────────────────────────────────────────────────
        note_y = hy + 2 * (card_h + gap) + 24
        page.add_container(p,
            "💡  Este archivo contiene 8 pestañas:  Resumen · Inventario · Networking · "
            "Compute · Database & Storage · Connectivity · Security · Gestión & Usuarios",
            STYLES["cover_alert"], 20, note_y, (card_w + gap) * 4 - gap, 36)

        return page

    # ── Página 2: Inventario ──────────────────────────────────────────────────

    def _build_page_inventory(self, infra: InfrastructureData) -> _Page:
        page = _Page()
        p    = "1"
        vy   = 20
        cx   = 20

        page.add_container(p, "📋  Inventario de recursos — " + infra.region,
                           STYLES["label_title"], cx, vy, 800, 36)
        vy += 52

        STYLE_TH  = "rounded=0;whiteSpace=wrap;html=1;fillColor=#1E3A5F;strokeColor=#374151;fontColor=#FFFFFF;fontSize=11;fontStyle=1;align=left;spacingLeft=6;"
        STYLE_TD  = "rounded=0;whiteSpace=wrap;html=1;fillColor=#F9FAFB;strokeColor=#D1D5DB;fontSize=11;fontColor=#111827;align=left;spacingLeft=6;"
        STYLE_TD2 = "rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#D1D5DB;fontSize=11;fontColor=#111827;align=left;spacingLeft=6;"
        STYLE_SEC = "text;html=1;strokeColor=none;fillColor=#EEF2FF;align=left;verticalAlign=middle;spacingLeft=10;fontSize=12;fontStyle=1;fontColor=#4338CA;rounded=1;"
        ROW_H = HDR_H = 28

        def _table(title, headers, rows, col_widths):
            nonlocal vy
            if not rows:
                return
            page.add_container(p, title, STYLE_SEC, cx, vy, sum(col_widths), 26)
            vy += 30
            hx = cx
            for hi, hdr in enumerate(headers):
                page.add_container(p, hdr, STYLE_TH, hx, vy, col_widths[hi], HDR_H)
                hx += col_widths[hi]
            vy += HDR_H
            for ri, row_vals in enumerate(rows):
                style = STYLE_TD if ri % 2 == 0 else STYLE_TD2
                rx2   = cx
                for ci2, val in enumerate(row_vals):
                    txt = str(val) if val else "—"
                    txt = txt[:48] + "…" if len(txt) > 48 else txt
                    page.add_container(p, txt, style, rx2, vy, col_widths[ci2], ROW_H)
                    rx2 += col_widths[ci2]
                vy += ROW_H
            vy += 24

        _table("🔷  VPCs", ["Nombre", "ID", "CIDR", "Subnets"],
               [(v.name or "—", v.resource_id, v.cidr_block, str(len(v.subnets))) for v in infra.vpcs],
               [200, 230, 140, 80])

        _table("🔶  Subnets", ["Nombre", "ID", "CIDR", "AZ", "Tipo"],
               [(s.name or "—", s.resource_id, s.cidr_block, s.availability_zone,
                 "Pública" if s.is_public else "Privada")
                for v in infra.vpcs for s in v.subnets],
               [200, 230, 140, 120, 80])

        _table("🌐  Internet Gateways", ["Nombre", "ID", "VPC"],
               [(g.name or "—", g.resource_id, g.vpc_id) for g in infra.internet_gateways],
               [200, 230, 230])

        _table("🔀  NAT Gateways", ["Nombre", "ID", "IP Pública", "Estado"],
               [(g.name or "—", g.resource_id, g.public_ip or "—", g.state) for g in infra.nat_gateways],
               [200, 230, 130, 100])

        _table("📌  Elastic IPs", ["ID", "IP Pública", "Interface"],
               [(e.resource_id, e.public_ip, e.network_interface_id or "—") for e in infra.elastic_ips],
               [230, 130, 300])

        _table("🖥️  EC2 Instances", ["Nombre", "ID", "Tipo", "Estado", "IP Privada", "IP Pública"],
               [(i.name or "—", i.resource_id, i.instance_type, i.state,
                 i.private_ip or "—", i.public_ip or "—") for i in infra.instances],
               [180, 200, 100, 80, 120, 120])

        if infra.rds_instances:
            _table("🗄️  RDS Instances", ["Nombre", "ID", "Motor", "Versión", "Clase", "Estado", "Multi-AZ"],
                   [(r.name or "—", r.resource_id, r.engine, r.engine_version,
                     r.instance_class, r.status, "Sí" if r.multi_az else "No")
                    for r in infra.rds_instances],
                   [160, 220, 80, 80, 140, 80, 70])

        dynamodb_tables = getattr(infra, "dynamodb_tables", [])
        if dynamodb_tables:
            _table("⚡  DynamoDB Tables", ["Nombre", "ARN", "Billing", "Estado"],
                   [(t.name or "—", t.resource_id, t.billing_mode, t.status) for t in dynamodb_tables],
                   [180, 340, 130, 100])

        if infra.load_balancers:
            _table("⚖️  Load Balancers", ["Nombre", "Tipo", "Scheme", "DNS"],
                   [(lb.name or "—", lb.type, lb.scheme, lb.dns_name) for lb in infra.load_balancers],
                   [160, 80, 100, 420])

        if infra.ecs_clusters:
            _table("📦  ECS Clusters", ["Nombre", "ID/ARN", "Servicios", "Tasks activas", "Estado"],
                   [(c.name or "—", c.resource_id, str(len(c.services)), str(c.running_tasks), c.status)
                    for c in infra.ecs_clusters],
                   [180, 300, 90, 110, 80])

        if infra.eks_clusters:
            _table("☸️  EKS Clusters", ["Nombre", "Versión", "Estado", "VPC"],
                   [(c.name or "—", c.version, c.status, c.vpc_id) for c in infra.eks_clusters],
                   [180, 90, 90, 230])

        if infra.efs_file_systems:
            _table("💾  EFS File Systems", ["Nombre", "ID", "Modo", "Estado", "Cifrado"],
                   [(f.name or "—", f.resource_id, f.performance_mode,
                     f.lifecycle_state, "Sí" if f.encrypted else "No")
                    for f in infra.efs_file_systems],
                   [180, 220, 120, 100, 80])

        if infra.transit_gateways:
            _table("🔁  Transit Gateways", ["Nombre", "ID", "ASN", "Estado"],
                   [(t.name or "—", t.resource_id, str(t.amazon_asn), t.state)
                    for t in infra.transit_gateways],
                   [180, 230, 80, 80])

        if infra.vpn_gateways:
            _table("🔒  VPN Gateways", ["Nombre", "ID", "Estado", "VPC"],
                   [(v.name or "—", v.resource_id, v.state, v.vpc_id) for v in infra.vpn_gateways],
                   [180, 230, 80, 230])

        if infra.customer_gateways:
            _table("🏢  Customer Gateways", ["ID", "IP", "BGP ASN", "Estado"],
                   [(g.resource_id, g.ip_address, g.bgp_asn, g.state) for g in infra.customer_gateways],
                   [230, 130, 90, 90])

        if infra.direct_connect_connections:
            _table("🔌  Direct Connect", ["Nombre", "ID", "Ancho de banda", "Estado"],
                   [(d.name or "—", d.resource_id, d.bandwidth, d.state)
                    for d in infra.direct_connect_connections],
                   [200, 230, 140, 90])

        if infra.vpc_peerings:
            _table("🔗  VPC Peerings",
                   ["ID", "VPC Origen", "CIDR Origen", "VPC Destino", "CIDR Destino", "Estado"],
                   [(p2.resource_id, p2.requester_vpc_id, p2.requester_cidr,
                     p2.accepter_vpc_id, p2.accepter_cidr, p2.state)
                    for p2 in infra.vpc_peerings],
                   [200, 200, 130, 200, 130, 80])

        if infra.security_groups:
            _table("🛡️  Security Groups", ["Nombre", "ID", "Ingress rules", "Egress rules"],
                   [(sg.name or "—", sg.resource_id,
                     str(len(sg.ingress_rules)), str(len(sg.egress_rules)))
                    for sg in infra.security_groups],
                   [200, 230, 110, 110])

        return page

    # ── Página 3: Networking ──────────────────────────────────────────────────

    def _build_page_networking(self, infra: InfrastructureData) -> _Page:
        page         = _Page()
        p            = "1"
        subnet_icons = self._prepare_subnet_icons(infra)

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

        vy = 60 + ICON_SLOT_H + 32
        for vpc in infra.vpcs:
            saz = self._subnets_by_az(vpc, subnet_icons)
            if not saz:
                continue
            _, _, vpc_h = self._build_vpc(page, p, vpc, saz, 40, vy)
            vy += vpc_h + VPC_GAP

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

        for igw in infra.internet_gateways:
            igw_n = page.node_map.get(igw.resource_id)
            vpc_n = page.node_map.get(igw.vpc_id)
            if igw_n and vpc_n:
                page.add_edge(p, igw_n, vpc_n, loose=True)

        return page

    # ── Página 4: Compute ─────────────────────────────────────────────────────

    def _build_page_compute(self, infra: InfrastructureData) -> _Page:
        page         = _Page()
        p            = "1"
        subnet_icons = self._prepare_subnet_icons_compute_only(infra)
        vy           = 20

        if infra.instances:
            self._section_header(page, "EC2 Instances", 40, vy)
            vy += 36
            for vpc in infra.vpcs:
                saz = self._subnets_by_az(vpc, subnet_icons)
                saz_filtered = {az: [s for s in subnets if s["_icons"]]
                                for az, subnets in saz.items()}
                saz_filtered = {az: s for az, s in saz_filtered.items() if s}
                if not saz_filtered:
                    continue
                _, _, vpc_h = self._build_vpc(page, p, vpc, saz_filtered, 40, vy)
                vy += vpc_h + VPC_GAP

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
        p    = "1"
        vy   = 20
        cx   = 20

        page.add_container(p, "👤  Gestión & Usuarios",
                           STYLES["label_title"], cx, vy, 700, 36)
        vy += 52

        iam = getattr(infra, "iam_summary", None)

        if not iam:
            page.add_container(p,
                "⚠️  Datos de gestión de identidad no disponibles aún.\n\n"
                "Esta pestaña está reservada para:\n"
                "· IAM — roles y grupos (custom)\n"
                "· AWS IAM Identity Center (SSO)\n"
                "· AWS Organizations — estructura de cuentas\n\n"
                "La extracción de estos recursos se incorporará en una próxima fase.",
                STYLES["placeholder_box"], cx, vy, 560, 180)
            return page

        # ── Metadatos de la cuenta ────────────────────────────────────────────
        meta = [
            f"🏷️  Alias de cuenta:  {iam.account_alias or '(sin alias)'}",
            f"👥  Usuarios IAM:  {iam.users_count}",
            f"🔐  MFA activo:  {'✅ Sí' if iam.mfa_enabled else '⚠️ No'}",
            f"🔑  Password Policy:  {'✅ Configurada' if iam.password_policy else '⚠️ No configurada'}",
        ]
        for line in meta:
            page.add_container(p, line, STYLES["cover_meta"], cx, vy, 600, 30)
            vy += 34
        vy += 16

        STYLE_TH  = "rounded=0;whiteSpace=wrap;html=1;fillColor=#1E3A5F;strokeColor=#374151;fontColor=#FFFFFF;fontSize=11;fontStyle=1;align=left;spacingLeft=6;"
        STYLE_TD  = "rounded=0;whiteSpace=wrap;html=1;fillColor=#FFF0F0;strokeColor=#FECACA;fontSize=11;fontColor=#111827;align=left;spacingLeft=6;"
        STYLE_TD2 = "rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#FECACA;fontSize=11;fontColor=#111827;align=left;spacingLeft=6;"
        STYLE_SEC = "text;html=1;strokeColor=none;fillColor=#FEE2E2;align=left;verticalAlign=middle;spacingLeft=10;fontSize=12;fontStyle=1;fontColor=#991b1b;rounded=1;"
        ROW_H = HDR_H = 28

        def _table(title, headers, rows, col_widths):
            nonlocal vy
            if not rows:
                return
            page.add_container(p, title, STYLE_SEC, cx, vy, sum(col_widths), 26)
            vy += 30
            hx = cx
            for hi, hdr in enumerate(headers):
                page.add_container(p, hdr, STYLE_TH, hx, vy, col_widths[hi], HDR_H)
                hx += col_widths[hi]
            vy += HDR_H
            for ri, row_vals in enumerate(rows):
                style = STYLE_TD if ri % 2 == 0 else STYLE_TD2
                rx2   = cx
                for ci2, val in enumerate(row_vals):
                    txt = str(val) if val else "—"
                    txt = txt[:50] + "…" if len(txt) > 50 else txt
                    page.add_container(p, txt, style, rx2, vy, col_widths[ci2], ROW_H)
                    rx2 += col_widths[ci2]
                vy += ROW_H
            vy += 24

        # Roles IAM (solo custom)
        if iam.roles:
            _table("🎭  Roles IAM (custom — excluidos roles de servicio AWS)",
                   ["Nombre", "Descripción", "Creado", "Último uso", "Políticas adjuntas"],
                   [(r.name, r.description[:40] or "—", r.created_at,
                     r.last_used or "—", ", ".join(r.attached_policies[:3]) or "—")
                    for r in iam.roles],
                   [200, 200, 90, 90, 220])
        else:
            page.add_container(p, "ℹ️  No se encontraron roles IAM custom en esta cuenta.",
                               STYLES["cover_alert"], cx, vy, 600, 30)
            vy += 40

        # Grupos IAM
        if iam.groups:
            _table("👥  Grupos IAM",
                   ["Nombre", "Usuarios", "Políticas adjuntas"],
                   [(g.name, str(g.user_count), ", ".join(g.attached_policies[:3]) or "—")
                    for g in iam.groups],
                   [220, 80, 400])
        else:
            page.add_container(p, "ℹ️  No se encontraron grupos IAM en esta cuenta.",
                               STYLES["cover_alert"], cx, vy, 600, 30)
            vy += 40

        # Usuarios IAM
        users = getattr(iam, "users", [])
        if users:
            _table("🧑  Usuarios IAM",
                   ["Username", "Creado", "Último login", "MFA", "Grupos", "Políticas adjuntas"],
                   [(u.username,
                     u.created_at,
                     u.last_login or "—",
                     "✅" if u.mfa_active else "⚠️ No",
                     ", ".join(u.groups) or "—",
                     ", ".join(u.attached_policies[:2]) or "—")
                    for u in users],
                   [160, 90, 100, 60, 180, 210])
        else:
            page.add_container(p, "ℹ️  No se encontraron usuarios IAM en esta cuenta.",
                               STYLES["cover_alert"], cx, vy, 600, 30)
            vy += 40

        # Nota sobre Identity Center
        vy += 8
        page.add_container(p,
            "ℹ️  AWS IAM Identity Center (SSO) y AWS Organizations operan a nivel de Management Account "
            "y requieren acceso desde la cuenta raíz de la organización.",
            STYLES["placeholder_box"], cx, vy, 700, 40)

        return page

    # ── Punto de entrada ──────────────────────────────────────────────────────

    def generate(self, infra: InfrastructureData) -> str:
        pages = [
            ("Resumen",            self._build_page_summary(infra)),
            ("Inventario",         self._build_page_inventory(infra)),
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
