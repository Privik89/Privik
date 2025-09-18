"""
Threat Feeds API Router
Manages threat intelligence feeds and real-time updates
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Any
from ..database import get_db
from ..security.hmac_auth import verify_request
from ..services.threat_feed_manager import ThreatFeedManager
from ..models.threat_feed import ThreatFeed, ThreatFeedRecord
import structlog

logger = structlog.get_logger()
router = APIRouter()

@router.get("/feeds")
async def list_threat_feeds(
    active_only: bool = Query(True, description="Show only active feeds"),
    db: Session = Depends(get_db),
    _: dict = Depends(verify_request)
):
    """List all threat feeds"""
    try:
        query = db.query(ThreatFeed)
        if active_only:
            query = query.filter(ThreatFeed.is_active == True)
        
        feeds = query.order_by(ThreatFeed.created_at.desc()).all()
        
        return {
            "feeds": [
                {
                    "id": feed.id,
                    "name": feed.name,
                    "source_type": feed.source_type,
                    "category": feed.category,
                    "description": feed.description,
                    "status": feed.status,
                    "last_updated": feed.last_updated.isoformat() if feed.last_updated else None,
                    "next_update": feed.next_update.isoformat() if feed.next_update else None,
                    "total_records": feed.total_records,
                    "error_count": feed.error_count,
                    "is_active": feed.is_active,
                    "created_at": feed.created_at.isoformat() if feed.created_at else None
                }
                for feed in feeds
            ]
        }
        
    except Exception as e:
        logger.error("Error listing threat feeds", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/feeds")
async def create_threat_feed(
    name: str,
    source_type: str,
    feed_url: Optional[str] = None,
    webhook_url: Optional[str] = None,
    api_key: Optional[str] = None,
    category: Optional[str] = None,
    description: Optional[str] = None,
    update_interval: int = 3600,
    confidence_threshold: float = 0.7,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_request)
):
    """Create a new threat feed"""
    try:
        if source_type not in ['webhook', 'api', 'file']:
            raise HTTPException(status_code=400, detail="source_type must be 'webhook', 'api', or 'file'")
        
        # Check if feed name already exists
        existing = db.query(ThreatFeed).filter(ThreatFeed.name == name).first()
        if existing:
            raise HTTPException(status_code=409, detail="Feed name already exists")
        
        async with ThreatFeedManager() as manager:
            feed = await manager.create_feed(
                name=name,
                source_type=source_type,
                feed_url=feed_url,
                webhook_url=webhook_url,
                api_key=api_key,
                category=category,
                description=description
            )
            
            # Update additional properties
            feed.update_interval = update_interval
            feed.confidence_threshold = confidence_threshold
            db.commit()
            
            return {
                "message": "Threat feed created successfully",
                "feed_id": feed.id,
                "feed_name": feed.name
            }
        
    except Exception as e:
        logger.error("Error creating threat feed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create feed: {str(e)}")

@router.delete("/feeds/{feed_id}")
async def delete_threat_feed(
    feed_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_request)
):
    """Delete a threat feed"""
    try:
        async with ThreatFeedManager() as manager:
            await manager.delete_feed(feed_id)
            
            return {"message": "Threat feed deleted successfully"}
        
    except Exception as e:
        logger.error("Error deleting threat feed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to delete feed: {str(e)}")

@router.get("/feeds/status")
async def get_feed_status(
    db: Session = Depends(get_db),
    _: dict = Depends(verify_request)
):
    """Get overall threat feed status"""
    try:
        async with ThreatFeedManager() as manager:
            status = await manager.get_feed_status()
            return status
        
    except Exception as e:
        logger.error("Error getting feed status", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/feeds/{feed_id}/update")
async def manual_feed_update(
    feed_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_request)
):
    """Manually trigger feed update"""
    try:
        feed = db.query(ThreatFeed).filter(ThreatFeed.id == feed_id).first()
        if not feed:
            raise HTTPException(status_code=404, detail="Feed not found")
        
        async with ThreatFeedManager() as manager:
            await manager._process_single_feed(feed)
            
            return {"message": "Feed updated successfully"}
        
    except Exception as e:
        logger.error("Error updating feed", feed_id=feed_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to update feed: {str(e)}")

@router.get("/feeds/{feed_id}/records")
async def get_feed_records(
    feed_id: int,
    indicator_type: Optional[str] = Query(None, description="Filter by indicator type"),
    limit: int = Query(100, description="Maximum number of records"),
    db: Session = Depends(get_db),
    _: dict = Depends(verify_request)
):
    """Get records from a specific threat feed"""
    try:
        query = db.query(ThreatFeedRecord).filter(ThreatFeedRecord.feed_id == feed_id)
        
        if indicator_type:
            query = query.filter(ThreatFeedRecord.indicator_type == indicator_type)
        
        records = query.order_by(ThreatFeedRecord.last_seen.desc()).limit(limit).all()
        
        return {
            "feed_id": feed_id,
            "records": [
                {
                    "id": record.id,
                    "indicator": record.indicator,
                    "indicator_type": record.indicator_type,
                    "threat_type": record.threat_type,
                    "confidence": record.confidence,
                    "severity": record.severity,
                    "description": record.description,
                    "tags": record.tags,
                    "first_seen": record.first_seen.isoformat(),
                    "last_seen": record.last_seen.isoformat(),
                    "expires_at": record.expires_at.isoformat() if record.expires_at else None
                }
                for record in records
            ]
        }
        
    except Exception as e:
        logger.error("Error getting feed records", feed_id=feed_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/feeds/{feed_name}/webhook")
async def webhook_update(
    feed_name: str,
    webhook_data: Any,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_request)
):
    """Receive webhook update for a threat feed"""
    try:
        async with ThreatFeedManager() as manager:
            await manager.add_webhook_update(feed_name, webhook_data)
            
            return {"message": "Webhook update processed successfully"}
        
    except Exception as e:
        logger.error("Error processing webhook", feed_name=feed_name, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to process webhook: {str(e)}")
