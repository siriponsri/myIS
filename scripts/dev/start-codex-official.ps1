[CmdletBinding()]
param(
    [string]$ProfileRoot,
    [switch]$WhatIf,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$CodexArgs
)

$ErrorActionPreference = 'Stop'
$checker = Join-Path $PSScriptRoot 'check-codex-profile.ps1'
& $checker -ProfileName official -ProfileRoot $ProfileRoot -WhatIf:$WhatIf
if ($WhatIf) { exit 0 }
$resolvedProfile = if ($ProfileRoot) { [IO.Path]::GetFullPath($ProfileRoot) } else { Join-Path $HOME '.codex-official' }
$oldHome = $env:CODEX_HOME
$oldStore = $env:MYIS_STORE
$oldMlflow = $env:MYIS_MLFLOW_STORE
try {
    $env:CODEX_HOME = $resolvedProfile
    Remove-Item Env:MYIS_STORE -ErrorAction SilentlyContinue
    Remove-Item Env:MYIS_MLFLOW_STORE -ErrorAction SilentlyContinue
    Write-Output 'Starting Codex with the official profile. Verify /status manually.'
    & codex @CodexArgs
    exit $LASTEXITCODE
}
finally {
    if ($null -eq $oldHome) { Remove-Item Env:CODEX_HOME -ErrorAction SilentlyContinue } else { $env:CODEX_HOME = $oldHome }
    if ($null -eq $oldStore) { Remove-Item Env:MYIS_STORE -ErrorAction SilentlyContinue } else { $env:MYIS_STORE = $oldStore }
    if ($null -eq $oldMlflow) { Remove-Item Env:MYIS_MLFLOW_STORE -ErrorAction SilentlyContinue } else { $env:MYIS_MLFLOW_STORE = $oldMlflow }
}
