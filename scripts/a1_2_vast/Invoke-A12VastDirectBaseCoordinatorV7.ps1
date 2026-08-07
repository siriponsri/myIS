[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)] [ValidateSet('stage-repair', 'verify', 'start', 'status', 'collect', 'teardown')] [string]$Action,
    [Parameter(Mandatory = $true)] [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9.-]{0,252}$')] [string]$HostName,
    [Parameter(Mandatory = $true)] [ValidateRange(1, 65535)] [int]$Port,
    [Parameter(Mandatory = $true)] [ValidatePattern('^[A-Za-z_][A-Za-z0-9_-]{0,31}$')] [string]$UserName,
    [Parameter(Mandatory = $true)] [string]$KeyPath,
    [string]$BundlePath = '', [string]$ImageReference = 'pytorch/pytorch:2.6.0-cuda11.8-cudnn9-runtime',
    [string]$ExpectedManifestDigest = 'sha256:2428b92ebbaeceba5572b98c18c8a94e43162bead6e88588ad54471147c58a20',
    [string]$ExpectedBundleSha256 = '', [string]$CollectPath = '', [string]$ExpectedGitCommit = '', [string]$ExpectedGitTree = '',
    [ValidatePattern('^/opt/myis/[A-Za-z0-9._/-]+$')] [string]$RemoteRoot = '/opt/myis/a1.2-v7',
    [ValidatePattern('^/opt/myis/[A-Za-z0-9._/-]+$')] [string]$SourceRemoteRoot = '/opt/myis/a1.2-v6',
    [string]$ReceiptPath = '', [switch]$DryRun
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'
if ($RemoteRoot.Contains('..') -or $SourceRemoteRoot.Contains('..') -or $RemoteRoot -eq $SourceRemoteRoot) {
    throw 'Remote roots must be distinct absolute /opt/myis paths without traversal.'
}
$PinnedImageReference = 'pytorch/pytorch:2.6.0-cuda11.8-cudnn9-runtime'
$PinnedManifestDigest = 'sha256:2428b92ebbaeceba5572b98c18c8a94e43162bead6e88588ad54471147c58a20'
if ($ImageReference -cne $PinnedImageReference) { throw 'ImageReference must equal the pinned direct-base image.' }
if ($ExpectedManifestDigest -cne $PinnedManifestDigest) { throw 'ExpectedManifestDigest must equal the pinned linux/amd64 OCI manifest digest.' }

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
$bundleActualSha256 = $null

switch ($Action) {
    'stage-repair' {
        if ($ExpectedGitCommit -notmatch '^[a-f0-9]{40,64}$') { throw 'ExpectedGitCommit is required and invalid.' }
        if ($ExpectedGitTree -notmatch '^[a-f0-9]{40,64}$') { throw 'ExpectedGitTree is required and invalid.' }
        if ($ExpectedBundleSha256 -notmatch '^[a-f0-9]{64}$') { throw 'ExpectedBundleSha256 is required and invalid.' }
        $bundle = Resolve-ExistingPath $BundlePath 'Frozen v7 code bundle' Leaf
        $bundleActualSha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $bundle).Hash.ToLowerInvariant()
        if ($bundleActualSha256 -cne $ExpectedBundleSha256) { throw 'Frozen v7 code bundle SHA-256 does not match ExpectedBundleSha256.' }
        $prepare = "set -eu; test ! -e ${RemoteRoot}; for arm in ARM-02 ARM-03 ARM-04 ARM-05; do test -f ${SourceRemoteRoot}/models/`$arm/SHA256SUMS; test -f ${SourceRemoteRoot}/models/`$arm/runtime-file-manifest.v4.json; test -f ${SourceRemoteRoot}/jobs/`$arm.json; done; test -f ${SourceRemoteRoot}/wheelhouse/SHA256SUMS; test -f ${SourceRemoteRoot}/supplement-wheelhouse-v7/supplement-wheelhouse-v7/SHA256SUMS; test -f ${SourceRemoteRoot}/supplement-wheelhouse-v7/supplement-wheelhouse-v7/SUPPLEMENT_VALIDATION.json; mkdir -p ${RemoteRoot}/incoming ${RemoteRoot}/current ${RemoteRoot}/models ${RemoteRoot}/wheelhouse ${RemoteRoot}/jobs ${RemoteRoot}/supplement-wheelhouse-v7 ${outputRoot}; cp -a ${SourceRemoteRoot}/models/. ${RemoteRoot}/models/; cp -a ${SourceRemoteRoot}/wheelhouse/. ${RemoteRoot}/wheelhouse/; cp -a ${SourceRemoteRoot}/jobs/. ${RemoteRoot}/jobs/; cp -a ${SourceRemoteRoot}/supplement-wheelhouse-v7/supplement-wheelhouse-v7/. ${RemoteRoot}/supplement-wheelhouse-v7/"
        Invoke-NativeSafe ssh ($ssh + @($target, $prepare)) | Out-Null
        Invoke-NativeSafe scp ($scp + @($bundle, "${target}:${RemoteRoot}/incoming/frozen-code-bundle.tar.gz")) | Out-Null
        $extract = "set -eu; tar --no-same-owner -xzf ${RemoteRoot}/incoming/frozen-code-bundle.tar.gz -C ${RemoteRoot}/current; test -f ${RemoteRoot}/current/BUNDLE_MANIFEST.json"
        Invoke-NativeSafe ssh ($ssh + @($target, $extract)) | Out-Null
    }
    'verify' {
        if ($ExpectedGitCommit -notmatch '^[a-f0-9]{40,64}$') { throw 'ExpectedGitCommit is required and invalid.' }
        if ($ExpectedGitTree -notmatch '^[a-f0-9]{40,64}$') { throw 'ExpectedGitTree is required and invalid.' }
        if ($ExpectedBundleSha256 -notmatch '^[a-f0-9]{64}$') { throw 'ExpectedBundleSha256 is required and invalid.' }
        $verify = "HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PIP_NO_INDEX=1 PYTHONDONTWRITEBYTECODE=1 MYIS_REMOTE_MODE=a1_2_preflight_only bash ${RemoteRoot}/current/scripts/a1_2_vast/remote-bootstrap-direct-base-v7.sh $ImageReference $RemoteRoot $ExpectedGitCommit $ExpectedGitTree $ExpectedManifestDigest $ExpectedBundleSha256"
        Invoke-NativeSafe ssh ($ssh + @($target, $verify)) | Out-Null
    }
    'start' {
        $launch = "HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PIP_NO_INDEX=1 PYTHONDONTWRITEBYTECODE=1 MYIS_REMOTE_MODE=a1_2_preflight_only bash ${RemoteRoot}/current/scripts/a1_2_vast/remote-live-preflight-v6.sh ${RemoteRoot} ${ExpectedManifestDigest}"
        Invoke-NativeSafe ssh ($ssh + @($target, $launch)) | Out-Null
    }
    'status' {
        $status = "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=${RemoteRoot}/current/src ${RemoteRoot}/venv/bin/python -m myis_research.armindex.a1_2_vast remote-status --output-root ${outputRoot}"
        Invoke-NativeSafe ssh ($ssh + @($target, $status)) | Out-Null
    }
    'collect' {
        $destination = Resolve-ExistingPath $CollectPath 'Collect path' Container
        $export = "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=${RemoteRoot}/current/src ${RemoteRoot}/venv/bin/python -m myis_research.armindex.a1_2_vast safe-export --output-root ${outputRoot} --allowlist ${RemoteRoot}/current/control/armindex/a1.2/safe-export-allowlist.v6.json --archive ${outputRoot}/safe-export.tar.gz"
        Invoke-NativeSafe ssh ($ssh + @($target, $export)) | Out-Null
        Invoke-NativeSafe scp ($scp + @("${target}:${outputRoot}/safe-export.tar.gz", $destination)) | Out-Null
    }
    'teardown' {
        $stop = "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=${RemoteRoot}/current/src ${RemoteRoot}/venv/bin/python -m myis_research.armindex.a1_2_vast guest-stop --output-root ${outputRoot}"
        Invoke-NativeSafe ssh ($ssh + @($target, $stop)) | Out-Null
    }
}

$receipt = [ordered]@{
    schema_version = 'myis.armindex-a1.2-direct-base-coordinator.v7'
    action = $Action
    status = $(if ($DryRun) { 'dry_run_validated' } else { 'completed' })
    repair_lineage = 'v6_model_wheelhouse_job_bytes_reused_on_same_instance'
    image_reference = $ImageReference
    expected_manifest_digest = $ExpectedManifestDigest
    expected_git_commit = $(if ([string]::IsNullOrWhiteSpace($ExpectedGitCommit)) { $null } else { $ExpectedGitCommit })
    expected_git_tree = $(if ([string]::IsNullOrWhiteSpace($ExpectedGitTree)) { $null } else { $ExpectedGitTree })
    expected_bundle_sha256 = $(if ([string]::IsNullOrWhiteSpace($ExpectedBundleSha256)) { $null } else { $ExpectedBundleSha256 })
    verified_local_bundle_sha256 = $bundleActualSha256
    remote_root = $RemoteRoot
    source_remote_root = $SourceRemoteRoot
    access_material_recorded = $false
    provider_destroyed = $false
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
