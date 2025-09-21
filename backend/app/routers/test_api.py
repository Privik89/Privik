"""
Test API endpoints for debugging
"""

from fastapi import APIRouter
from datetime import datetime

router = APIRouter(prefix="/api/test", tags=["test"])

@router.get("/dashboard/stats")
async def test_dashboard_stats():
    """Test dashboard stats endpoint"""
    return {
        "stats": {
            "emailsScanned": 12456,
            "threatsDetected": 23,
            "quarantined": 8,
            "detectionRate": 99.2
        },
        "metrics": {
            "threatTypes": [
                {"name": "Phishing", "count": 12, "percentage": 52, "color": "#dc2626"},
                {"name": "Malware", "count": 7, "percentage": 30, "color": "#f59e0b"},
                {"name": "Spam", "count": 4, "percentage": 18, "color": "#10b981"}
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
            }
        ],
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/emails")
async def test_email_search():
    """Test email search endpoint"""
    return {
        "results": [
            {
                "id": 1,
                "subject": "Urgent: Verify Your Account",
                "sender": "suspicious@fake-bank.com",
                "recipient": "user@company.com",
                "timestamp": "2024-01-15T14:30:25",
                "status": "blocked",
                "threatType": "phishing",
                "severity": "high",
                "size": "2.3 KB"
            },
            {
                "id": 2,
                "subject": "Your Amazon Order Confirmation",
                "sender": "support@amazon.com",
                "recipient": "user@company.com",
                "timestamp": "2024-01-15T10:15:00",
                "status": "delivered",
                "threatType": "none",
                "severity": "none",
                "size": "15.7 KB"
            }
        ],
        "totalCount": 2,
        "hasMore": False
    }

@router.get("/settings")
async def test_settings():
    """Test settings endpoint"""
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
            }
        },
        "notifications": {
            "emailNotifications": True,
            "pushNotifications": False
        }
    }
