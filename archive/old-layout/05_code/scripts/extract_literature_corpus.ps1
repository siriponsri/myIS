[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$researchRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$myisRoot = Split-Path $researchRoot -Parent
$appRoot = Join-Path $myisRoot '00_App'
$workspaceRoot = Split-Path (Split-Path $myisRoot -Parent) -Parent
$archiveManifest = Join-Path $workspaceRoot '99_Archive\00_myIS\workspaces\thaiphalex-hyperresearch-review-20260726\source-packet\00-governance\LOCAL_CORPUS_MANIFEST.csv'
$extractRoot = Join-Path $researchRoot 'tmp\literature-corpus-extract'

if (-not (Test-Path -LiteralPath $archiveManifest -PathType Leaf)) {
    throw "Missing archived manifest: $archiveManifest"
}

$rows = @(
    Import-Csv -LiteralPath $archiveManifest |
        Where-Object { $_.dedup_role -eq 'canonical' }
)

$newRows = @(
    [pscustomobject]@{ unique_id = 'U151'; repo_relative_path = 'research/ref-paper/is1/pdfs/85_skillopt_lite_better_and_faster_agent.pdf' }
    [pscustomobject]@{ unique_id = 'U152'; repo_relative_path = 'research/ref-paper/is1/pdfs/86_marginal_advantage_accumulation_for_memory_driven_agent.pdf' }
    [pscustomobject]@{ unique_id = 'U153'; repo_relative_path = 'research/ref-paper/is1/pdfs/87_skillgrad_optimizing_agent_skills_like_gradient_descent.pdf' }
)

foreach ($row in $newRows) {
    $source = Join-Path $appRoot $row.repo_relative_path
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
        throw "Missing source PDF: $source"
    }
    $row | Add-Member -NotePropertyName sha256 -NotePropertyValue ((Get-FileHash -Algorithm SHA256 -LiteralPath $source).Hash.ToLowerInvariant())
    $rows += $row
}

if ($rows.Count -ne 153) {
    throw "Expected 153 canonical PDFs, found $($rows.Count)"
}

New-Item -ItemType Directory -Force -Path $extractRoot | Out-Null
$index = 0
foreach ($row in $rows) {
    $index += 1
    $source = Join-Path $appRoot $row.repo_relative_path
    $infoPath = Join-Path $extractRoot "$($row.sha256).info.txt"
    $textPath = Join-Path $extractRoot "$($row.sha256).txt"
    if (-not (Test-Path -LiteralPath $infoPath -PathType Leaf)) {
        $info = & pdfinfo $source
        if ($LASTEXITCODE -ne 0) {
            throw "pdfinfo failed for $source"
        }
        Set-Content -LiteralPath $infoPath -Value $info -Encoding utf8
    }
    if (-not (Test-Path -LiteralPath $textPath -PathType Leaf)) {
        & pdftotext -layout $source $textPath
        if ($LASTEXITCODE -ne 0) {
            throw "pdftotext failed for $source"
        }
    }
    Write-Host ("[{0:d3}/153] {1}" -f $index, $row.unique_id)
}

Write-Host "EXTRACTION_CACHE=$extractRoot"
Write-Host "EXTRACTED_PDFS=$($rows.Count)"
