# Privik Production Deployment Guide

## 🚀 **Production-Ready Deployment**

This guide provides step-by-step instructions for deploying Privik in production environments.

---

## 📋 **Pre-Deployment Checklist**

### **✅ System Requirements**
- **OS**: Ubuntu 20.04+ / CentOS 8+ / RHEL 8+
- **CPU**: 8+ cores (16+ recommended)
- **RAM**: 16GB+ (32GB+ recommended)
- **Storage**: 100GB+ SSD storage
- **Network**: Stable internet connection
- **Firewall**: Ports 8000 (backend), 3000 (frontend), 8001 (LLM)

### **✅ Prerequisites**
- Python 3.9+
- Node.js 16+
- PostgreSQL 13+ (or SQLite for development)
- Redis (optional, for caching)
- Docker (optional, for containerized deployment)

---

## 🏗️ **Deployment Options**

### **1. 🐳 Docker Deployment (Recommended)**

#### **Quick Start with Docker Compose**
```bash
# Clone repository
git clone https://github.com/your-org/privik.git
cd privik

# Create environment file
cp backend/.env.example backend/.env
# Edit backend/.env with your configuration

# Start services
docker-compose up -d

# Check status
docker-compose ps
```

#### **Docker Compose Configuration**
```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/privik
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=privik
      - POSTGRES_USER=privik
      - POSTGRES_PASSWORD=secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:6-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### **2. 🖥️ Traditional Deployment**

#### **Backend Deployment**
```bash
# Create virtual environment
python3 -m venv privik_env
source privik_env/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env

# Initialize database
cd backend
alembic upgrade head

# Start backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### **Frontend Deployment**
```bash
# Install dependencies
cd frontend
npm install

# Build for production
npm run build

# Serve with nginx or similar
npm run start
```

---

## 🔧 **Configuration**

### **Backend Configuration**
```bash
# backend/.env
DATABASE_URL=postgresql://user:pass@localhost:5432/privik
SECRET_KEY=your-secret-key-here
ENVIRONMENT=production
LOG_LEVEL=INFO

# Email settings
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# AI/ML settings
AI_ENABLED=true
MODEL_PATH=/path/to/your/models
CONFIDENCE_THRESHOLD=0.7

# SIEM integration
SIEM_ENABLED=true
SIEM_TYPE=splunk
SIEM_HOST=your-siem-host
SIEM_API_KEY=your-api-key
```

### **Frontend Configuration**
```javascript
// frontend/src/config.js
const config = {
  apiUrl: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  environment: process.env.NODE_ENV || 'development',
  features: {
    aiEnabled: true,
    siemEnabled: true,
    mobileEnabled: true
  }
};
```

---

## 🔐 **Security Configuration**

### **SSL/TLS Setup**
```bash
# Generate SSL certificate
sudo certbot certonly --standalone -d your-domain.com

# Configure nginx
sudo nano /etc/nginx/sites-available/privik

# Enable site
sudo ln -s /etc/nginx/sites-available/privik /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### **Firewall Configuration**
```bash
# Configure UFW firewall
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 8000/tcp  # Backend API
sudo ufw allow 3000/tcp  # Frontend
sudo ufw enable
```

### **Database Security**
```sql
-- Create dedicated database user
CREATE USER privik_user WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE privik TO privik_user;
GRANT USAGE ON SCHEMA public TO privik_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO privik_user;
```

---

## 📊 **Monitoring and Logging**

### **Application Monitoring**
```bash
# Install monitoring tools
sudo apt install prometheus node-exporter grafana

# Configure Prometheus
sudo nano /etc/prometheus/prometheus.yml

# Start monitoring services
sudo systemctl start prometheus
sudo systemctl start node-exporter
sudo systemctl start grafana-server
```

### **Log Management**
```bash
# Configure log rotation
sudo nano /etc/logrotate.d/privik

# Example logrotate configuration
/var/log/privik/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 privik privik
}
```

### **Health Checks**
```bash
# Backend health check
curl -f http://localhost:8000/health

# Frontend health check
curl -f http://localhost:3000

# Database health check
pg_isready -h localhost -p 5432 -U privik_user
```

---

## 🔄 **Backup and Recovery**

### **Database Backup**
```bash
# Create backup script
cat > /opt/privik/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/privik/backups"
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -h localhost -U privik_user privik > $BACKUP_DIR/privik_$DATE.sql
gzip $BACKUP_DIR/privik_$DATE.sql
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
EOF

# Make executable and schedule
chmod +x /opt/privik/backup.sh
crontab -e
# Add: 0 2 * * * /opt/privik/backup.sh
```

### **Application Backup**
```bash
# Backup configuration files
tar -czf /opt/privik/backups/config_$(date +%Y%m%d).tar.gz \
    backend/.env \
    frontend/src/config.js \
    /etc/nginx/sites-available/privik
```

---

## 🚀 **Scaling and Performance**

### **Load Balancing**
```nginx
# nginx load balancer configuration
upstream backend {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

server {
    listen 80;
    server_name your-domain.com;
    
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### **Caching Strategy**
```python
# Redis caching configuration
import redis
from functools import wraps

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_result(expire_time=300):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            result = redis_client.get(cache_key)
            if result:
                return json.loads(result)
            result = func(*args, **kwargs)
            redis_client.setex(cache_key, expire_time, json.dumps(result))
            return result
        return wrapper
    return decorator
```

---

## 🔧 **Maintenance and Updates**

### **Update Process**
```bash
# Create update script
cat > /opt/privik/update.sh << 'EOF'
#!/bin/bash
cd /opt/privik
git pull origin main

# Update backend
cd backend
pip install -r requirements.txt
alembic upgrade head

# Update frontend
cd ../frontend
npm install
npm run build

# Restart services
sudo systemctl restart privik-backend
sudo systemctl restart privik-frontend
EOF

chmod +x /opt/privik/update.sh
```

### **Systemd Services**
```ini
# /etc/systemd/system/privik-backend.service
[Unit]
Description=Privik Backend
After=network.target

[Service]
Type=simple
User=privik
WorkingDirectory=/opt/privik/backend
Environment=PATH=/opt/privik/venv/bin
ExecStart=/opt/privik/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## 🧪 **Testing and Validation**

### **Deployment Testing**
```bash
# Run comprehensive tests
python test_comprehensive.py

# API endpoint testing
curl -X POST http://localhost:8000/api/ingest/email \
  -H "Content-Type: application/json" \
  -d '{"subject": "Test", "content": "Test content"}'

# Frontend testing
npm test -- --coverage
```

### **Performance Testing**
```bash
# Load testing with Apache Bench
ab -n 1000 -c 10 http://localhost:8000/health

# API performance testing
locust -f load_test.py --host=http://localhost:8000
```

---

## 📞 **Support and Troubleshooting**

### **Common Issues**

#### **Database Connection Issues**
```bash
# Check database status
sudo systemctl status postgresql

# Test connection
psql -h localhost -U privik_user -d privik

# Check logs
sudo tail -f /var/log/postgresql/postgresql-*.log
```

#### **Backend Service Issues**
```bash
# Check service status
sudo systemctl status privik-backend

# View logs
sudo journalctl -u privik-backend -f

# Restart service
sudo systemctl restart privik-backend
```

#### **Frontend Issues**
```bash
# Check build status
cd frontend
npm run build

# Check for dependency issues
npm audit

# Clear cache
npm cache clean --force
```

### **Support Resources**
- **Documentation**: `/docs` directory
- **Logs**: `/var/log/privik/`
- **Configuration**: `/opt/privik/config/`
- **Backups**: `/opt/privik/backups/`

---

## 🎯 **Post-Deployment Checklist**

### **✅ Verification Steps**
- [ ] All services running and healthy
- [ ] SSL certificates installed and valid
- [ ] Database backups configured and tested
- [ ] Monitoring and alerting set up
- [ ] Security configurations applied
- [ ] Performance benchmarks met
- [ ] Documentation updated
- [ ] Team training completed

### **✅ Security Audit**
- [ ] Firewall rules configured
- [ ] SSL/TLS properly configured
- [ ] Database security hardened
- [ ] Application secrets secured
- [ ] Access controls implemented
- [ ] Audit logging enabled

### **✅ Performance Validation**
- [ ] Response times under 2 seconds
- [ ] Throughput meets requirements
- [ ] Resource usage within limits
- [ ] Caching working effectively
- [ ] Load balancing functional

---

*"Secure deployment, secure operations"*
