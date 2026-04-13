from models.infra_model import RDSInstance


class RDSExtractor:

    def __init__(self, session):
        self.rds_client = session.get_client('rds')

    def extract_rds_instances(self) -> list[RDSInstance]:
        paginator = self.rds_client.get_paginator('describe_db_instances')
        instances = []

        for page in paginator.paginate():
            for db_data in page["DBInstances"]:
                rds = RDSInstance(
                    resource_id=db_data["DBInstanceIdentifier"],
                    name=db_data.get("DBName"),
                    engine=db_data.get("Engine", ""),
                    engine_version=db_data.get("EngineVersion", ""),
                    instance_class=db_data.get("DBInstanceClass", ""),
                    status=db_data.get("DBInstanceStatus", ""),
                    vpc_id=db_data.get("DBSubnetGroup", {}).get("VpcId", ""),
                    availability_zone=db_data.get("AvailabilityZone", ""),
                    multi_az=db_data.get("MultiAZ", False),
                    publicly_accessible=db_data.get("PubliclyAccessible", False),
                    security_groups=[sg["VpcSecurityGroupId"] for sg in db_data.get("VpcSecurityGroups", [])],
                )
                instances.append(rds)

        return instances
