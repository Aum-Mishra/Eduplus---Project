param(
    [switch]$SetupOnly
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendVenv = Join-Path $root ".venv_backend"
$rasaVenv = Join-Path $root ".venv_rasa"
$ragVenv = Join-Path $root ".venv_rag"
$uiDir = Join-Path $root "UI Eduplus"
$chatbotDir = Join-Path $root "Chatbot"
$ragBackendDir = Join-Path $root "llm_isolated_service\EduNavigator\backend"

function Write-Step([string]$message) {
    Write-Host "`n==== $message ====" -ForegroundColor Cyan
}

function Assert-Command([string]$commandName, [string]$helpText) {
    if (-not (Get-Command $commandName -ErrorAction SilentlyContinue)) {
        throw "$commandName is not available. $helpText"
    }
}

function Get-VenvPython([string]$venvPath) {
    return Join-Path $venvPath "Scripts\python.exe"
}

function Get-VenvExe([string]$venvPath, [string]$exeName) {
    return Join-Path $venvPath "Scripts\$exeName"
}

function Ensure-Venv([string]$venvPath) {
    if (-not (Test-Path $venvPath)) {
        & py -3.10 -m venv $venvPath
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to create virtual environment at $venvPath"
        }
    }
}

function Upgrade-Pip([string]$pythonExe) {
    & $pythonExe -m pip install --upgrade pip setuptools wheel
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to upgrade pip in $pythonExe"
    }
}

function Install-Requirements([string]$pythonExe, [string]$requirementsFile) {
    & $pythonExe -m pip install -r $requirementsFile
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install requirements from $requirementsFile"
    }
}

function Ensure-PkgResources([string]$pythonExe) {
    & $pythonExe -c "import pkg_resources"
    if ($LASTEXITCODE -ne 0) {
        & $pythonExe -m pip install --force-reinstall setuptools==65.5.1
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to restore pkg_resources in the Rasa environment"
        }
    }
}

function Assert-RasaModelExists {
    $modelsDir = Join-Path $chatbotDir "models"
    $modelFiles = Get-ChildItem -Path $modelsDir -Filter *.tar.gz -File -ErrorAction SilentlyContinue
    return ($null -ne $modelFiles -and $modelFiles.Count -gt 0)
}

Assert-Command "py" "Install the Python launcher with Python 3.10 available."
Assert-Command "node" "Install Node.js."
Assert-Command "npm" "Install npm with Node.js."

Write-Step "Checking Python 3.10"
& py -3.10 --version
if ($LASTEXITCODE -ne 0) {
    throw "Python 3.10 was not found. Install Python 3.10 and retry."
}

Write-Step "Checking Node.js and npm"
& node --version
if ($LASTEXITCODE -ne 0) {
    throw "Node.js was not found. Install Node.js and retry."
}
& npm --version
if ($LASTEXITCODE -ne 0) {
    throw "npm was not found. Install Node.js and retry."
}

Write-Step "Creating virtual environments"
Ensure-Venv $backendVenv
Ensure-Venv $rasaVenv
Ensure-Venv $ragVenv

$backendPython = Get-VenvPython $backendVenv
$rasaPython = Get-VenvPython $rasaVenv
$ragPython = Get-VenvPython $ragVenv
$rasaExe = Get-VenvExe $rasaVenv "rasa.exe"

Write-Step "Upgrading pip in each environment"
Upgrade-Pip $backendPython
Upgrade-Pip $rasaPython
Upgrade-Pip $ragPython

Write-Step "Installing backend dependencies"
Install-Requirements $backendPython (Join-Path $root "requirements.backend.txt")
Ensure-PkgResources $backendPython

Write-Step "Installing Rasa dependencies"
Install-Requirements $rasaPython (Join-Path $root "requirements.rasa.txt")
Ensure-PkgResources $rasaPython

Write-Step "Installing RAG dependencies"
Install-Requirements $ragPython (Join-Path $root "requirements.rag.txt")

Write-Step "Installing frontend dependencies"
Push-Location $uiDir
try {
    & npm install
    if ($LASTEXITCODE -ne 0) {
        throw "npm install failed in UI Eduplus"
    }
}
finally {
    Pop-Location
}

Write-Step "Preparing Rasa model"
if (-not (Assert-RasaModelExists)) {
    Push-Location $chatbotDir
    try {
        & $rasaExe train
        if ($LASTEXITCODE -ne 0) {
            throw "Rasa training failed"
        }
    }
    finally {
        Pop-Location
    }
}

Write-Step "Validating backend imports"
& $backendPython -c "import flask, pandas, numpy, sklearn, xgboost, requests, joblib, language_tool_python, textstat, reportlab, chardet; print('backend imports ok')"
if ($LASTEXITCODE -ne 0) {
    throw "Backend import validation failed"
}

Write-Step "Validating Rasa installation"
& $rasaExe --version
if ($LASTEXITCODE -ne 0) {
    throw "Rasa version check failed"
}
& $rasaPython -c "import pydantic, pandas, requests, fuzzywuzzy, reportlab; print('rasa imports ok'); print('pydantic=' + pydantic.__version__)"
if ($LASTEXITCODE -ne 0) {
    throw "Rasa environment validation failed"
}

Write-Step "Validating RAG imports"
& $ragPython -c "import pydantic, fastapi, uvicorn, langchain, langchain_community, langchain_core, langchain_text_splitters, faiss, sentence_transformers, google.generativeai, numpy, requests, orjson, aiofiles, jinja2; print('rag imports ok'); print('pydantic=' + pydantic.__version__)"
if ($LASTEXITCODE -ne 0) {
    throw "RAG environment validation failed"
}

Write-Step "Validating frontend node modules"
Push-Location $uiDir
try {
    if (-not (Test-Path (Join-Path $uiDir "node_modules"))) {
        throw "UI Eduplus\node_modules was not created"
    }
    & npm --version
    if ($LASTEXITCODE -ne 0) {
        throw "npm validation failed"
    }
}
finally {
    Pop-Location
}

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "EDUPLUS SETUP COMPLETE" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "Backend venv : $backendVenv"
Write-Host "Rasa venv    : $rasaVenv"
Write-Host "RAG venv     : $ragVenv"
Write-Host "Frontend deps : UI Eduplus\node_modules"
Write-Host "Rasa model    : $(if (Assert-RasaModelExists) { 'available' } else { 'trained during setup' })"
Write-Host ""
Write-Host "Next step: .\start_all.ps1" -ForegroundColor Green
