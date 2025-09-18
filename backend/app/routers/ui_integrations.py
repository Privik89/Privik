"""
UI Proxy for Integrations: start and status endpoints without HMAC.
Protected by UI guard (IP allowlist / role header).
"""

from fastapi import APIRouter, Depends, HTTPException
import structlog

from ..services.email_gateway_service import get_email_gateway_service, EmailGatewayService
from ..security.ui_guard import ui_guard
from ..security.jwt_auth import verify_jwt_admin
from ..database import SessionLocal
from ..models.integration_state import IntegrationState


logger = structlog.get_logger()
router = APIRouter(prefix="/api/ui/integrations", tags=["ui-integrations"], dependencies=[Depends(ui_guard), Depends(verify_jwt_admin)])


@router.post("/start")
async def ui_start_integrations(gateway_service: EmailGatewayService = Depends(get_email_gateway_service)):
  try:
    await gateway_service.email_integrations.start_monitoring()
    return {"status": "started"}
  except Exception as e:
    logger.error("UI start integrations error", error=str(e))
    raise HTTPException(status_code=500, detail="Failed to start integrations")


@router.get("/status")
async def ui_integrations_status(gateway_service: EmailGatewayService = Depends(get_email_gateway_service)):
  try:
    integrations = gateway_service.email_integrations.integrations if gateway_service.email_integrations else {}
    return {
      name: {
        "connected": integ.is_connected,
        "last_sync": getattr(integ, "last_sync", None)
        ,"errors": getattr(integ, "error_count", 0)
        ,"retry_backoff": getattr(integ, "retry_backoff", 0)
        ,"cursor": getattr(integ, "_cursor", None)
      }
      for name, integ in integrations.items()
    }
  except Exception as e:
    logger.error("UI integrations status error", error=str(e))
    raise HTTPException(status_code=500, detail="Failed to get integration status")


@router.post("/reconnect")
async def ui_reconnect(gateway_service: EmailGatewayService = Depends(get_email_gateway_service)):
  try:
    await gateway_service.email_integrations.initialize()
    return {"status": "reconnected"}
  except Exception as e:
    logger.error("UI reconnect error", error=str(e))
    raise HTTPException(status_code=500, detail="Failed to reconnect integrations")


@router.post("/reset-state")
async def ui_reset_state(name: str | None = None):
  db = SessionLocal()
  try:
    if name:
      st = db.query(IntegrationState).filter(IntegrationState.name == name).first()
      if st:
        db.delete(st)
    else:
      db.query(IntegrationState).delete()
    db.commit()
    return {"status": "reset"}
  finally:
    db.close()


@router.post("/toggles")
async def ui_set_integrations_toggles(
  gmail: bool | None = None,
  microsoft365: bool | None = None,
  imap: bool | None = None,
  gateway_service: EmailGatewayService = Depends(get_email_gateway_service)
):
  """Set desired toggles; in Phase 1, we update in-memory and return desired state.
  In production, persist to config store and reload services.
  """
  try:
    desired = {
      'gmail': bool(gmail) if gmail is not None else gateway_service.config.get('email_integrations', {}).get('gmail', {}).get('enabled', False),
      'microsoft365': bool(microsoft365) if microsoft365 is not None else gateway_service.config.get('email_integrations', {}).get('microsoft365', {}).get('enabled', False),
      'imap': bool(imap) if imap is not None else gateway_service.config.get('email_integrations', {}).get('imap', {}).get('enabled', False),
    }
    # Update in-memory config for current process lifetime
    gateway_service.config.setdefault('email_integrations', {})
    for name, flag in desired.items():
      gateway_service.config['email_integrations'].setdefault(name, {})['enabled'] = flag
    return { 'desired': desired }
  except Exception as e:
    logger.error("UI toggles error", error=str(e))
    raise HTTPException(status_code=500, detail="Failed to set toggles")


