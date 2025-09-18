"""
Sandbox Router: CAPE status and test detonation endpoints.
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from typing import Dict, Any
import aiofiles
import os
import tempfile
import structlog

from ..services.email_gateway import EmailGateway
from ..services.real_time_sandbox import RealTimeSandbox
from ..services.email_gateway_service import get_email_gateway_service, EmailGatewayService
from ..security.hmac_auth import verify_request


logger = structlog.get_logger()
router = APIRouter(prefix="/api/sandbox", tags=["sandbox"], dependencies=[Depends(verify_request)])


@router.get("/status")
async def sandbox_status(gateway_service: EmailGatewayService = Depends(get_email_gateway_service)):
    try:
        sandbox = getattr(gateway_service, 'sandbox_service', None)
        # Fallback: EmailGateway instance may hold sandbox; expose via service if needed
        cape_info = {
            'enabled': bool(getattr(gateway_service, 'cape_enabled', False)) if gateway_service else False
        }
        return {
            'running': gateway_service.is_running if gateway_service else False,
            'cape_enabled': cape_info['enabled']
        }
    except Exception as e:
        logger.error("Sandbox status error", error=str(e))
        raise HTTPException(status_code=500, detail="Sandbox status error")


@router.post("/detonate-test")
async def detonate_test_file(
    file: UploadFile = File(...),
    gateway_service: EmailGatewayService = Depends(get_email_gateway_service)
):
    try:
        # Save uploaded file to temp
        suffix = os.path.splitext(file.filename)[1] if file.filename else ""
        async with aiofiles.tempfile.NamedTemporaryFile('wb', delete=False, suffix=suffix) as tmp:
            content = await file.read()
            await tmp.write(content)
            tmp_path = tmp.name
        # Use the real-time sandbox from the gateway layer if available
        # For now, instantiate a default RealTimeSandbox using gateway config
        sandbox_cfg = {
            'cape_enabled': True if os.getenv('CAPE_ENABLED', 'false').lower() == 'true' else False,
            'cape_base_url': os.getenv('CAPE_BASE_URL', ''),
            'cape_api_token': os.getenv('CAPE_API_TOKEN', ''),
            'sandbox_timeout': 300
        }
        sandbox = RealTimeSandbox(sandbox_cfg)
        result = await sandbox.analyze_attachment(tmp_path, os.path.splitext(tmp_path)[1].lower())
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
        return {
            'verdict': result.verdict,
            'confidence': result.confidence,
            'threat_indicators': result.threat_indicators,
            'network_sampled': len(result.network_activity)
        }
    except Exception as e:
        logger.error("Detonation error", error=str(e))
        raise HTTPException(status_code=500, detail="Detonation error")


