# Privik Troubleshooting Guide

## 🚨 **Common Issues and Solutions**

### **Backend Issues**

#### **Backend Won't Start**
**Symptoms:**
- Server fails to start
- IndentationError or syntax errors
- Import errors

**Solutions:**
```bash
# Check Python version
python3 --version  # Should be 3.11+

# Recreate virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# Check for syntax errors
./venv/bin/python -m py_compile backend/app/services/sandbox.py
```

#### **Database Issues**
**Symptoms:**
- "no such table" errors
- Database connection failures

**Solutions:**
```bash
# Create database tables
./venv/bin/python -c "
import sys
sys.path.append('backend')
from backend.app.database import create_tables
create_tables()
print('Database tables created')
"

# Check database file
ls -la backend/privik.db
```

#### **API Endpoints Not Working**
**Symptoms:**
- 404 errors on API calls
- CORS errors
- Timeout errors

**Solutions:**
```bash
# Check server status
curl http://localhost:8000/health

# Check API documentation
curl http://localhost:8000/docs

# Restart server
pkill -f uvicorn
./venv/bin/python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### **Frontend Issues**

#### **Frontend Won't Start**
**Symptoms:**
- "react-scripts: not found" error
- "Cannot find module" errors
- npm start fails

**Solutions:**
```bash
# Install dependencies
cd frontend
npm install

# Install react-scripts specifically
npm install react-scripts

# Start manually
npm start
```

#### **Missing Files**
**Symptoms:**
- "Could not find a required file" error
- Missing index.html or manifest.json

**Solutions:**
```bash
# Create missing files
mkdir -p frontend/public
# Files should be created automatically by setup scripts
```

#### **Proxy Errors**
**Symptoms:**
- "Proxy error: Could not proxy request"
- ECONNREFUSED errors

**Solutions:**
```bash
# Ensure backend is running
curl http://localhost:8000/health

# Check proxy configuration in package.json
cat frontend/package.json | grep proxy
```

### **Cross-Platform Issues**

#### **Windows Compatibility**
**Symptoms:**
- PowerShell errors
- "source: not recognized" errors
- Path issues

**Solutions:**
```cmd
# Use Windows batch files
setup_windows.bat
start_privik_windows.bat

# Use Command Prompt instead of PowerShell
cmd /c "setup_windows.bat"
```

#### **Linux Permission Issues**
**Symptoms:**
- "Permission denied" errors
- Cannot execute scripts

**Solutions:**
```bash
# Make scripts executable
chmod +x setup_linux.sh
chmod +x start_privik.sh

# Run with proper permissions
sudo chown -R $USER:$USER .
```

#### **macOS Issues**
**Symptoms:**
- Xcode command line tools missing
- Homebrew issues

**Solutions:**
```bash
# Install Xcode command line tools
xcode-select --install

# Install dependencies with Homebrew
brew install python3 node
```

### **Performance Issues**

#### **Slow Response Times**
**Symptoms:**
- API calls taking >5 seconds
- Frontend loading slowly
- High CPU usage

**Solutions:**
```bash
# Check system resources
htop
free -h
df -h

# Optimize Python
export PYTHONOPTIMIZE=1
export PYTHONDONTWRITEBYTECODE=1

# Clear caches
rm -rf __pycache__
rm -rf frontend/node_modules/.cache
```

#### **Memory Issues**
**Symptoms:**
- Out of memory errors
- System becomes unresponsive
- Process killed

**Solutions:**
```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head

# Increase swap space
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### **Database Performance**
**Symptoms:**
- Slow database queries
- Database locks
- High I/O usage

**Solutions:**
```bash
# Check database size
ls -lh backend/privik.db

# Optimize database
sqlite3 backend/privik.db "VACUUM;"

# Check for locks
lsof backend/privik.db
```

### **Network Issues**

#### **Port Already in Use**
**Symptoms:**
- "Address already in use" errors
- Cannot bind to port 8000 or 3000

**Solutions:**
```bash
# Find processes using ports
sudo netstat -tulpn | grep :8000
sudo netstat -tulpn | grep :3000

# Kill processes
sudo fuser -k 8000/tcp
sudo fuser -k 3000/tcp

# Use different ports
./venv/bin/python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8001 --reload
```

#### **Firewall Issues**
**Symptoms:**
- Cannot access from other machines
- Connection refused errors

**Solutions:**
```bash
# Check firewall status
sudo ufw status

# Allow ports
sudo ufw allow 8000
sudo ufw allow 3000

# Check iptables
sudo iptables -L
```

### **AI/ML Issues**

#### **Model Training Failures**
**Symptoms:**
- "No existing models found" errors
- Model accuracy issues
- Training timeouts

**Solutions:**
```bash
# Check model files
ls -la backend/models/

# Retrain models
./venv/bin/python -c "
from backend.app.services.ai_threat_detection import AITreatDetection
ai = AITreatDetection()
ai.train_initial_models()
"

# Check dependencies
pip list | grep -E "(scikit-learn|pandas|numpy)"
```

#### **Playwright Issues**
**Symptoms:**
- Browser automation failures
- "Browser not found" errors

**Solutions:**
```bash
# Install Playwright browsers
./venv/bin/playwright install chromium

# Check browser installation
./venv/bin/playwright --version

# Test browser
./venv/bin/python -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch()
    print('Browser working')
    browser.close()
"
```

### **Dependency Issues**

#### **Python Package Issues**
**Symptoms:**
- Import errors
- Version conflicts
- Missing packages

**Solutions:**
```bash
# Check Python version
python3 --version

# Reinstall packages
pip uninstall -r backend/requirements.txt -y
pip install -r backend/requirements.txt

# Check for conflicts
pip check
```

#### **Node.js Package Issues**
**Symptoms:**
- npm install failures
- Version conflicts
- Missing packages

**Solutions:**
```bash
# Check Node.js version
node --version
npm --version

# Clear npm cache
npm cache clean --force

# Reinstall packages
rm -rf frontend/node_modules
cd frontend
npm install
```

### **Configuration Issues**

#### **Environment Variables**
**Symptoms:**
- Configuration not loading
- Default values being used
- Environment-specific issues

**Solutions:**
```bash
# Check environment variables
env | grep -E "(ENVIRONMENT|DEBUG|DATABASE)"

# Set environment variables
export ENVIRONMENT=development
export DEBUG=true
export PYTHONPATH="${PWD}/backend:${PYTHONPATH}"
```

#### **File Permissions**
**Symptoms:**
- Cannot read/write files
- Permission denied errors
- File ownership issues

**Solutions:**
```bash
# Check file permissions
ls -la backend/
ls -la frontend/

# Fix permissions
chmod -R 755 backend/
chmod -R 755 frontend/
chown -R $USER:$USER .
```

### **Logging and Debugging**

#### **Enable Debug Logging**
```bash
# Set debug environment
export DEBUG=true
export LOG_LEVEL=DEBUG

# Check logs
tail -f backend.log
tail -f frontend.log
```

#### **Check System Logs**
```bash
# Check system logs
sudo journalctl -u privik
sudo tail -f /var/log/syslog

# Check application logs
tail -f backend/uvicorn.log
```

### **Recovery Procedures**

#### **Complete System Reset**
```bash
# Stop all processes
pkill -f uvicorn
pkill -f npm
pkill -f node

# Clean up
rm -rf venv
rm -rf frontend/node_modules
rm -f backend/privik.db

# Reinstall
./setup_linux.sh
```

#### **Database Recovery**
```bash
# Backup database
cp backend/privik.db backend/privik.db.backup

# Recreate database
rm -f backend/privik.db
./venv/bin/python -c "
import sys
sys.path.append('backend')
from backend.app.database import create_tables
create_tables()
"
```

#### **Configuration Recovery**
```bash
# Reset configuration
cp backend/app/core/config.py.backup backend/app/core/config.py

# Reset environment
unset ENVIRONMENT
unset DEBUG
unset DATABASE_URL
```

### **Getting Help**

#### **Collect Debug Information**
```bash
# System information
uname -a
python3 --version
node --version
npm --version

# Process information
ps aux | grep -E "(uvicorn|npm|node)"

# Network information
netstat -tulpn | grep -E "(8000|3000)"

# Disk usage
df -h
du -sh backend/ frontend/
```

#### **Contact Support**
- **Documentation**: Check [USER_GUIDE.md](USER_GUIDE.md)
- **Changelog**: Check [CHANGELOG.md](CHANGELOG.md)
- **Issues**: Create GitHub issue with debug information
- **Email**: support@privik.com

---

## 📋 **Quick Reference**

### **Common Commands**
```bash
# Start backend
./venv/bin/python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

# Start frontend
cd frontend && npm start

# Test API
curl http://localhost:8000/health

# Check processes
ps aux | grep -E "(uvicorn|npm|node)"

# Kill processes
pkill -f uvicorn
pkill -f npm
```

### **Useful URLs**
- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### **Important Files**
- **Backend Config**: `backend/app/core/config.py`
- **Database**: `backend/privik.db`
- **Frontend Config**: `frontend/package.json`
- **Setup Scripts**: `setup_linux.sh`, `setup_windows.bat`

---

**Last Updated**: September 10, 2025  
**Version**: 1.0.0  
**Compatibility**: Python 3.11+, Node.js 16+, Linux/Windows/macOS
