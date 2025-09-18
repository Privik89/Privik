"""
Quarantine API Router
Manages email quarantine operations
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Any
from ..database import get_db
from ..security.hmac_auth import verify_request
from ..services.quarantine_manager import QuarantineManager
from ..models.quarantine import EmailQuarantine, QuarantineAction
from ..models.email import Email
import structlog

logger = structlog.get_logger()
router = APIRouter()

@router.get("/quarantine")
async def list_quarantined_emails(
    status: Optional[str] = Query(None, description="Filter by quarantine status"),
    reason: Optional[str] = Query(None, description="Filter by quarantine reason"),
    limit: int = Query(100, description="Maximum number of emails to return"),
    offset: int = Query(0, description="Number of emails to skip"),
    db: Session = Depends(get_db),
    _: dict = Depends(verify_request)
):
    """List quarantined emails"""
    try:
        query = db.query(EmailQuarantine)
        
        if status:
            query = query.filter(EmailQuarantine.status == status)
        
        if reason:
            query = query.filter(EmailQuarantine.quarantine_reason == reason)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        quarantined_emails = query.order_by(
            EmailQuarantine.created_at.desc()
        ).offset(offset).limit(limit).all()
        
        return {
            "emails": [
                {
                    "id": q.id,
                    "email_id": q.email_id,
                    "quarantine_reason": q.quarantine_reason,
                    "threat_score": q.threat_score,
                    "confidence": q.confidence,
                    "status": q.status,
                    "quarantined_at": q.quarantined_at.isoformat(),
                    "quarantined_by": q.quarantined_by,
                    "quarantine_duration": q.quarantine_duration,
                    "reviewed_at": q.reviewed_at.isoformat() if q.reviewed_at else None,
                    "reviewed_by": q.reviewed_by,
                    "action_taken": q.action_taken,
                    "action_reason": q.action_reason,
                    "analysis_details": q.analysis_details
                }
                for q in quarantined_emails
            ],
            "total_count": total_count,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error("Error listing quarantined emails", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/quarantine/{quarantine_id}")
async def get_quarantined_email(
    quarantine_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_request)
):
    """Get details of a quarantined email"""
    try:
        quarantine = db.query(EmailQuarantine).filter(
            EmailQuarantine.id == quarantine_id
        ).first()
        
        if not quarantine:
            raise HTTPException(status_code=404, detail="Quarantine record not found")
        
        # Get email details
        email = db.query(Email).filter(Email.id == quarantine.email_id).first()
        
        return {
            "quarantine": {
                "id": quarantine.id,
                "email_id": quarantine.email_id,
                "quarantine_reason": quarantine.quarantine_reason,
                "threat_score": quarantine.threat_score,
                "confidence": quarantine.confidence,
                "status": quarantine.status,
                "quarantined_at": quarantine.quarantined_at.isoformat(),
                "quarantined_by": quarantine.quarantined_by,
                "quarantine_duration": quarantine.quarantine_duration,
                "reviewed_at": quarantine.reviewed_at.isoformat() if quarantine.reviewed_at else None,
                "reviewed_by": quarantine.reviewed_by,
                "review_notes": quarantine.review_notes,
                "action_taken": quarantine.action_taken,
                "action_reason": quarantine.action_reason,
                "action_taken_at": quarantine.action_taken_at.isoformat() if quarantine.action_taken_at else None,
                "action_taken_by": quarantine.action_taken_by,
                "analysis_details": quarantine.analysis_details,
                "user_notified": quarantine.user_notified
            },
            "email": {
                "id": email.id if email else None,
                "subject": email.subject if email else None,
                "sender": email.sender if email else None,
                "recipients": email.recipients if email else None,
                "message_id": email.message_id if email else None,
                "received_at": email.received_at.isoformat() if email and email.received_at else None,
                "content_preview": email.content[:500] if email and email.content else None
            } if email else None
        }
        
    except Exception as e:
        logger.error("Error getting quarantined email", quarantine_id=quarantine_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/quarantine/{quarantine_id}/release")
async def release_quarantined_email(
    quarantine_id: int,
    released_by: str,
    release_reason: Optional[str] = None,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_request)
):
    """Release an email from quarantine"""
    try:
        async with QuarantineManager() as manager:
            success = await manager.release_email(
                quarantine_id=quarantine_id,
                released_by=released_by,
                release_reason=release_reason
            )
            
            if success:
                return {"message": "Email released from quarantine successfully"}
            else:
                raise HTTPException(status_code=500, detail="Failed to release email")
        
    except Exception as e:
        logger.error("Error releasing email", quarantine_id=quarantine_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to release email: {str(e)}")

@router.post("/quarantine/{quarantine_id}/delete")
async def delete_quarantined_email(
    quarantine_id: int,
    deleted_by: str,
    delete_reason: Optional[str] = None,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_request)
):
    """Delete a quarantined email"""
    try:
        async with QuarantineManager() as manager:
            success = await manager.delete_quarantined_email(
                quarantine_id=quarantine_id,
                deleted_by=deleted_by,
                delete_reason=delete_reason
            )
            
            if success:
                return {"message": "Quarantined email deleted successfully"}
            else:
                raise HTTPException(status_code=500, detail="Failed to delete email")
        
    except Exception as e:
        logger.error("Error deleting quarantined email", quarantine_id=quarantine_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to delete email: {str(e)}")

@router.post("/quarantine/{quarantine_id}/whitelist")
async def whitelist_sender(
    quarantine_id: int,
    whitelisted_by: str,
    whitelist_reason: Optional[str] = None,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_request)
):
    """Whitelist sender and release email"""
    try:
        async with QuarantineManager() as manager:
            success = await manager.whitelist_sender(
                quarantine_id=quarantine_id,
                whitelisted_by=whitelisted_by,
                whitelist_reason=whitelist_reason
            )
            
            if success:
                return {"message": "Sender whitelisted and email released successfully"}
            else:
                raise HTTPException(status_code=500, detail="Failed to whitelist sender")
        
    except Exception as e:
        logger.error("Error whitelisting sender", quarantine_id=quarantine_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to whitelist sender: {str(e)}")

@router.post("/quarantine/{quarantine_id}/blacklist")
async def blacklist_sender(
    quarantine_id: int,
    blacklisted_by: str,
    blacklist_reason: Optional[str] = None,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_request)
):
    """Blacklist sender and delete email"""
    try:
        async with QuarantineManager() as manager:
            success = await manager.blacklist_sender(
                quarantine_id=quarantine_id,
                blacklisted_by=blacklisted_by,
                blacklist_reason=blacklist_reason
            )
            
            if success:
                return {"message": "Sender blacklisted and email deleted successfully"}
            else:
                raise HTTPException(status_code=500, detail="Failed to blacklist sender")
        
    except Exception as e:
        logger.error("Error blacklisting sender", quarantine_id=quarantine_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to blacklist sender: {str(e)}")

@router.post("/quarantine/bulk-action")
async def bulk_quarantine_action(
    quarantine_ids: List[int],
    action: str,
    performed_by: str,
    action_reason: Optional[str] = None,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_request)
):
    """Perform bulk action on quarantined emails"""
    try:
        if len(quarantine_ids) > 100:
            raise HTTPException(status_code=400, detail="Maximum 100 emails per bulk action")
        
        if action not in ['release', 'delete', 'whitelist', 'blacklist']:
            raise HTTPException(status_code=400, detail="Invalid action")
        
        async with QuarantineManager() as manager:
            result = await manager.bulk_quarantine_action(
                quarantine_ids=quarantine_ids,
                action=action,
                performed_by=performed_by,
                action_reason=action_reason
            )
            
            return result
        
    except Exception as e:
        logger.error("Error in bulk quarantine action", error=str(e))
        raise HTTPException(status_code=500, detail=f"Bulk action failed: {str(e)}")

@router.get("/quarantine/statistics")
async def get_quarantine_statistics(
    db: Session = Depends(get_db),
    _: dict = Depends(verify_request)
):
    """Get quarantine statistics"""
    try:
        async with QuarantineManager() as manager:
            stats = await manager.get_quarantine_statistics()
            return stats
        
    except Exception as e:
        logger.error("Error getting quarantine statistics", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")
