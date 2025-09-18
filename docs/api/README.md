# API Documentation

## Overview

The Privik API provides comprehensive endpoints for email security analysis, threat detection, user management, and system administration. All API endpoints are secured with HMAC authentication and provide detailed responses with proper error handling.

## Base URL

```
Production: https://api.privik.com
Development: http://localhost:8000
```

## Authentication

### HMAC Authentication

All API endpoints require HMAC authentication using the following headers:

```
X-API-Key-ID: your_api_key_id
X-API-Timestamp: unix_timestamp
X-API-Nonce: random_nonce
X-API-Signature: hmac_signature
```

### Signature Generation

```python
import hmac
import hashlib
import time
import secrets

def generate_hmac_signature(method, path, body, timestamp, nonce, secret):
    message = f"{method}\n{path}\n{body}\n{timestamp}\n{nonce}"
    signature = hmac.new(
        secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature

# Example usage
timestamp = str(int(time.time()))
nonce = secrets.token_urlsafe(16)
signature = generate_hmac_signature(
    "POST", "/api/email-gateway/process", 
    json.dumps(request_body), timestamp, nonce, api_secret
)
```

## Core Endpoints

### Email Gateway

#### Process Email
```http
POST /api/email-gateway/process
```

**Request Body:**
```json
{
  "message_id": "msg_123",
  "subject": "Email Subject",
  "sender": "sender@example.com",
  "recipient": "recipient@company.com",
  "body": "Email body content",
  "headers": {
    "From": "sender@example.com",
    "To": "recipient@company.com",
    "Subject": "Email Subject"
  },
  "attachments": [
    {
      "filename": "document.pdf",
      "content_type": "application/pdf",
      "size": 1024000
    }
  ],
  "links": ["https://example.com"]
}
```

**Response:**
```json
{
  "message_id": "msg_123",
  "threat_score": 0.75,
  "verdict": "suspicious",
  "indicators": ["urgent_language", "suspicious_domain"],
  "action": "quarantine",
  "processing_time": 0.5
}
```

#### Process Email Async
```http
POST /api/email-gateway/process-async
```

**Response:**
```json
{
  "task_id": "task_123",
  "status": "queued",
  "estimated_completion": "2024-01-15T10:30:00Z"
}
```

#### Get Statistics
```http
GET /api/email-gateway/statistics
```

**Response:**
```json
{
  "total_emails_processed": 10000,
  "threats_detected": 500,
  "false_positives": 25,
  "processing_time_avg": 0.5,
  "last_24h": {
    "emails_processed": 1000,
    "threats_detected": 50
  }
}
```

### Sandbox Analysis

#### Get Sandbox Status
```http
GET /api/sandbox/status
```

**Response:**
```json
{
  "status": "active",
  "active_analyses": 5,
  "completed_analyses": 100,
  "failed_analyses": 2,
  "queue_size": 3
}
```

#### Detonate Test File
```http
POST /api/sandbox/detonate-test
```

**Request Body:**
```json
{
  "file_path": "/path/to/file.pdf",
  "file_hash": "sha256_hash",
  "analysis_type": "full"
}
```

**Response:**
```json
{
  "analysis_id": "analysis_123",
  "status": "queued",
  "estimated_completion": "2024-01-15T10:35:00Z"
}
```

### SOC Dashboard

#### Get Incidents
```http
GET /api/soc/incidents?limit=50&offset=0&severity=high
```

**Response:**
```json
{
  "incidents": [
    {
      "incident_id": "inc_123",
      "threat_type": "phishing",
      "severity": "high",
      "timestamp": "2024-01-15T10:00:00Z",
      "status": "investigating",
      "affected_users": 5
    }
  ],
  "total_count": 150,
  "has_more": true
}
```

#### Get Incident Details
```http
GET /api/soc/incidents/{incident_id}
```

**Response:**
```json
{
  "incident_id": "inc_123",
  "threat_type": "phishing",
  "severity": "high",
  "timestamp": "2024-01-15T10:00:00Z",
  "status": "investigating",
  "description": "Phishing email targeting employees",
  "analysis_results": {
    "verdict": "malicious",
    "threat_score": 0.95,
    "malware_family": "Trojan.Generic"
  },
  "artifacts": {
    "screenshots": ["screenshot1.png"],
    "reports": ["analysis_report.json"]
  },
  "affected_users": [
    {
      "user_id": "user_123",
      "email": "user@company.com",
      "risk_level": "high"
    }
  ]
}
```

### AI/ML Services

#### Train ML Models
```http
POST /api/ai-ml/ml/train?days_back=30
```

**Response:**
```json
{
  "success": true,
  "training_data_counts": {
    "emails": 1000,
    "domains": 500,
    "behaviors": 2000
  },
  "model_results": {
    "email_classifier": {
      "accuracy": 0.95,
      "precision": 0.92,
      "recall": 0.88
    }
  }
}
```

#### Get Model Status
```http
GET /api/ai-ml/ml/models/status
```

**Response:**
```json
{
  "models": {
    "email_classifier": {
      "status": "loaded",
      "version": "1.2.0",
      "last_trained": "2024-01-15T09:00:00Z",
      "accuracy": 0.95
    },
    "domain_classifier": {
      "status": "loading",
      "version": "1.1.0",
      "last_trained": "2024-01-14T15:00:00Z"
    }
  },
  "total_models": 2,
  "loaded_models": 1
}
```

#### Detect Behavioral Anomalies
```http
GET /api/ai-ml/behavior/anomalies?limit=20
```

**Response:**
```json
{
  "anomalies": [
    {
      "user_id": "user_123",
      "anomaly_score": 0.85,
      "risk_level": "high",
      "metrics": {
        "suspicious_click_rate": 0.8,
        "emails_per_day": 200,
        "time_variance": 15.2
      },
      "timestamp": "2024-01-15T10:00:00Z"
    }
  ],
  "total_users_analyzed": 100
}
```

#### Start Threat Hunting Campaign
```http
POST /api/ai-ml/threat-hunting/campaign?campaign_name=Test%20Campaign&time_range=7
```

**Response:**
```json
{
  "campaign_id": "campaign_123",
  "campaign_name": "Test Campaign",
  "findings": [
    {
      "type": "suspicious_email",
      "title": "Suspicious Email: Phishing Attempt",
      "description": "Email from phishing@malicious.com with phishing verdict",
      "confidence": 0.95,
      "recommended_action": "quarantine_and_investigate"
    }
  ],
  "threat_indicators": [
    {
      "type": "email_address",
      "value": "phishing@malicious.com",
      "confidence": 0.95
    }
  ]
}
```

### Integrations

#### Start Email Integration
```http
POST /api/integrations/start
```

**Request Body:**
```json
{
  "integration": "gmail",
  "config": {
    "refresh_token": "gmail_refresh_token",
    "user_email": "admin@company.com"
  }
}
```

**Response:**
```json
{
  "status": "started",
  "integration": "gmail",
  "connection_id": "conn_123"
}
```

#### Get Integration Status
```http
GET /api/integrations/status
```

**Response:**
```json
{
  "gmail": {
    "status": "active",
    "last_sync": "2024-01-15T10:00:00Z",
    "emails_processed": 1000,
    "errors": 0
  },
  "o365": {
    "status": "inactive",
    "last_sync": null,
    "emails_processed": 0,
    "errors": 5
  }
}
```

### Compliance

#### Generate Compliance Report
```http
POST /api/compliance/reports/generate
```

**Request Body:**
```json
{
  "framework": "soc2_type_ii",
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": "2024-01-31T23:59:59Z",
  "include_recommendations": true
}
```

**Response:**
```json
{
  "report_metadata": {
    "framework": "soc2_type_ii",
    "report_id": "soc2_report_20240115_143022",
    "compliance_score": 0.92,
    "generated_at": "2024-01-15T14:30:22Z"
  },
  "executive_summary": {
    "overall_score": 0.92,
    "key_highlights": ["Strong security controls implementation"]
  },
  "recommendations": [
    {
      "category": "access_controls",
      "priority": "medium",
      "recommendation": "Implement automated access provisioning"
    }
  ]
}
```

### Webhooks

#### Create Webhook
```http
POST /api/webhooks
```

**Request Body:**
```json
{
  "name": "Security Alerts",
  "url": "https://your-system.com/webhook",
  "events": ["email_threat_detected", "user_behavior_anomaly"],
  "timeout": 30,
  "retry_count": 3
}
```

**Response:**
```json
{
  "success": true,
  "webhook_id": "webhook_123",
  "webhook_secret": "secret_key_123",
  "created_at": "2024-01-15T10:00:00Z"
}
```

#### Trigger Webhook
```http
POST /api/webhooks/trigger/{event_type}
```

**Request Body:**
```json
{
  "email_id": "email_123",
  "threat_type": "phishing",
  "threat_score": 0.95
}
```

**Response:**
```json
{
  "success": true,
  "event_type": "email_threat_detected",
  "subscribed_webhooks": 2
}
```

### Multi-Tenant

#### Create Tenant
```http
POST /api/tenants
```

**Request Body:**
```json
{
  "name": "Company ABC",
  "domain": "companyabc.com",
  "tenant_type": "enterprise",
  "plan": "professional",
  "admin_contact": {
    "name": "Admin User",
    "email": "admin@companyabc.com"
  }
}
```

**Response:**
```json
{
  "success": true,
  "tenant_id": "tenant_123",
  "created_at": "2024-01-15T10:00:00Z",
  "trial_ends_at": "2024-02-14T10:00:00Z"
}
```

#### Add User to Tenant
```http
POST /api/tenants/{tenant_id}/users
```

**Request Body:**
```json
{
  "email": "user@companyabc.com",
  "name": "John Doe",
  "role": "user",
  "permissions": ["read_emails", "view_reports"]
}
```

**Response:**
```json
{
  "success": true,
  "user_id": "user_123",
  "tenant_id": "tenant_123"
}
```

## Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": {
      "field": "email",
      "reason": "Invalid email format"
    },
    "timestamp": "2024-01-15T10:00:00Z",
    "request_id": "req_123"
  }
}
```

### HTTP Status Codes

- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `202 Accepted` - Request accepted for processing
- `400 Bad Request` - Invalid request parameters
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

### Rate Limiting

- **Default**: 1000 requests per hour per API key
- **Burst**: 100 requests per minute
- **Headers**: Rate limit information in response headers
  ```
  X-RateLimit-Limit: 1000
  X-RateLimit-Remaining: 999
  X-RateLimit-Reset: 1642248000
  ```

## SDKs and Libraries

### Python SDK

```python
from privik import PrivikClient

client = PrivikClient(
    api_key_id="your_api_key_id",
    api_secret="your_api_secret",
    base_url="https://api.privik.com"
)

# Process email
result = client.process_email({
    "message_id": "msg_123",
    "subject": "Test Email",
    "sender": "test@example.com",
    "recipient": "user@company.com",
    "body": "Email content"
})

print(f"Threat Score: {result['threat_score']}")
print(f"Verdict: {result['verdict']}")
```

### JavaScript SDK

```javascript
import { PrivikClient } from '@privik/sdk';

const client = new PrivikClient({
  apiKeyId: 'your_api_key_id',
  apiSecret: 'your_api_secret',
  baseUrl: 'https://api.privik.com'
});

// Process email
const result = await client.processEmail({
  messageId: 'msg_123',
  subject: 'Test Email',
  sender: 'test@example.com',
  recipient: 'user@company.com',
  body: 'Email content'
});

console.log(`Threat Score: ${result.threatScore}`);
console.log(`Verdict: ${result.verdict}`);
```

## Webhooks

### Webhook Events

- `email_threat_detected` - Malicious email detected
- `user_behavior_anomaly` - User behavior anomaly detected
- `sandbox_analysis_complete` - Sandbox analysis completed
- `compliance_violation` - Compliance violation detected
- `system_alert` - System-level alert
- `incident_created` - Security incident created
- `incident_resolved` - Security incident resolved

### Webhook Payload

```json
{
  "event_type": "email_threat_detected",
  "timestamp": "2024-01-15T10:00:00Z",
  "data": {
    "email_id": "email_123",
    "threat_type": "phishing",
    "threat_score": 0.95,
    "sender": "phishing@malicious.com",
    "recipient": "user@company.com"
  }
}
```

### Webhook Security

Webhooks are secured with HMAC signatures:

```python
import hmac
import hashlib

def verify_webhook_signature(payload, signature, secret):
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected_signature)
```

## Examples

### Complete Email Processing Flow

```python
import requests
import json
import time
import hmac
import hashlib

def process_email_with_privik(email_data):
    # Generate HMAC signature
    timestamp = str(int(time.time()))
    nonce = "random_nonce_123"
    method = "POST"
    path = "/api/email-gateway/process"
    body = json.dumps(email_data)
    
    message = f"{method}\n{path}\n{body}\n{timestamp}\n{nonce}"
    signature = hmac.new(
        api_secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    # Make request
    headers = {
        "Content-Type": "application/json",
        "X-API-Key-ID": api_key_id,
        "X-API-Timestamp": timestamp,
        "X-API-Nonce": nonce,
        "X-API-Signature": signature
    }
    
    response = requests.post(
        "https://api.privik.com/api/email-gateway/process",
        json=email_data,
        headers=headers
    )
    
    return response.json()

# Example usage
email_data = {
    "message_id": "msg_123",
    "subject": "URGENT: Verify Your Account",
    "sender": "noreply@suspicious-bank.com",
    "recipient": "user@company.com",
    "body": "Your account will be closed in 24 hours. Click here to verify.",
    "links": ["https://fake-bank.com/verify"]
}

result = process_email_with_privik(email_data)
print(f"Threat Score: {result['threat_score']}")
print(f"Verdict: {result['verdict']}")
```

## Support

For API support and questions:

- **Documentation**: [docs/api/](docs/api/)
- **Issues**: [GitHub Issues](https://github.com/your-org/privik/issues)
- **Email**: api-support@privik.com
- **Status Page**: [status.privik.com](https://status.privik.com)
