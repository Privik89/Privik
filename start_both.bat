@echo off
echo Starting Privik Email Security Platform...
echo.
echo Starting Backend and Frontend servers...
echo.

REM Start backend in new window
start "Privik Backend" cmd /k "cd /d "%~dp0" && call venv\Scripts\activate.bat && cd backend && echo Starting FastAPI server... && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

REM Wait a moment for backend to start
timeout /t 5 /nobreak >nul

REM Start frontend in new window
start "Privik Frontend" cmd /k "cd /d "%~dp0\frontend" && echo Starting React server... && npm start"

echo.
echo Both servers are starting...
echo.
echo Backend will be available at: http://localhost:8000
echo Backend API docs: http://localhost:8000/docs
echo Frontend will be available at: http://localhost:3000
echo.
echo Press any key to exit this launcher...
pause >nul
