$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendVenv = Join-Path $root ".venv_backend"
$rasaVenv = Join-Path $root ".venv_rasa"
$ragVenv = Join-Path $root ".venv_rag"
$uiDir = Join-Path $root "UI Eduplus"
$chatbotDir = Join-Path $root "Chatbot"
$ragBackendDir = Join-Path $root "llm_isolated_service"
$runtimeDir = Join-Path $root ".eduplus_runtime"
$manifestPath = Join-Path $runtimeDir "service-manifest.json"

function Write-Step([string]$message) {
    Write-Host "`n==== $message ====" -ForegroundColor Cyan
}

function Get-VenvPython([string]$venvPath) {
    return Join-Path $venvPath "Scripts\python.exe"
}

function Get-VenvExe([string]$venvPath, [string]$exeName) {
    return Join-Path $venvPath "Scripts\$exeName"
}

function Assert-ServiceReady([string]$path, [string]$errorMessage) {
    if (-not (Test-Path $path)) {
        throw $errorMessage
    }
}

Assert-ServiceReady $backendVenv "Run .\setup_all.ps1 first so .venv_backend exists."
Assert-ServiceReady $rasaVenv "Run .\setup_all.ps1 first so .venv_rasa exists."
Assert-ServiceReady $ragVenv "Run .\setup_all.ps1 first so .venv_rag exists."
Assert-ServiceReady (Join-Path $uiDir "node_modules") "Run .\setup_all.ps1 first so UI Eduplus dependencies are installed."

$chatbotModel = Get-ChildItem -Path (Join-Path $chatbotDir "models") -Filter *.tar.gz -File -ErrorAction SilentlyContinue
if (-not $chatbotModel) {
    throw "No trained Rasa model was found in Chatbot\models. Run .\setup_all.ps1 so the model can be trained once before starting the system."
}

New-Item -ItemType Directory -Path $runtimeDir -Force | Out-Null

$backendPython = Get-VenvPython $backendVenv
$rasaExe = Get-VenvExe $rasaVenv "rasa.exe"
$ragPython = Get-VenvPython $ragVenv

Write-Host "========================================"
Write-Host "EDUPLUS SYSTEM"
Write-Host "========================================"
Write-Host "Backend       : http://localhost:5000"
Write-Host "Frontend      : http://localhost:5173"
Write-Host "Rasa          : http://localhost:5005"
Write-Host "Rasa Actions  : http://localhost:5055"
Write-Host "LLM/RAG       : http://localhost:8001"
Write-Host "========================================"

Write-Step "Starting Flask backend"
$backendProcess = Start-Process -FilePath $backendPython -ArgumentList @("app.py") -WorkingDirectory $root -PassThru

Write-Step "Starting React frontend"
$frontendProcess = Start-Process -FilePath "npm.cmd" -ArgumentList @("run", "dev", "--", "--host", "127.0.0.1", "--port", "5173") -WorkingDirectory $uiDir -PassThru

Write-Step "Starting Rasa action server"
$rasaActionsProcess = Start-Process -FilePath $rasaExe -ArgumentList @("run", "actions", "--cors", "*", "--port", "5055") -WorkingDirectory $chatbotDir -PassThru

Write-Step "Starting Rasa webhook server"
$rasaServerProcess = Start-Process -FilePath $rasaExe -ArgumentList @("run", "--enable-api", "--cors", "*", "--port", "5005") -WorkingDirectory $chatbotDir -PassThru

Write-Step "Starting LLM/RAG Flask service"
$ragProcess = Start-Process `
    -FilePath $ragPython `
    -ArgumentList @("app.py") `
    -WorkingDirectory $ragBackendDir `
    -PassThru

$manifest = [ordered]@{
    startedAt = (Get-Date).ToString("s")
    services = @(
        [ordered]@{ name = "backend"; pid = $backendProcess.Id; port = 5000; url = "http://localhost:5000"; workingDirectory = $root },
        [ordered]@{ name = "frontend"; pid = $frontendProcess.Id; port = 5173; url = "http://localhost:5173"; workingDirectory = $uiDir },
        [ordered]@{ name = "rasa-actions"; pid = $rasaActionsProcess.Id; port = 5055; url = "http://localhost:5055"; workingDirectory = $chatbotDir },
        [ordered]@{ name = "rasa-server"; pid = $rasaServerProcess.Id; port = 5005; url = "http://localhost:5005"; workingDirectory = $chatbotDir },
        [ordered]@{ name = "rag"; pid = $ragProcess.Id; port = 8001; url = "http://localhost:8001"; workingDirectory = $ragBackendDir }
    )
}

$manifest | ConvertTo-Json -Depth 5 | Set-Content -Path $manifestPath -Encoding UTF8

Write-Host ""
Write-Host "Services launched. Use .\check_services.ps1 to verify readiness." -ForegroundColor Green
Write-Host "Use .\stop_all.ps1 to stop the EduPlus services started here." -ForegroundColor Green
