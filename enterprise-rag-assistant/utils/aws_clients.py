import boto3
from .config import Config

class AWSClientManager:
    def __init__(self):
        # If explicit AWS keys are set in .env, use them (highest priority — permanent IAM user).
        # Otherwise fall back to the named SSO profile from ~/.aws/config.
        # This allows a future upgrade to a dedicated IAM user without any other code changes.
        if Config.AWS_ACCESS_KEY_ID and Config.AWS_SECRET_ACCESS_KEY:
            self.session = boto3.Session(
                aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
                region_name=Config.AWS_REGION,
            )
        elif Config.AWS_PROFILE:
            # Use a named profile from ~/.aws/config (e.g. the SSO profile)
            self.session = boto3.Session(
                profile_name=Config.AWS_PROFILE,
                region_name=Config.AWS_REGION,
            )
        else:
            # Fall back to boto3's default credential chain
            self.session = boto3.Session(region_name=Config.AWS_REGION)

        self._bedrock_runtime = None
        self._bedrock_agent_runtime = None
        self._s3 = None
        self._dynamodb = None

    @property
    def bedrock_runtime(self):
        if self._bedrock_runtime is None:
            self._bedrock_runtime = self.session.client("bedrock-runtime")
        return self._bedrock_runtime

    @property
    def bedrock_agent_runtime(self):
        if self._bedrock_agent_runtime is None:
            self._bedrock_agent_runtime = self.session.client("bedrock-agent-runtime")
        return self._bedrock_agent_runtime

    @property
    def s3(self):
        if self._s3 is None:
            self._s3 = self.session.client("s3")
        return self._s3

    @property
    def dynamodb(self):
        if self._dynamodb is None:
            self._dynamodb = self.session.resource("dynamodb")
        return self._dynamodb

# Singleton instance
aws_manager = AWSClientManager()
