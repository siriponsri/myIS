[CmdletBinding()]
param(
    [string]$OutputPath = '',
    [switch]$KeepBuildArtifacts
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$presentationRoot = Join-Path $repositoryRoot 'docs\presentation'
$buildRoot = Join-Path $presentationRoot 'pptx-build'
$assetsRoot = Join-Path $buildRoot 'assets'
$qaRoot = Join-Path $buildRoot 'qa'
$skillRoot = 'C:\Users\Siripon Sri\.codex\plugins\cache\openai-primary-runtime\presentations\26.802.11031\skills\presentations'
$artifactSetup = Join-Path $skillRoot 'container_tools\setup_artifact_tool_workspace.mjs'
$rasterizer = Join-Path $skillRoot 'container_tools\rasterize_svg.mjs'
$generator = Join-Path $repositoryRoot 'scripts\build_armindex_advisor_talk_pptx.mjs'

if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    $OutputPath = Join-Path $presentationRoot 'ArmIndex_Advisor_Talk_A0_A3_2026-08-18.pptx'
}

$resolvedPresentationRoot = [IO.Path]::GetFullPath($presentationRoot).TrimEnd('\')
$resolvedBuildRoot = [IO.Path]::GetFullPath($buildRoot)
if (-not $resolvedBuildRoot.StartsWith("$resolvedPresentationRoot\", [StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to use a build directory outside the presentation root: $resolvedBuildRoot"
}

function Assert-FileExists {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Required file is missing: $Path"
    }
}

Assert-FileExists -Path $artifactSetup
Assert-FileExists -Path $rasterizer
Assert-FileExists -Path $generator

if (Test-Path -LiteralPath $resolvedBuildRoot) {
    Remove-Item -LiteralPath $resolvedBuildRoot -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $assetsRoot, $qaRoot | Out-Null

Push-Location $env:USERPROFILE
try {
    & node $artifactSetup --workspace $resolvedBuildRoot
    if ($LASTEXITCODE -ne 0) {
        throw 'Artifact Tool workspace setup failed.'
    }
}
finally {
    Pop-Location
}

$figureRoot = Join-Path $presentationRoot 'material\figures'
$svgFigures = @(
    '01_dapfam_family_record_anatomy.svg',
    '02_retrieval_system_stack.svg',
    '03_a0_split_and_leakage_control.svg',
    '04_a1_representation_programs.svg',
    '05_a1_mean_out_recall.svg',
    '06_a2_execution_and_reserve_flow.svg',
    '07_a3_transfer_complementarity_harnessopt.svg',
    'armindex-research-program.svg',
    'dapfam-protocol.svg',
    'patent-retrieval-pipeline.svg'
) | ForEach-Object { Join-Path $figureRoot $_ }

foreach ($svg in $svgFigures) {
    Assert-FileExists -Path $svg
}

foreach ($svg in $svgFigures) {
    $pngName = [IO.Path]::GetFileNameWithoutExtension($svg) + '.png'
    $pngPath = Join-Path $assetsRoot $pngName
    Push-Location $env:USERPROFILE
    try {
        & node $rasterizer --input $svg --output $pngPath
        if ($LASTEXITCODE -ne 0) {
            throw "SVG rasterization failed: $svg"
        }
    }
    finally {
        Pop-Location
    }
}

$rasterSources = @{
    'a12-v16-20260811-r15.efficiency-cell-eda.v16.png' = 'outputs\figures\armindex\a12-v16-20260811-r15.efficiency-cell-eda.v16.png'
    'a1.2-dense-overflow-eda-v1.png' = 'outputs\figures\armindex\a1.2-dense-overflow-eda-v1.png'
    'a2-goal004-outcomes.png' = 'outputs\figures\armindex\a2-goal004\a2-goal004-outcomes.png'
}

foreach ($entry in $rasterSources.GetEnumerator()) {
    $sourcePath = Join-Path $repositoryRoot $entry.Value
    Assert-FileExists -Path $sourcePath
    Copy-Item -LiteralPath $sourcePath -Destination (Join-Path $assetsRoot $entry.Key) -Force
}

$workspaceGenerator = Join-Path $resolvedBuildRoot 'build_armindex_advisor_talk_pptx.mjs'
Copy-Item -LiteralPath $generator -Destination $workspaceGenerator -Force

$resolvedOutput = [IO.Path]::GetFullPath($OutputPath)
$outputDirectory = Split-Path -Parent $resolvedOutput
New-Item -ItemType Directory -Force -Path $outputDirectory | Out-Null

& node $workspaceGenerator --assets $assetsRoot --output $resolvedOutput --qa $qaRoot
if ($LASTEXITCODE -ne 0) {
    throw 'PPTX generation failed.'
}

$inspectionPath = "$resolvedOutput.inspect.ndjson"
Copy-Item -LiteralPath (Join-Path $qaRoot 'deck.inspect.ndjson') -Destination $inspectionPath -Force
Write-Output "Built: $resolvedOutput"
Write-Output "Inspection: $inspectionPath"

if (-not $KeepBuildArtifacts) {
    Remove-Item -LiteralPath $resolvedBuildRoot -Recurse -Force
}
