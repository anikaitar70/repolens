# Run the FastAPI backend (Windows-friendly defaults)
#
# Usage:
#   .\scripts\start-backend.ps1
#   .\scripts\start-backend.ps1 -Port 9000

param(
    [int]$Port = 8080
)

$ErrorActionPreference = "Stop"
$BackendRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location (Join-Path $BackendRoot "backend")

if (-not (Test-Path ".\venv\Scripts\python.exe")) {
    Write-Host "Virtual environment not found. Run .\scripts\setup-backend.ps1 first." -ForegroundColor Yellow
    exit 1
}

Write-Host "Starting RepoLens backend on http://127.0.0.1:$Port" -ForegroundColor Green
Write-Host "If this port fails, try: .\scripts\start-backend.ps1 -Port 9000" -ForegroundColor DarkGray

& ".\venv\Scripts\python.exe" -m uvicorn app.main:app --reload --host 127.0.0.1 --port $Port
