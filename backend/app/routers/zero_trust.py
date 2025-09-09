"""
Zero-Trust API Router
Provides endpoints for zero-trust email security operations
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel

from ..database import get_db
from ..services.zero_trust_orchestrator import ZeroTrustOrchestrator
from ..core.config import get_settings

router = APIRouter(prefix="/zero-trust", tags=["zero-trust"])
settings = get_settings()

# Initialize zero-trust orchestrator
zero_trust_config = {
    'email_gateway': {
        'link_rewrite_domain': 'links.privik.com',
        'attachment_storage': '/tmp/attachments',
        'zero_trust_policies': {
            'internal_domains': ['company.com', 'internal.com'],
            'high_risk_users': ['ceo@company.com', 'cfo@company.com'],
            'blocked_senders': []
        }
    },
    'sandbox': {
        'max_concurrent_sandboxes': 10,
        'sandbox_timeout': 300
    },
    'ai_detection': {
        'model_storage_path': './models',
        'retrain_interval': 7,
        'min_training_samples': 1000
    },
    'zero_trust_policies': {
        'enforcement_level': 'strict',
        'internal_domains': ['company.com', 'internal.com'],
        'high_risk_users': ['ceo@company.com', 'cfo@company.com']
    }
}

zero_trust_orchestrator = ZeroTrustOrchestrator(zero_trust_config)


class EmailProcessingRequest(BaseModel):
    message_id: str
    subject: str
    sender: str
    recipients: List[str]
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    headers: Optional[Dict[str, str]] = None


class LinkClickRequest(BaseModel):
    url: str
    user_id: str
    user_context: Optional[Dict[str, Any]] = None
    email_context: Optional[Dict[str, Any]] = None


class AttachmentRequest(BaseModel):
    filename: str
    file_path: str
    file_type: str
    file_size: int
    user_id: str
    user_context: Optional[Dict[str, Any]] = None


class ZeroTrustResponse(BaseModel):
    action: str
    confidence: float
    threat_score: float
    threat_type: str
    indicators: List[str]
    processing_time: float
    analysis_details: Dict[str, Any]


@router.on_event("startup")
async def startup_event():
    """Initialize zero-trust orchestrator on startup"""
    try:
        await zero_trust_orchestrator.initialize()
    except Exception as e:
        print(f"Failed to initialize zero-trust orchestrator: {e}")


@router.post("/email/process", response_model=ZeroTrustResponse)
async def process_email(
    request: EmailProcessingRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Process email through zero-trust pipeline"""
    try:
        # Convert request to email data
        email_data = {
            'message_id': request.message_id,
            'subject': request.subject,
            'sender': request.sender,
            'recipients': request.recipients,
            'body_text': request.body_text,
            'body_html': request.body_html,
            'attachments': request.attachments or [],
            'headers': request.headers or {},
            'has_links': bool(request.body_text and 'http' in request.body_text),
            'has_attachments': bool(request.attachments)
        }
        
        # Process through zero-trust pipeline
        result = await zero_trust_orchestrator.process_email(email_data)
        
        # Store result in database (background task)
        background_tasks.add_task(store_email_result, email_data, result, db)
        
        return ZeroTrustResponse(
            action=result.action,
            confidence=result.confidence,
            threat_score=result.threat_score,
            threat_type=result.threat_type,
            indicators=result.indicators,
            processing_time=result.processing_time,
            analysis_details=result.analysis_details
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing email: {str(e)}")


@router.post("/link/click", response_model=ZeroTrustResponse)
async def process_link_click(
    request: LinkClickRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Process link click through zero-trust pipeline"""
    try:
        # Convert request to click data
        click_data = {
            'url': request.url,
            'user_id': request.user_id,
            'user_context': request.user_context or {},
            'email_context': request.email_context or {},
            'timestamp': datetime.utcnow()
        }
        
        # Process through zero-trust pipeline
        result = await zero_trust_orchestrator.process_link_click(click_data)
        
        # Store result in database (background task)
        background_tasks.add_task(store_link_result, click_data, result, db)
        
        return ZeroTrustResponse(
            action=result.action,
            confidence=result.confidence,
            threat_score=result.threat_score,
            threat_type=result.threat_type,
            indicators=result.indicators,
            processing_time=result.processing_time,
            analysis_details=result.analysis_details
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing link click: {str(e)}")


@router.post("/attachment/process", response_model=ZeroTrustResponse)
async def process_attachment(
    request: AttachmentRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Process attachment through zero-trust pipeline"""
    try:
        # Convert request to attachment data
        attachment_data = {
            'filename': request.filename,
            'file_path': request.file_path,
            'file_type': request.file_type,
            'file_size': request.file_size,
            'user_id': request.user_id,
            'user_context': request.user_context or {},
            'timestamp': datetime.utcnow()
        }
        
        # Process through zero-trust pipeline
        result = await zero_trust_orchestrator.process_attachment(attachment_data)
        
        # Store result in database (background task)
        background_tasks.add_task(store_attachment_result, attachment_data, result, db)
        
        return ZeroTrustResponse(
            action=result.action,
            confidence=result.confidence,
            threat_score=result.threat_score,
            threat_type=result.threat_type,
            indicators=result.indicators,
            processing_time=result.processing_time,
            analysis_details=result.analysis_details
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing attachment: {str(e)}")


@router.get("/statistics")
async def get_zero_trust_statistics():
    """Get zero-trust processing statistics"""
    try:
        stats = await zero_trust_orchestrator.get_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting statistics: {str(e)}")


@router.put("/policies")
async def update_zero_trust_policies(policies: Dict[str, Any]):
    """Update zero-trust policies"""
    try:
        await zero_trust_orchestrator.update_policies(policies)
        return {"status": "success", "message": "Policies updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating policies: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check for zero-trust system"""
    try:
        stats = await zero_trust_orchestrator.get_statistics()
        return {
            "status": "healthy",
            "components": stats.get('components_status', {}),
            "total_processed": stats.get('total_processed', 0),
            "enforcement_level": stats.get('enforcement_level', 'unknown')
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# Background tasks for storing results
async def store_email_result(email_data: Dict[str, Any], result: Any, db: Session):
    """Store email processing result in database"""
    try:
        # This would store the result in your database
        # Implementation depends on your database schema
        pass
    except Exception as e:
        print(f"Error storing email result: {e}")


async def store_link_result(click_data: Dict[str, Any], result: Any, db: Session):
    """Store link click result in database"""
    try:
        # This would store the result in your database
        # Implementation depends on your database schema
        pass
    except Exception as e:
        print(f"Error storing link result: {e}")


async def store_attachment_result(attachment_data: Dict[str, Any], result: Any, db: Session):
    """Store attachment result in database"""
    try:
        # This would store the result in your database
        # Implementation depends on your database schema
        pass
    except Exception as e:
        print(f"Error storing attachment result: {e}")


# Additional endpoints for advanced features

@router.post("/email/batch-process")
async def batch_process_emails(
    requests: List[EmailProcessingRequest],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Process multiple emails in batch"""
    try:
        results = []
        
        for request in requests:
            email_data = {
                'message_id': request.message_id,
                'subject': request.subject,
                'sender': request.sender,
                'recipients': request.recipients,
                'body_text': request.body_text,
                'body_html': request.body_html,
                'attachments': request.attachments or [],
                'headers': request.headers or {},
                'has_links': bool(request.body_text and 'http' in request.body_text),
                'has_attachments': bool(request.attachments)
            }
            
            result = await zero_trust_orchestrator.process_email(email_data)
            results.append(ZeroTrustResponse(
                action=result.action,
                confidence=result.confidence,
                threat_score=result.threat_score,
                threat_type=result.threat_type,
                indicators=result.indicators,
                processing_time=result.processing_time,
                analysis_details=result.analysis_details
            ))
            
            # Store result in background
            background_tasks.add_task(store_email_result, email_data, result, db)
        
        return {"results": results, "total_processed": len(results)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error batch processing emails: {str(e)}")


@router.get("/models/status")
async def get_model_status():
    """Get AI model status and metrics"""
    try:
        # Get model metrics from AI detection system
        model_metrics = await zero_trust_orchestrator.ai_detection.get_model_metrics()
        return {
            "models": model_metrics,
            "status": "active"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting model status: {str(e)}")


@router.post("/models/retrain")
async def retrain_models(training_data: Dict[str, Any]):
    """Retrain AI models with new data"""
    try:
        await zero_trust_orchestrator.ai_detection.retrain_models(training_data)
        return {"status": "success", "message": "Models retrained successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retraining models: {str(e)}")


@router.get("/policies/current")
async def get_current_policies():
    """Get current zero-trust policies"""
    try:
        return {
            "policies": zero_trust_orchestrator.policies,
            "enforcement_level": zero_trust_orchestrator.enforcement_level
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting policies: {str(e)}")


@router.post("/test/email")
async def test_email_processing(email_data: Dict[str, Any]):
    """Test email processing with sample data"""
    try:
        result = await zero_trust_orchestrator.process_email(email_data)
        return {
            "test_result": ZeroTrustResponse(
                action=result.action,
                confidence=result.confidence,
                threat_score=result.threat_score,
                threat_type=result.threat_type,
                indicators=result.indicators,
                processing_time=result.processing_time,
                analysis_details=result.analysis_details
            ),
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error testing email processing: {str(e)}")


@router.post("/test/link")
async def test_link_processing(click_data: Dict[str, Any]):
    """Test link processing with sample data"""
    try:
        result = await zero_trust_orchestrator.process_link_click(click_data)
        return {
            "test_result": ZeroTrustResponse(
                action=result.action,
                confidence=result.confidence,
                threat_score=result.threat_score,
                threat_type=result.threat_type,
                indicators=result.indicators,
                processing_time=result.processing_time,
                analysis_details=result.analysis_details
            ),
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error testing link processing: {str(e)}")


@router.post("/test/attachment")
async def test_attachment_processing(attachment_data: Dict[str, Any]):
    """Test attachment processing with sample data"""
    try:
        result = await zero_trust_orchestrator.process_attachment(attachment_data)
        return {
            "test_result": ZeroTrustResponse(
                action=result.action,
                confidence=result.confidence,
                threat_score=result.threat_score,
                threat_type=result.threat_type,
                indicators=result.indicators,
                processing_time=result.processing_time,
                analysis_details=result.analysis_details
            ),
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error testing attachment processing: {str(e)}")
