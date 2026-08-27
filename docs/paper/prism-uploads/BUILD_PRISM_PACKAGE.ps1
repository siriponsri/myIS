[CmdletBinding()]
param(
    [string]$PackageName = "myIS_prism_manuscript_package_20260828.zip"
)

$ErrorActionPreference = "Stop"
$paperRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$archivePath = Join-Path $PSScriptRoot $PackageName
$stagingRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("myIS-prism-" + [guid]::NewGuid().ToString("N"))
$packageRoot = Join-Path $stagingRoot ([System.IO.Path]::GetFileNameWithoutExtension($PackageName))
$bibStylePath = (& kpsewhich IEEEtran.bst).Trim()

if (-not $bibStylePath -or -not (Test-Path -LiteralPath $bibStylePath -PathType Leaf)) {
    throw "Could not locate IEEEtran.bst with kpsewhich. Install an IEEEtran-capable TeX distribution before building the package."
}

$files = @(
    "00_READ_ME_FIRST.md",
    "01_STORY_ARC_BEYOND_THE_RETRIEVER.md",
    "02_PRISM_MASTER_BRIEF.md",
    "CHANGES.md",
    "PRISM_EDIT_INSTRUCTIONS.md",
    "SOURCE_MANIFEST.md",
    "stats.json",
    "main.tex",
    "main.pdf",
    "IEEEtran.cls",
    "references/references.bib",
    "evidence/CORE_EVIDENCE_A1_A7.md",
    "evidence/RELATED_WORK_POSITIONING.md",
    "evidence/RESEARCH_PROTOCOL.md",
    "venue/ISAINLP_2026_SUBMISSION_GUIDELINES.md",
    "venue/RULES_AND_TEMPLATE.md",
    "figures/rebuilt/overview_evidence_map.pdf",
    "figures/rebuilt/fig1_a3_transfer.pdf",
    "figures/rebuilt/fig2_a5_confirmation.pdf",
    "figures/rebuilt/fig3_a7_diagnosis.pdf"
)

try {
    New-Item -ItemType Directory -Path $packageRoot -Force | Out-Null
    foreach ($relativePath in $files) {
        $sourcePath = Join-Path $paperRoot $relativePath
        if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) {
            throw "Required Prism package file is missing: $relativePath"
        }
        $destinationPath = Join-Path $packageRoot $relativePath
        New-Item -ItemType Directory -Path (Split-Path $destinationPath -Parent) -Force | Out-Null
        Copy-Item -LiteralPath $sourcePath -Destination $destinationPath
    }

    Copy-Item -LiteralPath (Join-Path $paperRoot "PRISM_PACKAGE_README.md") -Destination (Join-Path $packageRoot "README.md")
    Copy-Item -LiteralPath $bibStylePath -Destination (Join-Path $packageRoot "IEEEtran.bst")

    $manifestPath = Join-Path $packageRoot "PACKAGE_SHA256SUMS.txt"
    Get-ChildItem -LiteralPath $packageRoot -Recurse -File |
        Sort-Object FullName |
        ForEach-Object {
            $relativePath = $_.FullName.Substring($packageRoot.Length + 1).Replace("\", "/")
            "{0}  ./{1}" -f (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant(), $relativePath
        } |
        Set-Content -LiteralPath $manifestPath -Encoding ascii

    if (Test-Path -LiteralPath $archivePath) {
        Remove-Item -LiteralPath $archivePath -Force
    }
    Compress-Archive -LiteralPath $packageRoot -DestinationPath $archivePath -CompressionLevel Optimal
    Write-Output ("Created: {0}" -f $archivePath)
    Write-Output ("SHA256: {0}" -f (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant())
}
finally {
    if (Test-Path -LiteralPath $stagingRoot) {
        Remove-Item -LiteralPath $stagingRoot -Recurse -Force
    }
}
