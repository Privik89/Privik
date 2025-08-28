# Privik Endpoint Agent

🛡️ **AI-powered, zero-trust email security for real-time phishing protection**

The Privik Endpoint Agent is a cross-platform security agent that provides real-time protection against email-based threats, malicious files, and suspicious links. It works in conjunction with the Privik server to deliver comprehensive endpoint security.

## 🚀 Features

### **Email Security**
- **Real-time Email Monitoring**: Scans emails from Thunderbird, Outlook, and Apple Mail
- **Threat Detection**: Identifies phishing, BEC, and fraud attempts
- **Attachment Analysis**: Detects malicious files and executables
- **Link Analysis**: Analyzes URLs for phishing and malware

### **File System Protection**
- **File Monitoring**: Watches for suspicious file creation and modification
- **Threat Analysis**: Analyzes files for malware indicators
- **Real-time Alerts**: Immediate notification of threats

### **Link Protection**
- **URL Analysis**: Comprehensive threat analysis of links
- **Safe Browsing**: Integration with threat intelligence
- **Link Rewriting**: Secure proxy for suspicious links

### **Security Features**
- **Encrypted Communication**: AES-256-GCM encryption with RSA signatures
- **JWT Authentication**: Secure API communication
- **Certificate Validation**: Server certificate verification
- **Cross-platform**: Windows, macOS, and Linux support

## 📋 Requirements

### **System Requirements**
- **Python**: 3.8 or higher
- **OS**: Windows 10+, macOS 10.14+, or Linux (Ubuntu 18.04+, CentOS 7+)
- **Memory**: 512MB RAM minimum, 1GB recommended
- **Storage**: 100MB free space
- **Network**: Internet connection for server communication

### **Dependencies**
- **Python packages**: See `requirements.txt`
- **System libraries**: 
  - Linux: `libmagic`, `libssl`, `libffi`
  - macOS: `libmagic` (via Homebrew)
  - Windows: Included with Python packages

## 🛠️ Installation

### **Quick Install (Linux/macOS)**

```bash
# Clone the repository
git clone <repository-url>
cd Privik

# Run the installation script
./install_agent.sh
```

### **Manual Installation**

1. **Install system dependencies**:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install python3 python3-pip python3-venv python3-dev \
       build-essential libssl-dev libffi-dev libmagic1
   
   # CentOS/RHEL
   sudo yum install python3 python3-pip python3-devel \
       gcc openssl-devel libffi-devel file-devel
   
   # macOS
   brew install python openssl libffi libmagic
   ```

2. **Create virtual environment**:
   ```bash
   python3 -m venv agent_env
   source agent_env/bin/activate
   pip install --upgrade pip
   ```

3. **Install Python dependencies**:
   ```bash
   pip install -r agent/requirements.txt
   ```

4. **Configure the agent**:
   ```bash
   mkdir -p ~/.config/privik
   # Edit ~/.config/privik/agent_config.json
   ```

## ⚙️ Configuration

### **Configuration File**

The agent configuration is stored in `~/.config/privik/agent_config.json`:

```json
{
  "agent_id": "unique-agent-id",
  "agent_name": "privik-agent-hostname",
  "version": "1.0.0",
  "server_url": "http://localhost:8000",
  "server_api_key": "your-api-key",
  "encryption_enabled": true,
  "certificate_verification": true,
  "email_scan_interval": 30,
  "attachment_scan_enabled": true,
  "browser_monitoring": true,
  "link_rewrite_enabled": true,
  "safe_browsing_enabled": true,
  "file_scan_enabled": true,
  "max_file_size": 52428800,
  "log_level": "INFO",
  "max_concurrent_scans": 5,
  "cache_size": 1000,
  "cache_ttl": 3600
}
```

### **Environment Variables**

You can also configure the agent using environment variables:

```bash
export PRIVIK_SERVER_URL="http://your-server:8000"
export PRIVIK_API_KEY="your-api-key"
export PRIVIK_JWT_SECRET="your-jwt-secret"
export PRIVIK_LOG_LEVEL="INFO"
```

## 🚀 Usage

### **Starting the Agent**

```bash
# Using the startup script
./start_agent.sh

# Direct execution
source agent_env/bin/activate
python agent/start_agent.py

# With custom configuration
python agent/start_agent.py --config /path/to/config.json
```

### **Command Line Options**

```bash
python agent/start_agent.py [OPTIONS]

Options:
  --config PATH     Path to configuration file
  --log-level LEVEL Logging level (DEBUG, INFO, WARNING, ERROR)
  --log-file PATH   Log file path
  --daemon          Run as daemon
  --version         Show version and exit
  --help            Show help message
```

### **System Service**

#### **Linux (systemd)**
```bash
# Enable and start the service
sudo systemctl enable privik-agent
sudo systemctl start privik-agent

# Check status
sudo systemctl status privik-agent

# View logs
sudo journalctl -u privik-agent -f
```

#### **macOS (launchd)**
```bash
# Load the service
launchctl load ~/Library/LaunchAgents/com.privik.agent.plist

# Check status
launchctl list | grep privik

# Unload the service
launchctl unload ~/Library/LaunchAgents/com.privik.agent.plist
```

## 📊 Monitoring

### **Agent Status**

The agent provides real-time status information:

```bash
# Check agent status
curl http://localhost:8000/api/agent/status

# View agent logs
tail -f /tmp/privik-agent.log
```

### **Dashboard Integration**

The agent integrates with the Privik SOC dashboard to provide:

- **Real-time alerts**: Immediate threat notifications
- **Agent status**: Health and performance metrics
- **Threat analytics**: Detailed threat analysis
- **User risk profiles**: Behavioral analysis

## 🔧 Troubleshooting

### **Common Issues**

#### **Connection Failed**
```bash
# Check server connectivity
curl http://your-server:8000/health

# Verify configuration
cat ~/.config/privik/agent_config.json
```

#### **Permission Errors**
```bash
# Fix file permissions
chmod 600 ~/.config/privik/agent_config.json
chmod 600 ~/.config/privik/agent_private_key.pem
```

#### **Dependency Issues**
```bash
# Reinstall dependencies
source agent_env/bin/activate
pip install --force-reinstall -r agent/requirements.txt
```

### **Log Analysis**

The agent uses structured logging. Common log levels:

- **DEBUG**: Detailed debugging information
- **INFO**: General operational messages
- **WARNING**: Potential issues
- **ERROR**: Error conditions

### **Performance Tuning**

For high-traffic environments:

```json
{
  "max_concurrent_scans": 10,
  "email_scan_interval": 15,
  "cache_size": 2000,
  "max_file_size": 104857600
}
```

## 🔒 Security

### **Encryption**

- **Communication**: AES-256-GCM encryption
- **Authentication**: JWT tokens with HMAC-SHA256
- **Signatures**: RSA-PSS with SHA-256
- **Certificates**: X.509 certificate validation

### **Privacy**

- **Local Processing**: Sensitive data processed locally
- **Minimal Data**: Only threat indicators sent to server
- **Configurable**: Full control over data sharing

### **Compliance**

- **GDPR**: Configurable data retention
- **SOC 2**: Audit logging and monitoring
- **HIPAA**: Encrypted data transmission

## 🤝 Support

### **Documentation**

- **User Guide**: This README
- **API Documentation**: Server API docs
- **Configuration**: Configuration examples

### **Community**

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Security**: Security advisories

### **Enterprise Support**

For enterprise customers:
- **Priority Support**: 24/7 support
- **Custom Integration**: API customization
- **Training**: Staff training and workshops

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **FastAPI**: Modern web framework
- **SQLAlchemy**: Database ORM
- **Cryptography**: Security primitives
- **Watchdog**: File system monitoring
- **Structlog**: Structured logging

---

**🛡️ Protect your endpoints with Privik - AI-powered, zero-trust email security**
