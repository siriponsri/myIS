<#
.SYNOPSIS
Checks or creates project-owned myIS skill junctions without replacing files.

.EXAMPLE
.\05_code\scripts\sync_project_skills.ps1 -Mode Sync
#>
[CmdletBinding()]
param(
    [ValidateSet("Check", "Sync")]
    [string]$Mode = "Check",

    [string]$CodexRoot = [System.IO.Path]::Combine(
        [Environment]::GetFolderPath([Environment+SpecialFolder]::UserProfile),
        ".codex",
        "skills"
    ),

    [string]$ClaudeRoot = [System.IO.Path]::Combine(
        [Environment]::GetFolderPath([Environment+SpecialFolder]::UserProfile),
        ".claude",
        "skills"
    )
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$skillNames = @(
    "myis-record-research-session",
    "myis-review-research-rigor",
    "myis-run-harnessopt"
)

$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")).Path
$canonicalRoot = Join-Path $repositoryRoot ".agents\skills"

function Get-NormalizedPath {
    param([Parameter(Mandatory = $true)][string]$Path)

    return [System.IO.Path]::GetFullPath($Path).TrimEnd(
        [System.IO.Path]::DirectorySeparatorChar,
        [System.IO.Path]::AltDirectorySeparatorChar
    )
}

function Test-ManagedJunction {
    param(
        [Parameter(Mandatory = $true)][string]$LinkPath,
        [Parameter(Mandatory = $true)][string]$ExpectedTarget
    )

    if (-not (Test-Path -LiteralPath $LinkPath)) {
        return $false
    }

    $item = Get-Item -LiteralPath $LinkPath -Force
    if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -eq 0) {
        throw "Refusing to replace a real file or directory: $LinkPath"
    }

    $actualTargets = @($item.Target) | ForEach-Object { Get-NormalizedPath -Path $_ }
    $expected = Get-NormalizedPath -Path $ExpectedTarget
    if ($actualTargets -notcontains $expected) {
        throw "Refusing to replace a junction with another target: $LinkPath"
    }

    return $true
}

function Invoke-SkillRoot {
    param([Parameter(Mandatory = $true)][string]$DestinationRoot)

    if ($Mode -eq "Sync" -and -not (Test-Path -LiteralPath $DestinationRoot)) {
        New-Item -ItemType Directory -Path $DestinationRoot -Force | Out-Null
    }

    foreach ($skillName in $skillNames) {
        $source = Join-Path $canonicalRoot $skillName
        $link = Join-Path $DestinationRoot $skillName

        if (-not (Test-Path -LiteralPath (Join-Path $source "SKILL.md"))) {
            throw "Canonical skill is incomplete: $source"
        }

        if (Test-ManagedJunction -LinkPath $link -ExpectedTarget $source) {
            Write-Output "OK   $link -> $source"
            continue
        }

        if ($Mode -eq "Check") {
            Write-Output "MISS $link -> $source"
            continue
        }

        New-Item -ItemType Junction -Path $link -Target $source | Out-Null
        Write-Output "LINK $link -> $source"
    }
}

Invoke-SkillRoot -DestinationRoot $CodexRoot
Invoke-SkillRoot -DestinationRoot $ClaudeRoot
