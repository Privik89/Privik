#!/bin/bash

echo "🚀 Starting Privik Email Security Platform (Full Stack)..."

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

# Check if we're in the right directory
if [ ! -f "README.md" ] || [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    print_error "Please run this script from the Privik project root directory"
    exit 1
fi

print_status "Privik project structure verified"

# Check prerequisites
print_status "Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.8+"
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js 16+"
    echo "Visit: https://nodejs.org/"
    exit 1
fi

# Check npm
if ! command -v npm &> /dev/null; then
    print_error "npm is not installed. Please install npm"
    exit 1
fi

print_success "All prerequisites met"
print_status "Python version: $(python3 --version)"
print_status "Node.js version: $(node --version)"
print_status "npm version: $(npm --version)"

# Function to start backend
start_backend() {
    print_status "Starting Privik Backend..."
    
    # Check if virtual environment exists
    if [ ! -d ".venv" ]; then
        print_warning "Virtual environment not found. Creating one..."
        python3 -m venv .venv
    fi
    
    # Activate virtual environment
    source .venv/bin/activate
    
    # Install backend dependencies
    if [ ! -d "backend/__pycache__" ]; then
        print_status "Installing backend dependencies..."
        pip install -r backend/requirements.txt
    fi
    
    # Set environment variables
    export ENVIRONMENT=development
    export DEBUG=true
    
    # Start backend server
    cd backend
    print_success "Backend starting on http://localhost:8000"
    print_status "API Documentation: http://localhost:8000/docs"
    
    # Start uvicorn in background
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
    BACKEND_PID=$!
    
    cd ..
    print_success "Backend started with PID: $BACKEND_PID"
}

# Function to start frontend
start_frontend() {
    print_status "Starting Privik Frontend..."
    
    cd frontend
    
    # Install frontend dependencies if needed
    if [ ! -d "node_modules" ]; then
        print_status "Installing frontend dependencies..."
        npm install
    fi
    
    # Start frontend server
    print_success "Frontend starting on http://localhost:3000"
    print_status "Backend API proxy: http://localhost:8000"
    
    # Start npm in background
    npm start &
    FRONTEND_PID=$!
    
    cd ..
    print_success "Frontend started with PID: $FRONTEND_PID"
}

# Function to cleanup on exit
cleanup() {
    print_status "Shutting down Privik services..."
    
    if [ ! -z "$BACKEND_PID" ]; then
        print_status "Stopping backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        print_status "Stopping frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID 2>/dev/null
    fi
    
    print_success "All services stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start services
start_backend

# Wait a moment for backend to start
sleep 3

start_frontend

print_success "🎉 Privik Email Security Platform is now running!"
echo ""
echo "📊 Dashboard: http://localhost:3000"
echo "🔧 API Docs:  http://localhost:8000/docs"
echo "🏥 Health:    http://localhost:8000/health"
echo ""
echo "⏹️  Press Ctrl+C to stop all services"
echo "----------------------------------------"

# Wait for user to stop
wait
