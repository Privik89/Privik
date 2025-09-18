"""
UI Policies Proxy: Get/Update zero-trust policies via JWT/UI guard.
"""

from fastapi import APIRouter, Depends, HTTPException
import structlog
from typing import Optional, Dict

from ..services.email_gateway_service import get_email_gateway_service, EmailGatewayService
from ..security.ui_guard import ui_guard
from ..security.jwt_auth import verify_jwt_admin


logger = structlog.get_logger()
router = APIRouter(prefix="/api/ui/policies", tags=["ui-policies"], dependencies=[Depends(ui_guard), Depends(verify_jwt_admin)])


@router.get("")
async def get_policies(gateway_service: EmailGatewayService = Depends(get_email_gateway_service)):
    try:
        return gateway_service.zero_trust_policies
    except Exception as e:
        logger.error("Get policies error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get policies")


@router.post("/update")
async def update_policies(payload: Dict, gateway_service: EmailGatewayService = Depends(get_email_gateway_service)):
    try:
        await gateway_service.update_zero_trust_policies(payload)
        return {"status": "success"}
    except Exception as e:
        logger.error("Update policies error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update policies")


