import boto3
from models.infra_model import DirectConnectConnection


class DXExtractor:

    def __init__(self, region_name: str = "us-east-1"):
        self.dx_client = boto3.client('directconnect', region_name=region_name)

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
