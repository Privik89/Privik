"""
Incident Correlation API Router
Manages security incident correlation and timeline analysis
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Any
from ..database import get_db
from ..security.hmac_auth import verify_request
from ..services.incident_correlation import IncidentCorrelationService
from ..models.incident_correlation import SecurityIncident, IncidentTimelineEvent
from datetime import datetime
import structlog

logger = structlog.get_logger()
router = APIRouter()

@router.get("/incidents")
async def list_incidents(
    incident_type: Optional[str] = Query(None, description="Filter by incident type"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, description="Maximum number of incidents to return"),
    offset: int = Query(0, description="Number of incidents to skip"),
    db: Session = Depends(get_db),
    _: dict = Depends(verify_request)
):
    """List security incidents"""
    try:
        query = db.query(SecurityIncident)
        
        if incident_type:
            query = query.filter(SecurityIncident.incident_type == incident_type)
        
        if severity:
            query = query.filter(SecurityIncident.severity == severity)
        
        if status:
            query = query.filter(SecurityIncident.status == status)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        incidents = query.order_by(
            SecurityIncident.created_at.desc()
        ).offset(offset).limit(limit).all()
        
        return {
            "incidents": [
                {
                    "id": incident.id,
                    "incident_id": incident.incident_id,
                    "incident_type": incident.incident_type,
                    "severity": incident.severity,
                    "status": incident.status,
                    "title": incident.title,
                    "description": incident.description,
                    "first_seen": incident.first_seen.isoformat(),
                    "last_seen": incident.last_seen.isoformat(),
                    "confidence_score": incident.confidence_score,
                    "assigned_to": incident.assigned_to,
                    "created_at": incident.created_at.isoformat(),
                    "email_count": len(incident.emails) if incident.emails else 0
                }
                for incident in incidents
            ],
            "total_count": total_count,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error("Error listing incidents", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/incidents/{incident_id}")
async def get_incident_details(
    incident_id: str,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_request)
):
    """Get details of a specific incident"""
    try:
        incident = db.query(SecurityIncident).filter(
            SecurityIncident.incident_id == incident_id
        ).first()
        
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
        
        # Get related emails
        emails = []
        for email in incident.emails:
            emails.append({
                "id": email.id,
                "subject": email.subject,
                "sender": email.sender,
                "recipients": email.recipients,
                "received_at": email.received_at.isoformat() if email.received_at else None,
                "threat_score": email.threat_score,
                "ai_verdict": email.ai_verdict
            })
        
        # Get correlations
        correlations = []
        for correlation in incident.correlations:
            correlations.append({
                "id": correlation.id,
                "correlation_type": correlation.correlation_type,
                "correlation_value": correlation.correlation_value,
                "correlation_confidence": correlation.correlation_confidence,
                "first_correlated": correlation.first_correlated.isoformat(),
                "last_correlated": correlation.last_correlated.isoformat()
            })
        
        return {
            "incident": {
                "id": incident.id,
                "incident_id": incident.incident_id,
                "incident_type": incident.incident_type,
                "severity": incident.severity,
                "status": incident.status,
                "title": incident.title,
                "description": incident.description,
                "summary": incident.summary,
                "threat_actors": incident.threat_actors,
                "attack_vectors": incident.attack_vectors,
                "indicators": incident.indicators,
                "confidence_score": incident.confidence_score,
                "correlation_factors": incident.correlation_factors,
                "first_seen": incident.first_seen.isoformat(),
                "last_seen": incident.last_seen.isoformat(),
                "assigned_to": incident.assigned_to,
                "assigned_at": incident.assigned_at.isoformat() if incident.assigned_at else None,
                "resolved_at": incident.resolved_at.isoformat() if incident.resolved_at else None,
                "resolved_by": incident.resolved_by,
                "tags": incident.tags,
                "notes": incident.notes,
                "created_at": incident.created_at.isoformat(),
                "updated_at": incident.updated_at.isoformat()
            },
            "emails": emails,
            "correlations": correlations
        }
        
    except Exception as e:
        logger.error("Error getting incident details", incident_id=incident_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/incidents/{incident_id}/timeline")
async def get_incident_timeline(
    incident_id: str,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_request)
):
    """Get timeline for a specific incident"""
    try:
        async with IncidentCorrelationService() as service:
            timeline = await service.get_incident_timeline(incident_id)
            return timeline
        
    except Exception as e:
        logger.error("Error getting incident timeline", incident_id=incident_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/incidents/{incident_id}/assign")
async def assign_incident(
    incident_id: str,
    assigned_to: str,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_request)
):
    """Assign incident to a user"""
    try:
        incident = db.query(SecurityIncident).filter(
            SecurityIncident.incident_id == incident_id
        ).first()
        
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
        
        incident.assigned_to = assigned_to
        incident.assigned_at = datetime.utcnow()
        
        db.commit()
        
        return {"message": "Incident assigned successfully"}
        
    except Exception as e:
        logger.error("Error assigning incident", incident_id=incident_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/incidents/{incident_id}/resolve")
async def resolve_incident(
    incident_id: str,
    resolved_by: str,
    resolution_notes: Optional[str] = None,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_request)
):
    """Resolve an incident"""
    try:
        incident = db.query(SecurityIncident).filter(
            SecurityIncident.incident_id == incident_id
        ).first()
        
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
        
        incident.status = 'resolved'
        incident.resolved_at = datetime.utcnow()
        incident.resolved_by = resolved_by
        incident.notes = resolution_notes
        
        db.commit()
        
        return {"message": "Incident resolved successfully"}
        
    except Exception as e:
        logger.error("Error resolving incident", incident_id=incident_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/incidents/statistics")
async def get_incident_statistics(
    db: Session = Depends(get_db),
    _: dict = Depends(verify_request)
):
    """Get incident statistics"""
    try:
        async with IncidentCorrelationService() as service:
            stats = await service.get_incident_statistics()
            return stats
        
    except Exception as e:
        logger.error("Error getting incident statistics", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/incidents/{incident_id}/related")
async def get_related_incidents(
    incident_id: str,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_request)
):
    """Get incidents related to a specific incident"""
    try:
        incident = db.query(SecurityIncident).filter(
            SecurityIncident.incident_id == incident_id
        ).first()
        
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
        
        # Find related incidents through correlations
        related_incident_ids = []
        for correlation in incident.correlations:
            if correlation.related_incident_id:
                related_incident_ids.append(correlation.related_incident_id)
        
        # Get related incidents
        related_incidents = db.query(SecurityIncident).filter(
            SecurityIncident.id.in_(related_incident_ids)
        ).all()
        
        return {
            "related_incidents": [
                {
                    "incident_id": rel.incident_id,
                    "incident_type": rel.incident_type,
                    "severity": rel.severity,
                    "status": rel.status,
                    "title": rel.title,
                    "first_seen": rel.first_seen.isoformat(),
                    "last_seen": rel.last_seen.isoformat()
                }
                for rel in related_incidents
            ]
        }
        
    except Exception as e:
        logger.error("Error getting related incidents", incident_id=incident_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")
