[CmdletBinding()]
param(
    [Parameter()]
    [string]$SourceRoot,
    [Parameter()]
    [string]$OwnerRoot,
    [Parameter()]
    [string]$MlflowRoot,
    [switch]$SkipNotebook
)

$ErrorActionPreference = "Stop"
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$arguments = @("run", "--no-sync", "python", "05_code/scripts/prepare_f1_g1.py")
if ($SourceRoot) { $arguments += @("--source-root", $SourceRoot) }
if ($OwnerRoot) { $arguments += @("--owner-root", $OwnerRoot) }
if ($MlflowRoot) { $arguments += @("--mlflow-root", $MlflowRoot) }
if ($SkipNotebook) { $arguments += "--skip-notebook" }

Push-Location $repositoryRoot
try {
    & uv @arguments
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    $validation = @("run", "--no-sync", "python", "05_code/scripts/validate_f1_g1_preparation.py")
    if ($OwnerRoot) { $validation += @("--owner-root", $OwnerRoot) }
    & uv @validation
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
