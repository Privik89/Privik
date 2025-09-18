"""
UI Artifacts Proxy: Streams MinIO/S3 objects with basic UI guard.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
import boto3
from botocore.client import Config
import structlog

from ..core.config import get_settings
from ..security.ui_guard import ui_guard
from ..security.jwt_auth import verify_jwt_admin


logger = structlog.get_logger()
router = APIRouter(prefix="/api/ui/artifacts", tags=["ui-artifacts"], dependencies=[Depends(ui_guard), Depends(verify_jwt_admin)])


@router.get("/get")
async def get_artifact(key: str = Query(..., description="Object key in bucket")):
    try:
        settings = get_settings()
        client = boto3.client(
            's3',
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            config=Config(signature_version='s3v4'),
            region_name='us-east-1',
        )
        obj = client.get_object(Bucket=settings.s3_bucket_name, Key=key)
        content_type = obj.get('ContentType', 'application/octet-stream')
        body = obj['Body']
        return StreamingResponse(body, media_type=content_type)
    except Exception as e:
        logger.error("Artifact fetch failed", key=key, error=str(e))
        raise HTTPException(status_code=404, detail="Artifact not found")


