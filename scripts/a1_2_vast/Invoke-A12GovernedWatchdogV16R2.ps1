[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][int]$InstanceId,
    [Parameter(Mandatory = $true)][string]$SshHost,
    [Parameter(Mandatory = $true)][int]$SshPort,
    [Parameter(Mandatory = $true)][string]$SshKeyPath,
    [Parameter(Mandatory = $true)][string]$OwnerConnectionFile,
    [Parameter(Mandatory = $true)][string]$OutputDirectory,
    [string]$KnownHostsPath = '',
    [Parameter(Mandatory = $true)][datetime]$TtlDeadlineUtc,
    [Parameter(Mandatory = $true)][string]$ExpectedHostname,
    [Parameter(Mandatory = $true)][string]$ExpectedInstanceIdentitySha256,
    [Parameter(Mandatory = $true)][string]$ExpectedGpuUuidSetSha256,
    [Parameter(Mandatory = $true)][decimal]$MaximumTotalHourlyUsd,
    [ValidateSet('AuthenticatedCli', 'OwnerDashboardSsh')][string]$ProviderObservationMode = 'AuthenticatedCli',
    [string]$VastCliPath = '',
    [decimal]$OwnerDashboardTotalHourlyUsd = -1,
    [string]$OwnerDashboardEvidenceSha256 = '',
    [switch]$OwnerManualDestroyReady,
    [int]$IntervalSeconds = 30,
    [int]$RuntimeProbeTimeoutSeconds = 45,
    [string]$SshExecutablePath = ''
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
if ($IntervalSeconds -lt 10 -or $IntervalSeconds -gt 300) { throw 'IntervalSeconds must be between 10 and 300.' }
$ssh = if ($SshExecutablePath) { [IO.Path]::GetFullPath($SshExecutablePath) } else { 'C:\Windows\System32\OpenSSH\ssh.exe' }
$sshKeyscan = 'C:\Windows\System32\OpenSSH\ssh-keyscan.exe'
$sshKeygen = 'C:\Windows\System32\OpenSSH\ssh-keygen.exe'
$taskKill = 'C:\Windows\System32\taskkill.exe'
if ($RuntimeProbeTimeoutSeconds -lt 1 -or $RuntimeProbeTimeoutSeconds -gt 300) { throw 'RuntimeProbeTimeoutSeconds must be between 1 and 300.' }
foreach ($path in @($ssh, $sshKeyscan, $sshKeygen, $taskKill, $SshKeyPath, $OwnerConnectionFile)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Required watchdog input is unavailable: $path" }
}
if ($ProviderObservationMode -eq 'AuthenticatedCli') {
    if (-not $VastCliPath -or -not (Test-Path -LiteralPath $VastCliPath -PathType Leaf)) {
        throw 'AuthenticatedCli mode requires a valid VastCliPath.'
    }
}
else {
    if ($OwnerDashboardEvidenceSha256 -notmatch '^[0-9a-f]{64}$') {
        throw 'OwnerDashboardSsh mode requires an aggregate-safe dashboard evidence SHA-256.'
    }
    if ($OwnerDashboardTotalHourlyUsd -lt 0) {
        throw 'OwnerDashboardSsh mode requires the Owner-observed total hourly price.'
    }
    if (-not $OwnerManualDestroyReady.IsPresent) {
        throw 'OwnerDashboardSsh mode requires Owner manual dashboard destroy readiness.'
    }
}
if ($ExpectedInstanceIdentitySha256 -notmatch '^[0-9a-f]{64}$' -or $ExpectedGpuUuidSetSha256 -notmatch '^[0-9a-f]{64}$') {
    throw 'Expected identity commitments must be lowercase SHA-256 values.'
}
$output = [IO.Path]::GetFullPath($OutputDirectory)
[IO.Directory]::CreateDirectory($output) | Out-Null
$lockPath = Join-Path $output 'watchdog.lock'
$heartbeatPath = Join-Path $output 'heartbeat.json'
$stopPath = Join-Path $output 'stop.requested'
$knownHostsPath = if ($KnownHostsPath) {
    [IO.Path]::GetFullPath($KnownHostsPath)
}
else {
    Join-Path $output 'attempt-known_hosts'
}
if ($knownHostsPath -match '\s') {
    throw 'KnownHostsPath must not contain whitespace because Windows OpenSSH does not reliably parse it.'
}
$knownHostsParent = Split-Path -Parent $knownHostsPath
if ($knownHostsParent) { [IO.Directory]::CreateDirectory($knownHostsParent) | Out-Null }
$lockStream = [IO.File]::Open($lockPath, [IO.FileMode]::OpenOrCreate, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
$rateComparisonTolerance = [decimal]::Parse('0.000000000000001', [Globalization.NumberStyles]::Number, [Globalization.CultureInfo]::InvariantCulture)

function Get-Sha256Text([string]$Value) {
    $sha = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($Value)))).Replace('-', '').ToLowerInvariant() }
    finally { $sha.Dispose() }
}

function Get-OwnerFingerprint {
    $text = [IO.File]::ReadAllText([IO.Path]::GetFullPath($OwnerConnectionFile))
    $labeled = [regex]::Matches(
        $text,
        '(?m)^\s*SSH_HOST_FINGERPRINT:\s*(SHA256:[A-Za-z0-9+/=]+)\s*$'
    ) | ForEach-Object { $_.Groups[1].Value } | Select-Object -Unique
    if (@($labeled).Count -eq 1) { return [string]$labeled }
    if (@($labeled).Count -gt 1) { throw 'owner_fingerprint_pin_invalid' }
    $values = [regex]::Matches($text, 'SHA256:[A-Za-z0-9+/=]+') | ForEach-Object { $_.Value } | Select-Object -Unique
    if (@($values).Count -ne 1) { throw 'owner_fingerprint_pin_invalid' }
    return [string]$values
}

function Get-ProviderStatusText([object]$Value) {
    if ($null -eq $Value) { return '' }
    return ([string]$Value).Trim().ToLowerInvariant()
}

function Get-ProviderDecimal([string]$RawJson, [string]$Field) {
    $pattern = '"' + [regex]::Escape($Field) + '"\s*:\s*(-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?)'
    $match = [regex]::Match($RawJson, $pattern)
    if (-not $match.Success) { throw "provider_numeric_field_missing_$Field" }
    try {
        return [decimal]::Parse(
            $match.Groups[1].Value,
            [Globalization.NumberStyles]::Number,
            [Globalization.CultureInfo]::InvariantCulture
        )
    }
    catch { throw "provider_numeric_field_invalid_$Field" }
}

function Ensure-HostKeyPin {
    $script:HostKeyStage = 'read_owner_pin'
    $expected = Get-OwnerFingerprint
    if (Test-Path -LiteralPath $knownHostsPath -PathType Leaf) {
        $script:HostKeyStage = 'existing_pin'
        $entry = & $sshKeygen -F "[$SshHost]:$SshPort" -f $knownHostsPath 2>$null
        if ($LASTEXITCODE -ne 0 -or -not $entry) { throw 'ssh_known_hosts_pin_drift' }
        $observedLine = (& $sshKeygen -lf $knownHostsPath -E sha256 2>$null | Out-String)
        $observed = ([regex]::Match($observedLine, 'SHA256:[A-Za-z0-9+/=]+')).Value
        if (-not $observed -or $observed -ne $expected) { throw 'ssh_fingerprint_mismatch' }
        return
    }
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

function Stop-ChildProcessTree([Diagnostics.Process]$Process) {
    if ($null -eq $Process) { return }
    try {
        if (-not $Process.HasExited) {
            & $taskKill /PID $Process.Id /T /F 2>$null | Out-Null
            $Process.WaitForExit()
        }
    }
    catch { }
}

function Invoke-PinnedSsh([string]$Command) {
    $encodedCommand = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($Command))
    $remoteCommand = "echo $encodedCommand | base64 -d | bash"
    $arguments = @(
        '-i', ('"' + $SshKeyPath + '"'), '-p', $SshPort,
        '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=12',
        '-o', 'StrictHostKeyChecking=yes', '-o', ("UserKnownHostsFile=$knownHostsPath"),
        '-o', 'LogLevel=ERROR', ("root@$SshHost"), ('"' + $remoteCommand + '"')
    )
    $process = $null
    try {
        $startInfo = New-Object Diagnostics.ProcessStartInfo
        $startInfo.FileName = $ssh
        $startInfo.Arguments = [string]::Join(' ', [string[]]$arguments)
        $startInfo.UseShellExecute = $false
        $startInfo.CreateNoWindow = $true
        $startInfo.RedirectStandardOutput = $true
        $startInfo.RedirectStandardError = $true
        $process = New-Object Diagnostics.Process
        $process.StartInfo = $startInfo
        if (-not $process.Start()) { throw 'ssh_runtime_probe_failed' }
        if (-not $process.WaitForExit($RuntimeProbeTimeoutSeconds * 1000)) {
            Stop-ChildProcessTree $process
            throw 'ssh_runtime_probe_timeout'
        }
        if ($process.ExitCode -ne 0) { throw 'ssh_runtime_probe_failed' }
        return $process.StandardOutput.ReadToEnd()
    }
    finally {
        Stop-ChildProcessTree $process
        if ($null -ne $process) { $process.Dispose() }
    }
}

function Write-Heartbeat(
    [string]$Status,
    [string]$Reason,
    [bool]$ProviderOk,
    [decimal]$Rate,
    [bool]$RuntimeOk,
    [bool]$GpuOk
) {
    $now = [DateTime]::UtcNow
    $process = Get-Process -Id $PID
    $body = [ordered]@{
        schema_version = 'myis.armindex-a1.2-governed-watchdog.v16'; status = $Status
        generated_at_utc = $now.ToString('o'); process_id = $PID
        process_created_at_utc = $process.StartTime.ToUniversalTime().ToString('o')
        instance_id = $InstanceId; instance_identity_sha256 = $ExpectedInstanceIdentitySha256
        provider_observation_mode = $ProviderObservationMode
        provider_authenticated = ($ProviderObservationMode -eq 'AuthenticatedCli')
        provider_status_match = $ProviderOk; quote_total_hourly_usd = $Rate
        owner_dashboard_evidence_sha256 = if ($ProviderObservationMode -eq 'OwnerDashboardSsh') { $OwnerDashboardEvidenceSha256 } else { $null }
        owner_manual_destroy_ready = ($ProviderObservationMode -eq 'OwnerDashboardSsh' -and $OwnerManualDestroyReady.IsPresent)
        runtime_identity_match = $RuntimeOk; gpu_identity_4_of_4 = $GpuOk
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
        $reason = $null; $providerOk = $false; $runtimeOk = $false; $gpuOk = $false
        $rate = [decimal]0; $probeStage = 'host_key'
        try {
            if (Test-Path -LiteralPath $stopPath) { $reason = 'owner_local_stop_requested' }
            elseif ([DateTime]::UtcNow -ge $TtlDeadlineUtc.ToUniversalTime()) { $reason = 'ttl_expired' }
            else {
                Ensure-HostKeyPin
                $probeStage = 'ssh_runtime'
                $runtimeProbe = @'
PYTHONDONTWRITEBYTECODE=1 python - <<'PY'
import hashlib, json, platform, socket, subprocess, torch
assert platform.machine() == 'x86_64'
assert torch.cuda.is_available()
assert torch.cuda.device_count() == 4
rows = subprocess.check_output(
    ['nvidia-smi', '--query-gpu=uuid,name,memory.total', '--format=csv,noheader,nounits'],
    text=True,
).splitlines()
parsed = []
for row in rows:
    uuid, name, memory = [part.strip() for part in row.split(',', 2)]
    parsed.append({'uuid': uuid, 'name': name, 'memory_mib': int(memory)})
uuid_hash = hashlib.sha256('\n'.join(sorted(x['uuid'] for x in parsed)).encode()).hexdigest()
print(json.dumps({
    'hostname': socket.gethostname(),
    'python': platform.python_version(),
    'torch': torch.__version__,
    'cuda': torch.version.cuda,
    'gpu_count': len(parsed),
    'gpu_names_match': all(x['name'] == 'NVIDIA GeForce RTX 3090' for x in parsed),
    'gpu_memory_min_mib': min(x['memory_mib'] for x in parsed),
    'gpu_uuid_set_sha256': uuid_hash,
}))
PY
'@
                $runtimeRaw = Invoke-PinnedSsh $runtimeProbe
                # Vast may prepend a provider banner before the one-line JSON probe.
                $runtimeLines = (($runtimeRaw -join "`n") -split "`r?`n")
                $runtimeJson = @($runtimeLines | Where-Object { ([string]$_).TrimStart().StartsWith('{') })
                if ($runtimeJson.Count -ne 1) { throw 'runtime_probe_json_invalid' }
                $runtime = ($runtimeJson[0] | ConvertFrom-Json)
                $runtimeOk = (
                    $runtime.hostname -eq $ExpectedHostname -and
                    $runtime.python -eq '3.11.11' -and
                    $runtime.torch -eq '2.6.0+cu118' -and
                    $runtime.cuda -eq '11.8'
                )
                $gpuOk = (
                    $runtime.gpu_count -eq 4 -and
                    $runtime.gpu_names_match -eq $true -and
                    [int]$runtime.gpu_memory_min_mib -ge 24000 -and
                    $runtime.gpu_uuid_set_sha256 -eq $ExpectedGpuUuidSetSha256
                )
                if (-not $runtimeOk) { $reason = 'runtime_identity_mismatch' }
                elseif (-not $gpuOk) { $reason = 'gpu_identity_mismatch' }
                $probeStage = 'provider'
                if (-not $reason -and $ProviderObservationMode -eq 'AuthenticatedCli') {
                    $raw = & $VastCliPath show instance $InstanceId --raw 2>$null
                    if ($LASTEXITCODE -ne 0 -or -not $raw) { throw 'provider_query_failed' }
                    $rawJson = $raw -join "`n"
                    $provider = ($rawJson | ConvertFrom-Json)
                    if ($provider -is [array]) { $provider = $provider[0] }
                    $providerOk = (
                        [int]$provider.id -eq $InstanceId -and
                        (Get-ProviderStatusText $provider.actual_status) -eq 'running' -and
                        (Get-ProviderStatusText $provider.intended_status) -eq 'running' -and
                        (Get-ProviderStatusText $provider.verification) -eq 'verified'
                    )
                    $rate = Get-ProviderDecimal $rawJson 'dph_total'
                }
                elseif (-not $reason) {
                    $providerOk = $OwnerManualDestroyReady.IsPresent
                    $rate = $OwnerDashboardTotalHourlyUsd
                }
                if (-not $reason -and -not $providerOk) { $reason = 'provider_identity_or_status_mismatch' }
                elseif (-not $reason -and $rate -gt ($MaximumTotalHourlyUsd + $rateComparisonTolerance)) { $reason = 'provider_quote_increased' }
            }
        }
        catch {
            if (-not $reason) {
                $message = [string]$_.Exception.Message
                $knownReasons = @(
                    'ssh_keyscan_failed', 'ssh_fingerprint_mismatch', 'ssh_known_hosts_pin_drift',
                    'owner_fingerprint_pin_invalid', 'ssh_runtime_probe_failed', 'ssh_runtime_probe_timeout', 'provider_query_failed'
                )
                $reason = ($knownReasons | Where-Object { $message -like "*$_*" } | Select-Object -First 1)
                if (-not $reason -and $probeStage -eq 'host_key') { $reason = "watchdog_host_key_${script:HostKeyStage}_failed" }
                if (-not $reason) { $reason = "watchdog_${probeStage}_failed" }
            }
        }
        if ($reason) { Write-Heartbeat 'HARD_STOP' $reason $providerOk $rate $runtimeOk $gpuOk; break }
        Write-Heartbeat 'PASS' $null $providerOk $rate $runtimeOk $gpuOk
        Start-Sleep -Seconds $IntervalSeconds
    }
}
finally { $lockStream.Dispose() }
