import json
import re
import urllib.request
import urllib.error
from datetime import datetime, timezone


NOTION_API = "https://api.notion.com/v1"


class NotionGenerator:

    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization":  f"Bearer {token}",
            "Content-Type":   "application/json",
            "Notion-Version": "2022-06-28",
        }

    def _request(self, method: str, path: str, body: dict = None) -> dict:
        url  = f"{NOTION_API}{path}"
        data = json.dumps(body).encode() if body else None
        req  = urllib.request.Request(url, data=data, headers=self.headers, method=method)
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            raise Exception(f"Notion API {e.code}: {e.read().decode()}")

    # ── Helpers de bloques ────────────────────────────────────────────────────

    def _heading1(self, text: str) -> dict:
        return {"object": "block", "type": "heading_1",
                "heading_1": {"rich_text": [{"type": "text", "text": {"content": text[:2000]}}]}}

    def _heading2(self, text: str) -> dict:
        return {"object": "block", "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": text[:2000]}}]}}

    def _paragraph(self, text: str) -> dict:
        return {"object": "block", "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": text[:2000]}}]}}

    def _callout(self, text: str, emoji: str = "☁️") -> dict:
        return {"object": "block", "type": "callout",
                "callout": {"rich_text": [{"type": "text", "text": {"content": text[:2000]}}],
                            "icon": {"type": "emoji", "emoji": emoji}}}

    def _divider(self) -> dict:
        return {"object": "block", "type": "divider", "divider": {}}

    def _image(self, url: str, caption: str = "") -> dict:
        return {"object": "block", "type": "image",
                "image": {"type": "external", "external": {"url": url},
                          "caption": [{"type": "text", "text": {"content": caption}}] if caption else []}}

    def _code(self, text: str, language: str = "plain text") -> dict:
        return {"object": "block", "type": "code",
                "code": {"rich_text": [{"type": "text", "text": {"content": text[:2000]}}],
                         "language": language}}

    def _md_to_blocks(self, md: str) -> list:
        """Convierte Markdown básico a bloques de Notion."""
        blocks = []
        for line in md.split("\n"):
            line = line.rstrip()
            if not line:
                continue
            if line.startswith("# "):
                blocks.append(self._heading1(line[2:]))
            elif line.startswith("## "):
                blocks.append(self._heading2(line[3:]))
            elif line.startswith("### "):
                blocks.append(self._heading2(line[4:]))
            elif line.startswith("- ") or line.startswith("* "):
                blocks.append(self._paragraph(f"• {line[2:]}"))
            elif re.match(r"^\d+\.", line):
                blocks.append(self._paragraph(line))
            elif line.startswith(">"):
                blocks.append(self._callout(line[1:].strip(), "💡"))
            else:
                # Limpiar markdown inline básico
                clean = re.sub(r"\*\*(.+?)\*\*", r"\1", line)
                clean = re.sub(r"\*(.+?)\*",   r"\1", clean)
                clean = re.sub(r"`(.+?)`",      r"\1", clean)
                if clean.strip():
                    blocks.append(self._paragraph(clean))
        return blocks

    # ── Crear página en Notion ────────────────────────────────────────────────

    def create_analysis_page(self,
                              parent_page_id: str,
                              group_name:     str,
                              account_name:   str,
                              account_id:     str,
                              region:         str,
                              user_email:     str,
                              documentation:  str,
                              suggestions:    str,
                              diagram_url:    str = None) -> str:
        """
        Crea una subpágina dentro de parent_page_id con el análisis completo.
        Devuelve la URL de la página creada.
        """
        now   = datetime.now(timezone.utc)
        title = f"Análisis — {account_name} ({region}) — {now.strftime('%d/%m/%Y %H:%M')}"

        # ── Crear la página vacía ─────────────────────────────────────────────
        page = self._request("POST", "/pages", {
            "parent":     {"type": "page_id", "page_id": parent_page_id},
            "properties": {
                "title": {
                    "title": [{"type": "text", "text": {"content": title}}]
                }
            },
        })
        page_id  = page["id"]
        page_url = page.get("url", f"https://notion.so/{page_id.replace('-', '')}")

        # ── Construir bloques del contenido ───────────────────────────────────
        blocks = []

        # Callout de metadatos
        meta = (
            f"🏢  Cliente: {group_name or '—'}\n"
            f"🗂️  Cuenta: {account_name}\n"
            f"🔑  Account ID: {account_id}\n"
            f"🌍  Región: {region}\n"
            f"👤  Analizado por: {user_email or '—'}\n"
            f"📅  Fecha: {now.strftime('%d/%m/%Y a las %H:%M UTC')}"
        )

        blocks.append(self._callout(meta, "☁️"))
        blocks.append(self._divider())

        # Documentación técnica
        blocks.append(self._heading1("📄 Documentación técnica"))
        blocks += self._md_to_blocks(documentation)
        blocks.append(self._divider())

        # Sugerencias Well-Architected
        blocks.append(self._heading1("💡 Sugerencias Well-Architected"))
        blocks += self._md_to_blocks(suggestions)

        # Diagrama (si hay URL pública)
        if diagram_url:
            blocks.append(self._divider())
            blocks.append(self._heading1("🏗️ Diagrama de arquitectura"))
            blocks.append(self._paragraph(
                "Vista del resumen de infraestructura. "
                "El diagrama completo con 7 pestañas está disponible en el archivo .drawio adjunto."
            ))
            blocks.append(self._image(diagram_url, f"Diagrama {account_name} — {region}"))

        # ── Añadir bloques en lotes de 100 (límite de la API) ─────────────────
        for i in range(0, len(blocks), 100):
            self._request("PATCH", f"/blocks/{page_id}/children", {
                "children": blocks[i:i + 100]
            })

        return page_url
