"""
UI Proxy for Sandbox: Exposes endpoints without HMAC for frontend use.
Ensure CORS and network access are restricted in production.
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
import structlog
import os
import aiofiles

from ..services.real_time_sandbox import RealTimeSandbox
from ..services.email_gateway_service import get_email_gateway_service, EmailGatewayService
from ..security.ui_guard import ui_guard
from ..security.jwt_auth import verify_jwt_admin


logger = structlog.get_logger()
router = APIRouter(prefix="/api/ui/sandbox", tags=["ui-sandbox"], dependencies=[Depends(ui_guard), Depends(verify_jwt_admin)])


@router.get("/status")
async def ui_sandbox_status(gateway_service: EmailGatewayService = Depends(get_email_gateway_service)):
    try:
        cape_enabled = bool(os.getenv('CAPE_ENABLED', 'false').lower() == 'true')
        return {
            'running': gateway_service.is_running if gateway_service else False,
            'cape_enabled': cape_enabled
        }
    except Exception as e:
        logger.error("UI sandbox status error", error=str(e))
        raise HTTPException(status_code=500, detail="Sandbox status error")


@router.post("/detonate-test")
async def ui_detonate_test_file(
    file: UploadFile = File(...),
    gateway_service: EmailGatewayService = Depends(get_email_gateway_service)
):
    try:
        suffix = os.path.splitext(file.filename)[1] if file.filename else ""
        async with aiofiles.tempfile.NamedTemporaryFile('wb', delete=False, suffix=suffix) as tmp:
            content = await file.read()
            await tmp.write(content)
            tmp_path = tmp.name
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
        logger.error("UI detonation error", error=str(e))
        raise HTTPException(status_code=500, detail="Detonation error")


