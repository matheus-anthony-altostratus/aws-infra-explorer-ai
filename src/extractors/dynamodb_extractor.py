from models.infra_model import DynamoDBTable


class DynamoDBExtractor:

    def __init__(self, session):
        self.client = session.get_client("dynamodb")

    def extract_tables(self) -> list[DynamoDBTable]:
        tables = []
        paginator = self.client.get_paginator("list_tables")

        for page in paginator.paginate():
            for table_name in page["TableNames"]:
                try:
                    detail = self.client.describe_table(TableName=table_name)["Table"]
                    billing = detail.get("BillingModeSummary", {})
                    billing_mode = billing.get("BillingMode", "PROVISIONED")
                    throughput = detail.get("ProvisionedThroughput", {})
                    sse = detail.get("SSEDescription", {})

                    tables.append(DynamoDBTable(
                        resource_id=detail["TableArn"],
                        name=table_name,
                        status=detail.get("TableStatus", ""),
                        billing_mode=billing_mode,
                        read_capacity=throughput.get("ReadCapacityUnits", 0),
                        write_capacity=throughput.get("WriteCapacityUnits", 0),
                        item_count=detail.get("ItemCount", 0),
                        size_bytes=detail.get("TableSizeBytes", 0),
                        encryption=sse.get("Status", "NOT_ENABLED"),
                    ))
                except Exception:
                    continue

        return tables
