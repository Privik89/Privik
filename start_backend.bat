@echo off
echo Starting Privik Backend Server...
cd /d "%~dp0"
call venv\Scripts\activate.bat
cd backend
echo Starting FastAPI server on http://localhost:8000
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
pause
