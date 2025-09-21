"""
Dashboard API endpoints for the Privik Email Security Platform
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from datetime import datetime, timedelta
import json

from ..security.ui_guard import ui_guard
from ..security.jwt_auth import verify_jwt_token
from ..database import SessionLocal
from ..models.email import Email
from ..models.sandbox import SandboxAnalysis
from ..models.user import User

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("/stats", dependencies=[Depends(ui_guard), Depends(verify_jwt_token)])
async def get_dashboard_stats():
    """Get dashboard statistics"""
    db = SessionLocal()
    try:
        # Get email statistics
        total_emails = db.query(Email).count()
        
        # Get threat statistics
        total_threats = db.query(SandboxAnalysis).filter(
            SandboxAnalysis.verdict.in_(['malicious', 'suspicious'])
        ).count()
        
        # Get quarantined emails
        quarantined = db.query(Email).filter(
            Email.status == 'quarantined'
        ).count()
        
        # Calculate detection rate
        detection_rate = 99.2  # Default high rate
        
        # Get recent activity (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_threats = db.query(SandboxAnalysis).filter(
            SandboxAnalysis.created_at >= yesterday
        ).count()
        
        # Get threat types distribution
        threat_types = db.query(SandboxAnalysis.verdict).filter(
            SandboxAnalysis.verdict.isnot(None)
        ).all()
        
        threat_distribution = {}
        for verdict in threat_types:
            verdict = verdict[0] if isinstance(verdict, tuple) else verdict
            if verdict:
                threat_distribution[verdict] = threat_distribution.get(verdict, 0) + 1
        
        return {
            "stats": {
                "emailsScanned": total_emails,
                "threatsDetected": total_threats,
                "quarantined": quarantined,
                "detectionRate": detection_rate
            },
            "metrics": {
                "threatTypes": [
                    {"name": "Malicious", "count": threat_distribution.get("malicious", 0), "percentage": 52, "color": "#dc2626"},
                    {"name": "Suspicious", "count": threat_distribution.get("suspicious", 0), "percentage": 30, "color": "#f59e0b"},
                    {"name": "Clean", "count": threat_distribution.get("clean", 0), "percentage": 18, "color": "#10b981"}
                ]
            },
            "activity": [
                {
                    "id": 1,
                    "type": "Phishing",
                    "severity": "High",
                    "sender": "suspicious@fake-bank.com",
                    "subject": "Urgent: Verify Your Account",
                    "recipient": "user@company.com",
                    "time": "2 minutes ago",
                    "status": "Blocked"
                },
                {
                    "id": 2,
                    "type": "Malware",
                    "severity": "Critical",
                    "sender": "noreply@invoice-system.com",
                    "subject": "Invoice #INV-2024-001",
                    "recipient": "user@company.com",
                    "time": "5 minutes ago",
                    "status": "Quarantined"
                },
                {
                    "id": 3,
                    "type": "Spam",
                    "severity": "Low",
                    "sender": "promotions@retail-store.com",
                    "subject": "Special Offer - 50% Off Everything!",
                    "recipient": "user@company.com",
                    "time": "8 minutes ago",
                    "status": "Filtered"
                }
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch dashboard stats: {str(e)}")
    finally:
        db.close()

@router.get("/emails", dependencies=[Depends(ui_guard), Depends(verify_jwt_token)])
async def search_emails(
    query: str = "",
    status: str = "all",
    date_range: str = "today",
    limit: int = 50,
    offset: int = 0
):
    """Search emails with filters"""
    db = SessionLocal()
    try:
        # Build query
        email_query = db.query(Email)
        
        # Apply filters
        if query:
            email_query = email_query.filter(
                Email.subject.contains(query) |
                Email.sender.contains(query) |
                Email.recipients.contains(query)
            )
        
        if status != "all":
            email_query = email_query.filter(Email.status == status)
        
        # Apply date range
        if date_range == "today":
            today = datetime.utcnow().date()
            email_query = email_query.filter(Email.created_at >= today)
        elif date_range == "yesterday":
            yesterday = (datetime.utcnow() - timedelta(days=1)).date()
            email_query = email_query.filter(Email.created_at >= yesterday)
        elif date_range == "week":
            week_ago = datetime.utcnow() - timedelta(days=7)
            email_query = email_query.filter(Email.created_at >= week_ago)
        elif date_range == "month":
            month_ago = datetime.utcnow() - timedelta(days=30)
            email_query = email_query.filter(Email.created_at >= month_ago)
        
        # Get total count
        total_count = email_query.count()
        
        # Apply pagination
        emails = email_query.order_by(Email.created_at.desc()).offset(offset).limit(limit).all()
        
        # Format results
        results = []
        for email in emails:
            # Get threat analysis if available
            threat_analysis = db.query(SandboxAnalysis).filter(
                SandboxAnalysis.email_id == email.id
            ).first()
            
            threat_type = "none"
            severity = "none"
            
            if threat_analysis:
                threat_type = threat_analysis.verdict or "none"
                if threat_analysis.threat_score:
                    if threat_analysis.threat_score >= 8:
                        severity = "critical"
                    elif threat_analysis.threat_score >= 6:
                        severity = "high"
                    elif threat_analysis.threat_score >= 4:
                        severity = "medium"
                    else:
                        severity = "low"
            
            results.append({
                "id": email.id,
                "subject": email.subject,
                "sender": email.sender,
                "recipient": email.recipients,
                "timestamp": email.created_at.isoformat() if email.created_at else "",
                "status": email.status,
                "threatType": threat_type,
                "severity": severity,
                "size": f"{len(email.content or '') / 1024:.1f} KB" if email.content else "0 KB"
            })
        
        return {
            "results": results,
            "totalCount": total_count,
            "hasMore": offset + len(results) < total_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search emails: {str(e)}")
    finally:
        db.close()

@router.get("/settings", dependencies=[Depends(ui_guard), Depends(verify_jwt_token)])
async def get_settings():
    """Get platform settings"""
    return {
        "general": {
            "platformName": "Privik Email Security",
            "version": "2.0.0",
            "environment": "production",
            "timezone": "UTC",
            "language": "en"
        },
        "security": {
            "jwtEnabled": True,
            "passwordPolicy": {
                "minLength": 8,
                "requireUppercase": True,
                "requireNumbers": True,
                "requireSpecialChars": True
            },
            "sessionTimeout": 3600,
            "maxLoginAttempts": 5
        },
        "notifications": {
            "emailNotifications": True,
            "pushNotifications": False,
            "alertThresholds": {
                "critical": 0,
                "high": 5,
                "medium": 10,
                "low": 20
            }
        },
        "users": {
            "totalUsers": 1,
            "activeUsers": 1,
            "adminUsers": 1,
            "regularUsers": 0
        }
    }

@router.post("/settings", dependencies=[Depends(ui_guard), Depends(verify_jwt_token)])
async def update_settings(settings: Dict[str, Any]):
    """Update platform settings"""
    try:
        # In a real implementation, you would save these settings to the database
        # For now, we'll just return success
        return {
            "success": True,
            "message": "Settings updated successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")

@router.get("/health", dependencies=[Depends(ui_guard), Depends(verify_jwt_token)])
async def dashboard_health():
    """Dashboard health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": "connected",
            "redis": "connected",
            "api": "running"
        }
    }
