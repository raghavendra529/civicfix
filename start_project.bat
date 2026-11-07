@echo off
title CivicFix Platform
echo ===================================================
echo Starting CivicFix Municipal Infrastructure Platform
echo ===================================================

cd /d "%~dp0"

echo [1/2] Verifying Python Environment...
python --version
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH.
    pause
    exit /b 1
)

echo [2/2] Launching Backend Server...
echo The browser will open automatically once the server is ready.
python backend\app.py

pause
