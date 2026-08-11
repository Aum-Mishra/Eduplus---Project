$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$runtimeDir = Join-Path $root ".eduplus_runtime"
$manifestPath = Join-Path $runtimeDir "service-manifest.json"

function Write-Step([string]$message) {
    Write-Host "`n==== $message ====" -ForegroundColor Cyan
}

function Stop-ProcessTree([int]$processId, [string]$serviceName) {
    try {
        & taskkill /PID $processId /T /F | Out-Null
        Write-Host "[OK] Stopped $serviceName (PID $processId)"
    }
    catch {
        Write-Host "[FAILED] Could not stop $serviceName (PID $processId): $($_.Exception.Message)"
    }
}

if (-not (Test-Path $manifestPath)) {
    Write-Host "No EduPlus runtime manifest was found. Nothing to stop."
    exit 0
}

$manifest = Get-Content -Path $manifestPath -Raw | ConvertFrom-Json

Write-Step "Stopping EduPlus services"
foreach ($service in $manifest.services) {
    if ($null -ne $service.pid -and [int]$service.pid -gt 0) {
        Stop-ProcessTree -processId ([int]$service.pid) -serviceName ([string]$service.name)
    }
}

Remove-Item -Path $manifestPath -Force -ErrorAction SilentlyContinue
Write-Host "`nEduPlus services stop request completed."
