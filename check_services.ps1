$ErrorActionPreference = "Stop"

function Test-HttpService([string]$name, [string]$url) {
    try {
        $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 5
        if ($response) {
            return "[OK] $name"
        }
    }
    catch {
        $response = $_.Exception.Response
        if ($response -and $response.StatusCode) {
            $statusCode = [int]$response.StatusCode
            if ($statusCode -ge 200 -and $statusCode -lt 500) {
                return "[OK] $name"
            }
        }
    }

    return "[FAILED] $name"
}

function Test-TcpService([string]$name, [int]$port) {
    $connection = Test-NetConnection -ComputerName "127.0.0.1" -Port $port -WarningAction SilentlyContinue
    if ($connection.TcpTestSucceeded) {
        return "[OK] $name"
    }

    return "[FAILED] $name"
}

$checks = @(
    @{ Name = "Flask :5000"; Url = "http://localhost:5000/api/health" },
    @{ Name = "React :5173"; Url = "http://localhost:5173/" },
    @{ Name = "Rasa :5005"; Url = "http://localhost:5005/status" },
    @{ Name = "Actions :5055"; Port = 5055 },
    @{ Name = "RAG :8001"; Url = "http://localhost:8001/health" }
)

foreach ($check in $checks) {
    if ($check.ContainsKey("Url")) {
        Write-Host (Test-HttpService -name $check.Name -url $check.Url)
    }
    else {
        Write-Host (Test-TcpService -name $check.Name -port $check.Port)
    }
}
