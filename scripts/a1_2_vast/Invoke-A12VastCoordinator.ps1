[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('upload', 'verify', 'start', 'status', 'collect', 'teardown')]
    [string]$Action,

    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9.-]{0,252}$')]
    [string]$HostName,

    [Parameter(Mandatory = $true)]
    [ValidateRange(1, 65535)]
    [int]$Port,

    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[A-Za-z_][A-Za-z0-9_-]{0,31}$')]
    [string]$UserName,

    [Parameter(Mandatory = $true)]
    [string]$KeyPath,

    [string]$BundlePath = '',
    [string]$ImageArchivePath = '',
    [string]$ImageReference = '',
    [string]$CollectPath = '',
    [string]$ExpectedGitCommit = '',
    [string]$ExpectedGitTree = '',
    [string]$ExpectedImageDigest = '',
    [ValidatePattern('^/opt/myis/[A-Za-z0-9._/-]+$')]
    [string]$RemoteRoot = '/opt/myis/a1.2-v2',
    [string]$ReceiptPath = '',
    [switch]$DryRun
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'

if ($RemoteRoot.Contains('..')) {
    throw 'RemoteRoot must not contain parent traversal.'
}

function Resolve-Leaf {
    param([string]$Value, [string]$Label)
    if ([string]::IsNullOrWhiteSpace($Value) -or -not (Test-Path -LiteralPath $Value -PathType Leaf)) {
        throw "$Label is missing: $Value"
    }
    return (Resolve-Path -LiteralPath $Value).ProviderPath
}

function Invoke-NativeSafe {
    param([string]$Executable, [string[]]$Arguments)
    if ($DryRun) { return @() }
    $nativeOutput = @(& $Executable @Arguments)
    $nativeExitCode = $LASTEXITCODE
    if ($nativeExitCode -ne 0) {
        throw "$Executable failed with exit code $nativeExitCode."
    }
    return $nativeOutput
}

$resolvedKey = Resolve-Leaf -Value $KeyPath -Label 'SSH key'
$target = "$UserName@$HostName"
$sshCommon = @('-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-p', "$Port", '-i', $resolvedKey)
$scpCommon = @('-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-P', "$Port", '-i', $resolvedKey)
$startedAt = [DateTime]::UtcNow.ToString('o')
$remoteStatus = $null

switch ($Action) {
    'upload' {
        $resolvedBundle = Resolve-Leaf -Value $BundlePath -Label 'Frozen bundle'
        $resolvedImageArchive = Resolve-Leaf -Value $ImageArchivePath -Label 'Frozen image archive'
        if ($ImageReference -notmatch '^[A-Za-z0-9._/-]+:[A-Za-z0-9._-]+$') { throw 'ImageReference is invalid.' }
        $prepareCommand = "set -e; mkdir -p ${RemoteRoot}/incoming ${RemoteRoot}/models ${RemoteRoot}/output; test ! -e ${RemoteRoot}/current; mkdir ${RemoteRoot}/current"
        Invoke-NativeSafe -Executable 'ssh' -Arguments ($sshCommon + @($target, $prepareCommand)) | Out-Null
        Invoke-NativeSafe -Executable 'scp' -Arguments ($scpCommon + @($resolvedBundle, "${target}:${RemoteRoot}/incoming/frozen-bundle.tar.gz")) | Out-Null
        Invoke-NativeSafe -Executable 'scp' -Arguments ($scpCommon + @($resolvedImageArchive, "${target}:${RemoteRoot}/incoming/runtime-image.tar")) | Out-Null
        $extractCommand = "set -e; tar --no-same-owner -xzf ${RemoteRoot}/incoming/frozen-bundle.tar.gz -C ${RemoteRoot}/current; test -f ${RemoteRoot}/current/BUNDLE_MANIFEST.json; docker load --input ${RemoteRoot}/incoming/runtime-image.tar >/dev/null; docker image inspect $ImageReference >/dev/null"
        Invoke-NativeSafe -Executable 'ssh' -Arguments ($sshCommon + @($target, $extractCommand)) | Out-Null
    }
    'verify' {
        if ($ExpectedGitCommit -notmatch '^[a-f0-9]{40,64}$') { throw 'ExpectedGitCommit is required and invalid.' }
        if ($ExpectedGitTree -notmatch '^[a-f0-9]{40,64}$') { throw 'ExpectedGitTree is required and invalid.' }
        if ($ExpectedImageDigest -notmatch '^sha256:[a-f0-9]{64}$') { throw 'ExpectedImageDigest is required and invalid.' }
        if ($ImageReference -notmatch '^[A-Za-z0-9._/-]+:[A-Za-z0-9._-]+$') { throw 'ImageReference is invalid.' }
        $verifyCommand = "MYIS_REMOTE_MODE=a1_2_preflight_only bash ${RemoteRoot}/current/scripts/a1_2_vast/remote-bootstrap.sh $ImageReference ${RemoteRoot}/current ${RemoteRoot}/output ${RemoteRoot}/models $ExpectedGitCommit $ExpectedGitTree $ExpectedImageDigest"
        Invoke-NativeSafe -Executable 'ssh' -Arguments ($sshCommon + @($target, $verifyCommand)) | Out-Null
    }
    'start' {
        if ($ImageReference -notmatch '^[A-Za-z0-9._/-]+:[A-Za-z0-9._-]+$') { throw 'ImageReference is invalid.' }
        if ($ExpectedImageDigest -notmatch '^sha256:[a-f0-9]{64}$') { throw 'ExpectedImageDigest is required and invalid.' }
        $launchCommand = "PYTHONPATH=${RemoteRoot}/current/src MYIS_REMOTE_MODE=a1_2_preflight_only python -m myis_research.armindex.a1_2_vast launch-detached --bundle-root ${RemoteRoot}/current --output-root ${RemoteRoot}/output --image-reference $ImageReference --image-digest $ExpectedImageDigest"
        Invoke-NativeSafe -Executable 'ssh' -Arguments ($sshCommon + @($target, $launchCommand)) | Out-Null
    }
    'status' {
        $statusCommand = "PYTHONPATH=${RemoteRoot}/current/src python -m myis_research.armindex.a1_2_vast remote-status --output-root ${RemoteRoot}/output"
        $statusText = (Invoke-NativeSafe -Executable 'ssh' -Arguments ($sshCommon + @($target, $statusCommand))) -join "`n"
        if (-not $DryRun -and -not [string]::IsNullOrWhiteSpace($statusText)) {
            $remoteStatus = $statusText | ConvertFrom-Json
        }
    }
    'collect' {
        if ([string]::IsNullOrWhiteSpace($CollectPath)) { throw 'CollectPath is required for collect.' }
        $resolvedCollectRoot = [IO.Path]::GetFullPath($CollectPath)
        if (-not (Test-Path -LiteralPath $resolvedCollectRoot -PathType Container)) {
            throw "CollectPath is missing: $CollectPath"
        }
        Invoke-NativeSafe -Executable 'scp' -Arguments ($scpCommon + @("${target}:${RemoteRoot}/output/safe-export.tar.gz", $resolvedCollectRoot)) | Out-Null
    }
    'teardown' {
        # This stops guest work only. Provider destruction is Owner-local and
        # belongs to Invoke-A12VastWatchdog.ps1.
        $stopCommand = "PYTHONPATH=${RemoteRoot}/current/src python -m myis_research.armindex.a1_2_vast guest-stop --output-root ${RemoteRoot}/output"
        Invoke-NativeSafe -Executable 'ssh' -Arguments ($sshCommon + @($target, $stopCommand)) | Out-Null
    }
}

$receipt = [ordered]@{
    schema_version = 'myis.armindex-a1.2-local-coordinator-action.v2'
    action = $Action
    status = $(if ($DryRun) { 'dry_run_validated' } else { 'completed' })
    started_at = $startedAt
    completed_at = [DateTime]::UtcNow.ToString('o')
    host_sha256 = ([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash([Text.Encoding]::UTF8.GetBytes($HostName))).Replace('-', '').ToLowerInvariant())
    port = $Port
    remote_root = $RemoteRoot
    access_material_recorded = $false
    provider_destroyed = $false
    guest_teardown_only = ($Action -eq 'teardown')
    remote_status = $remoteStatus
}

if (-not [string]::IsNullOrWhiteSpace($ReceiptPath)) {
    $receiptTarget = [IO.Path]::GetFullPath($ReceiptPath)
    $parent = Split-Path -Parent $receiptTarget
    if (-not (Test-Path -LiteralPath $parent -PathType Container)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
    $utf8NoBom = New-Object Text.UTF8Encoding($false)
    [IO.File]::WriteAllText($receiptTarget, (($receipt | ConvertTo-Json -Depth 8) + "`n"), $utf8NoBom)
}

$receipt | ConvertTo-Json -Depth 8
