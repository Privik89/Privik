# Privik Cross-Platform Setup Guide

## 🖥️ **Supported Operating Systems**

- ✅ **Linux** (Ubuntu, Debian, CentOS, RHEL)
- ✅ **Windows** (Windows 10/11, Windows Server 2019+)
- ✅ **macOS** (macOS 10.15+)

## 🚀 **Quick Start**

### **Linux/macOS**
```bash
# 1. Setup (one-time)
./setup_linux.sh

# 2. Start the platform
./start_privik.sh
```

### **Windows**
```cmd
# 1. Setup (one-time)
setup_windows.bat

# 2. Start the platform
start_privik_windows.bat
```

## 📋 **Prerequisites**

### **All Platforms**
- **Python 3.11+** (required for AI/ML features)
- **Node.js 16+** (for frontend development)
- **Git** (for version control)

### **Linux/macOS**
- **bash** shell
- **curl** (for health checks)

### **Windows**
- **PowerShell 5.1+** or **Command Prompt**
- **Windows Subsystem for Linux (WSL)** (optional, for Linux compatibility)

## 🔧 **Installation Steps**

### **Linux/macOS Installation**

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-org/privik.git
   cd privik
   ```

2. **Run the setup script:**
   ```bash
   chmod +x setup_linux.sh
   ./setup_linux.sh
   ```

3. **Start the platform:**
   ```bash
   ./start_privik.sh
   ```

### **Windows Installation**

1. **Clone the repository:**
   ```cmd
   git clone https://github.com/your-org/privik.git
   cd privik
   ```

2. **Run the setup script:**
   ```cmd
   setup_windows.bat
   ```

3. **Start the platform:**
   ```cmd
   start_privik_windows.bat
   ```

## 🧪 **Testing**

### **Linux/macOS**
```bash
# Run comprehensive system test
./venv/bin/python test_system.py
```

### **Windows**
```cmd
# Run comprehensive system test
test_system_windows.bat
```

## 🌐 **Access Points**

Once started, the platform will be available at:

- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🔍 **Platform-Specific Features**

### **Linux/macOS**
- **Process Simulation**: Uses `bash`, `sh`, `python`
- **File Permissions**: Unix-style permissions
- **Background Services**: Uses `nohup` and process management

### **Windows**
- **Process Simulation**: Uses `cmd.exe`, `powershell.exe`, `python.exe`
- **File Permissions**: Windows ACL permissions
- **Background Services**: Uses Windows service management

## 🐛 **Troubleshooting**

### **Common Issues**

#### **Python Virtual Environment Issues**
```bash
# Linux/macOS
rm -rf venv
python3 -m venv venv
source venv/bin/activate

# Windows
rmdir /s venv
python -m venv venv
venv\Scripts\activate.bat
```

#### **Port Already in Use**
```bash
# Linux/macOS
sudo fuser -k 8000/tcp
sudo fuser -k 3000/tcp

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

#### **Playwright Browser Issues**
```bash
# Linux/macOS
./venv/bin/playwright install chromium

# Windows
venv\Scripts\playwright install chromium
```

### **Platform-Specific Issues**

#### **Linux**
- **Permission Denied**: Use `chmod +x` on shell scripts
- **Missing Dependencies**: Install with `apt-get install` or `yum install`

#### **Windows**
- **PowerShell Execution Policy**: Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
- **Long Path Names**: Enable long path support in Windows 10/11

#### **macOS**
- **Xcode Command Line Tools**: Install with `xcode-select --install`
- **Homebrew**: Install dependencies with `brew install`

## 📊 **Performance Considerations**

### **System Requirements**

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **CPU** | 2 cores | 4+ cores |
| **RAM** | 4GB | 8GB+ |
| **Storage** | 10GB | 50GB+ |
| **Network** | 100Mbps | 1Gbps+ |

### **Platform-Specific Optimizations**

#### **Linux**
- Use `systemd` for service management
- Configure `ulimit` for file descriptors
- Use `nginx` for reverse proxy

#### **Windows**
- Use Windows Service for background operation
- Configure Windows Firewall
- Use IIS for reverse proxy

#### **macOS**
- Use `launchd` for service management
- Configure macOS Firewall
- Use Apache for reverse proxy

## 🔒 **Security Considerations**

### **All Platforms**
- **HTTPS**: Use SSL/TLS certificates in production
- **Firewall**: Configure appropriate firewall rules
- **Updates**: Keep all dependencies updated
- **Monitoring**: Implement logging and monitoring

### **Platform-Specific Security**

#### **Linux**
- **SELinux/AppArmor**: Configure mandatory access controls
- **User Permissions**: Run as non-root user
- **File Permissions**: Use proper file ownership

#### **Windows**
- **Windows Defender**: Configure antivirus exclusions
- **User Account Control**: Use appropriate UAC settings
- **Windows Firewall**: Configure inbound/outbound rules

#### **macOS**
- **Gatekeeper**: Configure application security
- **FileVault**: Enable disk encryption
- **Firewall**: Configure macOS firewall

## 📞 **Support**

For platform-specific issues:

- **Linux**: Check system logs in `/var/log/`
- **Windows**: Check Event Viewer and Windows logs
- **macOS**: Check Console.app and system logs

## 🚀 **Production Deployment**

### **Docker (Cross-Platform)**
```bash
# Build and run with Docker
docker-compose up -d
```

### **Kubernetes (Cross-Platform)**
```bash
# Deploy to Kubernetes
kubectl apply -f k8s/
```

### **Cloud Platforms**
- **AWS**: Use EC2, ECS, or EKS
- **Azure**: Use Virtual Machines, Container Instances, or AKS
- **GCP**: Use Compute Engine, Cloud Run, or GKE

---

**Need help?** Check our [troubleshooting guide](TROUBLESHOOTING.md) or [contact support](mailto:support@privik.com).
