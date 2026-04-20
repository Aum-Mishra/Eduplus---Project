param(
    [switch]$SetupOnly,
    [switch]$RunOnly
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPath = Join-Path $root ".venv_all"

function Write-Step([string]$msg) {
    Write-Host "`n==== $msg ====" -ForegroundColor Cyan
}

function Assert-Command([string]$cmd, [string]$helpText) {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
        throw "$cmd is not available. $helpText"
    }
}

function Invoke-InVenv([string]$command, [string]$workingDir = $root) {
    $activate = Join-Path $venvPath "Scripts\Activate.ps1"
    $full = "Set-Location '$workingDir'; & '$activate'; $command"
    powershell -NoProfile -ExecutionPolicy Bypass -Command $full
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed in venv: $command"
    }
}

if (-not $RunOnly) {
    Write-Step "Validating prerequisites"
    Assert-Command "py" "Install Python launcher and Python 3.10.x"
    Assert-Command "npm" "Install Node.js (for UI Eduplus)"

    & py -3.10 --version
    if ($LASTEXITCODE -ne 0) {
        throw "Python 3.10 is required for Rasa compatibility. Install Python 3.10 and retry."
    }

    Write-Step "Creating unified virtual environment"
    if (-not (Test-Path $venvPath)) {
        & py -3.10 -m venv $venvPath
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to create .venv_all"
        }
    }

    Write-Step "Installing unified Python dependencies"
    Invoke-InVenv "python -m pip install --upgrade pip setuptools wheel"
    Invoke-InVenv "pip install -r requirements.common.txt"

    Write-Step "Installing frontend dependencies"
    Set-Location (Join-Path $root "UI Eduplus")
    npm install
    if ($LASTEXITCODE -ne 0) {
        throw "npm install failed in UI Eduplus"
    }

    Write-Step "Checking/training ML models"
    if (-not (Test-Path (Join-Path $root "models\placement_model.pkl"))) {
        Invoke-InVenv "python train_models.py"
    }
    if (-not (Test-Path (Join-Path $root "models\salary_tier_model.pkl"))) {
        Invoke-InVenv "python train_salary_model.py"
    }

    Write-Step "Checking/training Rasa model"
    Set-Location (Join-Path $root "Chatbot")
    if (-not (Test-Path (Join-Path $root "Chatbot\models\current.tar.gz"))) {
        Invoke-InVenv "python -m rasa train" (Join-Path $root "Chatbot")
    }

    if ($SetupOnly) {
        Write-Host "`nSetup complete. Run .\setup_system.ps1 -RunOnly to start all services." -ForegroundColor Green
        exit 0
    }
}

Write-Step "Starting all services"

$activateBat = Join-Path $venvPath "Scripts\activate.bat"

# Main Flask backend (port 5000)
Start-Process cmd -ArgumentList "/k", "cd /d `"$root`" && call `"$activateBat`" && python app.py"

# Isolated LLM backend (port 8001)
Start-Process cmd -ArgumentList "/k", "cd /d `"$root\llm_isolated_service`" && call `"$activateBat`" && python app.py"

# Rasa action server (port 5055)
Start-Process cmd -ArgumentList "/k", "cd /d `"$root\Chatbot`" && call `"$activateBat`" && python -m rasa run actions --enable-api --cors * --port 5055"

# Rasa HTTP server (port 5005)
Start-Process cmd -ArgumentList "/k", "cd /d `"$root\Chatbot`" && call `"$activateBat`" && python -m rasa run --enable-api --cors * --port 5005"

# Frontend dev server (vite)
Start-Process cmd -ArgumentList "/k", "cd /d `"$root\UI Eduplus`" && npm run dev -- --host"

Write-Host "`nAll services launched in separate terminals:" -ForegroundColor Green
Write-Host "- Flask API: http://localhost:5000"
Write-Host "- Rasa API: http://localhost:5005"
Write-Host "- LLM API: http://localhost:8001"
Write-Host "- UI (Vite): check terminal output (typically http://localhost:5173)"
