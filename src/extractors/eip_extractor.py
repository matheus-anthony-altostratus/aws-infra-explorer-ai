from models.infra_model import ElasticIP


class EIPExtractor:

    def __init__(self, session):
        self.ec2_client = session.get_client('ec2')

    def extract_elastic_ips(self) -> list[ElasticIP]:
        response = self.ec2_client.describe_addresses()
        eips = []

        for eip_data in response["Addresses"]:
            tags = {tag["Key"]: tag["Value"] for tag in eip_data.get("Tags", [])}

            eip = ElasticIP(
                resource_id=eip_data.get("AllocationId", ""),
                name=tags.get("Name"),
                tags=tags,
                public_ip=eip_data.get("PublicIp", ""),
                association_id=eip_data.get("AssociationId", ""),
                instance_id=eip_data.get("InstanceId", ""),
                network_interface_id=eip_data.get("NetworkInterfaceId", ""),
                domain=eip_data.get("Domain", ""),
            )
            eips.append(eip)

        return eips
