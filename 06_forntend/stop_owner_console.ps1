Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

try {
    $processes = Get-CimInstance Win32_Process | Where-Object {
        $command = [string]$_.CommandLine
        ($command -like "*myis-dashboard*--port*8765*") -or
        ($command -like "*06_forntend/mlflow/mlflow.sh*start*") -or
        ($command -like "*06_forntend/mlflow/readonly_app.py*serve*--port*5000*")
    }

    $processIds = @($processes | Select-Object -ExpandProperty ProcessId -Unique)
    if ($processIds.Count -eq 0) {
        Write-Host "Owner Dashboard and MLflow viewer are already stopped."
        exit 0
    }

    Stop-Process -Id $processIds -Force -ErrorAction SilentlyContinue
    Write-Host "Stopped Owner Dashboard and read-only MLflow viewer."
    exit 0
}
catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
