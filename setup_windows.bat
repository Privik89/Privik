@echo off
echo ========================================
echo Privik Zero-Trust Email Security Setup
echo Windows Environment Setup
echo ========================================

echo.
echo [1/6] Creating Python virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: Failed to create virtual environment
    echo Please ensure Python 3.11+ is installed and in PATH
    pause
    exit /b 1
)

echo.
echo [2/6] Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

echo.
echo [3/6] Upgrading pip...
python -m pip install --upgrade pip

echo.
echo [4/6] Installing backend dependencies...
pip install -r backend\requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install backend dependencies
    pause
    exit /b 1
)

echo.
echo [5/6] Installing AI/ML dependencies...
pip install playwright scikit-learn joblib pandas numpy
if %errorlevel% neq 0 (
    echo ERROR: Failed to install AI/ML dependencies
    pause
    exit /b 1
)

echo.
echo [6/6] Installing Playwright browsers...
playwright install chromium
if %errorlevel% neq 0 (
    echo WARNING: Playwright browser installation failed
    echo You may need to install manually: playwright install chromium
)

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo To start the server:
echo   start_privik_windows.bat
echo.
echo To test the system:
echo   test_system_windows.bat
echo.
pause
