#!/bin/bash

echo "🚀 Starting Privik Email Security Platform on Linux..."

# Set environment variables
export ENVIRONMENT=development
export DEBUG=true

echo "✅ Environment: $ENVIRONMENT"
echo "✅ Debug mode: $DEBUG"

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Change to backend directory
cd backend

echo "✅ Working directory: $(pwd)"

# Start the server
echo "🌐 Starting FastAPI server..."
echo "📖 API Documentation: http://localhost:8000/docs"
echo "🔍 Health check: http://localhost:8000/health"
echo "⏹️  Press Ctrl+C to stop"
echo "----------------------------------------"

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
