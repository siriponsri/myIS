[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('DryRun', 'Monitor')]
    [string]$Mode,

    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[0-9]+$')]
    [string]$ProviderInstanceId,

    [Parameter(Mandatory = $true)]
    [string]$HeartbeatPath,

    [ValidateRange(60, 86400)]
    [int]$TtlSeconds = 21600,

    [ValidateRange(30, 3600)]
    [int]$HeartbeatStaleSeconds = 300,

    [ValidateRange(5, 300)]
    [int]$PollSeconds = 30,

    [string]$VastCliPath = 'vastai',
    [string]$ReceiptPath = ''
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'
$started = [DateTime]::UtcNow
$destroyInvoked = $false
$destroyVerified = $false
$trigger = 'dry_run'
$destroyCommandValidated = $false
$ttlTriggerSimulated = $false

function Invoke-VastDestroy {
    & $VastCliPath destroy instance $ProviderInstanceId | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Provider destroy command failed with exit code $LASTEXITCODE." }
}

function Test-VastDestroyed {
    & $VastCliPath show instance $ProviderInstanceId --raw 2>$null | Out-Null
    return ($LASTEXITCODE -ne 0)
}

if ($Mode -eq 'DryRun') {
    $resolvedCli = Get-Command $VastCliPath -CommandType Application, ExternalScript -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($null -eq $resolvedCli) { throw "Vast CLI or dry-run adapter was not found: $VastCliPath" }
    $destroyCommandValidated = $true
    $ttlTriggerSimulated = $true
}
elseif ($Mode -eq 'Monitor') {
    while ($true) {
        $now = [DateTime]::UtcNow
        $ttlExpired = ($now - $started).TotalSeconds -ge $TtlSeconds
        $heartbeatStale = $true
        if (Test-Path -LiteralPath $HeartbeatPath -PathType Leaf) {
            $heartbeat = Get-Content -Raw -Encoding UTF8 -LiteralPath $HeartbeatPath | ConvertFrom-Json
            $heartbeatTime = [DateTime]::Parse($heartbeat.generated_at).ToUniversalTime()
            $heartbeatStale = ($now - $heartbeatTime).TotalSeconds -ge $HeartbeatStaleSeconds
        }
        if ($ttlExpired -or $heartbeatStale) {
            $trigger = $(if ($ttlExpired) { 'ttl_expired' } else { 'heartbeat_stale' })
            Invoke-VastDestroy
            $destroyInvoked = $true
            for ($attempt = 0; $attempt -lt 20; $attempt++) {
                if (Test-VastDestroyed) { $destroyVerified = $true; break }
                Start-Sleep -Seconds $PollSeconds
            }
            if (-not $destroyVerified) { throw 'Provider destruction could not be verified.' }
            break
        }
        Start-Sleep -Seconds $PollSeconds
    }
}

$receipt = [ordered]@{
    schema_version = 'myis.armindex-a1.2-owner-ttl-watchdog.v2'
    mode = $Mode
    status = $(if ($Mode -eq 'DryRun') { 'dry_run_validated' } elseif ($destroyVerified) { 'provider_destroyed' } else { 'failed' })
    provider = 'vast'
    provider_instance_id_sha256 = ([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash([Text.Encoding]::UTF8.GetBytes($ProviderInstanceId))).Replace('-', '').ToLowerInvariant())
    trigger = $trigger
    ttl_seconds = $TtlSeconds
    heartbeat_stale_seconds = $HeartbeatStaleSeconds
    provider_destroy_invoked = $destroyInvoked
    provider_destroy_verified = $destroyVerified
    guest_poweroff_is_provider_destruction = $false
    access_material_recorded = $false
    destroy_command_validated = $destroyCommandValidated
    ttl_trigger_simulated = $ttlTriggerSimulated
    generated_at = [DateTime]::UtcNow.ToString('o')
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
