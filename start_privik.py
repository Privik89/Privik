#!/usr/bin/env python3
"""
Startup script for Privik Email Security Platform
"""

import os
import sys
import subprocess

def main():
    """Start the Privik platform with proper environment configuration."""
    
    print("🚀 Starting Privik Email Security Platform...")
    
    # Set environment variables
    os.environ["ENVIRONMENT"] = "development"
    os.environ["DEBUG"] = "true"
    
    print(f"✅ Environment: {os.environ.get('ENVIRONMENT')}")
    print(f"✅ Debug mode: {os.environ.get('DEBUG')}")
    
    # Change to backend directory
    backend_dir = os.path.join(os.path.dirname(__file__), "backend")
    os.chdir(backend_dir)
    
    print(f"✅ Working directory: {os.getcwd()}")
    
    # Start the server
    try:
        print("🌐 Starting FastAPI server...")
        print("📖 API Documentation will be available at: http://localhost:8000/docs")
        print("🔍 Health check: http://localhost:8000/health")
        print("⏹️  Press Ctrl+C to stop the server")
        print("-" * 60)
        
        # Run uvicorn
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000",
            "--reload"
        ])
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
