@echo off
echo ========================================
echo Privik Zero-Trust Email Security Platform
echo Starting Server (Windows)
echo ========================================

echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERROR: Virtual environment not found
    echo Please run setup_windows.bat first
    pause
    exit /b 1
)

echo.
echo Creating database tables...
python -c "import sys; sys.path.append('backend'); from backend.app.database import create_tables; create_tables(); print('Database tables created')"

echo.
echo Starting Privik server...
echo Server will be available at: http://localhost:8000
echo Press Ctrl+C to stop the server
echo.
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

pause
