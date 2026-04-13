from models.infra_model import EFSFileSystem


class EFSExtractor:

    def __init__(self, session):
        self.efs_client = session.get_client('efs')

    def extract_file_systems(self) -> list[EFSFileSystem]:
        paginator = self.efs_client.get_paginator('describe_file_systems')
        file_systems = []

        for page in paginator.paginate():
            for fs in page["FileSystems"]:
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
