# 🚀 Privik Email Security Platform - Production Deployment Guide

## 📋 Overview

This guide provides comprehensive instructions for deploying the **Privik Email Security Platform** to production environments. The platform is now enterprise-ready with full-stack integration, professional UI/UX, and robust error handling.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Database      │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   (PostgreSQL)  │
│   Port: 3000    │    │   Port: 8000    │    │   Port: 5432    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Redis Cache   │
                    │   Port: 6379    │
                    └─────────────────┘
```

## 🛠️ Prerequisites

### System Requirements
- **OS**: Windows 10/11, macOS 10.15+, or Linux (Ubuntu 20.04+)
- **RAM**: Minimum 4GB, Recommended 8GB+
- **Storage**: Minimum 10GB free space
- **Network**: Internet connection for dependencies

### Software Dependencies
- **Docker**: 20.10+ (Recommended)
- **Docker Compose**: 2.0+ (Recommended)
- **Node.js**: 18+ (For manual deployment)
- **Python**: 3.11+ (For manual deployment)
- **Git**: 2.30+ (For source control)

## 🚀 Deployment Options

### Option 1: Docker Deployment (Recommended)

#### 1.1 Quick Start with Docker
```bash
# Clone the repository
git clone https://github.com/your-org/privik.git
cd privik

# Start all services with Docker Compose
docker-compose up --build -d

# Verify services are running
docker-compose ps
```

#### 1.2 Production Docker Configuration
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  db:
    image: postgres:13-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    environment:
      POSTGRES_DB: privikdb
      POSTGRES_USER: privikuser
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"
    restart: unless-stopped

  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://privikuser:${DB_PASSWORD}@db:5432/privikdb
      REDIS_HOST: redis
      ENVIRONMENT: production
    depends_on:
      - db
      - redis
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    ports:
      - "80:80"
    environment:
      REACT_APP_BACKEND_URL: https://api.yourdomain.com
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
```

### Option 2: Manual Deployment

#### 2.1 Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://user:password@localhost:5432/privikdb"
export REDIS_HOST="localhost"
export ENVIRONMENT="production"

# Run database migrations
python -m alembic upgrade head

# Start the backend server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### 2.2 Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Set environment variables
export REACT_APP_BACKEND_URL="http://localhost:8000"

# Build for production
npm run build

# Serve the built files (using nginx or similar)
# Copy build/ contents to web server directory
```

### Option 3: Cloud Deployment

#### 3.1 AWS Deployment
```bash
# Using AWS CLI and ECS
aws ecs create-cluster --cluster-name privik-cluster

# Deploy using AWS Copilot
copilot app init privik
copilot env init --name production
copilot svc init --name frontend --svc-type "Load Balanced Web Service"
copilot svc init --name backend --svc-type "Backend Service"
copilot svc init --name database --svc-type "Database"
```

#### 3.2 Azure Deployment
```bash
# Using Azure CLI
az group create --name privik-rg --location eastus
az container create --resource-group privik-rg --name privik-app --image your-registry/privik:latest
```

#### 3.3 Google Cloud Deployment
```bash
# Using gcloud CLI
gcloud run deploy privik-frontend --source ./frontend --platform managed --region us-central1
gcloud run deploy privik-backend --source ./backend --platform managed --region us-central1
```

## 🔧 Configuration

### Environment Variables

#### Backend (.env)
```env
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/privikdb
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password

# Security
JWT_SECRET=your_jwt_secret_key
ENCRYPTION_KEY=your_encryption_key

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# External APIs
VIRUSTOTAL_API_KEY=your_virustotal_key
CAPE_API_TOKEN=your_cape_token

# Environment
ENVIRONMENT=production
LOG_LEVEL=INFO
```

#### Frontend (.env)
```env
# Backend API URL
REACT_APP_BACKEND_URL=http://localhost:8000

# Feature Flags
REACT_APP_ENABLE_ANALYTICS=true
REACT_APP_ENABLE_ERROR_REPORTING=true

# External Services
REACT_APP_GOOGLE_ANALYTICS_ID=your_ga_id
```

## 🛡️ Security Configuration

### SSL/TLS Setup
```nginx
# nginx.conf
server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Firewall Configuration
```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# iptables (CentOS/RHEL)
iptables -A INPUT -p tcp --dport 22 -j ACCEPT
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT
```

## 📊 Monitoring & Logging

### Application Monitoring
```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin
    volumes:
      - grafana_data:/var/lib/grafana

  loki:
    image: grafana/loki
    ports:
      - "3100:3100"

volumes:
  grafana_data:
```

### Log Aggregation
```yaml
# logging configuration
version: '3.8'

services:
  elasticsearch:
    image: elasticsearch:7.14.0
    environment:
      - discovery.type=single-node
    ports:
      - "9200:9200"

  kibana:
    image: kibana:7.14.0
    ports:
      - "5601:5601"
    environment:
      ELASTICSEARCH_HOSTS: http://elasticsearch:9200

  logstash:
    image: logstash:7.14.0
    volumes:
      - ./logging/logstash.conf:/usr/share/logstash/pipeline/logstash.conf
```

## 🔄 Backup & Recovery

### Database Backup
```bash
# Automated backup script
#!/bin/bash
BACKUP_DIR="/backups/privik"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup
pg_dump -h localhost -U privikuser privikdb > $BACKUP_DIR/privik_$DATE.sql

# Compress backup
gzip $BACKUP_DIR/privik_$DATE.sql

# Remove backups older than 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
```

### Application Backup
```bash
# Backup application data
tar -czf privik_backup_$DATE.tar.gz \
    ./backend/uploads \
    ./backend/logs \
    ./frontend/build \
    ./config
```

## 📈 Performance Optimization

### Database Optimization
```sql
-- Create indexes for better performance
CREATE INDEX idx_emails_timestamp ON emails(created_at);
CREATE INDEX idx_emails_status ON emails(status);
CREATE INDEX idx_threats_severity ON threats(severity);
CREATE INDEX idx_users_email ON users(email);

-- Optimize queries
EXPLAIN ANALYZE SELECT * FROM emails WHERE status = 'quarantined';
```

### Caching Strategy
```python
# Redis caching configuration
CACHE_CONFIG = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'privik',
        'TIMEOUT': 300,
    }
}
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Database Connection Issues
```bash
# Check database connectivity
psql -h localhost -U privikuser -d privikdb -c "SELECT 1;"

# Check database logs
docker logs privik_db_1
```

#### 2. Frontend Build Issues
```bash
# Clear npm cache
npm cache clean --force

# Remove node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

#### 3. Backend API Issues
```bash
# Check backend logs
docker logs privik_backend_1

# Test API endpoints
curl -X GET http://localhost:8000/health
curl -X GET http://localhost:8000/api/dashboard/stats
```

### Health Checks
```python
# health_check.py
import requests
import sys

def check_health():
    try:
        # Check backend
        response = requests.get('http://localhost:8000/health', timeout=5)
        if response.status_code != 200:
            return False
        
        # Check frontend
        response = requests.get('http://localhost:3000', timeout=5)
        if response.status_code != 200:
            return False
            
        return True
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

if __name__ == "__main__":
    if check_health():
        print("✅ All services are healthy")
        sys.exit(0)
    else:
        print("❌ Health check failed")
        sys.exit(1)
```

## 📞 Support & Maintenance

### Support Contacts
- **Technical Support**: support@privik.com
- **Documentation**: docs.privik.com
- **Community Forum**: community.privik.com

### Maintenance Schedule
- **Daily**: Automated backups, health checks
- **Weekly**: Security updates, performance monitoring
- **Monthly**: Full system updates, capacity planning
- **Quarterly**: Security audits, disaster recovery testing

## 🎯 Next Steps

1. **Set up monitoring and alerting**
2. **Configure automated backups**
3. **Implement CI/CD pipeline**
4. **Set up staging environment**
5. **Conduct security audit**
6. **Plan scaling strategy**

---

## 📚 Additional Resources

- [API Documentation](http://localhost:8000/docs)
- [User Manual](docs/user/README.md)
- [Developer Guide](docs/developer/README.md)
- [Security Guide](docs/security/README.md)
- [Troubleshooting Guide](docs/troubleshooting/README.md)

---

**🎉 Congratulations! Your Privik Email Security Platform is ready for production deployment!**
