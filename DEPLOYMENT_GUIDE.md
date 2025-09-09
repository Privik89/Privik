# Privik Deployment Guide

## 🚀 **Production Deployment Guide**

### **Overview**
This guide covers deploying the Privik Zero-Trust Email Security Platform in production environments, including cloud platforms, on-premises servers, and containerized deployments.

## 📋 **Prerequisites**

### **System Requirements**
- **CPU**: 4+ cores (8+ recommended)
- **RAM**: 8GB+ (16GB+ recommended)
- **Storage**: 100GB+ SSD
- **Network**: 1Gbps+ bandwidth
- **OS**: Linux (Ubuntu 20.04+), Windows Server 2019+, or macOS 10.15+

### **Software Requirements**
- **Python**: 3.11+
- **Node.js**: 16+
- **Database**: PostgreSQL 13+ (production) or SQLite (development)
- **Redis**: 6+ (for caching and session management)
- **Docker**: 20+ (optional, for containerized deployment)

## 🏗️ **Deployment Options**

### **Option 1: Traditional Server Deployment**

#### **Linux Server Setup**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.11 python3.11-venv python3.11-dev
sudo apt install -y nodejs npm postgresql redis-server
sudo apt install -y nginx certbot python3-certbot-nginx

# Create application user
sudo useradd -m -s /bin/bash privik
sudo usermod -aG sudo privik
```

#### **Application Deployment**
```bash
# Switch to application user
sudo su - privik

# Clone repository
git clone <repository-url> /home/privik/privik
cd /home/privik/privik

# Setup application
chmod +x setup_linux.sh
./setup_linux.sh

# Configure environment
cp .env.example .env
nano .env
```

#### **Environment Configuration**
```bash
# .env file
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql://privik:password@localhost/privik
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
```

### **Option 2: Docker Deployment**

#### **Docker Compose Setup**
```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=postgresql://privik:password@db:5432/privik
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - ./data:/app/data

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:8000
    depends_on:
      - backend

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=privik
      - POSTGRES_USER=privik
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:6-alpine
    volumes:
      - redis_data:/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - backend
      - frontend

volumes:
  postgres_data:
  redis_data:
```

#### **Docker Build Files**
```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```dockerfile
# frontend/Dockerfile
FROM node:16-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .

RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
```

### **Option 3: Kubernetes Deployment**

#### **Kubernetes Manifests**
```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: privik
```

```yaml
# k8s/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: privik-backend
  namespace: privik
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
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: privik-secrets
              key: redis-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
```

```yaml
# k8s/frontend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: privik-frontend
  namespace: privik
spec:
  replicas: 2
  selector:
    matchLabels:
      app: privik-frontend
  template:
    metadata:
      labels:
        app: privik-frontend
    spec:
      containers:
      - name: frontend
        image: privik/frontend:latest
        ports:
        - containerPort: 3000
        env:
        - name: REACT_APP_API_URL
          value: "http://privik-backend-service:8000"
```

## 🔧 **Configuration**

### **Database Configuration**

#### **PostgreSQL Setup**
```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE privik;
CREATE USER privik WITH PASSWORD 'secure-password';
GRANT ALL PRIVILEGES ON DATABASE privik TO privik;
\q

# Configure PostgreSQL
sudo nano /etc/postgresql/13/main/postgresql.conf
# Set: listen_addresses = 'localhost'
# Set: max_connections = 200

sudo nano /etc/postgresql/13/main/pg_hba.conf
# Add: local   privik   privik   md5
```

#### **Database Migration**
```bash
# Run database migrations
./venv/bin/python -c "
import sys
sys.path.append('backend')
from backend.app.database import create_tables
create_tables()
print('Database tables created')
"
```

### **Redis Configuration**

#### **Redis Setup**
```bash
# Install Redis
sudo apt install redis-server

# Configure Redis
sudo nano /etc/redis/redis.conf
# Set: bind 127.0.0.1
# Set: requirepass your-redis-password
# Set: maxmemory 256mb
# Set: maxmemory-policy allkeys-lru

# Start Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

### **Nginx Configuration**

#### **Nginx Setup**
```nginx
# /etc/nginx/sites-available/privik
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### **Enable Site**
```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/privik /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### **SSL Certificate**

#### **Let's Encrypt Setup**
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 🔒 **Security Configuration**

### **Firewall Setup**
```bash
# Configure UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### **Application Security**
```bash
# Set secure permissions
sudo chown -R privik:privik /home/privik/privik
sudo chmod -R 755 /home/privik/privik
sudo chmod 600 /home/privik/privik/.env

# Disable root login
sudo nano /etc/ssh/sshd_config
# Set: PermitRootLogin no
sudo systemctl restart ssh
```

### **Environment Variables**
```bash
# Secure environment variables
export SECRET_KEY=$(openssl rand -hex 32)
export DATABASE_URL="postgresql://privik:$(openssl rand -base64 32)@localhost/privik"
export REDIS_URL="redis://:$(openssl rand -base64 32)@localhost:6379"
```

## 📊 **Monitoring and Logging**

### **System Monitoring**
```bash
# Install monitoring tools
sudo apt install htop iotop nethogs

# Configure log rotation
sudo nano /etc/logrotate.d/privik
# Add:
# /home/privik/privik/logs/*.log {
#     daily
#     missingok
#     rotate 52
#     compress
#     delaycompress
#     notifempty
#     create 644 privik privik
# }
```

### **Application Monitoring**
```bash
# Install monitoring agent
sudo apt install prometheus-node-exporter

# Configure application metrics
export METRICS_ENABLED=true
export METRICS_PORT=9090
```

### **Log Management**
```bash
# Configure structured logging
export LOG_LEVEL=INFO
export LOG_FORMAT=json
export LOG_FILE=/home/privik/privik/logs/privik.log

# Create log directory
mkdir -p /home/privik/privik/logs
```

## 🚀 **Deployment Process**

### **Automated Deployment**
```bash
#!/bin/bash
# deploy.sh

set -e

echo "Starting deployment..."

# Backup current version
if [ -d "/home/privik/privik" ]; then
    cp -r /home/privik/privik /home/privik/privik.backup.$(date +%Y%m%d_%H%M%S)
fi

# Pull latest code
cd /home/privik/privik
git pull origin main

# Update dependencies
./venv/bin/pip install -r backend/requirements.txt
cd frontend && npm install && cd ..

# Run database migrations
./venv/bin/python -c "
import sys
sys.path.append('backend')
from backend.app.database import create_tables
create_tables()
"

# Restart services
sudo systemctl restart privik-backend
sudo systemctl restart privik-frontend
sudo systemctl reload nginx

echo "Deployment completed successfully!"
```

### **Service Configuration**
```ini
# /etc/systemd/system/privik-backend.service
[Unit]
Description=Privik Backend Service
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=privik
WorkingDirectory=/home/privik/privik
Environment=PATH=/home/privik/privik/venv/bin
ExecStart=/home/privik/privik/venv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/privik-frontend.service
[Unit]
Description=Privik Frontend Service
After=network.target privik-backend.service

[Service]
Type=simple
User=privik
WorkingDirectory=/home/privik/privik/frontend
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### **Enable Services**
```bash
# Enable and start services
sudo systemctl daemon-reload
sudo systemctl enable privik-backend
sudo systemctl enable privik-frontend
sudo systemctl start privik-backend
sudo systemctl start privik-frontend
```

## 🔄 **Backup and Recovery**

### **Backup Strategy**
```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/home/privik/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
pg_dump -h localhost -U privik privik > $BACKUP_DIR/database_$DATE.sql

# Backup application files
tar -czf $BACKUP_DIR/application_$DATE.tar.gz /home/privik/privik

# Backup configuration
tar -czf $BACKUP_DIR/config_$DATE.tar.gz /etc/nginx/sites-available/privik /etc/systemd/system/privik-*.service

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

### **Recovery Process**
```bash
#!/bin/bash
# restore.sh

BACKUP_DATE=$1
BACKUP_DIR="/home/privik/backups"

if [ -z "$BACKUP_DATE" ]; then
    echo "Usage: $0 <backup_date>"
    echo "Available backups:"
    ls -la $BACKUP_DIR
    exit 1
fi

# Stop services
sudo systemctl stop privik-backend
sudo systemctl stop privik-frontend

# Restore database
psql -h localhost -U privik privik < $BACKUP_DIR/database_$BACKUP_DATE.sql

# Restore application files
tar -xzf $BACKUP_DIR/application_$BACKUP_DATE.tar.gz -C /

# Restore configuration
tar -xzf $BACKUP_DIR/config_$BACKUP_DATE.tar.gz -C /

# Restart services
sudo systemctl start privik-backend
sudo systemctl start privik-frontend

echo "Restore completed: $BACKUP_DATE"
```

## 📈 **Performance Optimization**

### **Database Optimization**
```sql
-- PostgreSQL optimization
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;

-- Create indexes
CREATE INDEX idx_emails_received_at ON emails(received_at);
CREATE INDEX idx_emails_sender ON emails(sender);
CREATE INDEX idx_emails_threat_score ON emails(threat_score);
```

### **Application Optimization**
```bash
# Python optimization
export PYTHONOPTIMIZE=1
export PYTHONDONTWRITEBYTECODE=1

# Node.js optimization
export NODE_ENV=production
export NODE_OPTIONS="--max-old-space-size=4096"
```

### **Nginx Optimization**
```nginx
# nginx.conf optimizations
worker_processes auto;
worker_connections 1024;

gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

client_max_body_size 10M;
client_body_timeout 60s;
client_header_timeout 60s;
```

## 🔍 **Health Checks**

### **Application Health Checks**
```bash
#!/bin/bash
# health_check.sh

# Check backend
if ! curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "Backend health check failed"
    exit 1
fi

# Check frontend
if ! curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "Frontend health check failed"
    exit 1
fi

# Check database
if ! pg_isready -h localhost -U privik > /dev/null 2>&1; then
    echo "Database health check failed"
    exit 1
fi

# Check Redis
if ! redis-cli ping > /dev/null 2>&1; then
    echo "Redis health check failed"
    exit 1
fi

echo "All health checks passed"
```

### **Monitoring Script**
```bash
#!/bin/bash
# monitor.sh

while true; do
    if ! ./health_check.sh; then
        echo "Health check failed at $(date)"
        # Send alert
        curl -X POST "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK" \
             -H "Content-Type: application/json" \
             -d '{"text":"Privik health check failed"}'
    fi
    sleep 60
done
```

## 📞 **Support and Maintenance**

### **Log Monitoring**
```bash
# Monitor application logs
tail -f /home/privik/privik/logs/privik.log

# Monitor system logs
sudo journalctl -u privik-backend -f
sudo journalctl -u privik-frontend -f
```

### **Performance Monitoring**
```bash
# System resources
htop
iotop
nethogs

# Application metrics
curl http://localhost:8000/metrics
```

### **Update Process**
```bash
# Update application
cd /home/privik/privik
git pull origin main
./venv/bin/pip install -r backend/requirements.txt
cd frontend && npm install && cd ..
sudo systemctl restart privik-backend
sudo systemctl restart privik-frontend
```

---

## 📋 **Deployment Checklist**

### **Pre-Deployment**
- [ ] System requirements met
- [ ] Dependencies installed
- [ ] Database configured
- [ ] SSL certificates obtained
- [ ] Firewall configured
- [ ] Monitoring setup

### **Deployment**
- [ ] Application deployed
- [ ] Services configured
- [ ] Health checks passing
- [ ] Performance optimized
- [ ] Backup strategy implemented

### **Post-Deployment**
- [ ] Monitoring active
- [ ] Logs configured
- [ ] Alerts setup
- [ ] Documentation updated
- [ ] Team trained

---

**Last Updated**: September 10, 2025  
**Version**: 1.0.0  
**Compatibility**: Python 3.11+, Node.js 16+, Linux/Windows/macOS
