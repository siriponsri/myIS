[CmdletBinding()]
param(
    [switch]$Build,
    [switch]$Check,
    [switch]$Serve,
    [ValidateRange(1024, 65535)]
    [int]$Port = 8765
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not ($Build -or $Check -or $Serve)) {
    $Build = $true
    $Check = $true
}

if ($Serve) {
    $Build = $true
    $Check = $true
}

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$presentationRoot = Join-Path $repositoryRoot 'docs\presentation'
$sourceRoot = Join-Path $presentationRoot 'src'
$distRoot = Join-Path $presentationRoot 'dist'
$manifestPath = Join-Path $distRoot 'asset-manifest.json'
$reportPath = Join-Path $repositoryRoot 'docs\progress_report\update_A0_A1_A2_18AUG2026.md'

$bundle = @(
    [ordered]@{ role = 'deck'; source = (Join-Path $sourceRoot 'index.html'); destination = 'index.html' },
    [ordered]@{ role = 'stylesheet'; source = (Join-Path $sourceRoot 'styles.css'); destination = 'styles.css' },
    [ordered]@{ role = 'reveal-reset'; source = (Join-Path $presentationRoot 'vendor\reveal\reset.css'); destination = 'vendor\reveal\reset.css' },
    [ordered]@{ role = 'reveal-core'; source = (Join-Path $presentationRoot 'vendor\reveal\reveal.css'); destination = 'vendor\reveal\reveal.css' },
    [ordered]@{ role = 'reveal-runtime'; source = (Join-Path $presentationRoot 'vendor\reveal\reveal.js'); destination = 'vendor\reveal\reveal.js' },
    [ordered]@{ role = 'reveal-license'; source = (Join-Path $presentationRoot 'vendor\reveal\LICENSE'); destination = 'vendor\reveal\LICENSE' },
    [ordered]@{ role = 'a1-quality-figure'; source = (Join-Path $repositoryRoot 'outputs\figures\armindex\a12-v16-20260811-r15.quality-cell-eda.v16.png'); destination = 'assets\a1-quality-cell-eda.png' },
    [ordered]@{ role = 'a1-efficiency-figure'; source = (Join-Path $repositoryRoot 'outputs\figures\armindex\a12-v16-20260811-r15.efficiency-cell-eda.v16.png'); destination = 'assets\a1-efficiency-cell-eda.png' },
    [ordered]@{ role = 'a2-outcomes-figure'; source = (Join-Path $repositoryRoot 'outputs\figures\armindex\a2-goal004\a2-goal004-outcomes.png'); destination = 'assets\a2-outcomes.png' }
)

function Assert-FileExists {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Required file is missing: $Path"
    }
}

function Get-RelativeRepositoryPath {
    param([Parameter(Mandatory = $true)][string]$Path)

    $root = [IO.Path]::GetFullPath($repositoryRoot).TrimEnd('\') + '\'
    $fullPath = [IO.Path]::GetFullPath($Path)
    if (-not $fullPath.StartsWith($root, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Path is outside the repository root: $Path"
    }
    return $fullPath.Substring($root.Length).Replace('\', '/')
}

Assert-FileExists -Path $reportPath
foreach ($item in $bundle) {
    Assert-FileExists -Path $item.source
}

if ($Build) {
    if (Test-Path -LiteralPath $distRoot) {
        Remove-Item -LiteralPath $distRoot -Recurse -Force
    }

    New-Item -ItemType Directory -Force -Path $distRoot | Out-Null
    $manifestEntries = @()

    foreach ($item in $bundle) {
        $destination = Join-Path $distRoot $item.destination
        $destinationDirectory = Split-Path -Parent $destination
        New-Item -ItemType Directory -Force -Path $destinationDirectory | Out-Null
        Copy-Item -LiteralPath $item.source -Destination $destination -Force

        $manifestEntries += [ordered]@{
            role = $item.role
            source = Get-RelativeRepositoryPath -Path $item.source
            destination = $item.destination.Replace('\', '/')
            source_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $item.source).Hash.ToLowerInvariant()
            destination_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $destination).Hash.ToLowerInvariant()
        }
    }

    $manifest = [ordered]@{
        schema_version = 'myis.armindex-advisor-presentation-asset-manifest.v1'
        generated_at_utc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
        source_report = Get-RelativeRepositoryPath -Path $reportPath
        source_report_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $reportPath).Hash.ToLowerInvariant()
        assets = $manifestEntries
    }
    $manifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $manifestPath -Encoding utf8
    Write-Output "Built offline presentation bundle: $distRoot"
}

if ($Check) {
    Assert-FileExists -Path $manifestPath
    $manifest = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json
    $currentReportHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $reportPath).Hash.ToLowerInvariant()
    if ($manifest.source_report_sha256 -ne $currentReportHash) {
        throw 'The source progress report changed. Rebuild the presentation bundle.'
    }

    foreach ($asset in $manifest.assets) {
        $source = Join-Path $repositoryRoot $asset.source.Replace('/', '\\')
        $destination = Join-Path $distRoot $asset.destination.Replace('/', '\\')
        Assert-FileExists -Path $source
        Assert-FileExists -Path $destination

        $sourceHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $source).Hash.ToLowerInvariant()
        $destinationHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $destination).Hash.ToLowerInvariant()
        if ($sourceHash -ne $asset.source_sha256 -or $destinationHash -ne $asset.destination_sha256 -or $sourceHash -ne $destinationHash) {
            throw "Asset hash mismatch: $($asset.role)"
        }
    }

    $deckHtml = Get-Content -Raw -LiteralPath (Join-Path $distRoot 'index.html')
    foreach ($requiredText in @(
        'A1 completed the five-by-five common screen',
        'A2 closes with complete aggregate evidence and bounded winners',
        'A3 is prepared locally but remains fail-closed until Train-250 bindings',
        'frozen candidates accounted'
    )) {
        if (-not $deckHtml.Contains($requiredText)) {
            throw "Deck content guard failed: $requiredText"
        }
    }
    if ($deckHtml -match '[\u0E00-\u0E7F]') {
        throw 'Deck language guard failed: presentation source must be English-only.'
    }
    Write-Output 'PASS: presentation bundle, source report binding, and asset hashes are valid.'
}

if ($Serve) {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($null -eq $python) {
        throw 'python is required to serve the local presentation preview.'
    }

    $arguments = "-m http.server $Port --directory `"$distRoot`""
    $server = Start-Process -FilePath $python.Source -ArgumentList $arguments -PassThru -WindowStyle Hidden
    Write-Output "Presentation preview: http://127.0.0.1:$Port (server PID $($server.Id))"
}
