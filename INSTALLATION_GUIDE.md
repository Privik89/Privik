# Privik Email Security Platform - Installation Guide

## 🚀 **Quick Start (Recommended)**

### **Option 1: Docker Installation (Cross-Platform)**
```bash
# 1. Clone the repository
git clone <repository-url>
cd Privik

# 2. Start all services
docker-compose up --build

# 3. Access the platform
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
```

### **Option 2: Universal Scripts**
```bash
# Windows
start-privik.bat

# Linux/macOS
chmod +x start-privik.sh
./start-privik.sh
```

---

## 📋 **System Requirements**

### **Minimum Requirements**
- **CPU**: 2 cores, 2.0 GHz
- **RAM**: 4 GB
- **Storage**: 10 GB free space
- **OS**: Windows 10+, macOS 10.15+, Ubuntu 18.04+

### **Recommended Requirements**
- **CPU**: 4+ cores, 3.0+ GHz
- **RAM**: 8+ GB
- **Storage**: 50+ GB free space
- **Network**: Stable internet connection

---

## 🔧 **Prerequisites**

### **For Docker Installation**
- Docker Desktop 4.0+
- Docker Compose 2.0+

### **For Native Installation**
- Node.js 18.0+
- Python 3.11+
- Git 2.30+
- Redis (optional, for caching)

---

## 💻 **Platform-Specific Installation**

### **Windows Installation**

#### **Step 1: Install Prerequisites**
```powershell
# Install Node.js from https://nodejs.org
# Install Python from https://python.org
# Install Git from https://git-scm.com

# Verify installations
node --version
python --version
git --version
```

#### **Step 2: Clone Repository**
```powershell
git clone <repository-url>
cd Privik

# Configure Git for cross-platform compatibility
git config core.autocrlf true
```

#### **Step 3: Setup Backend**
```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

#### **Step 4: Setup Frontend**
```powershell
cd ..\frontend
npm install
```

#### **Step 5: Start Services**
```powershell
# Option 1: Use startup script
start-privik.bat

# Option 2: Manual start
# Backend (in one terminal)
cd backend
venv\Scripts\activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (in another terminal)
cd frontend
npm start
```

### **Linux/macOS Installation**

#### **Step 1: Install Prerequisites**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install nodejs npm python3 python3-pip python3-venv git

# macOS (with Homebrew)
brew install node python git

# Verify installations
node --version
python3 --version
git --version
```

#### **Step 2: Clone Repository**
```bash
git clone <repository-url>
cd Privik

# Configure Git for cross-platform compatibility
git config core.autocrlf input
```

#### **Step 3: Setup Backend**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### **Step 4: Setup Frontend**
```bash
cd ../frontend
npm install
```

#### **Step 5: Start Services**
```bash
# Option 1: Use startup script
chmod +x start-privik.sh
./start-privik.sh

# Option 2: Manual start
# Backend (in one terminal)
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (in another terminal)
cd frontend
npm start
```

---

## 🐳 **Docker Installation**

### **Step 1: Install Docker**
- **Windows**: Download Docker Desktop from docker.com
- **Linux**: Follow Docker installation guide for your distribution
- **macOS**: Download Docker Desktop from docker.com

### **Step 2: Clone and Start**
```bash
git clone <repository-url>
cd Privik
docker-compose up --build
```

### **Step 3: Verify Installation**
```bash
# Check running containers
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

## ⚙️ **Configuration**

### **Environment Variables**

#### **Backend Configuration**
Create `backend/.env` file:
```env
# Database
DATABASE_URL=sqlite:///./privik.db

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Security
JWT_SECRET=your-secret-key-here
ENCRYPTION_KEY=your-encryption-key-here

# Features
ENABLE_SANDBOX=true
ENABLE_ML_MODELS=true
ENABLE_SIEM_INTEGRATION=true

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

#### **Frontend Configuration**
Create `frontend/.env` file:
```env
# API Configuration
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000/ws

# Environment
NODE_ENV=development
CHOKIDAR_USEPOLLING=true
```

### **Docker Configuration**
Modify `docker-compose.yml` for your environment:
```yaml
services:
  backend:
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/privik
      - REDIS_URL=redis://redis:6379
```

---

## 🔍 **Verification**

### **Check Service Status**
```bash
# Backend health check
curl http://localhost:8000/health

# Frontend check
curl http://localhost:3000

# API documentation
open http://localhost:8000/docs
```

### **Expected Output**
- Backend: JSON response with service status
- Frontend: React application loads
- API Docs: Interactive API documentation

---

## 🚨 **Troubleshooting**

### **Common Issues**

#### **Port Already in Use**
```bash
# Find process using port
netstat -tulpn | grep :8000  # Linux/macOS
netstat -ano | findstr :8000  # Windows

# Kill process
kill -9 <PID>  # Linux/macOS
taskkill /f /pid <PID>  # Windows
```

#### **Permission Denied (Linux/macOS)**
```bash
# Make scripts executable
chmod +x start-privik.sh
chmod +x stop-privik.sh
```

#### **Node.js Compilation Issues**
```bash
# Clear npm cache
npm cache clean --force

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

#### **Python Import Errors**
```bash
# Recreate virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### **Docker Issues**
```bash
# Clean Docker system
docker system prune -a

# Rebuild containers
docker-compose down
docker-compose up --build
```

### **Log Analysis**
```bash
# Backend logs
tail -f backend/logs/app.log

# Frontend logs
# Check browser console (F12)

# Docker logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

---

## 🔧 **Advanced Configuration**

### **Production Deployment**

#### **Environment Setup**
```env
NODE_ENV=production
DATABASE_URL=postgresql://user:pass@host:5432/privik
REDIS_URL=redis://redis-host:6379
JWT_SECRET=production-secret-key
```

#### **Security Configuration**
```env
# Enable HTTPS
SSL_CERT_PATH=/path/to/cert.pem
SSL_KEY_PATH=/path/to/key.pem

# Database encryption
DB_ENCRYPTION_KEY=production-db-key

# API rate limiting
RATE_LIMIT_REQUESTS=1000
RATE_LIMIT_WINDOW=3600
```

### **Performance Tuning**

#### **Database Optimization**
```python
# backend/app/core/config.py
DB_POOL_SIZE = 20
DB_MAX_OVERFLOW = 30
DB_POOL_RECYCLE = 3600
```

#### **Frontend Optimization**
```json
// frontend/package.json
{
  "scripts": {
    "build": "react-scripts build",
    "start": "react-scripts start"
  }
}
```

---

## 📊 **Monitoring Setup**

### **Health Monitoring**
```bash
# Add to crontab for regular health checks
*/5 * * * * curl -f http://localhost:8000/health || echo "Backend down" | mail admin@company.com
```

### **Log Monitoring**
```bash
# Set up log rotation
sudo logrotate /etc/logrotate.d/privik
```

---

## 🔄 **Updates and Maintenance**

### **Updating the Platform**
```bash
# Pull latest changes
git pull origin main

# Update dependencies
cd backend && pip install -r requirements.txt
cd ../frontend && npm install

# Restart services
./stop-privik.sh
./start-privik.sh
```

### **Backup and Recovery**
```bash
# Backup database
pg_dump privik > backup_$(date +%Y%m%d).sql

# Backup configuration
tar -czf config_backup.tar.gz backend/.env frontend/.env
```

---

## 📞 **Support**

### **Getting Help**
1. **Check Documentation**: Review docs/ directory
2. **Check Logs**: Examine application logs
3. **Community Support**: GitHub issues and discussions
4. **Professional Support**: Contact support team

### **Reporting Issues**
When reporting issues, include:
- Operating system and version
- Installation method (Docker/Native)
- Error messages and logs
- Steps to reproduce
- Expected vs actual behavior

---

## 🎯 **Next Steps**

After successful installation:

1. **Access the Platform**: Visit http://localhost:3000
2. **Configure Settings**: Set up your email domains
3. **Test Features**: Try the email security features
4. **Read Documentation**: Explore the comprehensive docs/
5. **Set Up Monitoring**: Configure health checks and alerts

---

*This installation guide ensures successful deployment of the Privik Email Security Platform across all supported environments.*
