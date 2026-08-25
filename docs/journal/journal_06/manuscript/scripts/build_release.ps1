$ErrorActionPreference = "Stop"

$manuscriptDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$packageDir = (Resolve-Path (Join-Path $manuscriptDir "..")).Path
$evidenceDir = Join-Path $packageDir "evidence"
$pdfDir = Join-Path $packageDir "output\pdf"
$figureDir = Join-Path $packageDir "output\figures"

New-Item -ItemType Directory -Force -Path $evidenceDir, $pdfDir, $figureDir | Out-Null
$env:MPLCONFIGDIR = Join-Path $env:TEMP "mplconfig-rcrs-v06"
New-Item -ItemType Directory -Force -Path $env:MPLCONFIGDIR | Out-Null

function Invoke-Checked {
    param([string]$LogPath, [scriptblock]$Command)

    $savedPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & $Command *>&1 | Tee-Object -FilePath $LogPath
    $exitCode = $LASTEXITCODE
    $ErrorActionPreference = $savedPreference
    if ($exitCode -ne 0) {
        throw "Command failed with exit code $exitCode. See $LogPath"
    }
}

Push-Location $manuscriptDir
try {
    Invoke-Checked (Join-Path $evidenceDir "build_figures.log") { py -3.11 scripts/build_figures.py }
    Invoke-Checked (Join-Path $evidenceDir "build_main.log") {
        latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
    }

    $readerInput = '\def\RCRSReader{1}\input{main.tex}'
    Invoke-Checked (Join-Path $evidenceDir "reader_pass1.log") {
        pdflatex -interaction=nonstopmode -halt-on-error -jobname=reader_preview $readerInput
    }
    Invoke-Checked (Join-Path $evidenceDir "reader_bib.log") { bibtex reader_preview }
    Invoke-Checked (Join-Path $evidenceDir "reader_pass2.log") {
        pdflatex -interaction=nonstopmode -halt-on-error -jobname=reader_preview $readerInput
    }
    Invoke-Checked (Join-Path $evidenceDir "reader_pass3.log") {
        pdflatex -interaction=nonstopmode -halt-on-error -jobname=reader_preview $readerInput
    }
    Invoke-Checked (Join-Path $evidenceDir "title_pass.log") {
        latexmk -pdf -interaction=nonstopmode -halt-on-error title_page.tex
    }

    Copy-Item -Force main.pdf (Join-Path $pdfDir "RCRS_WPI_MANUSCRIPT_V06_SUBMISSION.pdf")
    Copy-Item -Force reader_preview.pdf (Join-Path $pdfDir "RCRS_WPI_MANUSCRIPT_V06_READER_PREVIEW.pdf")
    Copy-Item -Force title_page.pdf (Join-Path $pdfDir "RCRS_WPI_TITLE_PAGE_PLACEHOLDER_V06.pdf")
    Copy-Item -Force figures\graphical_abstract.pdf (Join-Path $figureDir "RCRS_WPI_GRAPHICAL_ABSTRACT_V06.pdf")
    Copy-Item -Force figures\graphical_abstract.png (Join-Path $figureDir "RCRS_WPI_GRAPHICAL_ABSTRACT_V06.png")

    $releaseFiles = @(
        Join-Path $pdfDir "RCRS_WPI_MANUSCRIPT_V06_SUBMISSION.pdf"
        Join-Path $pdfDir "RCRS_WPI_MANUSCRIPT_V06_READER_PREVIEW.pdf"
        Join-Path $pdfDir "RCRS_WPI_TITLE_PAGE_PLACEHOLDER_V06.pdf"
        Join-Path $figureDir "RCRS_WPI_GRAPHICAL_ABSTRACT_V06.pdf"
        Join-Path $figureDir "RCRS_WPI_GRAPHICAL_ABSTRACT_V06.png"
    )
    $releaseFiles | ForEach-Object { Get-FileHash -Algorithm SHA256 -LiteralPath $_ } |
        Select-Object @{Name="File"; Expression={ Split-Path $_.Path -Leaf }}, Hash |
        Export-Csv -NoTypeInformation -Encoding utf8 (Join-Path $evidenceDir "release_hashes.csv")
}
finally {
    Pop-Location
}
