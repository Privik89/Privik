@echo off
REM Privik Universal Stop Script (Windows)
setlocal enabledelayedexpansion

echo.
echo ========================================
echo   Stopping Privik Email Security Platform
echo ========================================
echo.

REM Stop Docker containers if running
docker --version >nul 2>&1
if %errorlevel% == 0 (
    echo [DOCKER] Stopping Docker containers...
    docker-compose down
    echo [SUCCESS] Docker containers stopped
)

REM Stop native processes
echo [NATIVE] Stopping native processes...

REM Kill processes on port 3000 (Frontend)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000') do (
    taskkill /f /pid %%a >nul 2>&1
)
echo [SUCCESS] Port 3000 freed

REM Kill processes on port 8000 (Backend)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do (
    taskkill /f /pid %%a >nul 2>&1
)
echo [SUCCESS] Port 8000 freed

REM Kill any remaining uvicorn processes
taskkill /f /im python.exe /fi "WINDOWTITLE eq Privik Backend*" >nul 2>&1
echo [SUCCESS] Backend processes stopped

REM Kill any remaining npm processes
taskkill /f /im node.exe /fi "WINDOWTITLE eq Privik Frontend*" >nul 2>&1
echo [SUCCESS] Frontend processes stopped

echo.
echo ========================================
echo   Privik Platform Stopped Successfully
echo ========================================
echo.
echo To start again, run:
echo   start-privik.bat    (Windows)
echo   ./start-privik.sh   (Linux/macOS)
echo.
echo Press any key to exit...
pause >nul
