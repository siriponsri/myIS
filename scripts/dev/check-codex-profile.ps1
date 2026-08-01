[CmdletBinding()]
param(
    [ValidateSet('official', 'maxplus')]
    [string]$ProfileName = 'official',
    [string]$ProfileRoot,
    [switch]$WhatIf
)

$ErrorActionPreference = 'Stop'
$label = $ProfileName.ToLowerInvariant()
if (-not $ProfileRoot) {
    $ProfileRoot = Join-Path $HOME (".codex-{0}" -f $label)
}
$profilePath = [IO.Path]::GetFullPath($ProfileRoot)
$codex = Get-Command codex -ErrorAction SilentlyContinue
if (-not $codex) { throw 'codex executable was not found on PATH.' }
$version = (& codex --version 2>$null | Select-Object -First 1)
if (-not $version) { throw 'codex version check failed.' }
$repo = (& git rev-parse --show-toplevel 2>$null)
if ($LASTEXITCODE -eq 0 -and $repo) {
    $repoPath = [IO.Path]::GetFullPath($repo.Trim())
    $repoPrefix = $repoPath.TrimEnd([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
    if ($profilePath.Equals($repoPath, [StringComparison]::OrdinalIgnoreCase) -or $profilePath.StartsWith($repoPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Codex profile must be outside the Git worktree.'
    }
}
if (-not (Test-Path -LiteralPath $profilePath -PathType Container)) {
    throw "Codex $label profile is missing: $profilePath. Create and authenticate it manually."
}
$config = Join-Path $profilePath 'config.toml'
if (-not (Test-Path -LiteralPath $config -PathType Leaf)) {
    throw "Codex $label profile config.toml is missing: $config"
}
if ($WhatIf) {
    Write-Output ("profile={0}; version={1}; root={2}; action=dry-run" -f $label, $version.Trim(), $profilePath)
    exit 0
}
Write-Output ("profile={0}; version={1}; root={2}; action=ready" -f $label, $version.Trim(), $profilePath)
