# CivicFix Platform Launch Script
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "Starting CivicFix Municipal Infrastructure Platform" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[1/2] $pythonVersion detected." -ForegroundColor Green
} catch {
    Write-Host "Error: Python is not installed or not in PATH." -ForegroundColor Red
    exit 1
}

# Start Backend
Write-Host "[2/2] Launching Flask Server on http://127.0.0.1:5000..." -ForegroundColor Yellow
Write-Host "The browser will open automatically once the server is ready." -ForegroundColor Cyan
python backend\app.py
