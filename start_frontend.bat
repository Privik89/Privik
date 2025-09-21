@echo off
echo Starting Privik Frontend Server...
cd /d "%~dp0\frontend"
echo Starting React development server on http://localhost:3000
npm start
pause
