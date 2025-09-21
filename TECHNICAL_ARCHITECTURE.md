# 🏗️ Privik Email Security Platform - Technical Architecture

## 📋 System Overview

The **Privik Email Security Platform** is built using a modern, scalable architecture that follows microservices principles and cloud-native patterns. The system is designed for high availability, security, and performance while maintaining flexibility for customization and integration.

## 🏛️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Load Balancer                           │
│                         (Nginx/HAProxy)                        │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────┼───────────────────────────────────────────┐
│                     │                                           │
│  ┌─────────────────┐│  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Frontend      ││  │   Backend       │  │   Database      │ │
│  │   (React SPA)   ││  │   (FastAPI)     │  │   (PostgreSQL)  │ │
│  │   Port: 3000    ││  │   Port: 8000    │  │   Port: 5432    │ │
│  └─────────────────┘│  └─────────────────┘  └─────────────────┘ │
│                     │                                           │
│  ┌─────────────────┐│  ┌─────────────────┐  ┌─────────────────┐ │
│  │   CDN/Static    ││  │   Redis Cache   │  │   Message Queue │ │
│  │   Assets        ││  │   Port: 6379    │  │   (RabbitMQ)    │ │
│  └─────────────────┘│  └─────────────────┘  └─────────────────┘ │
└─────────────────────┼───────────────────────────────────────────┘
                      │
┌─────────────────────┼───────────────────────────────────────────┐
│                     │                                           │
│  ┌─────────────────┐│  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Email Gateway ││  │   Threat Intel  │  │   AI/ML Engine  │ │
│  │   (SMTP/IMAP)   ││  │   Services      │  │   (TensorFlow)  │ │
│  │   Port: 25/993  ││  │   (External)    │  │   Port: 8501    │ │
│  └─────────────────┘│  └─────────────────┘  └─────────────────┘ │
└─────────────────────┼───────────────────────────────────────────┘
                      │
┌─────────────────────┼───────────────────────────────────────────┐
│                     │                                           │
│  ┌─────────────────┐│  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Monitoring    ││  │   Logging       │  │   Backup        │ │
│  │   (Prometheus)  ││  │   (ELK Stack)   │  │   (Automated)   │ │
│  │   Port: 9090    ││  │   Port: 9200    │  │   (S3/Local)    │ │
│  └─────────────────┘│  └─────────────────┘  └─────────────────┘ │
└─────────────────────┼───────────────────────────────────────────┘
```

## 🛠️ Technology Stack

### Frontend Layer
- **Framework**: React 18.2+
- **Build Tool**: Create React App / Vite
- **Styling**: CSS-in-JS, Tailwind CSS
- **State Management**: React Hooks, Context API
- **HTTP Client**: Axios, Fetch API
- **UI Components**: Custom components, Material-UI
- **Testing**: Jest, React Testing Library

### Backend Layer
- **Framework**: FastAPI 0.100+
- **Runtime**: Python 3.11+
- **ASGI Server**: Uvicorn with Gunicorn
- **Authentication**: JWT, OAuth2
- **API Documentation**: OpenAPI/Swagger
- **Validation**: Pydantic models
- **Testing**: Pytest, FastAPI TestClient

### Database Layer
- **Primary Database**: PostgreSQL 13+
- **Cache**: Redis 6+
- **Message Queue**: RabbitMQ / Apache Kafka
- **Search Engine**: Elasticsearch (optional)
- **File Storage**: MinIO / AWS S3

### Infrastructure Layer
- **Containerization**: Docker, Docker Compose
- **Orchestration**: Kubernetes (production)
- **Load Balancer**: Nginx, HAProxy
- **Monitoring**: Prometheus, Grafana
- **Logging**: ELK Stack (Elasticsearch, Logstash, Kibana)
- **CI/CD**: GitHub Actions, Jenkins

## 🔧 Core Components

### 1. Frontend Application

#### Architecture
```
src/
├── components/          # Reusable UI components
│   ├── Dashboard/       # Dashboard-specific components
│   ├── EmailSearch/     # Email search components
│   ├── Settings/        # Settings components
│   └── Common/          # Shared components
├── pages/              # Page-level components
├── hooks/              # Custom React hooks
├── services/           # API service layer
├── utils/              # Utility functions
└── styles/             # Global styles
```

#### Key Features
- **Responsive Design**: Mobile-first approach
- **Progressive Web App**: Offline capabilities
- **Real-time Updates**: WebSocket connections
- **Error Boundaries**: Graceful error handling
- **Lazy Loading**: Code splitting for performance

#### State Management
```javascript
// Context-based state management
const AppContext = createContext({
  user: null,
  settings: {},
  notifications: [],
  updateUser: () => {},
  updateSettings: () => {}
});

// Custom hooks for API integration
const useApi = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const execute = useCallback(async (apiCall) => {
    // API execution logic
  }, []);
  
  return { data, loading, error, execute };
};
```

### 2. Backend API

#### Architecture
```
backend/
├── app/
│   ├── api/            # API route definitions
│   ├── core/           # Core configuration
│   ├── models/         # Database models
│   ├── routers/        # API endpoint routers
│   ├── services/       # Business logic
│   ├── utils/          # Utility functions
│   └── main.py         # Application entry point
├── tests/              # Test suite
├── migrations/         # Database migrations
└── requirements.txt    # Dependencies
```

#### API Structure
```python
# FastAPI application structure
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Privik Email Security API",
    description="Enterprise email security platform",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routers
api_router = APIRouter()
api_router.include_router(dashboard.router, prefix="/dashboard")
api_router.include_router(email_search.router, prefix="/emails")
api_router.include_router(settings.router, prefix="/settings")

app.include_router(api_router, prefix="/api")
```

#### Database Models
```python
# SQLAlchemy models
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Email(Base):
    __tablename__ = "emails"
    
    id = Column(Integer, primary_key=True)
    subject = Column(String(255), nullable=False)
    sender = Column(String(255), nullable=False)
    recipient = Column(String(255), nullable=False)
    content = Column(Text)
    status = Column(String(50), default="pending")
    threat_score = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
class Threat(Base):
    __tablename__ = "threats"
    
    id = Column(Integer, primary_key=True)
    email_id = Column(Integer, ForeignKey("emails.id"))
    threat_type = Column(String(100))
    severity = Column(String(20))
    description = Column(Text)
    detected_at = Column(DateTime, default=datetime.utcnow)
```

### 3. Email Processing Engine

#### Architecture
```
Email Processing Pipeline:
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   SMTP      │───▶│   Parser    │───▶│   Scanner   │───▶│   Quarantine│
│   Gateway   │    │   Engine    │    │   Engine    │    │   Manager   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │                   │
       ▼                   ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Rate      │    │   Content   │    │   AI/ML     │    │   Delivery  │
│   Limiting  │    │   Analysis  │    │   Analysis  │    │   Engine    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

#### Processing Steps
1. **Email Reception**: SMTP/IMAP gateway receives emails
2. **Parsing**: Extract headers, body, attachments
3. **Rate Limiting**: Prevent spam and DoS attacks
4. **Content Analysis**: Text analysis, URL extraction
5. **AI/ML Scanning**: Threat detection using ML models
6. **Quarantine Decision**: Based on threat score
7. **Delivery**: Safe emails delivered, threats quarantined

### 4. AI/ML Engine

#### Models
- **LSTM Network**: Sequential pattern detection
- **CNN**: Image and attachment analysis
- **Isolation Forest**: Anomaly detection
- **Random Forest**: Classification and scoring

#### Training Pipeline
```python
# ML model training pipeline
class MLTrainingPipeline:
    def __init__(self):
        self.models = {
            'lstm': LSTMModel(),
            'cnn': CNNModel(),
            'isolation_forest': IsolationForestModel(),
            'random_forest': RandomForestModel()
        }
    
    def train_models(self, training_data):
        for name, model in self.models.items():
            model.train(training_data)
            model.save(f"models/{name}.pkl")
    
    def predict_threats(self, email_data):
        predictions = {}
        for name, model in self.models.items():
            predictions[name] = model.predict(email_data)
        return self.aggregate_predictions(predictions)
```

## 🔒 Security Architecture

### Authentication & Authorization
```python
# JWT-based authentication
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication")
        return User(username=username)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication")
```

### Data Encryption
- **At Rest**: AES-256 encryption for sensitive data
- **In Transit**: TLS 1.3 for all communications
- **Key Management**: Hardware Security Modules (HSM)
- **Secrets**: Kubernetes secrets, HashiCorp Vault

### Network Security
- **Firewall Rules**: Restrictive ingress/egress
- **VPN Access**: Site-to-site VPN for admin access
- **Network Segmentation**: Isolated subnets
- **DDoS Protection**: CloudFlare/AWS Shield

## 📊 Monitoring & Observability

### Metrics Collection
```python
# Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge

email_processed = Counter('emails_processed_total', 'Total emails processed')
threat_detected = Counter('threats_detected_total', 'Total threats detected')
processing_time = Histogram('email_processing_seconds', 'Email processing time')
active_connections = Gauge('active_connections', 'Active database connections')
```

### Logging Strategy
```python
# Structured logging
import structlog

logger = structlog.get_logger()

async def process_email(email_data):
    logger.info(
        "Processing email",
        email_id=email_data.id,
        sender=email_data.sender,
        recipient=email_data.recipient,
        processing_time=time.time() - start_time
    )
```

### Health Checks
```python
# Health check endpoints
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0",
        "services": {
            "database": await check_database(),
            "redis": await check_redis(),
            "external_apis": await check_external_apis()
        }
    }
```

## 🚀 Deployment Architecture

### Development Environment
```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
    environment:
      - REACT_APP_BACKEND_URL=http://localhost:8000
  
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/privikdb
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=privikdb
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:6-alpine
```

### Production Environment
```yaml
# kubernetes deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: privik-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: privik-backend
  template:
    metadata:
      labels:
        app: privik-backend
    spec:
      containers:
      - name: backend
        image: privik/backend:latest
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

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Tests
        run: |
          docker-compose -f docker-compose.test.yml up --abort-on-container-exit
  
  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build Images
        run: |
          docker build -t privik/frontend:latest ./frontend
          docker build -t privik/backend:latest ./backend
  
  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Kubernetes
        run: |
          kubectl apply -f k8s/
          kubectl rollout restart deployment/privik-backend
          kubectl rollout restart deployment/privik-frontend
```

## 📈 Scalability Considerations

### Horizontal Scaling
- **Stateless Services**: Backend services are stateless
- **Load Balancing**: Multiple backend instances
- **Database Sharding**: Horizontal partitioning
- **CDN**: Global content delivery

### Vertical Scaling
- **Resource Optimization**: Efficient memory usage
- **Database Tuning**: Query optimization
- **Caching Strategy**: Multi-level caching
- **Connection Pooling**: Database connection management

### Auto-scaling
```yaml
# Kubernetes HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: privik-backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: privik-backend
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## 🔧 Configuration Management

### Environment Variables
```bash
# Production environment
DATABASE_URL=postgresql://user:pass@db:5432/privikdb
REDIS_URL=redis://redis:6379
JWT_SECRET=your-secret-key
ENCRYPTION_KEY=your-encryption-key
LOG_LEVEL=INFO
ENVIRONMENT=production
```

### Configuration Files
```python
# config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    database_url: str
    redis_url: str
    jwt_secret: str
    encryption_key: str
    log_level: str = "INFO"
    environment: str = "development"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

## 🛡️ Disaster Recovery

### Backup Strategy
- **Database Backups**: Daily automated backups
- **File Backups**: Hourly incremental backups
- **Configuration Backups**: Version-controlled configs
- **Cross-region Replication**: Multi-region deployment

### Recovery Procedures
```bash
# Database recovery
pg_restore -h localhost -U user -d privikdb backup.sql

# Application recovery
kubectl apply -f k8s/
kubectl rollout restart deployment/privik-backend

# Data validation
python scripts/validate_data.py
```

---

## 📚 Additional Resources

- [API Documentation](http://localhost:8000/docs)
- [Deployment Guide](PRODUCTION_DEPLOYMENT_GUIDE.md)
- [Security Guide](docs/security/README.md)
- [Performance Guide](docs/performance/README.md)

---

**🏗️ The Privik Email Security Platform architecture is designed for enterprise-scale deployment with modern best practices!**
