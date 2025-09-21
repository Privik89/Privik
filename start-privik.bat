@echo off
REM Privik Universal Startup Script (Windows Batch)
setlocal enabledelayedexpansion

echo.
echo ========================================
echo   Privik Email Security Platform
echo   Windows Startup Script
echo ========================================
echo.

REM Check if Docker is available
docker --version >nul 2>&1
if %errorlevel% == 0 (
    echo [INFO] Docker detected. Using Docker deployment...
    goto :docker_deployment
) else (
    echo [INFO] Docker not found. Using native deployment...
    goto :native_deployment
)

:docker_deployment
echo.
echo [DOCKER] Starting Privik with Docker...
echo.

REM Stop any existing containers
echo [DOCKER] Stopping existing containers...
docker-compose down

REM Build and start services
echo [DOCKER] Building and starting services...
docker-compose up --build -d

REM Wait for services
echo [DOCKER] Waiting for services to start...
timeout /t 15 /nobreak >nul

REM Check service health
echo [DOCKER] Checking service health...
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel% == 0 (
    echo [SUCCESS] Backend is running at http://localhost:8000
) else (
    echo [WARNING] Backend is not responding yet
)

curl -s http://localhost:3000 >nul 2>&1
if %errorlevel% == 0 (
    echo [SUCCESS] Frontend is running at http://localhost:3000
) else (
    echo [WARNING] Frontend is still starting...
)

goto :show_info

:native_deployment
echo.
echo [NATIVE] Starting Privik with native installation...
echo.

REM Check if we're in the right directory
if not exist "backend" (
    echo [ERROR] Please run this script from the Privik root directory
    pause
    exit /b 1
)

REM Start backend
echo [NATIVE] Starting backend service...
start "Privik Backend" cmd /k "cd backend && python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

REM Wait a moment
timeout /t 5 /nobreak >nul

REM Start frontend
echo [NATIVE] Starting frontend service...
start "Privik Frontend" cmd /k "cd frontend && npm install && npm start"

REM Wait for services
echo [NATIVE] Waiting for services to start...
timeout /t 15 /nobreak >nul

:show_info
echo.
echo ========================================
echo   Privik Platform Status
echo ========================================
echo.
echo [ACCESS POINTS]
echo   Frontend:  http://localhost:3000
echo   Backend:   http://localhost:8000
echo   API Docs:  http://localhost:8000/docs
echo.
echo [SERVICES]
echo   Email Security:     Active
echo   Threat Detection:   Active
echo   AI/ML Analysis:     Active
echo   Sandbox Analysis:   Active
echo   Quarantine:         Active
echo.
echo [MANAGEMENT]
echo   Stop Services:      Ctrl+C in service windows
echo   View Logs:          Check service windows
echo   Restart:            Run this script again
echo.
echo [SUPPORT]
echo   Documentation:      docs/
echo   Troubleshooting:    docs/troubleshooting/
echo   API Reference:      http://localhost:8000/docs
echo.
echo ========================================
echo.

REM Keep window open
echo Press any key to exit...
pause >nul
