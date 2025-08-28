#!/bin/bash

# Privik Email Security Platform - Stop Script

echo "🛑 Stopping Privik Email Security Platform..."

# Kill all Privik-related processes
pkill -f "uvicorn.*app.main:app" 2>/dev/null || true
pkill -f "npm start" 2>/dev/null || true
pkill -f "node.*react-scripts" 2>/dev/null || true

# Kill processes on specific ports
sudo fuser -k 8000/tcp 2>/dev/null || true
sudo fuser -k 3000/tcp 2>/dev/null || true

echo "✅ Privik platform stopped successfully"
