"""
Email Gateway API Router
REST API endpoints for email gateway operations
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import structlog

from ..services.email_gateway_service import get_email_gateway_service, EmailGatewayService, EmailAction
from ..database import get_db
from sqlalchemy.orm import Session

logger = structlog.get_logger()
router = APIRouter(prefix="/api/email-gateway", tags=["email-gateway"])


class EmailProcessingRequest(BaseModel):
    """Request model for email processing"""
    message_id: str
    subject: str
    sender: str
    recipients: str
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    source: Optional[str] = "api"


class EmailProcessingResponse(BaseModel):
    """Response model for email processing"""
    email_id: str
    action: str
    threat_score: float
    threat_type: str
    confidence: float
    indicators: List[str]
    processing_time: float
    sandbox_result: Optional[Dict[str, Any]] = None
    ai_analysis: Optional[Dict[str, Any]] = None


class ZeroTrustPolicyUpdate(BaseModel):
    """Model for updating zero-trust policies"""
    default_action: Optional[str] = None
    threat_thresholds: Optional[Dict[str, float]] = None
    whitelist_domains: Optional[List[str]] = None
    blacklist_domains: Optional[List[str]] = None
    suspicious_keywords: Optional[List[str]] = None


class EmailGatewayStats(BaseModel):
    """Model for email gateway statistics"""
    emails_processed: int
    threats_detected: int
    emails_quarantined: int
    emails_blocked: int
    processing_time_avg: float


@router.post("/process", response_model=EmailProcessingResponse)
async def process_email(
    email_request: EmailProcessingRequest,
    background_tasks: BackgroundTasks,
    gateway_service: EmailGatewayService = Depends(get_email_gateway_service)
):
    """Process an email through the threat detection pipeline"""
    try:
        # Convert request to email data
        email_data = {
            'message_id': email_request.message_id,
            'subject': email_request.subject,
            'sender': email_request.sender,
            'recipients': email_request.recipients,
            'body_text': email_request.body_text,
            'body_html': email_request.body_html,
            'attachments': email_request.attachments or [],
            'source': email_request.source
        }
        
        # Process email
        result = await gateway_service.process_email(email_data)
        
        return EmailProcessingResponse(
            email_id=result.email_id,
            action=result.action.value,
            threat_score=result.threat_score,
            threat_type=result.threat_type,
            confidence=result.confidence,
            indicators=result.indicators,
            processing_time=result.processing_time,
            sandbox_result=result.sandbox_result,
            ai_analysis=result.ai_analysis
        )
        
    except Exception as e:
        logger.error(f"Error processing email: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing email: {str(e)}")


@router.post("/process-async")
async def process_email_async(
    email_request: EmailProcessingRequest,
    background_tasks: BackgroundTasks,
    gateway_service: EmailGatewayService = Depends(get_email_gateway_service)
):
    """Process an email asynchronously"""
    try:
        # Convert request to email data
        email_data = {
            'message_id': email_request.message_id,
            'subject': email_request.subject,
            'sender': email_request.sender,
            'recipients': email_request.recipients,
            'body_text': email_request.body_text,
            'body_html': email_request.body_html,
            'attachments': email_request.attachments or [],
            'source': email_request.source
        }
        
        # Add to processing queue
        await gateway_service.add_to_processing_queue(email_data)
        
        return {"status": "queued", "message": "Email added to processing queue"}
        
    except Exception as e:
        logger.error(f"Error queuing email: {e}")
        raise HTTPException(status_code=500, detail=f"Error queuing email: {str(e)}")


@router.get("/statistics", response_model=EmailGatewayStats)
async def get_statistics(
    gateway_service: EmailGatewayService = Depends(get_email_gateway_service)
):
    """Get email gateway processing statistics"""
    try:
        stats = await gateway_service.get_statistics()
        return EmailGatewayStats(**stats)
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting statistics: {str(e)}")


@router.post("/policies/update")
async def update_zero_trust_policies(
    policy_update: ZeroTrustPolicyUpdate,
    gateway_service: EmailGatewayService = Depends(get_email_gateway_service)
):
    """Update zero-trust policies"""
    try:
        # Convert to dict, filtering out None values
        policies = {k: v for k, v in policy_update.dict().items() if v is not None}
        
        await gateway_service.update_zero_trust_policies(policies)
        
        return {"status": "success", "message": "Zero-trust policies updated"}
        
    except Exception as e:
        logger.error(f"Error updating policies: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating policies: {str(e)}")


@router.get("/policies")
async def get_zero_trust_policies(
    gateway_service: EmailGatewayService = Depends(get_email_gateway_service)
):
    """Get current zero-trust policies"""
    try:
        return gateway_service.zero_trust_policies
        
    except Exception as e:
        logger.error(f"Error getting policies: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting policies: {str(e)}")


@router.post("/start")
async def start_email_gateway(
    gateway_service: EmailGatewayService = Depends(get_email_gateway_service)
):
    """Start the email gateway service"""
    try:
        if not gateway_service.is_running:
            # Start in background
            import asyncio
            asyncio.create_task(gateway_service.start())
            return {"status": "success", "message": "Email gateway service started"}
        else:
            return {"status": "already_running", "message": "Email gateway service is already running"}
            
    except Exception as e:
        logger.error(f"Error starting email gateway: {e}")
        raise HTTPException(status_code=500, detail=f"Error starting email gateway: {str(e)}")


@router.post("/stop")
async def stop_email_gateway(
    gateway_service: EmailGatewayService = Depends(get_email_gateway_service)
):
    """Stop the email gateway service"""
    try:
        if gateway_service.is_running:
            await gateway_service.stop()
            return {"status": "success", "message": "Email gateway service stopped"}
        else:
            return {"status": "not_running", "message": "Email gateway service is not running"}
            
    except Exception as e:
        logger.error(f"Error stopping email gateway: {e}")
        raise HTTPException(status_code=500, detail=f"Error stopping email gateway: {str(e)}")


@router.get("/status")
async def get_gateway_status(
    gateway_service: EmailGatewayService = Depends(get_email_gateway_service)
):
    """Get email gateway service status"""
    try:
        return {
            "is_running": gateway_service.is_running,
            "integrations_connected": len([i for i in gateway_service.email_integrations.integrations.values() if i.is_connected]) if gateway_service.email_integrations else 0,
            "ai_models_loaded": len(gateway_service.ai_threat_detection.models) if gateway_service.ai_threat_detection else 0,
            "sandbox_available": gateway_service.sandbox_service is not None
        }
        
    except Exception as e:
        logger.error(f"Error getting gateway status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting gateway status: {str(e)}")


@router.post("/test-email")
async def test_email_processing(
    gateway_service: EmailGatewayService = Depends(get_email_gateway_service)
):
    """Test email processing with a sample email"""
    try:
        # Create test email data
        test_email = {
            'message_id': 'test-email-001',
            'subject': 'Test Email - Urgent Action Required',
            'sender': 'test@example.com',
            'recipients': 'user@company.com',
            'body_text': 'This is a test email to verify the email gateway functionality.',
            'body_html': '<p>This is a test email to verify the email gateway functionality.</p>',
            'attachments': [],
            'source': 'test'
        }
        
        # Process test email
        result = await gateway_service.process_email(test_email)
        
        return {
            "status": "success",
            "test_result": {
                "email_id": result.email_id,
                "action": result.action.value,
                "threat_score": result.threat_score,
                "threat_type": result.threat_type,
                "confidence": result.confidence,
                "indicators": result.indicators,
                "processing_time": result.processing_time
            }
        }
        
    except Exception as e:
        logger.error(f"Error testing email processing: {e}")
        raise HTTPException(status_code=500, detail=f"Error testing email processing: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint for email gateway"""
    return {
        "status": "healthy",
        "service": "email-gateway",
        "timestamp": "2025-01-09T01:00:00Z"
    }
