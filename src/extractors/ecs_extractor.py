from models.infra_model import ECSCluster, ECSService


class ECSExtractor:

    def __init__(self, session):
        self.ecs_client = session.get_client('ecs')

    def extract_ecs_clusters(self) -> list[ECSCluster]:
        paginator = self.ecs_client.get_paginator('list_clusters')
        cluster_arns = []
        for page in paginator.paginate():
            cluster_arns.extend(page["clusterArns"])

        if not cluster_arns:
            return []

        response = self.ecs_client.describe_clusters(clusters=cluster_arns)
        clusters = []

        for c in response["clusters"]:
            tags = {tag["key"]: tag["value"] for tag in c.get("tags", [])}

            cluster = ECSCluster(
                resource_id=c.get("clusterArn", ""),
                name=c.get("clusterName"),
                tags=tags,
                status=c.get("status", ""),
                registered_instances=c.get("registeredContainerInstancesCount", 0),
                running_tasks=c.get("runningTasksCount", 0),
                pending_tasks=c.get("pendingTasksCount", 0),
                services=self._extract_services(c["clusterArn"]),
            )
            clusters.append(cluster)

        return clusters

    def _extract_services(self, cluster_arn: str) -> list[ECSService]:
        paginator = self.ecs_client.get_paginator('list_services')
        service_arns = []
        for page in paginator.paginate(cluster=cluster_arn):
            service_arns.extend(page["serviceArns"])

        if not service_arns:
            return []

        response = self.ecs_client.describe_services(cluster=cluster_arn, services=service_arns)
        services = []

        for s in response["services"]:
            service = ECSService(
                service_name=s.get("serviceName", ""),
                status=s.get("status", ""),
                desired_count=s.get("desiredCount", 0),
                running_count=s.get("runningCount", 0),
                launch_type=s.get("launchType", ""),
                task_definition=s.get("taskDefinition", ""),
            )
            services.append(service)

        return services
