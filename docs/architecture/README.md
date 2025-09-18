# System Architecture

## Overview

Privik is built on a modern, scalable architecture that implements zero-trust security principles throughout the entire email processing pipeline. The system is designed to handle high-volume email processing while providing real-time threat detection and analysis.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Privik Platform                         │
├─────────────────────────────────────────────────────────────────┤
│  Frontend (React)  │  API Gateway  │  Admin Dashboard          │
├─────────────────────────────────────────────────────────────────┤
│                    Core Services Layer                         │
│  Email Gateway  │  AI/ML Engine  │  Sandbox  │  SOC Dashboard │
├─────────────────────────────────────────────────────────────────┤
│                    Integration Layer                           │
│  Email Sources  │  SIEM  │  LDAP/AD  │  Webhooks  │  Compliance│
├─────────────────────────────────────────────────────────────────┤
│                    Data Layer                                  │
│  PostgreSQL  │  Redis  │  MinIO  │  CAPEv2  │  VirusTotal    │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Email Gateway Service

The Email Gateway Service is the central component that orchestrates the entire email processing pipeline.

**Responsibilities:**
- Email ingestion from multiple sources (Gmail, O365, IMAP/POP3)
- Email parsing and feature extraction
- AI-powered threat analysis
- Real-time sandboxing coordination
- Policy enforcement and action execution

**Key Features:**
- **Multi-source Integration**: Supports Gmail, Microsoft 365, and IMAP/POP3
- **Incremental Processing**: Uses persistent cursors for efficient email fetching
- **Retry Logic**: Exponential backoff for failed operations
- **Rate Limiting**: Built-in rate limiting to prevent API abuse

```python
class EmailGatewayService:
    def __init__(self):
        self.email_analyzer = EmailAnalyzer()
        self.sandbox = RealTimeSandbox()
        self.policy_engine = PolicyEngine()
        self.training_logger = TrainingLogger()
    
    async def process_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        # 1. Parse and validate email
        parsed_email = await self._parse_email(email_data)
        
        # 2. Extract features for AI analysis
        features = await self._extract_features(parsed_email)
        
        # 3. Run AI threat analysis
        threat_analysis = await self.email_analyzer.analyze_email(parsed_email)
        
        # 4. Apply zero-trust policies
        policy_result = await self.policy_engine.evaluate_policies(
            parsed_email, threat_analysis
        )
        
        # 5. Execute actions based on verdict
        action_result = await self._execute_actions(policy_result)
        
        # 6. Log for training data
        await self.training_logger.log_email_analysis(
            parsed_email, threat_analysis, action_result
        )
        
        return action_result
```

### 2. AI/ML Engine

The AI/ML Engine provides comprehensive threat detection using multiple machine learning models.

**Components:**
- **Email Classifier**: LSTM-based email intent classification
- **Domain Classifier**: CNN-based domain reputation analysis
- **Behavioral Analyzer**: Isolation Forest for anomaly detection
- **Ensemble Classifier**: Combines multiple models for final verdict

**Model Architecture:**
```
Input Email → Feature Extraction → Model Ensemble → Threat Score
     ↓              ↓                    ↓              ↓
  Raw Data    Numerical Features    ML Models    Final Verdict
```

**Training Pipeline:**
```python
class MLTrainingPipeline:
    async def train_model(self, model_type: str) -> Dict[str, Any]:
        # 1. Collect training data
        training_data = await self._collect_training_data(model_type)
        
        # 2. Feature engineering
        features = await self._engineer_features(training_data)
        
        # 3. Model training
        model = await self._train_model(model_type, features)
        
        # 4. Cross-validation
        cv_results = await self._cross_validate(model, features)
        
        # 5. Model persistence
        await self._save_model(model, model_type)
        
        return {
            "model_type": model_type,
            "accuracy": cv_results["accuracy"],
            "precision": cv_results["precision"],
            "recall": cv_results["recall"]
        }
```

### 3. Real-Time Sandbox

The Real-Time Sandbox provides click-time analysis of links and attachments.

**Architecture:**
```
User Click → Link Rewrite → Sandbox Analysis → Verdict → User Notification
     ↓            ↓              ↓              ↓              ↓
  Original    Rewritten      CAPEv2/Playwright  Threat Score  Safe/Block
```

**Key Features:**
- **Multi-environment Support**: Windows, macOS, Linux sandboxes
- **Evasion Detection**: Advanced evasion technique detection
- **Artifact Collection**: Screenshots, network traffic, file system changes
- **Real-time Analysis**: Sub-minute analysis completion

```python
class RealTimeSandbox:
    async def analyze_link_click(self, url: str, user_id: str) -> Dict[str, Any]:
        # 1. Submit to CAPEv2 for analysis
        task_id = await self._submit_to_cape(url)
        
        # 2. Monitor analysis progress
        while not await self._is_analysis_complete(task_id):
            await asyncio.sleep(5)
        
        # 3. Retrieve analysis results
        results = await self._get_analysis_results(task_id)
        
        # 4. Upload artifacts to MinIO
        artifacts = await self._upload_artifacts(results)
        
        # 5. Generate verdict
        verdict = await self._generate_verdict(results)
        
        return {
            "verdict": verdict,
            "threat_score": results["threat_score"],
            "artifacts": artifacts
        }
```

### 4. SOC Dashboard

The SOC Dashboard provides real-time monitoring and incident management.

**Components:**
- **Incident Management**: Real-time incident tracking and resolution
- **Timeline Visualization**: Incident correlation and timeline analysis
- **AI Copilot**: LLM-powered incident analysis and recommendations
- **Threat Intelligence**: Integration with external threat feeds

**Dashboard Architecture:**
```
Real-time Events → Event Processing → Incident Correlation → Dashboard Display
       ↓                ↓                    ↓                    ↓
   Email/Click      Threat Analysis      Campaign Detection    SOC Analyst
```

## Data Flow Architecture

### 1. Email Processing Flow

```
Email Source → Ingestion → Parsing → AI Analysis → Policy Evaluation → Action
     ↓            ↓          ↓           ↓              ↓              ↓
  Gmail/O365   Validation  Features   Threat Score   Zero-Trust    Quarantine/
  IMAP/POP3    & Parsing   Extraction   & Verdict     Policies     Allow/Block
```

### 2. Click-Time Analysis Flow

```
User Click → Link Rewrite → Sandbox → Analysis → Verdict → User Action
     ↓            ↓           ↓          ↓          ↓          ↓
  Original    Rewritten    CAPEv2    Behavioral   Threat    Safe/Block
   Link        Link       Analysis   Analysis     Score     Notification
```

### 3. Behavioral Analysis Flow

```
User Actions → Behavior Collection → Anomaly Detection → Risk Scoring → Alerts
      ↓              ↓                    ↓                  ↓           ↓
   Clicks/Logins   Feature Extraction   Isolation Forest   Risk Level   SOC Alert
```

## Security Architecture

### 1. Zero-Trust Principles

**Never Trust, Always Verify:**
- All emails are treated as potentially malicious
- Every link and attachment is analyzed before execution
- User behavior is continuously monitored for anomalies
- All communications are authenticated and encrypted

**Security Layers:**
```
┌─────────────────────────────────────────────────────────┐
│                    Security Layers                      │
├─────────────────────────────────────────────────────────┤
│  Application Security  │  API Security  │  Data Security │
├─────────────────────────────────────────────────────────┤
│  HMAC Authentication   │  JWT Tokens    │  Encryption    │
│  Input Validation      │  Rate Limiting │  Access Control│
│  Output Sanitization   │  CORS Policy   │  Audit Logging │
└─────────────────────────────────────────────────────────┘
```

### 2. Authentication & Authorization

**HMAC Authentication:**
```python
def verify_hmac_signature(request: Request) -> bool:
    # Extract headers
    api_key_id = request.headers.get("X-API-Key-ID")
    timestamp = request.headers.get("X-API-Timestamp")
    nonce = request.headers.get("X-API-Nonce")
    signature = request.headers.get("X-API-Signature")
    
    # Verify timestamp (prevent replay attacks)
    if not _is_timestamp_valid(timestamp):
        return False
    
    # Verify nonce (prevent replay attacks)
    if not _is_nonce_valid(nonce):
        return False
    
    # Verify signature
    expected_signature = _generate_signature(
        request.method, request.url.path, 
        request.body, timestamp, nonce, api_secret
    )
    
    return hmac.compare_digest(signature, expected_signature)
```

**JWT Authorization:**
```python
def verify_jwt_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET, 
            algorithms=["HS256"]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")
```

### 3. Data Protection

**Encryption at Rest:**
- Database: AES-256 encryption for sensitive fields
- File Storage: MinIO with server-side encryption
- Configuration: Encrypted environment variables

**Encryption in Transit:**
- TLS 1.3 for all API communications
- HTTPS for web interfaces
- Encrypted database connections

## Scalability Architecture

### 1. Horizontal Scaling

**Load Balancing:**
```
Internet → Load Balancer → API Gateway → Application Servers
    ↓           ↓              ↓              ↓
  Users    Nginx/HAProxy   FastAPI      Multiple Instances
```

**Database Scaling:**
- **Read Replicas**: For read-heavy operations
- **Connection Pooling**: Efficient database connections
- **Query Optimization**: Indexed queries and caching

### 2. Caching Strategy

**Multi-Level Caching:**
```
Application → Redis Cache → Database
     ↓            ↓           ↓
  In-Memory    Distributed   Persistent
   Cache        Cache        Storage
```

**Cache Namespaces:**
- `email_analysis`: Cached email analysis results
- `domain_reputation`: Domain reputation scores
- `user_behavior`: User behavior profiles
- `threat_intelligence`: Threat intelligence data

### 3. Message Queue Architecture

**Async Processing:**
```
Email Processing → Message Queue → Background Workers
       ↓               ↓                ↓
   Fast Response    Reliable Queue    Heavy Processing
```

**Queue Types:**
- **Email Processing**: High-priority email analysis
- **Sandbox Analysis**: File and link analysis
- **Training Data**: ML model training data collection
- **Notifications**: Webhook and alert delivery

## Integration Architecture

### 1. Email Source Integration

**Gmail Integration:**
```python
class GmailIntegration:
    async def fetch_emails(self, cursor: str = None) -> List[Dict[str, Any]]:
        # Use Gmail API with historyId for incremental fetching
        if cursor:
            history = await self.gmail_service.get_history(cursor)
            return await self._process_history(history)
        else:
            messages = await self.gmail_service.list_messages()
            return await self._process_messages(messages)
```

**Microsoft 365 Integration:**
```python
class Microsoft365Integration:
    async def fetch_emails(self, delta_link: str = None) -> List[Dict[str, Any]]:
        # Use Microsoft Graph API with delta queries
        if delta_link:
            response = await self.graph_client.get_delta(delta_link)
        else:
            response = await self.graph_client.get_messages()
        
        return await self._process_response(response)
```

### 2. SIEM Integration

**Real-time Event Streaming:**
```python
class SIEMIntegration:
    async def stream_event(self, event_data: Dict[str, Any]) -> bool:
        # Normalize event data
        normalized_event = await self._normalize_event(event_data)
        
        # Stream to multiple SIEM platforms
        results = []
        for siem_connection in self.active_connections:
            result = await self._stream_to_siem(
                siem_connection, normalized_event
            )
            results.append(result)
        
        return all(results)
```

### 3. LDAP/AD Integration

**Authentication Flow:**
```python
class LDAPAuthService:
    async def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
        # 1. Connect to LDAP server
        connection = await self._connect_to_ldap()
        
        # 2. Authenticate user
        user_dn = self._construct_user_dn(username)
        auth_result = await self._authenticate(connection, user_dn, password)
        
        # 3. Get user details and groups
        user_details = await self._get_user_details(connection, user_dn)
        user_groups = await self._get_user_groups(connection, user_dn)
        
        return {
            "success": auth_result,
            "user_details": user_details,
            "user_groups": user_groups
        }
```

## Monitoring & Observability

### 1. Health Monitoring

**Multi-Service Health Checks:**
```python
class HealthMonitor:
    async def check_health(self) -> Dict[str, Any]:
        health_status = {
            "database": await self._check_database(),
            "redis": await self._check_redis(),
            "minio": await self._check_minio(),
            "cape": await self._check_cape(),
            "external_apis": await self._check_external_apis()
        }
        
        overall_status = "healthy" if all(
            status["status"] == "healthy" 
            for status in health_status.values()
        ) else "unhealthy"
        
        return {
            "status": overall_status,
            "services": health_status,
            "timestamp": datetime.now().isoformat()
        }
```

### 2. Performance Monitoring

**Metrics Collection:**
- **API Response Times**: P50, P95, P99 latencies
- **Throughput**: Requests per second
- **Error Rates**: 4xx and 5xx error percentages
- **Resource Usage**: CPU, memory, disk usage

### 3. Logging Architecture

**Structured Logging:**
```python
import structlog

logger = structlog.get_logger()

# Application logs
logger.info("Email processed", 
           message_id="msg_123", 
           threat_score=0.75, 
           verdict="suspicious")

# Audit logs
logger.info("User authenticated", 
           user_id="user_123", 
           method="ldap", 
           success=True)

# Security logs
logger.warning("Suspicious activity detected", 
              user_id="user_123", 
              activity_type="anomaly", 
              risk_score=0.85)
```

## Deployment Architecture

### 1. Container Architecture

**Docker Compose Setup:**
```yaml
version: '3.8'
services:
  privik-api:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/privik
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
      - minio
  
  privik-frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:8000
  
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=privik
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7
    volumes:
      - redis_data:/data
  
  minio:
    image: minio/minio
    command: server /data
    environment:
      - MINIO_ACCESS_KEY=minioadmin
      - MINIO_SECRET_KEY=minioadmin
    volumes:
      - minio_data:/data
```

### 2. Production Deployment

**Kubernetes Architecture:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: privik-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: privik-api
  template:
    metadata:
      labels:
        app: privik-api
    spec:
      containers:
      - name: privik-api
        image: privik/api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: privik-secrets
              key: database-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
```

## Disaster Recovery

### 1. Backup Strategy

**Automated Backups:**
- **Database**: Daily full backups with point-in-time recovery
- **File Storage**: MinIO bucket replication
- **Configuration**: Encrypted configuration backups
- **Logs**: Centralized log aggregation and retention

### 2. High Availability

**Multi-Region Deployment:**
- **Primary Region**: Active production environment
- **Secondary Region**: Standby environment for failover
- **Data Replication**: Real-time data synchronization
- **Health Monitoring**: Automated failover triggers

## Performance Optimization

### 1. Database Optimization

**Indexing Strategy:**
```sql
-- Email processing indexes
CREATE INDEX idx_emails_timestamp ON emails(created_at);
CREATE INDEX idx_emails_sender ON emails(sender);
CREATE INDEX idx_emails_recipient ON emails(recipient);

-- Threat analysis indexes
CREATE INDEX idx_threat_analysis_email_id ON threat_analysis(email_id);
CREATE INDEX idx_threat_analysis_verdict ON threat_analysis(verdict);

-- User behavior indexes
CREATE INDEX idx_user_behavior_user_id ON user_behavior(user_id);
CREATE INDEX idx_user_behavior_timestamp ON user_behavior(timestamp);
```

### 2. Caching Optimization

**Redis Caching:**
```python
class CacheManager:
    async def get_email_analysis(self, email_hash: str) -> Optional[Dict[str, Any]]:
        # Check cache first
        cached_result = await self.redis.get(f"email_analysis:{email_hash}")
        if cached_result:
            return json.loads(cached_result)
        
        # If not in cache, compute and store
        result = await self._compute_email_analysis(email_hash)
        await self.redis.setex(
            f"email_analysis:{email_hash}", 
            3600,  # 1 hour TTL
            json.dumps(result)
        )
        
        return result
```

This architecture provides a robust, scalable, and secure foundation for the Privik zero-trust email security platform, ensuring high performance and reliability while maintaining the highest security standards.
