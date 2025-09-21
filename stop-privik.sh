#!/bin/bash

# Privik Universal Stop Script (Linux/macOS)
set -e

echo "🛑 Stopping Privik Email Security Platform..."

# Check if Docker is available
if command -v docker &> /dev/null; then
    echo "🐳 Stopping Docker containers..."
    docker-compose down
    echo "✅ Docker containers stopped"
fi

# Stop any native processes
echo "🔄 Stopping native processes..."

# Kill backend processes
if pgrep -f "uvicorn app.main:app" > /dev/null; then
    pkill -f "uvicorn app.main:app"
    echo "✅ Backend service stopped"
fi

# Kill frontend processes
if pgrep -f "react-scripts start" > /dev/null; then
    pkill -f "react-scripts start"
    echo "✅ Frontend service stopped"
fi

# Kill Node.js processes on port 3000
if lsof -ti:3000 > /dev/null 2>&1; then
    lsof -ti:3000 | xargs kill -9
    echo "✅ Port 3000 freed"
fi

# Kill Python processes on port 8000
if lsof -ti:8000 > /dev/null 2>&1; then
    lsof -ti:8000 | xargs kill -9
    echo "✅ Port 8000 freed"
fi

echo ""
echo "🎉 Privik Platform stopped successfully!"
echo ""
echo "To start again, run: ./start-privik.sh"
