[CmdletBinding()]
param(
    [ValidateSet('validate-pending')]
    [string]$Action = 'validate-pending',
    [string]$RepositoryRoot
)

$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($RepositoryRoot)) {
    $RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
}

if ($Action -ne 'validate-pending') { throw 'Only local pending validation is available before A2 closeout.' }

$python = Join-Path $RepositoryRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'Project Python is unavailable.' }

$required = @(
    'control\budgets\armindex-budget-extension-a3-v1.json',
    'control\armindex\a3\a3-five-arm-preparation-authority.v1.json',
    'control\armindex\a3\a3-five-arm-preparation-manifest.v1.json',
    'schemas\armindex\a3-five-arm-preparation-manifest.v1.json',
    'schemas\armindex\a3-five-arm-preparation-authority.v1.json',
    'schemas\armindex\armindex-budget-extension-a3-v1.json',
    'scripts\validate_a3_five_arm_preparation.py',
    'tests\test_armindex_a3_execution_preparation.py'
)
foreach ($relative in $required) {
    if (-not (Test-Path -LiteralPath (Join-Path $RepositoryRoot $relative) -PathType Leaf)) {
        throw "Missing A3 pending artifact: $relative"
    }
}

Push-Location $RepositoryRoot
try {
    $env:PYTHONPATH = 'src'
    & $python scripts/validate_a3_five_arm_preparation.py --repository-root $RepositoryRoot
    if ($LASTEXITCODE -ne 0) { throw 'A3 pending manifest validation failed.' }
    & $python -m pytest -q tests/test_armindex_a3_execution_preparation.py
    if ($LASTEXITCODE -ne 0) { throw 'A3 pending test validation failed.' }
}
finally {
    Pop-Location
}
