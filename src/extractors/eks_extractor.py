from models.infra_model import EKSCluster


class EKSExtractor:

    def __init__(self, session):
        self.eks_client = session.get_client('eks')

    def extract_eks_clusters(self) -> list[EKSCluster]:
        paginator = self.eks_client.get_paginator('list_clusters')
        cluster_names = []
        for page in paginator.paginate():
            cluster_names.extend(page["clusters"])

        clusters = []
        for name in cluster_names:
            response = self.eks_client.describe_cluster(name=name)
            c = response["cluster"]
            tags = c.get("tags", {})
            vpc_config = c.get("resourcesVpcConfig", {})

            cluster = EKSCluster(
                resource_id=c.get("arn", ""),
                name=c.get("name"),
                tags=tags,
                version=c.get("version", ""),
                status=c.get("status", ""),
                endpoint=c.get("endpoint", ""),
                vpc_id=vpc_config.get("vpcId", ""),
                subnet_ids=vpc_config.get("subnetIds", []),
                security_groups=vpc_config.get("securityGroupIds", []),
            )
            clusters.append(cluster)

        return clusters
