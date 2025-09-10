from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case, desc
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from ..database import get_db
from ..models.email import Email, EmailAttachment
from ..models.click import ClickEvent, LinkAnalysis
from ..models.sandbox import SandboxAnalysis
from ..models.user import User, UserRiskProfile

router = APIRouter(prefix="/soc", tags=["soc"])


class ThreatSummary(BaseModel):
    total_emails: int
    suspicious_emails: int
    malicious_emails: int
    total_clicks: int
    suspicious_clicks: int
    blocked_clicks: int
    total_attachments: int
    suspicious_attachments: int
    malicious_attachments: int


class UserRiskSummary(BaseModel):
    user_id: str
    email: str
    risk_score: float
    risk_level: str
    total_clicks: int
    suspicious_clicks: int
    last_activity: Optional[datetime]


class ThreatTimeline(BaseModel):
    timestamp: datetime
    event_type: str
    threat_score: float
    verdict: str
    details: dict


@router.get("/dashboard", response_model=ThreatSummary)
async def get_dashboard_summary(
    days: int = Query(7, description="Number of days to look back"),
    db: Session = Depends(get_db)
):
    """Get threat summary for SOC dashboard."""
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Email statistics
    email_stats = db.query(
        func.count(Email.id).label('total'),
        func.sum(case((Email.is_suspicious == True, 1), else_=0)).label('suspicious'),
        func.sum(case((Email.ai_verdict == 'malicious', 1), else_=0)).label('malicious')
    ).filter(Email.created_at >= start_date).first()
    
    # Click statistics
    click_stats = db.query(
        func.count(ClickEvent.id).label('total'),
        func.sum(case((ClickEvent.is_suspicious == True, 1), else_=0)).label('suspicious'),
        func.sum(case((ClickEvent.ai_verdict == 'malicious', 1), else_=0)).label('blocked')
    ).filter(ClickEvent.created_at >= start_date).first()
    
    # Attachment statistics
    attachment_stats = db.query(
        func.count(EmailAttachment.id).label('total'),
        func.sum(case((EmailAttachment.threat_score > 0.5, 1), else_=0)).label('suspicious'),
        func.sum(case((EmailAttachment.sandbox_verdict == 'malicious', 1), else_=0)).label('malicious')
    ).filter(EmailAttachment.created_at >= start_date).first()
    
    return ThreatSummary(
        total_emails=email_stats.total or 0,
        suspicious_emails=email_stats.suspicious or 0,
        malicious_emails=email_stats.malicious or 0,
        total_clicks=click_stats.total or 0,
        suspicious_clicks=click_stats.suspicious or 0,
        blocked_clicks=click_stats.blocked or 0,
        total_attachments=attachment_stats.total or 0,
        suspicious_attachments=attachment_stats.suspicious or 0,
        malicious_attachments=attachment_stats.malicious or 0
    )


@router.get("/users/risk", response_model=List[UserRiskSummary])
async def get_user_risk_profiles(
    limit: int = Query(50, description="Number of users to return"),
    db: Session = Depends(get_db)
):
    """Get user risk profiles for SOC monitoring."""
    
    users = db.query(User).order_by(desc(User.risk_score)).limit(limit).all()
    
    return [
        UserRiskSummary(
            user_id=user.user_id,
            email=user.email,
            risk_score=user.risk_score,
            risk_level=user.risk_level,
            total_clicks=user.total_clicks,
            suspicious_clicks=user.suspicious_clicks,
            last_activity=user.last_activity
        )
        for user in users
    ]


@router.get("/timeline", response_model=List[ThreatTimeline])
async def get_threat_timeline(
    days: int = Query(7, description="Number of days to look back"),
    limit: int = Query(100, description="Number of events to return"),
    db: Session = Depends(get_db)
):
    """Get threat timeline for SOC monitoring."""
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get suspicious emails
    suspicious_emails = db.query(Email).filter(
        Email.created_at >= start_date,
        Email.is_suspicious == True
    ).order_by(desc(Email.created_at)).limit(limit).all()
    
    # Get suspicious clicks
    suspicious_clicks = db.query(ClickEvent).filter(
        ClickEvent.created_at >= start_date,
        ClickEvent.is_suspicious == True
    ).order_by(desc(ClickEvent.created_at)).limit(limit).all()
    
    # Get suspicious attachments
    suspicious_attachments = db.query(EmailAttachment).filter(
        EmailAttachment.created_at >= start_date,
        EmailAttachment.threat_score > 0.5
    ).order_by(desc(EmailAttachment.created_at)).limit(limit).all()
    
    # Combine and sort events
    events = []
    
    for email in suspicious_emails:
        events.append(ThreatTimeline(
            timestamp=email.created_at,
            event_type="suspicious_email",
            threat_score=email.threat_score,
            verdict=email.ai_verdict or "unknown",
            details={
                "subject": email.subject,
                "sender": email.sender,
                "message_id": email.message_id
            }
        ))
    
    for click in suspicious_clicks:
        events.append(ThreatTimeline(
            timestamp=click.created_at,
            event_type="suspicious_click",
            threat_score=click.threat_score,
            verdict=click.ai_verdict or "unknown",
            details={
                "url": click.original_url,
                "user_id": click.user_id
            }
        ))
    
    for attachment in suspicious_attachments:
        events.append(ThreatTimeline(
            timestamp=attachment.created_at,
            event_type="suspicious_attachment",
            threat_score=attachment.threat_score,
            verdict=attachment.sandbox_verdict or "unknown",
            details={
                "filename": attachment.filename,
                "file_size": attachment.file_size
            }
        ))
    
    # Sort by timestamp (newest first)
    events.sort(key=lambda x: x.timestamp, reverse=True)
    
    return events[:limit]


@router.get("/alerts")
async def get_active_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity (low, medium, high, critical)"),
    db: Session = Depends(get_db)
):
    """Get active security alerts for SOC triage."""
    
    # Get high-threat emails
    high_threat_emails = db.query(Email).filter(
        Email.threat_score > 0.7,
        Email.created_at >= datetime.utcnow() - timedelta(hours=24)
    ).all()
    
    # Get high-threat clicks
    high_threat_clicks = db.query(ClickEvent).filter(
        ClickEvent.threat_score > 0.7,
        ClickEvent.created_at >= datetime.utcnow() - timedelta(hours=24)
    ).all()
    
    # Get malicious attachments
    malicious_attachments = db.query(EmailAttachment).filter(
        EmailAttachment.sandbox_verdict == "malicious",
        EmailAttachment.created_at >= datetime.utcnow() - timedelta(hours=24)
    ).all()
    
    alerts = []
    
    for email in high_threat_emails:
        alerts.append({
            "id": f"email_{email.id}",
            "type": "suspicious_email",
            "severity": "high" if email.threat_score > 0.8 else "medium",
            "timestamp": email.created_at,
            "threat_score": email.threat_score,
            "title": f"Suspicious Email: {email.subject}",
            "description": f"Email from {email.sender} with threat score {email.threat_score:.2f}",
            "details": {
                "sender": email.sender,
                "subject": email.subject,
                "verdict": email.ai_verdict
            }
        })
    
    for click in high_threat_clicks:
        alerts.append({
            "id": f"click_{click.id}",
            "type": "suspicious_click",
            "severity": "high" if click.threat_score > 0.8 else "medium",
            "timestamp": click.created_at,
            "threat_score": click.threat_score,
            "title": f"Suspicious Click: {click.original_url[:50]}...",
            "description": f"User {click.user_id} clicked suspicious link",
            "details": {
                "url": click.original_url,
                "user_id": click.user_id,
                "verdict": click.ai_verdict
            }
        })
    
    for attachment in malicious_attachments:
        alerts.append({
            "id": f"attachment_{attachment.id}",
            "type": "malicious_attachment",
            "severity": "critical",
            "timestamp": attachment.created_at,
            "threat_score": attachment.threat_score,
            "title": f"Malicious Attachment: {attachment.filename}",
            "description": f"Malicious file detected: {attachment.filename}",
            "details": {
                "filename": attachment.filename,
                "file_size": attachment.file_size,
                "verdict": attachment.sandbox_verdict
            }
        })
    
    # Filter by severity if specified
    if severity:
        alerts = [alert for alert in alerts if alert["severity"] == severity]
    
    # Sort by timestamp (newest first)
    alerts.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return alerts


@router.get("/stats/hourly")
async def get_hourly_stats(
    days: int = Query(7, description="Number of days to look back"),
    db: Session = Depends(get_db)
):
    """Get hourly threat statistics for trend analysis."""
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get hourly email counts
    hourly_emails = db.query(
        func.date_trunc('hour', Email.created_at).label('hour'),
        func.count(Email.id).label('total'),
        func.sum(case((Email.is_suspicious == True, 1), else_=0)).label('suspicious')
    ).filter(
        Email.created_at >= start_date
    ).group_by(
        func.date_trunc('hour', Email.created_at)
    ).order_by(
        func.date_trunc('hour', Email.created_at)
    ).all()
    
    # Get hourly click counts
    hourly_clicks = db.query(
        func.date_trunc('hour', ClickEvent.created_at).label('hour'),
        func.count(ClickEvent.id).label('total'),
        func.sum(case((ClickEvent.is_suspicious == True, 1), else_=0)).label('suspicious')
    ).filter(
        ClickEvent.created_at >= start_date
    ).group_by(
        func.date_trunc('hour', ClickEvent.created_at)
    ).order_by(
        func.date_trunc('hour', ClickEvent.created_at)
    ).all()
    
    return {
        "emails": [
            {
                "hour": str(stat.hour),
                "total": stat.total,
                "suspicious": stat.suspicious
            }
            for stat in hourly_emails
        ],
        "clicks": [
            {
                "hour": str(stat.hour),
                "total": stat.total,
                "suspicious": stat.suspicious
            }
            for stat in hourly_clicks
        ]
    }
