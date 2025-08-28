#!/bin/bash

# Privik Email Security Platform - Linux Startup Script
# This script handles all startup issues and provides a robust solution

set -e  # Exit on any error

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

# Function to check if a port is in use
port_in_use() {
    netstat -tuln 2>/dev/null | grep -q ":$1 "
}

# Function to kill processes on a port
kill_port() {
    if port_in_use $1; then
        print_warning "Port $1 is in use. Killing existing process..."
        sudo fuser -k $1/tcp 2>/dev/null || true
        sleep 2
    fi
}

# Function to cleanup on exit
cleanup() {
    print_status "Cleaning up processes..."
    pkill -f "uvicorn.*app.main:app" 2>/dev/null || true
    pkill -f "npm start" 2>/dev/null || true
    pkill -f "node.*react-scripts" 2>/dev/null || true
    print_success "Cleanup completed"
}

# Set trap for cleanup
trap cleanup EXIT

# Main startup function
main() {
    print_status "Starting Privik Email Security Platform..."
    print_status "Platform: Linux"
    print_status "Working Directory: $(pwd)"
    
    # Check prerequisites
    print_status "Checking prerequisites..."
    
    if ! command_exists python3; then
        print_error "Python 3 is not installed. Please install Python 3.8+"
        exit 1
    fi
    
    if ! command_exists node; then
        print_error "Node.js is not installed. Please install Node.js 16+"
        exit 1
    fi
    
    if ! command_exists npm; then
        print_error "npm is not installed. Please install npm"
        exit 1
    fi
    
    print_success "All prerequisites are installed"
    
    # Check if we're in the right directory
    if [ ! -f "backend/app/main.py" ] || [ ! -f "frontend/package.json" ]; then
        print_error "Please run this script from the Privik project root directory"
        exit 1
    fi
    
    # Kill any existing processes
    print_status "Cleaning up any existing processes..."
    kill_port 8000
    kill_port 3000
    
    # Setup environment
    print_status "Setting up environment..."
    export ENVIRONMENT="development"
    export DEBUG="true"
    export PYTHONPATH="${PWD}/backend:${PYTHONPATH}"
    
    # Check and setup virtual environment
    if [ ! -d ".venv" ]; then
        print_status "Creating virtual environment..."
        python3 -m venv .venv
    fi
    
    # Activate virtual environment
    print_status "Activating virtual environment..."
    source .venv/bin/activate
    
    # Install Python dependencies
    print_status "Installing Python dependencies..."
    pip install --upgrade pip
    pip install -r backend/requirements.txt
    
    # Install Node.js dependencies
    print_status "Installing Node.js dependencies..."
    cd frontend
    npm install
    cd ..
    
    # Create SQLite database directory
    print_status "Setting up database..."
    mkdir -p backend
    touch backend/privik.db
    
    # Start backend
    print_status "Starting backend server..."
    cd backend
    nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > ../backend.log 2>&1 &
    BACKEND_PID=$!
    cd ..
    
    # Wait for backend to start
    print_status "Waiting for backend to start..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/health >/dev/null 2>&1; then
            print_success "Backend is running on http://localhost:8000"
            break
        fi
        if [ $i -eq 30 ]; then
            print_error "Backend failed to start. Check backend.log for details"
            exit 1
        fi
        sleep 1
    done
    
    # Start frontend
    print_status "Starting frontend server..."
    cd frontend
    nohup npm start > ../frontend.log 2>&1 &
    FRONTEND_PID=$!
    cd ..
    
    # Wait for frontend to start
    print_status "Waiting for frontend to start..."
    for i in {1..60}; do
        if curl -s http://localhost:3000 >/dev/null 2>&1; then
            print_success "Frontend is running on http://localhost:3000"
            break
        fi
        if [ $i -eq 60 ]; then
            print_error "Frontend failed to start. Check frontend.log for details"
            exit 1
        fi
        sleep 1
    done
    
    # Final status
    echo ""
    print_success "🎉 Privik Email Security Platform is now running!"
    echo ""
    echo -e "${GREEN}Frontend:${NC} http://localhost:3000"
    echo -e "${GREEN}Backend API:${NC} http://localhost:8000"
    echo -e "${GREEN}API Docs:${NC} http://localhost:8000/docs"
    echo ""
    echo -e "${YELLOW}Logs:${NC}"
    echo -e "  Backend: tail -f backend.log"
    echo -e "  Frontend: tail -f frontend.log"
    echo ""
    echo -e "${YELLOW}To stop the platform:${NC} Press Ctrl+C"
    echo ""
    
    # Keep the script running and monitor processes
    while true; do
        if ! kill -0 $BACKEND_PID 2>/dev/null; then
            print_error "Backend process died unexpectedly"
            exit 1
        fi
        if ! kill -0 $FRONTEND_PID 2>/dev/null; then
            print_error "Frontend process died unexpectedly"
            exit 1
        fi
        sleep 5
    done
}

# Run main function
main "$@"
