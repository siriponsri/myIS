[CmdletBinding()]
param(
    [string]$PackageName = "myIS_prism_manuscript_package_20260828.zip"
)

$ErrorActionPreference = "Stop"
$archivePath = Join-Path $PSScriptRoot $PackageName
$verifyRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("myIS-prism-verify-" + [guid]::NewGuid().ToString("N"))

try {
    if (-not (Test-Path -LiteralPath $archivePath -PathType Leaf)) {
        throw "Prism package not found: $archivePath"
    }
    New-Item -ItemType Directory -Path $verifyRoot | Out-Null
    Expand-Archive -LiteralPath $archivePath -DestinationPath $verifyRoot
    $packageRoot = Get-ChildItem -LiteralPath $verifyRoot -Directory | Select-Object -First 1
    if (-not $packageRoot) {
        throw "The ZIP does not contain a package root."
    }

    $manifestPath = Join-Path $packageRoot.FullName "PACKAGE_SHA256SUMS.txt"
    $invalid = foreach ($line in Get-Content -LiteralPath $manifestPath) {
        $separatorIndex = $line.IndexOf("  ./")
        $expectedHash = $line.Substring(0, $separatorIndex)
        $relativePath = $line.Substring($separatorIndex + 4).Replace("/", [string][char]92)
        $targetPath = Join-Path $packageRoot.FullName $relativePath
        if ((Get-FileHash -LiteralPath $targetPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expectedHash) {
            $relativePath
        }
    }
    if ($invalid) {
        throw ("Hash mismatch: " + ($invalid -join ", "))
    }

    Push-Location $packageRoot.FullName
    try {
        & latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
        if ($LASTEXITCODE -ne 0) {
            throw "latexmk failed"
        }
        & pdfinfo main.pdf | Select-String -Pattern "Pages|Page size"
    }
    finally {
        Pop-Location
    }

    Write-Output ("Verified: {0}" -f $archivePath)
}
finally {
    if (Test-Path -LiteralPath $verifyRoot) {
        Remove-Item -LiteralPath $verifyRoot -Recurse -Force
    }
}
