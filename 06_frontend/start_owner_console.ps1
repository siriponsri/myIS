param(
    [switch]$NoBrowser
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$DashboardUrl = "http://127.0.0.1:8765"
$MlflowUrl = "http://127.0.0.1:5000"
$RepositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path

function Test-LocalEndpoint {
    param([Parameter(Mandatory = $true)][string]$Uri)

    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $Uri -TimeoutSec 2
        return $response.StatusCode -eq 200
    }
    catch {
        return $false
    }
}

function Wait-ForEndpoint {
    param(
        [Parameter(Mandatory = $true)][string]$Uri,
        [Parameter(Mandatory = $true)][string]$ServiceName
    )

    $deadline = [DateTime]::UtcNow.AddSeconds(30)
    while ([DateTime]::UtcNow -lt $deadline) {
        if (Test-LocalEndpoint -Uri $Uri) {
            return
        }
        Start-Sleep -Milliseconds 250
    }
    throw "$ServiceName did not become ready at $Uri within 30 seconds."
}

function Resolve-GitBash {
    $candidates = @()
    if ($env:ProgramFiles) {
        $candidates += Join-Path $env:ProgramFiles "Git\bin\bash.exe"
    }
    $git = Get-Command git.exe -ErrorAction SilentlyContinue
    if ($git) {
        $gitRoot = Split-Path -Parent (Split-Path -Parent $git.Source)
        $candidates += Join-Path $gitRoot "bin\bash.exe"
    }
    foreach ($candidate in $candidates | Select-Object -Unique) {
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }
    throw "Git Bash was not found. Install Git for Windows before starting MLflow."
}

try {
    $uv = Get-Command uv.exe -ErrorAction SilentlyContinue
    if (-not $uv) {
        $uv = Get-Command uv -ErrorAction SilentlyContinue
    }
    if (-not $uv) {
        throw "uv was not found. The launcher never installs dependencies automatically."
    }

    if (-not (Test-LocalEndpoint -Uri "$DashboardUrl/healthz")) {
        Write-Host "Starting Owner Dashboard..."
        Start-Process `
            -FilePath $uv.Source `
            -ArgumentList @("run", "--no-sync", "myis-dashboard", "--repository-root", ".", "--port", "8765") `
            -WorkingDirectory $RepositoryRoot `
            -WindowStyle Hidden | Out-Null
        Wait-ForEndpoint -Uri "$DashboardUrl/healthz" -ServiceName "Owner Dashboard"
    }
    else {
        Write-Host "Owner Dashboard is already running."
    }

    if (-not (Test-LocalEndpoint -Uri "$MlflowUrl/health")) {
        Write-Host "Starting read-only MLflow viewer..."
        $gitBash = Resolve-GitBash
        Start-Process `
            -FilePath $gitBash `
            -ArgumentList @("06_frontend/mlflow/mlflow.sh", "start") `
            -WorkingDirectory $RepositoryRoot `
            -WindowStyle Hidden | Out-Null
        Wait-ForEndpoint -Uri "$MlflowUrl/health" -ServiceName "Read-only MLflow viewer"
    }
    else {
        Write-Host "Read-only MLflow viewer is already running."
    }

    Write-Host "Owner Dashboard: $DashboardUrl"
    Write-Host "Read-only MLflow: $MlflowUrl"
    if (-not $NoBrowser) {
        Start-Process -FilePath $DashboardUrl | Out-Null
        Start-Process -FilePath $MlflowUrl | Out-Null
    }
    exit 0
}
catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
