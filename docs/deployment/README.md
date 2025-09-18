# Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying Privik in various environments, from development to production. Privik supports multiple deployment methods including Docker Compose, Kubernetes, and cloud-native deployments.

## Prerequisites

### System Requirements

**Minimum Requirements:**
- CPU: 4 cores
- RAM: 8GB
- Storage: 100GB SSD
- Network: 1Gbps

**Recommended Requirements:**
- CPU: 8+ cores
- RAM: 16GB+
- Storage: 500GB+ SSD
- Network: 10Gbps

### Software Dependencies

- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Python**: 3.9+
- **Node.js**: 16+
- **PostgreSQL**: 13+
- **Redis**: 6+
- **Nginx**: 1.18+ (for production)

### External Services

- **CAPEv2**: For sandbox analysis
- **MinIO/S3**: For object storage
- **VirusTotal API**: For threat intelligence
- **Email Providers**: Gmail, Microsoft 365, IMAP/POP3

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/your-org/privik.git
cd privik
```

### 2. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

### 3. Start with Docker Compose

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### 4. Initialize Database

```bash
# Run database migrations
docker-compose exec privik-api alembic upgrade head

# Create initial admin user
docker-compose exec privik-api python -m app.cli create-admin
```

### 5. Access the Platform

- **Frontend**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Admin**: http://localhost:3000/admin

## Development Deployment

### Local Development Setup

#### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Start PostgreSQL and Redis
docker-compose -f docker-compose.dev.yml up -d postgres redis

# Run database migrations
alembic upgrade head

# Start the API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

#### 3. Development Services

```bash
# Start additional services for development
docker-compose -f docker-compose.dev.yml up -d

# Services include:
# - PostgreSQL (database)
# - Redis (caching)
# - MinIO (object storage)
# - CAPEv2 (sandbox)
```

### Development Configuration

```bash
# .env for development
DEBUG=true
LOG_LEVEL=DEBUG
DATABASE_URL=postgresql://postgres:password@localhost:5432/privik_dev
REDIS_URL=redis://localhost:6379/0
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
CAPE_BASE_URL=http://localhost:8000
CAPE_API_TOKEN=your_cape_token
```

## Production Deployment

### Docker Compose Production

#### 1. Production Configuration

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  privik-api:
    build: 
      context: ./backend
      dockerfile: Dockerfile.prod
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - MINIO_ENDPOINT=${MINIO_ENDPOINT}
      - MINIO_ACCESS_KEY=${MINIO_ACCESS_KEY}
      - MINIO_SECRET_KEY=${MINIO_SECRET_KEY}
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    depends_on:
      - postgres
      - redis
      - minio

  privik-frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=${API_URL}
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    restart: unless-stopped
    depends_on:
      - privik-api
      - privik-frontend

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    restart: unless-stopped

  minio:
    image: minio/minio
    command: server /data
    environment:
      - MINIO_ACCESS_KEY=${MINIO_ACCESS_KEY}
      - MINIO_SECRET_KEY=${MINIO_SECRET_KEY}
    volumes:
      - minio_data:/data
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  minio_data:
```

#### 2. Production Environment

```bash
# .env for production
DEBUG=false
LOG_LEVEL=INFO
DATABASE_URL=postgresql://privik:secure_password@postgres:5432/privik
REDIS_URL=redis://:secure_password@redis:6379/0
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=secure_access_key
MINIO_SECRET_KEY=secure_secret_key
HMAC_API_KEY_ID=your_api_key_id
HMAC_API_SECRET=your_secure_api_secret
JWT_SECRET=your_secure_jwt_secret
CAPE_BASE_URL=https://cape.your-domain.com
CAPE_API_TOKEN=your_cape_token
VIRUSTOTAL_API_KEY=your_virustotal_key
```

#### 3. SSL Configuration

```nginx
# nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream privik_api {
        server privik-api:8000;
    }

    upstream privik_frontend {
        server privik-frontend:3000;
    }

    server {
        listen 80;
        server_name your-domain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;

        location /api/ {
            proxy_pass http://privik_api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location / {
            proxy_pass http://privik_frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

#### 4. Deploy to Production

```bash
# Build and start production services
docker-compose -f docker-compose.prod.yml up -d --build

# Run database migrations
docker-compose -f docker-compose.prod.yml exec privik-api alembic upgrade head

# Create admin user
docker-compose -f docker-compose.prod.yml exec privik-api python -m app.cli create-admin

# Check service health
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs -f
```

### Kubernetes Deployment

#### 1. Namespace and Secrets

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: privik

---
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: privik-secrets
  namespace: privik
type: Opaque
data:
  database-url: <base64-encoded-database-url>
  redis-url: <base64-encoded-redis-url>
  hmac-secret: <base64-encoded-hmac-secret>
  jwt-secret: <base64-encoded-jwt-secret>
```

#### 2. ConfigMap

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: privik-config
  namespace: privik
data:
  LOG_LEVEL: "INFO"
  DEBUG: "false"
  MINIO_ENDPOINT: "minio:9000"
  CAPE_BASE_URL: "https://cape.your-domain.com"
```

#### 3. Database Deployment

```yaml
# k8s/postgres.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: privik
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15
        env:
        - name: POSTGRES_DB
          value: "privik"
        - name: POSTGRES_USER
          value: "privik"
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: privik-secrets
              key: postgres-password
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
      volumes:
      - name: postgres-storage
        persistentVolumeClaim:
          claimName: postgres-pvc

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
  namespace: privik
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Gi

---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: privik
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
```

#### 4. API Deployment

```yaml
# k8s/api.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: privik-api
  namespace: privik
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
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: privik-secrets
              key: redis-url
        envFrom:
        - configMapRef:
            name: privik-config
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: privik-api
  namespace: privik
spec:
  selector:
    app: privik-api
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
```

#### 5. Frontend Deployment

```yaml
# k8s/frontend.yaml
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
      - name: privik-frontend
        image: privik/frontend:latest
        ports:
        - containerPort: 3000
        env:
        - name: REACT_APP_API_URL
          value: "https://api.your-domain.com"
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "200m"

---
apiVersion: v1
kind: Service
metadata:
  name: privik-frontend
  namespace: privik
spec:
  selector:
    app: privik-frontend
  ports:
  - port: 3000
    targetPort: 3000
  type: ClusterIP
```

#### 6. Ingress

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: privik-ingress
  namespace: privik
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - your-domain.com
    - api.your-domain.com
    secretName: privik-tls
  rules:
  - host: your-domain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: privik-frontend
            port:
              number: 3000
  - host: api.your-domain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: privik-api
            port:
              number: 8000
```

#### 7. Deploy to Kubernetes

```bash
# Apply all configurations
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n privik
kubectl get services -n privik
kubectl get ingress -n privik

# Run database migrations
kubectl exec -n privik deployment/privik-api -- alembic upgrade head

# Create admin user
kubectl exec -n privik deployment/privik-api -- python -m app.cli create-admin
```

## Cloud Deployments

### AWS Deployment

#### 1. EKS Setup

```bash
# Create EKS cluster
eksctl create cluster \
  --name privik-cluster \
  --region us-west-2 \
  --nodegroup-name privik-nodes \
  --node-type t3.medium \
  --nodes 3 \
  --nodes-min 1 \
  --nodes-max 5

# Install AWS Load Balancer Controller
kubectl apply -k "github.com/aws/eks-charts/stable/aws-load-balancer-controller/crds?ref=master"
helm repo add eks https://aws.github.io/eks-charts
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=privik-cluster
```

#### 2. RDS Database

```bash
# Create RDS PostgreSQL instance
aws rds create-db-instance \
  --db-instance-identifier privik-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 15.4 \
  --master-username privik \
  --master-user-password YourSecurePassword \
  --allocated-storage 20 \
  --vpc-security-group-ids sg-12345678
```

#### 3. ElastiCache Redis

```bash
# Create ElastiCache Redis cluster
aws elasticache create-cache-cluster \
  --cache-cluster-id privik-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --num-cache-nodes 1 \
  --vpc-security-group-ids sg-12345678
```

### Google Cloud Deployment

#### 1. GKE Setup

```bash
# Create GKE cluster
gcloud container clusters create privik-cluster \
  --zone us-central1-a \
  --num-nodes 3 \
  --machine-type e2-medium \
  --enable-autoscaling \
  --min-nodes 1 \
  --max-nodes 5

# Get cluster credentials
gcloud container clusters get-credentials privik-cluster --zone us-central1-a
```

#### 2. Cloud SQL

```bash
# Create Cloud SQL PostgreSQL instance
gcloud sql instances create privik-db \
  --database-version POSTGRES_15 \
  --tier db-f1-micro \
  --region us-central1 \
  --root-password YourSecurePassword
```

### Azure Deployment

#### 1. AKS Setup

```bash
# Create AKS cluster
az aks create \
  --resource-group privik-rg \
  --name privik-cluster \
  --node-count 3 \
  --node-vm-size Standard_B2s \
  --enable-addons monitoring \
  --generate-ssh-keys

# Get cluster credentials
az aks get-credentials --resource-group privik-rg --name privik-cluster
```

## Monitoring and Logging

### Prometheus and Grafana

#### 1. Install Prometheus

```yaml
# monitoring/prometheus.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
    scrape_configs:
    - job_name: 'privik-api'
      static_configs:
      - targets: ['privik-api:8000']
      metrics_path: /metrics
```

#### 2. Install Grafana

```bash
# Install Grafana
helm repo add grafana https://grafana.github.io/helm-charts
helm install grafana grafana/grafana \
  --namespace monitoring \
  --set persistence.enabled=true \
  --set adminPassword=admin
```

### ELK Stack

#### 1. Elasticsearch

```yaml
# logging/elasticsearch.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: elasticsearch
  namespace: logging
spec:
  serviceName: elasticsearch
  replicas: 1
  selector:
    matchLabels:
      app: elasticsearch
  template:
    metadata:
      labels:
        app: elasticsearch
    spec:
      containers:
      - name: elasticsearch
        image: docker.elastic.co/elasticsearch/elasticsearch:8.8.0
        env:
        - name: discovery.type
          value: single-node
        - name: xpack.security.enabled
          value: "false"
        ports:
        - containerPort: 9200
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
```

#### 2. Kibana

```yaml
# logging/kibana.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kibana
  namespace: logging
spec:
  replicas: 1
  selector:
    matchLabels:
      app: kibana
  template:
    metadata:
      labels:
        app: kibana
    spec:
      containers:
      - name: kibana
        image: docker.elastic.co/kibana/kibana:8.8.0
        env:
        - name: ELASTICSEARCH_HOSTS
          value: http://elasticsearch:9200
        ports:
        - containerPort: 5601
```

## Backup and Recovery

### Database Backup

#### 1. Automated Backups

```bash
#!/bin/bash
# backup-db.sh

# Create backup
pg_dump $DATABASE_URL > /backups/privik-$(date +%Y%m%d-%H%M%S).sql

# Compress backup
gzip /backups/privik-$(date +%Y%m%d-%H%M%S).sql

# Remove old backups (keep 30 days)
find /backups -name "privik-*.sql.gz" -mtime +30 -delete
```

#### 2. Kubernetes CronJob

```yaml
# backup/cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: db-backup
  namespace: privik
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: postgres:15
            command:
            - /bin/bash
            - -c
            - |
              pg_dump $DATABASE_URL | gzip > /backup/privik-$(date +%Y%m%d-%H%M%S).sql.gz
              aws s3 cp /backup/privik-$(date +%Y%m%d-%H%M%S).sql.gz s3://privik-backups/
            env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: privik-secrets
                  key: database-url
            volumeMounts:
            - name: backup-storage
              mountPath: /backup
          volumes:
          - name: backup-storage
            persistentVolumeClaim:
              claimName: backup-pvc
          restartPolicy: OnFailure
```

### File Storage Backup

#### 1. MinIO Backup

```bash
#!/bin/bash
# backup-minio.sh

# Sync MinIO data to S3
mc mirror /data s3://privik-backups/minio/$(date +%Y%m%d)/

# Remove old backups
mc rm --recursive --force s3://privik-backups/minio/$(date -d '30 days ago' +%Y%m%d)/
```

## Security Hardening

### 1. Network Security

```yaml
# security/network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: privik-network-policy
  namespace: privik
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to: []
    ports:
    - protocol: TCP
      port: 5432  # PostgreSQL
    - protocol: TCP
      port: 6379  # Redis
    - protocol: TCP
      port: 9000  # MinIO
```

### 2. Pod Security

```yaml
# security/pod-security-policy.yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: privik-psp
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'downwardAPI'
    - 'persistentVolumeClaim'
  runAsUser:
    rule: 'MustRunAsNonRoot'
  seLinux:
    rule: 'RunAsAny'
  fsGroup:
    rule: 'RunAsAny'
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Issues

```bash
# Check database connectivity
kubectl exec -n privik deployment/privik-api -- python -c "
import psycopg2
conn = psycopg2.connect('$DATABASE_URL')
print('Database connection successful')
"

# Check database logs
kubectl logs -n privik deployment/postgres
```

#### 2. Redis Connection Issues

```bash
# Test Redis connection
kubectl exec -n privik deployment/privik-api -- python -c "
import redis
r = redis.from_url('$REDIS_URL')
print('Redis connection successful:', r.ping())
"
```

#### 3. API Health Check

```bash
# Check API health
curl -f http://localhost:8000/health

# Check API readiness
curl -f http://localhost:8000/ready
```

### Performance Tuning

#### 1. Database Optimization

```sql
-- Check slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Check index usage
SELECT schemaname, tablename, attname, n_distinct, correlation 
FROM pg_stats 
WHERE schemaname = 'public';
```

#### 2. Redis Optimization

```bash
# Check Redis memory usage
redis-cli info memory

# Check Redis performance
redis-cli --latency-history -i 1
```

## Maintenance

### 1. Updates and Upgrades

```bash
# Update application
kubectl set image deployment/privik-api privik-api=privik/api:v2.0.0 -n privik

# Rolling update
kubectl rollout status deployment/privik-api -n privik

# Rollback if needed
kubectl rollout undo deployment/privik-api -n privik
```

### 2. Scaling

```bash
# Scale API replicas
kubectl scale deployment privik-api --replicas=5 -n privik

# Auto-scaling
kubectl autoscale deployment privik-api --cpu-percent=70 --min=2 --max=10 -n privik
```

This deployment guide provides comprehensive instructions for deploying Privik in various environments, ensuring a smooth and secure deployment process.
