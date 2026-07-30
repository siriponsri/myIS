[CmdletBinding()]
param(
    [switch]$Apply
)

$ErrorActionPreference = 'Stop'
$researchRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$appRoot = Join-Path (Split-Path $researchRoot -Parent) '00_App'
$manifestPath = Join-Path $researchRoot '01_evidence\literature\catalog\corpus_manifest.csv'
$tierRoot = Join-Path $researchRoot '01_evidence'
$legacyObjectsRoot = Join-Path $researchRoot '01_evidence\private\literature\objects\sha256'
$legacyObjectsParent = Split-Path $legacyObjectsRoot -Parent

function Get-LowerSha256 {
    param([Parameter(Mandatory)][string]$Path)
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()
}

function Assert-PdfMatchesManifest {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)]$Row
    )
    $actualHash = Get-LowerSha256 -Path $Path
    if ($actualHash -ne $Row.sha256) {
        throw "SHA mismatch for $($Row.u_id): $actualHash != $($Row.sha256) at $Path"
    }
    if ((Get-Item -LiteralPath $Path).Length -ne [int64]$Row.size_bytes) {
        throw "Size mismatch for $($Row.u_id) at $Path"
    }
}

if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
    throw "Missing corpus manifest: $manifestPath"
}

$rows = @(Import-Csv -LiteralPath $manifestPath)
if ($rows.Count -ne 153) {
    throw "Expected 153 manifest rows, found $($rows.Count)"
}

$duplicateTargets = @($rows | Group-Object object_path | Where-Object Count -gt 1)
if ($duplicateTargets.Count -gt 0) {
    throw "Manifest contains duplicate PDF targets: $($duplicateTargets.Name -join ', ')"
}

$actions = @()
foreach ($row in $rows) {
    $target = [IO.Path]::GetFullPath((Join-Path $researchRoot $row.object_path))
    $expectedTierRoot = Join-Path $tierRoot "$($row.tier)-tier"
    $expectedPrefix = [IO.Path]::GetFullPath($expectedTierRoot) + [IO.Path]::DirectorySeparatorChar
    if (-not $target.StartsWith($expectedPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Target escapes canonical tier root for $($row.u_id): $target"
    }

    $locations = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    foreach ($candidate in @(
        $target,
        (Join-Path $legacyObjectsRoot "$($row.sha256.Substring(0, 2))\$($row.sha256).pdf"),
        (Join-Path $appRoot $row.legacy_primary_alias)
    )) {
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            [void]$locations.Add([IO.Path]::GetFullPath($candidate))
        }
    }
    foreach ($tier in @('A', 'B', 'C', 'N')) {
        $candidateRoot = Join-Path $tierRoot "$tier-tier"
        if (-not (Test-Path -LiteralPath $candidateRoot -PathType Container)) {
            continue
        }
        foreach ($candidate in Get-ChildItem -File -LiteralPath $candidateRoot -Filter "$($row.u_id)_*.pdf") {
            [void]$locations.Add($candidate.FullName)
        }
    }

    if ($locations.Count -eq 0) {
        throw "No PDF source found for $($row.u_id)"
    }
    if ($locations.Count -gt 1) {
        throw "Multiple PDF locations found for $($row.u_id); no automatic deletion: $($locations -join ', ')"
    }

    $source = @($locations)[0]
    Assert-PdfMatchesManifest -Path $source -Row $row
    $actions += [pscustomobject]@{
        u_id = $row.u_id
        tier = $row.tier
        source = $source
        target = $target
        move_required = -not $source.Equals($target, [StringComparison]::OrdinalIgnoreCase)
    }
}

$tierCounts = $rows | Group-Object tier | Sort-Object Name
Write-Host "MANIFEST_ROWS=$($rows.Count)"
foreach ($group in $tierCounts) {
    Write-Host "TIER_$($group.Name)=$($group.Count)"
}
Write-Host "MOVES_REQUIRED=$(@($actions | Where-Object move_required).Count)"
Write-Host "MODE=$(if ($Apply) { 'APPLY' } else { 'PREFLIGHT' })"

if (-not $Apply) {
    $actions | Where-Object move_required | Select-Object u_id, tier, source, target | Format-Table -AutoSize
    exit 0
}

$moved = 0
foreach ($action in $actions) {
    if (-not $action.move_required) {
        continue
    }
    $targetDirectory = Split-Path $action.target -Parent
    New-Item -ItemType Directory -Force -Path $targetDirectory | Out-Null
    Move-Item -LiteralPath $action.source -Destination $action.target
    $moved += 1
}

foreach ($row in $rows) {
    $target = Join-Path $researchRoot $row.object_path
    if (-not (Test-Path -LiteralPath $target -PathType Leaf)) {
        throw "Missing migrated target for $($row.u_id): $target"
    }
    Assert-PdfMatchesManifest -Path $target -Row $row
}

$tierPdfs = @(
    foreach ($tier in @('A', 'B', 'C', 'N')) {
        $candidateRoot = Join-Path $tierRoot "$tier-tier"
        if (Test-Path -LiteralPath $candidateRoot -PathType Container) {
            Get-ChildItem -File -LiteralPath $candidateRoot -Filter '*.pdf'
        }
    }
)
if ($tierPdfs.Count -ne 153) {
    throw "Expected 153 tier PDFs, found $($tierPdfs.Count)"
}

$legacyPdfs = @()
if (Test-Path -LiteralPath $legacyObjectsRoot -PathType Container) {
    $legacyPdfs = @(Get-ChildItem -File -Recurse -LiteralPath $legacyObjectsRoot -Filter '*.pdf')
}
if ($legacyPdfs.Count -ne 0) {
    throw "Legacy SHA store still contains PDFs: $($legacyPdfs.FullName -join ', ')"
}

if (Test-Path -LiteralPath $legacyObjectsParent -PathType Container) {
    $remainingFiles = @(Get-ChildItem -File -Recurse -LiteralPath $legacyObjectsParent)
    $expectedObjectsPath = [IO.Path]::GetFullPath(
        (Join-Path $researchRoot '01_evidence\private\literature\objects')
    )
    $resolvedObjectsPath = [IO.Path]::GetFullPath($legacyObjectsParent)
    if ($remainingFiles.Count -eq 0 -and $resolvedObjectsPath -eq $expectedObjectsPath) {
        Remove-Item -LiteralPath $legacyObjectsParent -Recurse -Force
    }
}

Write-Host "FILES_MOVED=$moved"
Write-Host "TIER_PDFS_HASH_VERIFIED=$($tierPdfs.Count)"
Write-Host "LEGACY_OBJECT_PDFS=$($legacyPdfs.Count)"
