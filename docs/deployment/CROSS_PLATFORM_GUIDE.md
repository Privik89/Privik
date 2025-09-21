# Cross-Platform Deployment Guide

## 🌍 **Universal Deployment Solutions**

This guide provides multiple deployment options that work seamlessly across **Windows**, **Linux**, and **macOS** environments.

---

## 🐳 **Option 1: Docker Deployment (Recommended)**

### **Prerequisites**
- Docker Desktop installed
- Docker Compose installed
- 4GB+ RAM available
- 10GB+ free disk space

### **Quick Start**
```bash
# Clone the repository
git clone <repository-url>
cd Privik

# Start all services
docker-compose up --build

# Access the platform
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### **Service Management**
```bash
# Start services in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Restart specific service
docker-compose restart backend
```

### **Production Deployment**
```bash
# Use production profile
docker-compose --profile production up -d

# Scale services
docker-compose up --scale backend=3 -d
```

---

## 💻 **Option 2: Native Installation**

### **Windows Installation**

#### **Prerequisites**
- Node.js 18+ installed
- Python 3.11+ installed
- Git installed

#### **Setup Steps**
```powershell
# 1. Clone repository
git clone <repository-url>
cd Privik

# 2. Configure Git for cross-platform compatibility
git config core.autocrlf true

# 3. Setup backend
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 4. Setup frontend
cd ..\frontend
npm install

# 5. Start services using provided scripts
# Use start_both.bat or start_both.ps1
```

#### **Windows Startup Scripts**
- `start_both.bat` - Starts both services in separate windows
- `start_backend.bat` - Starts only backend service
- `start_frontend.bat` - Starts only frontend service
- `start_both.ps1` - PowerShell version with enhanced features

### **Linux/macOS Installation**

#### **Prerequisites**
- Node.js 18+ installed
- Python 3.11+ installed
- Git installed

#### **Setup Steps**
```bash
# 1. Clone repository
git clone <repository-url>
cd Privik

# 2. Setup backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Setup frontend
cd ../frontend
npm install

# 4. Start services
# Use start-privik.sh script
chmod +x start-privik.sh
./start-privik.sh
```

---

## 🔧 **Cross-Platform Configuration**

### **Environment Variables**

#### **Backend Configuration**
```bash
# Database
DATABASE_URL=sqlite:///./privik.db  # Development
# DATABASE_URL=postgresql://user:pass@localhost/privik  # Production

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# Security
JWT_SECRET=your-secret-key
ENCRYPTION_KEY=your-encryption-key

# Features
ENABLE_SANDBOX=true
ENABLE_ML_MODELS=true
ENABLE_SIEM_INTEGRATION=true

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

#### **Frontend Configuration**
```bash
# API Configuration
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000/ws

# Environment
NODE_ENV=development
CHOKIDAR_USEPOLLING=true  # For file watching in containers
```

### **Path Resolution**
The platform automatically handles path differences between operating systems:

- **Windows**: Uses backslashes (`\`) and drives (`C:\`)
- **Linux/macOS**: Uses forward slashes (`/`) and Unix paths
- **Docker**: Uses Unix-style paths regardless of host OS

---

## 🚀 **Universal Startup Scripts**

### **Cross-Platform Script Features**
- Automatic OS detection
- Dependency checking
- Service health monitoring
- Error handling and recovery
- Logging and status reporting

### **Script Usage**

#### **Windows**
```powershell
# PowerShell (Recommended)
.\start_both.ps1

# Command Prompt
start_both.bat
```

#### **Linux/macOS**
```bash
# Make executable and run
chmod +x start-privik.sh
./start-privik.sh
```

### **Script Features**
- ✅ **OS Detection**: Automatically detects Windows/Linux/macOS
- ✅ **Dependency Check**: Verifies Node.js, Python, and other requirements
- ✅ **Service Management**: Starts/stops services gracefully
- ✅ **Health Monitoring**: Checks service availability
- ✅ **Error Recovery**: Handles common issues automatically
- ✅ **Logging**: Provides detailed status information

---

## 🔍 **Troubleshooting Cross-Platform Issues**

### **Common Issues & Solutions**

#### **1. Path Separator Issues**
**Problem**: Windows uses `\` while Linux/macOS uses `/`
**Solution**: 
```bash
# Configure Git for cross-platform compatibility
git config core.autocrlf true  # Windows
git config core.autocrlf input # Linux/macOS
```

#### **2. Line Ending Issues**
**Problem**: CRLF vs LF line endings
**Solution**: Git configuration handles this automatically
```bash
# Check current setting
git config core.autocrlf

# Set for current repository
git config core.autocrlf true
```

#### **3. Node.js Compilation Issues**
**Problem**: Native modules fail to compile
**Solution**: Use Docker or ensure proper build tools
```bash
# Windows
npm install --global windows-build-tools

# Linux
sudo apt-get install build-essential

# macOS
xcode-select --install
```

#### **4. Python Environment Issues**
**Problem**: Virtual environment activation differs
**Solution**: Use platform-specific activation commands
```bash
# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

#### **5. Permission Issues**
**Problem**: File permissions differ between OS
**Solution**: 
```bash
# Linux/macOS - Make scripts executable
chmod +x *.sh

# Windows - Run PowerShell as Administrator if needed
```

### **Dependency Installation Issues**

#### **Backend Dependencies**
```bash
# Common issues and solutions
pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt

# For specific packages
pip install psycopg2-binary  # PostgreSQL
pip install redis           # Redis
pip install playwright      # Browser automation
playwright install          # Install browsers
```

#### **Frontend Dependencies**
```bash
# Clear cache and reinstall
npm cache clean --force
rm -rf node_modules package-lock.json
npm install

# For Node.js compatibility issues
export NODE_OPTIONS="--openssl-legacy-provider"  # Linux/macOS
set NODE_OPTIONS=--openssl-legacy-provider       # Windows
```

---

## 📊 **Performance Optimization**

### **Cross-Platform Performance Tips**

#### **1. Use Docker for Consistency**
- Eliminates environment differences
- Provides consistent performance
- Easier dependency management
- Better resource utilization

#### **2. Optimize for Each Platform**
```bash
# Windows
# Use Windows Defender exclusions for project directory
# Enable Windows Subsystem for Linux (WSL) for better performance

# Linux
# Use systemd for service management
# Optimize file system settings

# macOS
# Use Homebrew for package management
# Optimize Docker Desktop settings
```

#### **3. Resource Management**
```yaml
# Docker Compose resource limits
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
```

---

## 🔐 **Security Considerations**

### **Cross-Platform Security**

#### **1. File Permissions**
```bash
# Linux/macOS - Secure file permissions
chmod 600 .env
chmod 700 logs/
chmod 755 scripts/

# Windows - Use NTFS permissions
# Right-click folder > Properties > Security
```

#### **2. Environment Variables**
```bash
# Use .env files for sensitive data
# Never commit .env files to version control
# Use different .env files for different environments
```

#### **3. Network Security**
```bash
# Docker - Use custom networks
docker network create privik-network

# Native - Use firewall rules
# Windows: Windows Defender Firewall
# Linux: iptables or ufw
# macOS: Built-in firewall
```

---

## 📈 **Monitoring & Maintenance**

### **Cross-Platform Monitoring**

#### **1. Health Checks**
```bash
# Docker health checks
docker-compose ps

# Native service checks
curl http://localhost:8000/health
curl http://localhost:3000
```

#### **2. Log Management**
```bash
# Docker logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Native logs
tail -f backend/logs/app.log
tail -f frontend/logs/npm.log
```

#### **3. Backup & Recovery**
```bash
# Docker volumes backup
docker run --rm -v privik_backend_data:/data -v $(pwd):/backup alpine tar czf /backup/backend-backup.tar.gz -C /data .

# Native backup
tar -czf privik-backup.tar.gz backend/data/ backend/logs/
```

---

## 🎯 **Best Practices**

### **Development**
1. **Use Docker for Development**: Ensures consistency across team
2. **Version Control**: Use `.gitattributes` for cross-platform compatibility
3. **Environment Isolation**: Use virtual environments for Python
4. **Dependency Management**: Pin versions in requirements.txt and package.json

### **Production**
1. **Container Orchestration**: Use Kubernetes or Docker Swarm
2. **Load Balancing**: Implement proper load balancing
3. **Monitoring**: Use centralized logging and monitoring
4. **Security**: Implement proper security measures

### **Testing**
1. **Cross-Platform Testing**: Test on multiple operating systems
2. **Automated Testing**: Use CI/CD pipelines
3. **Performance Testing**: Test performance on different platforms
4. **Security Testing**: Regular security audits

---

## 📞 **Support**

### **Getting Help**
1. **Check Logs**: Always check application logs first
2. **Documentation**: Refer to comprehensive documentation
3. **Community**: Check GitHub issues and discussions
4. **Professional Support**: Contact support team for enterprise issues

### **Reporting Issues**
When reporting cross-platform issues, include:
- Operating system and version
- Node.js and Python versions
- Error messages and logs
- Steps to reproduce
- Expected vs actual behavior

---

*This guide ensures that the Privik Email Security Platform works seamlessly across all major operating systems and deployment scenarios.*
