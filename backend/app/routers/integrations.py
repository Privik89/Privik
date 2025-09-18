"""
Integrations Router: control and status for email ingestion connectors.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import structlog

from ..services.email_gateway_service import get_email_gateway_service, EmailGatewayService
from ..core.config import get_settings
from ..security.hmac_auth import verify_request


logger = structlog.get_logger()
router = APIRouter(prefix="/api/integrations", tags=["integrations"], dependencies=[Depends(verify_request)])


class IntegrationToggles(BaseModel):
    gmail: bool | None = None
    microsoft365: bool | None = None
    imap: bool | None = None


@router.post("/start")
async def start_integrations(gateway_service: EmailGatewayService = Depends(get_email_gateway_service)):
    try:
        await gateway_service.email_integrations.start_monitoring()
        return {"status": "started"}
    except Exception as e:
        logger.error("Failed to start integrations", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to start integrations")


@router.get("/status")
async def integrations_status(gateway_service: EmailGatewayService = Depends(get_email_gateway_service)):
    try:
        integrations = gateway_service.email_integrations.integrations if gateway_service.email_integrations else {}
        return {
            name: {
                "connected": integ.is_connected,
                "last_sync": getattr(integ, "last_sync", None)
            }
            for name, integ in integrations.items()
        }
    except Exception as e:
        logger.error("Failed to get integration status", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get integration status")


@router.post("/toggles")
async def set_integration_toggles(payload: IntegrationToggles):
    try:
        settings = get_settings()
        # Note: Settings is cached; for phase 1, we only return desired state.
        desired = {
            "gmail": payload.gmail if payload.gmail is not None else settings.enable_gmail_ingest,
            "microsoft365": payload.microsoft365 if payload.microsoft365 is not None else settings.enable_o365_ingest,
            "imap": payload.imap if payload.imap is not None else settings.enable_imap_ingest,
        }
        return {"desired": desired, "note": "Apply via environment or config reload in production"}
    except Exception as e:
        logger.error("Failed to set toggles", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to set toggles")


