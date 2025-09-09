#!/bin/bash

# Privik Linux Setup Script
# Installs all dependencies and sets up the system

set -e

echo "🚀 Privik Linux Setup Script"
echo "=============================="

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "❌ This script is designed for Linux systems"
    exit 1
fi

# Check Python version
echo "🔍 Checking Python version..."
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then
    echo "✅ Python $python_version is compatible"
else
    echo "❌ Python $python_version is not compatible. Required: $required_version or higher"
    exit 1
fi

# Install system dependencies
echo "📦 Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    libssl-dev \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    libjpeg-dev \
    libpng-dev \
    curl \
    wget \
    git

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r backend/requirements.txt

# Install additional dependencies for new features
echo "📦 Installing additional dependencies..."
pip install \
    playwright \
    scikit-learn \
    joblib \
    pandas \
    numpy \
    aiohttp \
    structlog \
    fastapi \
    uvicorn \
    sqlalchemy \
    psycopg2-binary \
    redis \
    requests

# Install Playwright browsers
echo "🌐 Installing Playwright browsers..."
playwright install chromium
playwright install-deps chromium

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p models
mkdir -p /tmp/attachments
mkdir -p /tmp/sandbox
mkdir -p logs

# Set permissions
echo "🔐 Setting permissions..."
chmod 755 models
chmod 755 /tmp/attachments
chmod 755 /tmp/sandbox
chmod 755 logs

# Create environment file if it doesn't exist
if [ ! -f "backend/.env" ]; then
    echo "📝 Creating environment file..."
    cat > backend/.env << EOF
# App Settings
APP_NAME=Privik Email Security API
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=your-secret-key-here-$(openssl rand -hex 32)

# Database
DATABASE_URL=sqlite:///./privik.db

# Object Storage (S3-compatible)
S3_ENDPOINT_URL=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET_NAME=privik-artifacts

# AI/ML Services
OPENAI_API_KEY=your-openai-api-key
VIRUSTOTAL_API_KEY=your-virustotal-api-key

# Security Settings
SANDBOX_TIMEOUT=30
MAX_FILE_SIZE=50MB
ALLOWED_FILE_TYPES=.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.zip,.rar,.7z

# Zero-Trust Configuration
ZERO_TRUST_ENFORCEMENT_LEVEL=strict
ZERO_TRUST_INTERNAL_DOMAINS=company.com,internal.com
ZERO_TRUST_HIGH_RISK_USERS=ceo@company.com,cfo@company.com

# Sandbox Configuration
SANDBOX_MAX_CONCURRENT=10
SANDBOX_TIMEOUT=300
SANDBOX_STORAGE_PATH=/tmp/sandbox

# AI Model Configuration
AI_MODEL_STORAGE_PATH=./models
AI_RETRAIN_INTERVAL=7
AI_MIN_TRAINING_SAMPLES=1000

# Link Rewriting
LINK_REWRITE_DOMAIN=links.privik.com
ATTACHMENT_STORAGE_PATH=/tmp/attachments
EOF
    echo "✅ Environment file created"
else
    echo "✅ Environment file already exists"
fi

# Initialize AI models
echo "🧠 Initializing AI models..."
cd backend
python -c "
import asyncio
import sys
sys.path.append('.')
from app.services.ai_threat_detection import AIThreatDetection

async def init_models():
    config = {
        'model_storage_path': '../models',
        'retrain_interval': 7,
        'min_training_samples': 1000
    }
    
    ai_detection = AIThreatDetection(config)
    await ai_detection.initialize()
    print('AI models initialized successfully')
    await ai_detection.cleanup()

asyncio.run(init_models())
"
cd ..

# Test the installation
echo "🧪 Testing installation..."
python test_system.py

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Start the backend: cd backend && python -m uvicorn app.main:app --reload"
echo "3. Start the frontend: cd frontend && npm start"
echo "4. Access the system: http://localhost:3000"
echo ""
echo "For production deployment, see IMPLEMENTATION_GUIDE.md"
