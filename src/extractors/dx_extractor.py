from models.infra_model import DirectConnectConnection


class DXExtractor:

    def __init__(self, session):
        self.dx_client = session.get_client('directconnect')

    def extract_connections(self) -> list[DirectConnectConnection]:
        response = self.dx_client.describe_connections()
        connections = []

        for conn in response["connections"]:
            tags = {tag["key"]: tag["value"] for tag in conn.get("tags", [])}

            connection = DirectConnectConnection(
                resource_id=conn.get("connectionId", ""),
                name=conn.get("connectionName"),
                tags=tags,
                bandwidth=conn.get("bandwidth", ""),
                location=conn.get("location", ""),
                state=conn.get("connectionState", ""),
                vlan=conn.get("vlan", 0),
            )
            connections.append(connection)

        return connections
