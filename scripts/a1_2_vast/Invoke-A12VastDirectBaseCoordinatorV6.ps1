[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)] [ValidateSet('upload', 'verify', 'start', 'status', 'collect', 'teardown')] [string]$Action,
    [Parameter(Mandatory = $true)] [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9.-]{0,252}$')] [string]$HostName,
    [Parameter(Mandatory = $true)] [ValidateRange(1, 65535)] [int]$Port,
    [Parameter(Mandatory = $true)] [ValidatePattern('^[A-Za-z_][A-Za-z0-9_-]{0,31}$')] [string]$UserName,
    [Parameter(Mandatory = $true)] [string]$KeyPath,
    [string]$BundlePath = '', [string]$WheelhousePath = '', [string]$ModelRoot = '', [string]$JobManifestRoot = '',
    [string]$ImageReference = 'pytorch/pytorch:2.6.0-cuda11.8-cudnn9-runtime',
    [string]$ExpectedManifestDigest = 'sha256:2428b92ebbaeceba5572b98c18c8a94e43162bead6e88588ad54471147c58a20',
    [string]$ExpectedBundleSha256 = '', [string]$CollectPath = '', [string]$ExpectedGitCommit = '', [string]$ExpectedGitTree = '',
    [ValidatePattern('^/opt/myis/[A-Za-z0-9._/-]+$')] [string]$RemoteRoot = '/opt/myis/a1.2-v6',
    [string]$ReceiptPath = '', [switch]$DryRun
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'
if ($RemoteRoot.Contains('..')) { throw 'RemoteRoot must not contain parent traversal.' }

function Resolve-ExistingPath {
    param([string]$Value, [string]$Label, [ValidateSet('Leaf','Container')][string]$Kind)
    if ([string]::IsNullOrWhiteSpace($Value)) { throw "$Label is required." }
    $type = if ($Kind -eq 'Leaf') { 'Leaf' } else { 'Container' }
    if (-not (Test-Path -LiteralPath $Value -PathType $type)) { throw "$Label is missing: $Value" }
    return (Resolve-Path -LiteralPath $Value).ProviderPath
}

function Invoke-NativeSafe {
    param([string]$Executable, [string[]]$Arguments)
    if ($DryRun) { return @() }
    $output = @(& $Executable @Arguments)
    if ($LASTEXITCODE -ne 0) { throw "$Executable failed with exit code $LASTEXITCODE." }
    return $output
}

$key = Resolve-ExistingPath $KeyPath 'SSH key' Leaf
$target = "$UserName@$HostName"
$ssh = @('-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-p', "$Port", '-i', $key)
$scp = @('-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-P', "$Port", '-i', $key)
$outputRoot = "$RemoteRoot/output"

switch ($Action) {
    'upload' {
        $bundle = Resolve-ExistingPath $BundlePath 'Frozen code bundle' Leaf
        $wheelhouse = Resolve-ExistingPath $WheelhousePath 'Linux wheelhouse' Container
        $models = Resolve-ExistingPath $ModelRoot 'Runtime-minimal model root' Container
        $jobs = Resolve-ExistingPath $JobManifestRoot 'Safe job manifests' Container
        $prepare = "set -eu; test ! -e ${RemoteRoot}; mkdir -p ${RemoteRoot}/incoming ${RemoteRoot}/models ${RemoteRoot}/wheelhouse ${RemoteRoot}/jobs ${outputRoot} ${RemoteRoot}/current"
        Invoke-NativeSafe ssh ($ssh + @($target, $prepare)) | Out-Null
        Invoke-NativeSafe scp ($scp + @($bundle, "${target}:${RemoteRoot}/incoming/frozen-code-bundle.tar.gz")) | Out-Null
        Invoke-NativeSafe scp ($scp + @('-r', $wheelhouse, "${target}:${RemoteRoot}/incoming/wheelhouse")) | Out-Null
        Invoke-NativeSafe scp ($scp + @('-r', $models, "${target}:${RemoteRoot}/incoming/models")) | Out-Null
        Invoke-NativeSafe scp ($scp + @('-r', $jobs, "${target}:${RemoteRoot}/incoming/jobs")) | Out-Null
        $extract = "set -eu; tar --no-same-owner -xzf ${RemoteRoot}/incoming/frozen-code-bundle.tar.gz -C ${RemoteRoot}/current; cp -a ${RemoteRoot}/incoming/wheelhouse/. ${RemoteRoot}/wheelhouse/; cp -a ${RemoteRoot}/incoming/models/. ${RemoteRoot}/models/; cp -a ${RemoteRoot}/incoming/jobs/. ${RemoteRoot}/jobs/"
        Invoke-NativeSafe ssh ($ssh + @($target, $extract)) | Out-Null
    }
    'verify' {
        if ($ExpectedGitCommit -notmatch '^[a-f0-9]{40,64}$') { throw 'ExpectedGitCommit is required and invalid.' }
        if ($ExpectedGitTree -notmatch '^[a-f0-9]{40,64}$') { throw 'ExpectedGitTree is required and invalid.' }
        if ($ExpectedManifestDigest -notmatch '^sha256:[a-f0-9]{64}$') { throw 'ExpectedManifestDigest is invalid.' }
        if ($ExpectedBundleSha256 -notmatch '^[a-f0-9]{64}$') { throw 'ExpectedBundleSha256 is required and invalid.' }
        if ($ImageReference -notmatch '^[A-Za-z0-9._/-]+:[A-Za-z0-9._-]+$') { throw 'ImageReference is invalid.' }
        $verify = "HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PIP_NO_INDEX=1 MYIS_REMOTE_MODE=a1_2_preflight_only bash ${RemoteRoot}/current/scripts/a1_2_vast/remote-bootstrap-direct-base-v6.sh $ImageReference $RemoteRoot $ExpectedGitCommit $ExpectedGitTree $ExpectedManifestDigest $ExpectedBundleSha256"
        Invoke-NativeSafe ssh ($ssh + @($target, $verify)) | Out-Null
    }
    'start' {
        if ($ExpectedManifestDigest -notmatch '^sha256:[a-f0-9]{64}$') { throw 'ExpectedManifestDigest is invalid.' }
        $launch = "HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PIP_NO_INDEX=1 MYIS_REMOTE_MODE=a1_2_preflight_only bash ${RemoteRoot}/current/scripts/a1_2_vast/remote-live-preflight-v6.sh ${RemoteRoot} ${ExpectedManifestDigest}"
        Invoke-NativeSafe ssh ($ssh + @($target, $launch)) | Out-Null
    }
    'status' {
        $status = "PYTHONPATH=${RemoteRoot}/current/src ${RemoteRoot}/venv/bin/python -m myis_research.armindex.a1_2_vast remote-status --output-root ${outputRoot}"
        Invoke-NativeSafe ssh ($ssh + @($target, $status)) | Out-Null
    }
    'collect' {
        $destination = Resolve-ExistingPath $CollectPath 'Collect path' Container
        $export = "PYTHONPATH=${RemoteRoot}/current/src ${RemoteRoot}/venv/bin/python -m myis_research.armindex.a1_2_vast safe-export --output-root ${outputRoot} --allowlist ${RemoteRoot}/current/control/armindex/a1.2/safe-export-allowlist.v6.json --archive ${outputRoot}/safe-export.tar.gz"
        Invoke-NativeSafe ssh ($ssh + @($target, $export)) | Out-Null
        Invoke-NativeSafe scp ($scp + @("${target}:${outputRoot}/safe-export.tar.gz", $destination)) | Out-Null
    }
    'teardown' {
        $stop = "PYTHONPATH=${RemoteRoot}/current/src ${RemoteRoot}/venv/bin/python -m myis_research.armindex.a1_2_vast guest-stop --output-root ${outputRoot}"
        Invoke-NativeSafe ssh ($ssh + @($target, $stop)) | Out-Null
    }
}

$receipt = [ordered]@{
    schema_version = 'myis.armindex-a1.2-direct-base-coordinator.v6'
    action = $Action
    status = $(if ($DryRun) { 'dry_run_validated' } else { 'completed' })
    image_reference = $ImageReference
    expected_manifest_digest = $ExpectedManifestDigest
    expected_bundle_sha256 = $(if ([string]::IsNullOrWhiteSpace($ExpectedBundleSha256)) { $null } else { $ExpectedBundleSha256 })
    remote_root = $RemoteRoot
    access_material_recorded = $false
    provider_destroyed = $false
    guest_teardown_only = ($Action -eq 'teardown')
    measured_retrieval = $false
    completed_at = [DateTime]::UtcNow.ToString('o')
}
if (-not [string]::IsNullOrWhiteSpace($ReceiptPath)) {
    $targetPath = [IO.Path]::GetFullPath($ReceiptPath)
    $parent = Split-Path -Parent $targetPath
    if (-not (Test-Path -LiteralPath $parent -PathType Container)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
    [IO.File]::WriteAllText($targetPath, (($receipt | ConvertTo-Json -Depth 8) + "`n"), (New-Object Text.UTF8Encoding($false)))
}
$receipt | ConvertTo-Json -Depth 8
