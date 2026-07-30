param(
    [switch]$NoBrowser
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$DashboardPorts = 8765..8770
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
        [Parameter(Mandatory = $true)][string]$ServiceName,
        [int]$TimeoutSeconds = 30
    )

    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    while ([DateTime]::UtcNow -lt $deadline) {
        if (Test-LocalEndpoint -Uri $Uri) {
            return
        }
        Start-Sleep -Milliseconds 250
    }
    throw "$ServiceName did not become ready at $Uri within $TimeoutSeconds seconds."
}

function Test-ResearchDashboard {
    param([Parameter(Mandatory = $true)][string]$Uri)

    try {
        $response = Invoke-RestMethod -Uri "$Uri/healthz" -TimeoutSec 2
        return $response.status -eq "ok" -and $response.program_id -eq "myis-research"
    }
    catch {
        return $false
    }
}

function Find-ExistingDashboardUrl {
    foreach ($port in $DashboardPorts) {
        $uri = "http://127.0.0.1:$port"
        if (Test-ResearchDashboard -Uri $uri) {
            return $uri
        }
    }
    return $null
}

function Test-PortInUse {
    param([Parameter(Mandatory = $true)][int]$Port)

    return $null -ne (Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue)
}

function Resolve-FreeDashboardPort {
    foreach ($port in $DashboardPorts) {
        if (-not (Test-PortInUse -Port $port)) {
            return $port
        }
    }
    throw "No free Owner Dashboard port is available in 8765-8770."
}

function Assert-DashboardEnvironment {
    $required = @("myis-dashboard.exe", "myis-assets.exe", "myis-sessions.exe")
    foreach ($filename in $required) {
        $path = Join-Path $RepositoryRoot ".venv\Scripts\$filename"
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            throw "Dashboard environment is incomplete. Stop existing Owner Console processes, then run: uv sync --locked --extra dashboard --extra tracking --extra notebook --extra test"
        }
    }
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

    Assert-DashboardEnvironment
    $DashboardUrl = Find-ExistingDashboardUrl
    if (-not $DashboardUrl) {
        $DashboardPort = Resolve-FreeDashboardPort
        $DashboardUrl = "http://127.0.0.1:$DashboardPort"
        Write-Host "Starting Owner Dashboard..."
        Start-Process `
            -FilePath $uv.Source `
            -ArgumentList @("run", "--no-sync", "myis-dashboard", "--repository-root", ".", "--port", "$DashboardPort") `
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
        Wait-ForEndpoint -Uri "$MlflowUrl/health" -ServiceName "Read-only MLflow viewer" -TimeoutSeconds 90
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
