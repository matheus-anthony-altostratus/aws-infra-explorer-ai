import boto3
from models.infra_model import EFSFileSystem


class EFSExtractor:

    def __init__(self, region_name: str = "us-east-1"):
        self.efs_client = boto3.client('efs', region_name=region_name)

    def extract_file_systems(self) -> list[EFSFileSystem]:
        response = self.efs_client.describe_file_systems()
        file_systems = []

        for fs in response["FileSystems"]:
            tags = {tag["Key"]: tag["Value"] for tag in fs.get("Tags", [])}

            efs = EFSFileSystem(
                resource_id=fs.get("FileSystemId", ""),
                name=tags.get("Name"),
                tags=tags,
                size_bytes=fs.get("SizeInBytes", {}).get("Value", 0),
                performance_mode=fs.get("PerformanceMode", ""),
                lifecycle_state=fs.get("LifeCycleState", ""),
                encrypted=fs.get("Encrypted", False),
            )
            file_systems.append(efs)

        return file_systems
