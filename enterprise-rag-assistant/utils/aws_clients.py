import boto3
from .config import Config

class AWSClientManager:
    def __init__(self):
        self.session = boto3.Session(region_name=Config.AWS_REGION)
        self._bedrock_runtime = None
        self._bedrock_agent_runtime = None
        self._s3 = None

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

# Singleton instance
aws_manager = AWSClientManager()
