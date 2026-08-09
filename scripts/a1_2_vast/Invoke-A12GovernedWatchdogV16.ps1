[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][int]$InstanceId,
    [Parameter(Mandatory = $true)][string]$SshHost,
    [Parameter(Mandatory = $true)][int]$SshPort,
    [Parameter(Mandatory = $true)][string]$SshKeyPath,
    [Parameter(Mandatory = $true)][string]$OwnerConnectionFile,
    [Parameter(Mandatory = $true)][string]$OutputDirectory,
    [Parameter(Mandatory = $true)][datetime]$TtlDeadlineUtc,
    [Parameter(Mandatory = $true)][string]$ExpectedHostname,
    [Parameter(Mandatory = $true)][string]$ExpectedInstanceIdentitySha256,
    [Parameter(Mandatory = $true)][string]$ExpectedGpuUuidSetSha256,
    [Parameter(Mandatory = $true)][decimal]$MaximumTotalHourlyUsd,
    [Parameter(Mandatory = $true)][string]$VastCliPath,
    [int]$IntervalSeconds = 30
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
if ($IntervalSeconds -lt 10 -or $IntervalSeconds -gt 300) { throw 'IntervalSeconds must be between 10 and 300.' }
$ssh = 'C:\Windows\System32\OpenSSH\ssh.exe'
$sshKeyscan = 'C:\Windows\System32\OpenSSH\ssh-keyscan.exe'
$sshKeygen = 'C:\Windows\System32\OpenSSH\ssh-keygen.exe'
foreach ($path in @($ssh, $sshKeyscan, $sshKeygen, $SshKeyPath, $OwnerConnectionFile, $VastCliPath)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Required watchdog input is unavailable: $path" }
}
if ($ExpectedInstanceIdentitySha256 -notmatch '^[0-9a-f]{64}$' -or $ExpectedGpuUuidSetSha256 -notmatch '^[0-9a-f]{64}$') {
    throw 'Expected identity commitments must be lowercase SHA-256 values.'
}
$output = [IO.Path]::GetFullPath($OutputDirectory)
[IO.Directory]::CreateDirectory($output) | Out-Null
$lockPath = Join-Path $output 'watchdog.lock'
$heartbeatPath = Join-Path $output 'heartbeat.json'
$stopPath = Join-Path $output 'stop.requested'
$knownHostsPath = Join-Path $output 'attempt-known_hosts'
$lockStream = [IO.File]::Open($lockPath, [IO.FileMode]::OpenOrCreate, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)

function Get-Sha256Text([string]$Value) {
    $sha = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($Value)))).Replace('-', '').ToLowerInvariant() }
    finally { $sha.Dispose() }
}

function Get-OwnerFingerprint {
    $text = [IO.File]::ReadAllText([IO.Path]::GetFullPath($OwnerConnectionFile))
    $values = [regex]::Matches($text, 'SHA256:[A-Za-z0-9+/=]+') | ForEach-Object { $_.Value } | Select-Object -Unique
    if (@($values).Count -ne 1) { throw 'owner_fingerprint_pin_invalid' }
    return [string]$values[0]
}

function Ensure-HostKeyPin {
    $script:HostKeyStage = 'read_owner_pin'
    $expected = Get-OwnerFingerprint
    $script:HostKeyStage = 'keyscan'
    $raw = & $sshKeyscan -T 10 -p $SshPort -t ed25519 $SshHost 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $raw) { throw 'ssh_keyscan_failed' }
    $line = ($raw -join "`n")
    $script:HostKeyStage = 'fingerprint'
    $observedLine = ($raw | & $sshKeygen -lf - -E sha256 2>$null | Out-String)
    $observed = ([regex]::Match($observedLine, 'SHA256:[A-Za-z0-9+/=]+')).Value
    if (-not $observed -or $observed -ne $expected) { throw 'ssh_fingerprint_mismatch' }
    $script:HostKeyStage = 'known_hosts'
    if (Test-Path -LiteralPath $knownHostsPath -PathType Leaf) {
        if (([IO.File]::ReadAllText($knownHostsPath)) -ne $line.TrimEnd() + "`n") { throw 'ssh_known_hosts_pin_drift' }
    }
    else {
        [IO.File]::WriteAllText($knownHostsPath, $line.TrimEnd() + "`n", [Text.UTF8Encoding]::new($false))
    }
}

function Invoke-PinnedSsh([string]$Command) {
    & $ssh -i $SshKeyPath -p $SshPort -o BatchMode=yes -o ConnectTimeout=12 -o StrictHostKeyChecking=yes -o UserKnownHostsFile=$knownHostsPath -o LogLevel=ERROR "root@$SshHost" $Command
    if ($LASTEXITCODE -ne 0) { throw 'ssh_runtime_probe_failed' }
}

function Write-Heartbeat([string]$Status, [string]$Reason, [bool]$ProviderOk, [decimal]$Rate) {
    $now = [DateTime]::UtcNow
    $process = Get-Process -Id $PID
    $body = [ordered]@{
        schema_version = 'myis.armindex-a1.2-governed-watchdog.v16'; status = $Status
        generated_at_utc = $now.ToString('o'); process_id = $PID
        process_created_at_utc = $process.StartTime.ToUniversalTime().ToString('o')
        instance_id = $InstanceId; instance_identity_sha256 = $ExpectedInstanceIdentitySha256
        provider_status_match = $ProviderOk; quote_total_hourly_usd = $Rate
        ttl_deadline_utc = $TtlDeadlineUtc.ToUniversalTime().ToString('o')
        ttl_remaining_seconds = [math]::Max(0, [math]::Floor(($TtlDeadlineUtc.ToUniversalTime() - $now).TotalSeconds))
        hard_stop_reason = $Reason; provider_destroy_invoked = $false; access_material_recorded = $false
    }
    $unsigned = $body | ConvertTo-Json -Depth 4 -Compress
    $signed = [ordered]@{}; foreach ($key in $body.Keys) { $signed[$key] = $body[$key] }
    $signed['heartbeat_sha256'] = Get-Sha256Text $unsigned
    $temporary = "$heartbeatPath.$PID.tmp"
    [IO.File]::WriteAllText($temporary, ($signed | ConvertTo-Json -Depth 4), [Text.UTF8Encoding]::new($false))
    Move-Item -LiteralPath $temporary -Destination $heartbeatPath -Force
}

try {
    while ($true) {
        $reason = $null; $providerOk = $false; $rate = [decimal]0; $probeStage = 'host_key'
        try {
            if (Test-Path -LiteralPath $stopPath) { $reason = 'owner_local_stop_requested' }
            elseif ([DateTime]::UtcNow -ge $TtlDeadlineUtc.ToUniversalTime()) { $reason = 'ttl_expired' }
            else {
                Ensure-HostKeyPin
                $probeStage = 'ssh_runtime'
                $runtimeProbe = @'
PYTHONDONTWRITEBYTECODE=1 python - <<'PY'
import platform, torch
assert platform.machine() == 'x86_64'
assert torch.cuda.is_available()
assert torch.cuda.device_count() == 4
print('runtime_probe_ok')
PY
'@
                $runtime = Invoke-PinnedSsh $runtimeProbe
                $probeStage = 'provider'
                $raw = & $VastCliPath vastai show instance $InstanceId --raw 2>$null
                if ($LASTEXITCODE -ne 0 -or -not $raw) { throw 'provider_query_failed' }
                $provider = (($raw -join "`n") | ConvertFrom-Json)
                if ($provider -is [array]) { $provider = $provider[0] }
                $providerOk = ([int]$provider.id -eq $InstanceId -and $provider.actual_status -eq 'running' -and $provider.intended_status -eq 'running' -and $provider.verification -eq 'verified')
                $rate = [decimal]$provider.dph_total
                if (-not $providerOk) { $reason = 'provider_identity_or_status_mismatch' }
                elseif ($rate -gt $MaximumTotalHourlyUsd) { $reason = 'provider_quote_increased' }
            }
        }
        catch {
            if (-not $reason) {
                $message = [string]$_.Exception.Message
                $knownReasons = @(
                    'ssh_keyscan_failed', 'ssh_fingerprint_mismatch', 'ssh_known_hosts_pin_drift',
                    'owner_fingerprint_pin_invalid', 'ssh_runtime_probe_failed', 'provider_query_failed'
                )
                $reason = ($knownReasons | Where-Object { $message -like "*$_*" } | Select-Object -First 1)
                if (-not $reason -and $probeStage -eq 'host_key') { $reason = "watchdog_host_key_${script:HostKeyStage}_failed" }
                if (-not $reason) { $reason = "watchdog_${probeStage}_failed" }
            }
        }
        if ($reason) { Write-Heartbeat 'HARD_STOP' $reason $providerOk $rate; break }
        Write-Heartbeat 'PASS' $null $providerOk $rate
        Start-Sleep -Seconds $IntervalSeconds
    }
}
finally { $lockStream.Dispose() }
