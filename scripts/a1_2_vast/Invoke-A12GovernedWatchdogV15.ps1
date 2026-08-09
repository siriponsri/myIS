[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [int]$InstanceId,

    [Parameter(Mandatory = $true)]
    [string]$SshHost,

    [Parameter(Mandatory = $true)]
    [int]$SshPort,

    [Parameter(Mandatory = $true)]
    [string]$SshKeyPath,

    [Parameter(Mandatory = $true)]
    [string]$OwnerConnectionFile,

    [Parameter(Mandatory = $true)]
    [string]$OutputDirectory,

    [Parameter(Mandatory = $true)]
    [datetime]$TtlDeadlineUtc,

    [Parameter(Mandatory = $true)]
    [string]$ExpectedHostname,

    [Parameter(Mandatory = $true)]
    [string]$ExpectedInstanceIdentitySha256,

    [Parameter(Mandatory = $true)]
    [string]$ExpectedGpuUuidSetSha256,

    [Parameter(Mandatory = $true)]
    [decimal]$MaximumTotalHourlyUsd,

    [Parameter(Mandatory = $true)]
    [string]$VastCliPath,

    [int]$IntervalSeconds = 30
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

if ($IntervalSeconds -lt 10 -or $IntervalSeconds -gt 300) {
    throw 'IntervalSeconds must be between 10 and 300.'
}

$ssh = 'C:\Windows\System32\OpenSSH\ssh.exe'
$sshKeyscan = 'C:\Windows\System32\OpenSSH\ssh-keyscan.exe'
$sshKeygen = 'C:\Windows\System32\OpenSSH\ssh-keygen.exe'
foreach ($requiredPath in @($ssh, $sshKeyscan, $sshKeygen, $SshKeyPath, $OwnerConnectionFile, $VastCliPath)) {
    if (-not (Test-Path -LiteralPath $requiredPath -PathType Leaf)) {
        throw "Required watchdog input is unavailable: $requiredPath"
    }
}

$expectedHashPattern = '^[0-9a-f]{64}$'
if ($ExpectedInstanceIdentitySha256 -notmatch $expectedHashPattern -or
    $ExpectedGpuUuidSetSha256 -notmatch $expectedHashPattern) {
    throw 'Expected identity commitments must be lowercase SHA-256 values.'
}

$output = [IO.Path]::GetFullPath($OutputDirectory)
[IO.Directory]::CreateDirectory($output) | Out-Null
$lockPath = Join-Path $output 'watchdog.lock'
$heartbeatPath = Join-Path $output 'heartbeat.json'
$stopPath = Join-Path $output 'stop.requested'
$lockStream = [IO.File]::Open($lockPath, [IO.FileMode]::OpenOrCreate, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)

function Get-Sha256Text([string]$Value) {
    $sha = [Security.Cryptography.SHA256]::Create()
    try {
        return ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($Value)))).Replace('-', '').ToLowerInvariant()
    }
    finally {
        $sha.Dispose()
    }
}

function Write-Heartbeat([string]$Status, [string]$Reason, [hashtable]$Observation) {
    $now = [DateTime]::UtcNow
    $process = Get-Process -Id $PID
    $body = [ordered]@{
        schema_version = 'myis.armindex-a1.2-governed-watchdog.v15'
        status = $Status
        generated_at_utc = $now.ToString('o')
        process_id = $PID
        process_created_at_utc = $process.StartTime.ToUniversalTime().ToString('o')
        instance_id = $InstanceId
        instance_identity_sha256 = $ExpectedInstanceIdentitySha256
        fingerprint_owner_pin_count = $Observation.fingerprint_owner_pin_count
        fingerprint_live_present = [bool]$Observation.fingerprint_live_present
        fingerprint_keyscan_exit_code = $Observation.fingerprint_keyscan_exit_code
        ssh_fingerprint_match = [bool]$Observation.ssh_fingerprint_match
        runtime_identity_match = [bool]$Observation.runtime_identity_match
        gpu_identity_4_of_4 = [bool]$Observation.gpu_identity_4_of_4
        gpu_uuid_set_sha256 = $ExpectedGpuUuidSetSha256
        disk_free_gib = $Observation.disk_free_gib
        provider_authenticated = [bool]$Observation.provider_authenticated
        provider_status_match = [bool]$Observation.provider_status_match
        quote_total_hourly_usd = $Observation.quote_total_hourly_usd
        ttl_deadline_utc = $TtlDeadlineUtc.ToUniversalTime().ToString('o')
        ttl_remaining_seconds = [math]::Max(0, [math]::Floor(($TtlDeadlineUtc.ToUniversalTime() - $now).TotalSeconds))
        hard_stop_reason = $Reason
        provider_destroy_invoked = $false
        access_material_recorded = $false
    }
    $unsigned = $body | ConvertTo-Json -Depth 4 -Compress
    $signed = [ordered]@{}
    foreach ($key in $body.Keys) {
        $signed[$key] = $body[$key]
    }
    $signed['heartbeat_sha256'] = Get-Sha256Text $unsigned
    $temporaryPath = "$heartbeatPath.$PID.tmp"
    [IO.File]::WriteAllText($temporaryPath, ($signed | ConvertTo-Json -Depth 4), [Text.UTF8Encoding]::new($false))
    Move-Item -LiteralPath $temporaryPath -Destination $heartbeatPath -Force
}

function Get-FingerprintMatch {
    $ownerText = [IO.File]::ReadAllText([IO.Path]::GetFullPath($OwnerConnectionFile))
    $pins = [regex]::Matches($ownerText, 'SHA256:[A-Za-z0-9+/=]+') | ForEach-Object { $_.Value } | Select-Object -Unique
    $script:FingerprintDiagnostic = [ordered]@{
        owner_pin_count = @($pins).Count
        live_present = $false
        keyscan_exit_code = $null
    }
    if (@($pins).Count -ne 1) {
        return $false
    }
    $previousPreference = $ErrorActionPreference
    $ErrorActionPreference = 'SilentlyContinue'
    try {
        $scan = & $sshKeyscan -T 10 -p $SshPort -t ed25519 $SshHost 2>$null
        $script:FingerprintDiagnostic.keyscan_exit_code = $LASTEXITCODE
        if ($LASTEXITCODE -ne 0 -or -not $scan) {
            return $false
        }
        $fingerprintLine = $scan | & $sshKeygen -lf - -E sha256 2>$null
        $live = ([regex]::Match(($fingerprintLine -join "`n"), 'SHA256:[A-Za-z0-9+/=]+')).Value
        $script:FingerprintDiagnostic.live_present = [bool]$live
        if (-not $live) {
            return $false
        }
        return (@($pins) -contains $live)
    }
    finally {
        $ErrorActionPreference = $previousPreference
    }
}

function Get-RuntimeObservation {
    $remote = @'
PYTHONDONTWRITEBYTECODE=1 python - <<'PY'
import hashlib, json, os, platform, shutil, socket, subprocess, torch
rows = subprocess.check_output(
    ['nvidia-smi', '--query-gpu=uuid,name,memory.total', '--format=csv,noheader,nounits'],
    text=True,
).splitlines()
parsed = []
for row in rows:
    uuid, name, memory = [part.strip() for part in row.split(',', 2)]
    parsed.append({'uuid': uuid, 'name': name, 'memory_mib': int(memory)})
uuid_hash = hashlib.sha256('\n'.join(sorted(x['uuid'] for x in parsed)).encode()).hexdigest()
disk = shutil.disk_usage('/opt')
print(json.dumps({
    'hostname': socket.gethostname(),
    'arch': platform.machine(),
    'python': platform.python_version(),
    'torch': torch.__version__,
    'cuda': torch.version.cuda,
    'cuda_available': torch.cuda.is_available(),
    'gpu_count': len(parsed),
    'gpu_names_match': all(x['name'] == 'NVIDIA GeForce RTX 3090' for x in parsed),
    'gpu_memory_min_mib': min(x['memory_mib'] for x in parsed),
    'gpu_uuid_set_sha256': uuid_hash,
    'disk_free_gib': round(disk.free / 1024**3, 3),
}))
PY
'@
    $raw = & $ssh -i $SshKeyPath -p $SshPort -o BatchMode=yes -o ConnectTimeout=12 -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL -o LogLevel=ERROR "root@$SshHost" $remote
    if ($LASTEXITCODE -ne 0 -or -not $raw) {
        throw 'ssh_runtime_probe_failed'
    }
    return (($raw -join "`n") | ConvertFrom-Json)
}

function Get-ProviderObservation {
    $raw = & $VastCliPath vastai show instance $InstanceId --raw 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $raw) {
        throw 'provider_query_failed'
    }
    $record = (($raw -join "`n") | ConvertFrom-Json)
    if ($record -is [array]) {
        $record = $record[0]
    }
    return $record
}

$empty = @{
    ssh_fingerprint_match = $false
    runtime_identity_match = $false
    gpu_identity_4_of_4 = $false
    disk_free_gib = $null
    provider_authenticated = $false
    provider_status_match = $false
    quote_total_hourly_usd = $null
    fingerprint_owner_pin_count = $null
    fingerprint_live_present = $false
    fingerprint_keyscan_exit_code = $null
}

try {
    while ($true) {
        $observation = $empty.Clone()
        $reason = $null
        try {
            if (Test-Path -LiteralPath $stopPath) {
                $reason = 'owner_local_stop_requested'
            }
            elseif ([DateTime]::UtcNow -ge $TtlDeadlineUtc.ToUniversalTime()) {
                $reason = 'ttl_expired'
            }
            else {
                $fingerprintMatch = Get-FingerprintMatch
                $observation.fingerprint_owner_pin_count = $script:FingerprintDiagnostic.owner_pin_count
                $observation.fingerprint_live_present = $script:FingerprintDiagnostic.live_present
                $observation.fingerprint_keyscan_exit_code = $script:FingerprintDiagnostic.keyscan_exit_code
                if (-not $fingerprintMatch) {
                    $reason = 'ssh_fingerprint_mismatch'
                }
            }
            if (-not $reason) {
                $observation.ssh_fingerprint_match = $true
                $runtime = Get-RuntimeObservation
                $observation.disk_free_gib = [decimal]$runtime.disk_free_gib
                $observation.runtime_identity_match = (
                    $runtime.hostname -eq $ExpectedHostname -and
                    $runtime.arch -eq 'x86_64' -and
                    $runtime.python -eq '3.11.11' -and
                    $runtime.torch -eq '2.6.0+cu118' -and
                    $runtime.cuda -eq '11.8' -and
                    $runtime.cuda_available -eq $true
                )
                $observation.gpu_identity_4_of_4 = (
                    $runtime.gpu_count -eq 4 -and
                    $runtime.gpu_names_match -eq $true -and
                    [int]$runtime.gpu_memory_min_mib -ge 24000 -and
                    $runtime.gpu_uuid_set_sha256 -eq $ExpectedGpuUuidSetSha256
                )
                if (-not $observation.runtime_identity_match) {
                    $reason = 'runtime_identity_mismatch'
                }
                elseif (-not $observation.gpu_identity_4_of_4) {
                    $reason = 'gpu_identity_mismatch'
                }
                elseif ($observation.disk_free_gib -lt 20) {
                    $reason = 'disk_below_20_gib'
                }
                else {
                    $provider = Get-ProviderObservation
                    $observation.provider_authenticated = $true
                    $observation.provider_status_match = (
                        [int]$provider.id -eq $InstanceId -and
                        $provider.actual_status -eq 'running' -and
                        $provider.intended_status -eq 'running' -and
                        $provider.verification -eq 'verified'
                    )
                    $observation.quote_total_hourly_usd = [decimal]$provider.dph_total
                    if (-not $observation.provider_status_match) {
                        $reason = 'provider_identity_or_status_mismatch'
                    }
                    elseif ($observation.quote_total_hourly_usd -gt $MaximumTotalHourlyUsd) {
                        $reason = 'provider_quote_increased'
                    }
                }
            }
        }
        catch {
            $reason = if ($_.Exception.Message -match '^(ssh_runtime_probe_failed|provider_query_failed)$') {
                $_.Exception.Message
            }
            else {
                'watchdog_probe_failed'
            }
        }

        if ($reason) {
            Write-Heartbeat -Status 'HARD_STOP' -Reason $reason -Observation $observation
            break
        }
        Write-Heartbeat -Status 'PASS' -Reason $null -Observation $observation
        Start-Sleep -Seconds $IntervalSeconds
    }
}
finally {
    $lockStream.Dispose()
}
