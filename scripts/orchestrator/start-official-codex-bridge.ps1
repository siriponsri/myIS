[CmdletBinding()]
param(
    [ValidateRange(1, 65535)]
    [int]$Port = 8765,
    [string]$EventRoot,
    [switch]$WhatIf
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'

$repositoryRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$officialHome = Join-Path $env:USERPROFILE '.codex-official'
$maxplusHome = Join-Path $env:USERPROFILE '.codex'
$checker = Join-Path $repositoryRoot 'scripts\dev\check-codex-profile.ps1'

& $checker -ProfileName official -ProfileRoot $officialHome -WhatIf
& $checker -ProfileName maxplus -ProfileRoot $maxplusHome -WhatIf

$arguments = @(
    'run', '--no-sync', 'python', '-m',
    'myis_research.armindex.official_codex_bridge',
    $(if ($WhatIf) { 'what-if' } else { 'serve' }),
    '--repository-root', $repositoryRoot,
    '--official-home', $officialHome,
    '--maxplus-home', $maxplusHome
)
if ($EventRoot) {
    $arguments += @('--event-root', [IO.Path]::GetFullPath($EventRoot))
}
if (-not $WhatIf) {
    $arguments += @('--port', [string]$Port)
}

& uv @arguments
exit $LASTEXITCODE
