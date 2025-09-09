#!/bin/bash

# Privik Zero-Trust Email Security Platform
# Cross-platform startup script (Linux/macOS)

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Function to check if a command exists
command_exists() { command -v "$1" >/dev/null 2>&1; }

# Function to cleanup on exit
cleanup() {
    print_status "Cleaning up processes..."
    pkill -f "uvicorn.*app.main:app" 2>/dev/null || true
    pkill -f "npm start" 2>/dev/null || true
    print_success "Cleanup completed"
}

# Set trap for cleanup
trap cleanup EXIT

main() {
    print_status "🚀 Starting Privik Zero-Trust Email Security Platform..."
    print_status "Platform: $(uname -s)"
    print_status "Working Directory: $(pwd)"
    
    # Check prerequisites
    print_status "Checking prerequisites..."
    
    if ! command_exists python3; then
        print_error "Python 3 is not installed. Please install Python 3.11+"
        exit 1
    fi
    
    if ! command_exists node; then
        print_error "Node.js is not installed. Please install Node.js 16+"
        exit 1
    fi
    
    print_success "All prerequisites are installed"
    
    # Check if we're in the right directory
    if [ ! -f "backend/app/main.py" ]; then
        print_error "Please run this script from the Privik project root directory"
        exit 1
    fi
    
    # Setup environment
    print_status "Setting up environment..."
    export ENVIRONMENT="development"
    export DEBUG="true"
    export PYTHONPATH="${PWD}/backend:${PYTHONPATH}"
    
    # Check and setup virtual environment
    if [ ! -d "venv" ]; then
        print_status "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    print_status "Activating virtual environment..."
    source venv/bin/activate
    
    # Install Python dependencies
    print_status "Installing Python dependencies..."
    pip install --upgrade pip
    pip install -r backend/requirements.txt
    pip install playwright scikit-learn joblib pandas numpy
    
    # Install Playwright browsers
    print_status "Installing Playwright browsers..."
    playwright install chromium
    
    # Create database tables
    print_status "Setting up database..."
    python -c "import sys; sys.path.append('backend'); from backend.app.database import create_tables; create_tables(); print('Database tables created')"
    
    # Start backend
    print_status "Starting backend server..."
    print_success "Backend will be available at: http://localhost:8000"
    print_success "API Documentation: http://localhost:8000/docs"
    print_success "Health Check: http://localhost:8000/health"
    print_status "Press Ctrl+C to stop the server"
    echo ""
    
    python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
}

# Run main function
main "$@"
