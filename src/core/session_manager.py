import boto3


class SessionManager:

    def __init__(self, region_name: str = "eu-west-1", aws_access_key_id: str = None,
                 aws_secret_access_key: str = None, role_arn: str = None):
        self.region_name = region_name
        self.session = self._create_session(aws_access_key_id, aws_secret_access_key, role_arn)

    def _create_session(self, access_key: str, secret_key: str, role_arn: str) -> boto3.Session:
        # Modo 1: AssumeRole — para multicuenta
        if role_arn:
            sts_client = boto3.client("sts")
            response = sts_client.assume_role(
                RoleArn=role_arn,
                RoleSessionName="infra-explorer-session",
                DurationSeconds=3600,
            )
            credentials = response["Credentials"]
            return boto3.Session(
                aws_access_key_id=credentials["AccessKeyId"],
                aws_secret_access_key=credentials["SecretAccessKey"],
                aws_session_token=credentials["SessionToken"],
                region_name=self.region_name,
            )

        # Modo 2: Access Key + Secret Key — para la web
        if access_key and secret_key:
            return boto3.Session(
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=self.region_name,
            )

        # Modo 3: Entorno — usa credenciales del sistema (aws-vault, env vars, ~/.aws)
        return boto3.Session(region_name=self.region_name)

    def get_client(self, service_name: str):
        return self.session.client(service_name, region_name=self.region_name)
