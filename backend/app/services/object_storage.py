"""
S3/MinIO object storage helper for uploading artifacts (reports, screenshots).
"""

import io
import json
import boto3
from botocore.client import Config
from typing import Optional, Dict, Any
import structlog

from ..core.config import get_settings


logger = structlog.get_logger()


class ObjectStorage:
    def __init__(self):
        settings = get_settings()
        self.endpoint_url = settings.s3_endpoint_url
        self.bucket = settings.s3_bucket_name
        self.client = boto3.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            config=Config(signature_version='s3v4'),
            region_name='us-east-1',
        )

    def upload_bytes(self, key: str, data: bytes, content_type: str = 'application/octet-stream') -> str:
        try:
            self.client.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type)
            logger.info("Uploaded object", key=key)
            return key
        except Exception as e:
            logger.error("S3 upload failed", key=key, error=str(e))
            raise

    def upload_json(self, key: str, obj: Dict[str, Any]) -> str:
        data = json.dumps(obj).encode('utf-8')
        return self.upload_bytes(key, data, content_type='application/json')


