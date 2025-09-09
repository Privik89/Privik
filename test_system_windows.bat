@echo off
echo ========================================
echo Privik System Test - Windows
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
echo Running comprehensive system test...
python test_system.py

echo.
echo Test complete!
pause
