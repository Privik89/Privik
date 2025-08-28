#!/bin/bash

# Privik Endpoint Agent Installation Script
# Installs the agent on the current system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command_exists apt-get; then
            echo "debian"
        elif command_exists yum; then
            echo "rhel"
        elif command_exists pacman; then
            echo "arch"
        else
            echo "linux"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

# Function to install system dependencies
install_system_deps() {
    local os=$(detect_os)
    
    print_status "Installing system dependencies for $os..."
    
    case $os in
        "debian")
            sudo apt-get update
            sudo apt-get install -y python3 python3-pip python3-venv python3-dev \
                build-essential libssl-dev libffi-dev libmagic1
            ;;
        "rhel")
            sudo yum update -y
            sudo yum install -y python3 python3-pip python3-devel \
                gcc openssl-devel libffi-devel file-devel
            ;;
        "arch")
            sudo pacman -Syu --noconfirm
            sudo pacman -S --noconfirm python python-pip base-devel \
                openssl libffi file
            ;;
        "macos")
            if ! command_exists brew; then
                print_error "Homebrew is required for macOS installation"
                exit 1
            fi
            brew update
            brew install python openssl libffi libmagic
            ;;
        *)
            print_warning "Unknown OS, please install Python 3.8+ manually"
            ;;
    esac
    
    print_success "System dependencies installed"
}

# Function to create virtual environment
setup_virtual_env() {
    print_status "Setting up Python virtual environment..."
    
    if [ ! -d "agent_env" ]; then
        python3 -m venv agent_env
    fi
    
    source agent_env/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    print_success "Virtual environment created"
}

# Function to install Python dependencies
install_python_deps() {
    print_status "Installing Python dependencies..."
    
    source agent_env/bin/activate
    
    # Install dependencies
    pip install -r agent/requirements.txt
    
    print_success "Python dependencies installed"
}

# Function to create agent configuration
setup_agent_config() {
    print_status "Setting up agent configuration..."
    
    # Create config directory
    mkdir -p ~/.config/privik
    
    # Create default config if it doesn't exist
    if [ ! -f ~/.config/privik/agent_config.json ]; then
        cat > ~/.config/privik/agent_config.json << EOF
{
  "agent_id": "$(uuidgen)",
  "agent_name": "privik-agent-$(hostname)",
  "version": "1.0.0",
  "server_url": "http://localhost:8000",
  "server_api_key": "",
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
EOF
        print_success "Default configuration created"
    else
        print_warning "Configuration already exists, skipping"
    fi
}

# Function to create systemd service (Linux)
create_systemd_service() {
    if [[ "$(detect_os)" == "linux"* ]]; then
        print_status "Creating systemd service..."
        
        sudo tee /etc/systemd/system/privik-agent.service > /dev/null << EOF
[Unit]
Description=Privik Endpoint Agent
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/agent_env/bin
ExecStart=$(pwd)/agent_env/bin/python $(pwd)/agent/start_agent.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
        
        sudo systemctl daemon-reload
        print_success "Systemd service created"
    fi
}

# Function to create launchd service (macOS)
create_launchd_service() {
    if [[ "$(detect_os)" == "macos" ]]; then
        print_status "Creating launchd service..."
        
        mkdir -p ~/Library/LaunchAgents
        
        cat > ~/Library/LaunchAgents/com.privik.agent.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.privik.agent</string>
    <key>ProgramArguments</key>
    <array>
        <string>$(pwd)/agent_env/bin/python</string>
        <string>$(pwd)/agent/start_agent.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$(pwd)</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/privik-agent.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/privik-agent.error.log</string>
</dict>
</plist>
EOF
        
        print_success "Launchd service created"
    fi
}

# Function to create startup scripts
create_startup_scripts() {
    print_status "Creating startup scripts..."
    
    # Create start script
    cat > start_agent.sh << EOF
#!/bin/bash
# Start Privik Endpoint Agent

cd "$(dirname "\$0")"
source agent_env/bin/activate
python agent/start_agent.py "\$@"
EOF
    
    # Create stop script
    cat > stop_agent.sh << EOF
#!/bin/bash
# Stop Privik Endpoint Agent

pkill -f "privik.*agent"
echo "Agent stopped"
EOF
    
    # Make scripts executable
    chmod +x start_agent.sh stop_agent.sh
    
    print_success "Startup scripts created"
}

# Function to test installation
test_installation() {
    print_status "Testing installation..."
    
    source agent_env/bin/activate
    
    # Test Python imports
    python -c "
import sys
sys.path.insert(0, 'agent')
from agent import PrivikAgent
print('✅ Agent module imported successfully')
"
    
    print_success "Installation test passed"
}

# Function to display next steps
show_next_steps() {
    echo ""
    print_success "🎉 Privik Endpoint Agent installed successfully!"
    echo ""
    echo -e "${GREEN}Next Steps:${NC}"
    echo "1. Configure the agent:"
    echo "   nano ~/.config/privik/agent_config.json"
    echo ""
    echo "2. Start the agent:"
    echo "   ./start_agent.sh"
    echo ""
    echo "3. For automatic startup:"
    if [[ "$(detect_os)" == "linux"* ]]; then
        echo "   sudo systemctl enable privik-agent"
        echo "   sudo systemctl start privik-agent"
    elif [[ "$(detect_os)" == "macos" ]]; then
        echo "   launchctl load ~/Library/LaunchAgents/com.privik.agent.plist"
    fi
    echo ""
    echo -e "${YELLOW}Configuration:${NC}"
    echo "   Server URL: http://localhost:8000 (default)"
    echo "   Log Level: INFO (default)"
    echo "   Email Scan Interval: 30 seconds (default)"
    echo ""
    echo -e "${BLUE}Documentation:${NC}"
    echo "   Configuration: ~/.config/privik/agent_config.json"
    echo "   Logs: Check console output or system logs"
    echo ""
}

# Main installation function
main() {
    echo "🛡️  Privik Endpoint Agent Installation"
    echo "======================================"
    echo ""
    
    # Check if running as root
    if [[ $EUID -eq 0 ]]; then
        print_error "Do not run this script as root"
        exit 1
    fi
    
    # Check prerequisites
    if ! command_exists python3; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi
    
    # Install system dependencies
    install_system_deps
    
    # Setup virtual environment
    setup_virtual_env
    
    # Install Python dependencies
    install_python_deps
    
    # Setup agent configuration
    setup_agent_config
    
    # Create startup scripts
    create_startup_scripts
    
    # Create system service
    if [[ "$(detect_os)" == "linux"* ]]; then
        create_systemd_service
    elif [[ "$(detect_os)" == "macos" ]]; then
        create_launchd_service
    fi
    
    # Test installation
    test_installation
    
    # Show next steps
    show_next_steps
}

# Run main function
main "$@"
