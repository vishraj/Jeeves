import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    KNOWLEDGE_BASE_ID = os.getenv("KNOWLEDGE_BASE_ID", "")
    MODEL_ID = os.getenv("MODEL_ID", "anthropic.claude-3-5-sonnet-20240620-v1:0")

    # Optional: explicit IAM user keys (takes priority over profile)
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")

    # Optional: named AWS profile from ~/.aws/config (used when no explicit keys)
    AWS_PROFILE = os.getenv("AWS_PROFILE", "sso_profile")

    # S3 bucket for documents (optional depending on use case)
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "")

    @classmethod
    def validate(cls):
        if not cls.KNOWLEDGE_BASE_ID:
            print("WARNING: KNOWLEDGE_BASE_ID is not set in environment variables.")
        if not cls.AWS_REGION:
            print("WARNING: AWS_REGION is not set, defaulting to us-east-1.")

