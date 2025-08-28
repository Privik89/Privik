#!/bin/bash

echo "🚀 Starting Privik Frontend Development Server..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    echo "   Visit: https://nodejs.org/"
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm first."
    exit 1
fi

echo "✅ Node.js version: $(node --version)"
echo "✅ npm version: $(npm --version)"

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

echo "🌐 Starting React development server..."
echo "📖 Frontend will be available at: http://localhost:3000"
echo "🔗 Backend API proxy: http://localhost:8000"
echo "⏹️  Press Ctrl+C to stop"
echo "----------------------------------------"

# Start the development server
npm start
