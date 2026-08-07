[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)] [ValidateSet('stage-repair', 'verify', 'start', 'status', 'collect', 'teardown')] [string]$Action,
    [Parameter(Mandatory = $true)] [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9.-]{0,252}$')] [string]$HostName,
    [Parameter(Mandatory = $true)] [ValidateRange(1, 65535)] [int]$Port,
    [Parameter(Mandatory = $true)] [ValidatePattern('^[A-Za-z_][A-Za-z0-9_-]{0,31}$')] [string]$UserName,
    [Parameter(Mandatory = $true)] [string]$KeyPath,
    [string]$BundlePath = '',
    [string]$ExpectedBundleSha256 = '',
    [string]$ExpectedGitCommit = '',
    [string]$ExpectedGitTree = '',
    [string]$ImageReference = 'pytorch/pytorch:2.6.0-cuda11.8-cudnn9-runtime',
    [string]$ExpectedManifestDigest = 'sha256:2428b92ebbaeceba5572b98c18c8a94e43162bead6e88588ad54471147c58a20',
    [ValidatePattern('^/opt/myis/[A-Za-z0-9][A-Za-z0-9._-]{0,63}$')] [string]$RemoteRoot = '/opt/myis/a1.2-v9',
    [ValidatePattern('^/opt/myis/[A-Za-z0-9][A-Za-z0-9._-]{0,63}$')] [string]$SourceRemoteRoot = '/opt/myis/a1.2-v7',
    [ValidatePattern('^[a-z0-9][a-z0-9._-]{2,79}$')] [string]$AttemptId = '',
    [string]$CollectPath = '',
    [string]$ReceiptPath = '',
    [switch]$DryRun
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'

$PinnedImageReference = 'pytorch/pytorch:2.6.0-cuda11.8-cudnn9-runtime'
$PinnedManifestDigest = 'sha256:2428b92ebbaeceba5572b98c18c8a94e43162bead6e88588ad54471147c58a20'
if ($RemoteRoot -eq $SourceRemoteRoot) { throw 'RemoteRoot and SourceRemoteRoot must be distinct fresh /opt/myis roots.' }
if ($ImageReference -cne $PinnedImageReference) { throw 'ImageReference must equal the pinned direct-base image.' }
if ($ExpectedManifestDigest -cne $PinnedManifestDigest) { throw 'ExpectedManifestDigest must equal the pinned linux/amd64 OCI manifest digest.' }

function Resolve-ExistingPath {
    param([string]$Value, [string]$Label, [ValidateSet('Leaf', 'Container')][string]$Kind)
    if ([string]::IsNullOrWhiteSpace($Value)) { throw "$Label is required." }
    if (-not (Test-Path -LiteralPath $Value -PathType $Kind)) { throw "$Label is missing: $Value" }
    return (Resolve-Path -LiteralPath $Value).ProviderPath
}

function Assert-FrozenIdentity {
    if ($ExpectedGitCommit -notmatch '^[a-f0-9]{40,64}$') { throw 'ExpectedGitCommit is required and invalid.' }
    if ($ExpectedGitTree -notmatch '^[a-f0-9]{40,64}$') { throw 'ExpectedGitTree is required and invalid.' }
    if ($ExpectedBundleSha256 -notmatch '^[a-f0-9]{64}$') { throw 'ExpectedBundleSha256 is required and invalid.' }
}

function Assert-AttemptId {
    if ([string]::IsNullOrWhiteSpace($AttemptId)) { throw 'AttemptId is required for this action.' }
}

function Invoke-NativeSafe {
    param([string]$Executable, [string[]]$Arguments)
    if ($DryRun) { return @() }
    $output = @(& $Executable @Arguments)
    if ($LASTEXITCODE -ne 0) { throw "$Executable failed with exit code $LASTEXITCODE." }
    return $output
}

function Test-SafeLocalTar {
    param([string]$ArchivePath)
    $entries = Invoke-NativeSafe tar @('-tzf', $ArchivePath)
    foreach ($entry in $entries) {
        if ([string]::IsNullOrWhiteSpace($entry) -or $entry.StartsWith('/') -or $entry -eq '..' -or $entry.StartsWith('../') -or $entry.Contains('/../')) {
            throw "Unsafe archive member path: $entry"
        }
    }
    $verbose = Invoke-NativeSafe tar @('-tvzf', $ArchivePath)
    foreach ($line in $verbose) {
        if ([string]::IsNullOrWhiteSpace($line) -or $line[0] -ne '-') {
            throw 'Archive contains a non-regular member.'
        }
    }
}

function Test-V9Export {
    param([string]$ArchivePath)
    Test-SafeLocalTar $ArchivePath
    Invoke-NativeSafe uv @(
        'run', '--no-sync', 'python', '-m',
        'myis_research.armindex.a1_2_live_preflight_runtime_v9',
        'validate-export', '--archive', $ArchivePath
    ) | Out-Null
}

$key = Resolve-ExistingPath $KeyPath 'SSH key' Leaf
$target = "$UserName@$HostName"
$ssh = @('-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-p', "$Port", '-i', $key)
$scp = @('-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-P', "$Port", '-i', $key)
$outputRoot = "$RemoteRoot/output"
$marker = "$outputRoot/preflight/verification-pass.v9.json"
$localBundleSha256 = $null
$actionOutput = @()

switch ($Action) {
    'stage-repair' {
        Assert-FrozenIdentity
        $bundle = Resolve-ExistingPath $BundlePath 'Frozen v9 code bundle' Leaf
        $localBundleSha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $bundle).Hash.ToLowerInvariant()
        if ($localBundleSha256 -cne $ExpectedBundleSha256) { throw 'Frozen v9 code bundle SHA-256 does not match ExpectedBundleSha256.' }
        Test-SafeLocalTar $bundle
        $prepare = "set -eu; test ! -e $RemoteRoot; for arm in ARM-02 ARM-03 ARM-04 ARM-05; do test -f $SourceRemoteRoot/models/`$arm/SHA256SUMS; test -f $SourceRemoteRoot/models/`$arm/runtime-file-manifest.v4.json; test -f $SourceRemoteRoot/jobs/`$arm.json; done; test -f $SourceRemoteRoot/wheelhouse/SHA256SUMS; test -f $SourceRemoteRoot/supplement-wheelhouse-v7/SHA256SUMS; mkdir -p $RemoteRoot/incoming $RemoteRoot/current $RemoteRoot/models $RemoteRoot/wheelhouse $RemoteRoot/jobs $RemoteRoot/supplement-wheelhouse-v7 $outputRoot; cp -a $SourceRemoteRoot/models/. $RemoteRoot/models/; cp -a $SourceRemoteRoot/wheelhouse/. $RemoteRoot/wheelhouse/; cp -a $SourceRemoteRoot/jobs/. $RemoteRoot/jobs/; cp -a $SourceRemoteRoot/supplement-wheelhouse-v7/. $RemoteRoot/supplement-wheelhouse-v7/"
        Invoke-NativeSafe ssh ($ssh + @($target, $prepare)) | Out-Null
        Invoke-NativeSafe scp ($scp + @($bundle, "${target}:${RemoteRoot}/incoming/frozen-code-bundle.tar.gz")) | Out-Null

        # Validate archive bytes and members before tar is permitted to write the fresh root.
        $extract = "set -eu; archive=$RemoteRoot/incoming/frozen-code-bundle.tar.gz; actual=`$(sha256sum -- `"`$archive`" | awk '{print `$1}'); test `"`$actual`" = `"$ExpectedBundleSha256`"; python - `"`$archive`" <<'PY'`nimport sys, tarfile`nfrom pathlib import PurePosixPath`nwith tarfile.open(sys.argv[1], 'r:gz') as archive:`n    for member in archive.getmembers():`n        path = PurePosixPath(member.name)`n        if not member.isreg() or path.is_absolute() or '..' in path.parts or not member.name or member.name.startswith('./'):`n            raise SystemExit('unsafe tar member: ' + member.name)`nPY`ntar --no-same-owner --no-same-permissions --numeric-owner -xzf `"`$archive`" -C $RemoteRoot/current; test -f $RemoteRoot/current/BUNDLE_MANIFEST.json"
        $actionOutput = Invoke-NativeSafe ssh ($ssh + @($target, $extract))
    }
    'verify' {
        Assert-FrozenIdentity
        # The v9 bootstrap rechecks archive bytes before using any bundled Python.
        $verify = "HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PIP_NO_INDEX=1 PYTHONDONTWRITEBYTECODE=1 MYIS_REMOTE_MODE=a1_2_preflight_only bash $RemoteRoot/current/scripts/a1_2_vast/remote-bootstrap-direct-base-v9.sh $ImageReference $RemoteRoot $ExpectedGitCommit $ExpectedGitTree $ExpectedManifestDigest $ExpectedBundleSha256"
        $actionOutput = Invoke-NativeSafe ssh ($ssh + @($target, $verify))
    }
    'start' {
        Assert-FrozenIdentity
        Assert-AttemptId
        $launch = "HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PIP_NO_INDEX=1 PYTHONDONTWRITEBYTECODE=1 MYIS_REMOTE_MODE=a1_2_preflight_only PYTHONPATH=$RemoteRoot/current/src $RemoteRoot/venv/bin/python -m myis_research.armindex.a1_2_live_preflight_runtime_v9 validate-verification-marker --marker $marker --expected-commit $ExpectedGitCommit --expected-tree $ExpectedGitTree --expected-manifest-digest $ExpectedManifestDigest --expected-bundle-sha256 $ExpectedBundleSha256 && HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PIP_NO_INDEX=1 PYTHONDONTWRITEBYTECODE=1 MYIS_REMOTE_MODE=a1_2_preflight_only bash $RemoteRoot/current/scripts/a1_2_vast/remote-live-preflight-v9.sh $RemoteRoot $ExpectedManifestDigest $AttemptId"
        $actionOutput = Invoke-NativeSafe ssh ($ssh + @($target, $launch))
    }
    'status' {
        Assert-AttemptId
        $status = "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$RemoteRoot/current/src $RemoteRoot/venv/bin/python -m myis_research.armindex.a1_2_live_preflight_runtime_v9 status --output-root $outputRoot --attempt-id $AttemptId --marker $marker"
        $actionOutput = Invoke-NativeSafe ssh ($ssh + @($target, $status))
    }
    'collect' {
        Assert-FrozenIdentity
        Assert-AttemptId
        $destination = Resolve-ExistingPath $CollectPath 'Collect path' Container
        $remoteArchive = "$outputRoot/exports/$AttemptId.safe-export.tar.gz"
        $finalArchive = Join-Path $destination "a1.2-v9-$AttemptId-safe-export.tar.gz"
        $partialArchive = "$finalArchive.partial"
        $export = "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$RemoteRoot/current/src $RemoteRoot/venv/bin/python -m myis_research.armindex.a1_2_live_preflight_runtime_v9 validate-verification-marker --marker $marker --expected-commit $ExpectedGitCommit --expected-tree $ExpectedGitTree --expected-manifest-digest $ExpectedManifestDigest --expected-bundle-sha256 $ExpectedBundleSha256 && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$RemoteRoot/current/src $RemoteRoot/venv/bin/python -m myis_research.armindex.a1_2_live_preflight_runtime_v9 status --output-root $outputRoot --attempt-id $AttemptId --marker $marker --require-pass && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$RemoteRoot/current/src $RemoteRoot/venv/bin/python -m myis_research.armindex.a1_2_live_preflight_runtime_v9 safe-export --output-root $outputRoot --attempt-id $AttemptId --marker $marker --archive $remoteArchive"
        Invoke-NativeSafe ssh ($ssh + @($target, $export)) | Out-Null
        if ($DryRun) {
            $actionOutput = @('dry_run_collect_validation_complete')
            break
        }
        $remoteShaLine = Invoke-NativeSafe ssh ($ssh + @($target, "sha256sum -- $remoteArchive"))
        $remoteSha = (($remoteShaLine -join "`n") -split '\s+')[0].ToLowerInvariant()
        if ($remoteSha -notmatch '^[a-f0-9]{64}$') { throw 'Remote safe-export SHA-256 is malformed.' }
        if (Test-Path -LiteralPath $finalArchive -PathType Leaf) {
            $existingSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $finalArchive).Hash.ToLowerInvariant()
            if ($existingSha -cne $remoteSha) { throw 'Existing collected archive conflicts with the remote attempt SHA-256.' }
            Test-V9Export $finalArchive
            $actionOutput = @("retry_safe_existing_archive_sha256=$remoteSha")
            break
        }
        if (Test-Path -LiteralPath $partialArchive) { throw "Retry-safe collection found an unresolved partial archive: $partialArchive" }
        Invoke-NativeSafe scp ($scp + @("${target}:${remoteArchive}", $partialArchive)) | Out-Null
        $localSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $partialArchive).Hash.ToLowerInvariant()
        if ($localSha -cne $remoteSha) { throw 'Collected archive SHA-256 differs from the remote safe export.' }
        Test-V9Export $partialArchive
        Move-Item -LiteralPath $partialArchive -Destination $finalArchive
        $actionOutput = @("collected_archive_sha256=$remoteSha", "collected_archive=$finalArchive")
    }
    'teardown' {
        Assert-AttemptId
        # The v9 module owns process-creation identity matching; this is never provider destruction.
        $stop = "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$RemoteRoot/current/src $RemoteRoot/venv/bin/python -m myis_research.armindex.a1_2_live_preflight_runtime_v9 teardown --output-root $outputRoot --attempt-id $AttemptId --marker $marker --children-reaped"
        $actionOutput = Invoke-NativeSafe ssh ($ssh + @($target, $stop))
    }
}

$receipt = [ordered]@{
    schema_version = 'myis.armindex-a1.2-direct-base-coordinator.v9'
    action = $Action
    status = $(if ($DryRun) { 'dry_run_validated' } else { 'completed' })
    remote_root = $RemoteRoot
    source_remote_root = $SourceRemoteRoot
    attempt_id = $(if ([string]::IsNullOrWhiteSpace($AttemptId)) { $null } else { $AttemptId })
    image_reference = $ImageReference
    expected_manifest_digest = $ExpectedManifestDigest
    expected_git_commit = $(if ([string]::IsNullOrWhiteSpace($ExpectedGitCommit)) { $null } else { $ExpectedGitCommit })
    expected_git_tree = $(if ([string]::IsNullOrWhiteSpace($ExpectedGitTree)) { $null } else { $ExpectedGitTree })
    expected_bundle_sha256 = $(if ([string]::IsNullOrWhiteSpace($ExpectedBundleSha256)) { $null } else { $ExpectedBundleSha256 })
    verified_local_bundle_sha256 = $localBundleSha256
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
