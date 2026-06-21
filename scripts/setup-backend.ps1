# Create and configure the Python virtual environment on Windows
#
# Usage:
#   .\scripts\setup-backend.ps1

$ErrorActionPreference = "Stop"
$BackendRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$BackendDir = Join-Path $BackendRoot "backend"
Set-Location $BackendDir

function Find-Python {
    $candidates = @(
        { & py -3.12 -c "import sys; print(sys.executable)" 2>$null },
        { & py -3 -c "import sys; print(sys.executable)" 2>$null },
        { & python -c "import sys; print(sys.executable)" 2>$null }
    )

    foreach ($candidate in $candidates) {
        try {
            $path = Invoke-Expression $candidate
            if ($path -and (Test-Path $path)) {
                return $path.Trim()
            }
        } catch {
            continue
        }
    }

    throw "Python 3.12+ not found. Install from https://www.python.org/downloads/ (avoid partial Store installs)."
}

$python = Find-Python
Write-Host "Using Python: $python" -ForegroundColor Green

if (Test-Path ".\venv") {
    Write-Host "Removing existing virtual environment..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force ".\venv"
}

Write-Host "Creating virtual environment..." -ForegroundColor Green
& $python -m venv venv

if (-not (Test-Path ".\venv\Scripts\python.exe")) {
    throw "Virtual environment creation failed. Install Python from python.org instead of the Microsoft Store."
}

Write-Host "Installing dependencies..." -ForegroundColor Green
& ".\venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\venv\Scripts\pip.exe" install -r requirements.txt

if (-not (Test-Path ".\.env")) {
    Copy-Item ".\.env.example" ".\.env"
    Write-Host "Created backend/.env from .env.example" -ForegroundColor Green
}

Write-Host ""
Write-Host "Setup complete." -ForegroundColor Green
Write-Host "Start backend: ..\scripts\start-backend.ps1" -ForegroundColor Cyan
Write-Host "Default port: 8080 (Windows often blocks 8000)" -ForegroundColor DarkGray
