[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$PromptFile,

    [string]$WorkingDirectory = (Join-Path $PSScriptRoot '..\..'),

    [string]$OutputDirectory = '',

    [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9._-]*$')]
    [string]$Model = 'gpt-5.6-sol',

    [ValidateRange(1, 86400)]
    [int]$TimeoutSeconds = 1800,

    [switch]$WhatIf
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'

$officialHome = 'C:\Users\Siripon Sri\.codex-official'
$schemaCandidate = Join-Path $PSScriptRoot '..\..\orchestration\schemas\official-research-result.schema.json'
if ([string]::IsNullOrWhiteSpace($OutputDirectory)) {
    $OutputDirectory = Join-Path $PSScriptRoot '..\..\orchestration\results'
}

function Resolve-RequiredPath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [ValidateSet('Leaf', 'Container')]
        [string]$PathType,
        [Parameter(Mandatory = $true)]
        [string]$Label
    )

    if ([string]::IsNullOrWhiteSpace($Path)) {
        throw "$Label path is empty."
    }
    if (-not (Test-Path -LiteralPath $Path -PathType $PathType)) {
        throw "$Label path is missing or is not a $($PathType.ToLowerInvariant()): $Path"
    }
    return (Resolve-Path -LiteralPath $Path).ProviderPath
}

function ConvertTo-SingleQuotedLiteral {
    param([Parameter(Mandatory = $true)][string]$Value)
    return "'" + $Value.Replace("'", "''") + "'"
}

function Stop-ChildProcessTree {
    param([Parameter(Mandatory = $true)][System.Diagnostics.Process]$Process)

    if ($Process.HasExited) { return }
    if ($env:OS -eq 'Windows_NT') {
        $taskkill = Join-Path $env:SystemRoot 'System32\taskkill.exe'
        if (Test-Path -LiteralPath $taskkill -PathType Leaf) {
            & $taskkill /PID $Process.Id /T /F 2>$null | Out-Null
            return
        }
    }
    $Process.Kill()
}

$codexCommand = Get-Command codex -CommandType Application, ExternalScript -ErrorAction SilentlyContinue |
    Select-Object -First 1
if ($null -eq $codexCommand) {
    throw 'codex executable was not found on PATH.'
}
$codexPath = $codexCommand.Source
if (-not (Test-Path -LiteralPath $codexPath -PathType Leaf)) {
    throw "Resolved codex executable is missing: $codexPath"
}

$resolvedOfficialHome = Resolve-RequiredPath -Path $officialHome -PathType Container -Label 'Official Codex profile'
$officialConfig = Join-Path $resolvedOfficialHome 'config.toml'
$null = Resolve-RequiredPath -Path $officialConfig -PathType Leaf -Label 'Official Codex profile config'
$resolvedPrompt = Resolve-RequiredPath -Path $PromptFile -PathType Leaf -Label 'Prompt'
$resolvedWorkingDirectory = Resolve-RequiredPath -Path $WorkingDirectory -PathType Container -Label 'Working directory'
$resolvedOutputDirectory = Resolve-RequiredPath -Path $OutputDirectory -PathType Container -Label 'Output directory'
$resolvedSchema = Resolve-RequiredPath -Path $schemaCandidate -PathType Leaf -Label 'Output schema'

try {
    $schemaObject = Get-Content -Raw -Encoding UTF8 -LiteralPath $resolvedSchema | ConvertFrom-Json
}
catch {
    throw "Output schema is not valid JSON: $resolvedSchema"
}
if ($schemaObject.type -ne 'object') {
    throw "Output schema root must be an object schema: $resolvedSchema"
}

$prompt = Get-Content -Raw -Encoding UTF8 -LiteralPath $resolvedPrompt
if ([string]::IsNullOrWhiteSpace($prompt)) {
    throw "Prompt file is empty: $resolvedPrompt"
}

$runToken = '{0}-{1}' -f (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssfffZ'), ([guid]::NewGuid().ToString('N').Substring(0, 8))
$resultPath = Join-Path $resolvedOutputDirectory ("official-research-$runToken.json")
$stdoutPath = Join-Path $resolvedOutputDirectory ("official-research-$runToken.stdout.log")
$stderrPath = Join-Path $resolvedOutputDirectory ("official-research-$runToken.stderr.log")

if ($WhatIf) {
    [pscustomobject][ordered]@{
        action = 'validated'
        output_path = $resultPath
        stdout_path = $stdoutPath
        stderr_path = $stderrPath
        exit_code = $null
        timeout = $false
        provider = 'openai'
        model = $Model
    }
    return
}

$codexArguments = @(
    'exec',
    '--ephemeral',
    '--ignore-user-config',
    '--sandbox', 'read-only',
    '-C', $resolvedWorkingDirectory,
    '-m', $Model,
    '--output-schema', $resolvedSchema,
    '--output-last-message', $resultPath,
    '-'
)

# Encode the exact executable and argument array so paths with spaces survive
# Windows PowerShell 5.1 native argument parsing without a shell command string.
$argumentLiterals = @($codexArguments | ForEach-Object { ConvertTo-SingleQuotedLiteral -Value $_ })
$childScript = @"
`$codexPath = $(ConvertTo-SingleQuotedLiteral -Value $codexPath)
`$codexArguments = @($($argumentLiterals -join ', '))
& `$codexPath @codexArguments
exit `$LASTEXITCODE
"@
$encodedChildScript = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($childScript))
$powerShellExecutable = [System.Diagnostics.Process]::GetCurrentProcess().MainModule.FileName

$startInfo = New-Object System.Diagnostics.ProcessStartInfo
$startInfo.FileName = $powerShellExecutable
$startInfo.Arguments = "-NoLogo -NoProfile -NonInteractive -EncodedCommand $encodedChildScript"
$startInfo.WorkingDirectory = $resolvedWorkingDirectory
$startInfo.UseShellExecute = $false
$startInfo.CreateNoWindow = $true
$startInfo.RedirectStandardInput = $true
$startInfo.RedirectStandardOutput = $true
$startInfo.RedirectStandardError = $true
$startInfo.EnvironmentVariables['CODEX_HOME'] = $resolvedOfficialHome
$startInfo.EnvironmentVariables.Remove('MYIS_STORE')
$startInfo.EnvironmentVariables.Remove('MYIS_MLFLOW_STORE')

$process = New-Object System.Diagnostics.Process
$process.StartInfo = $startInfo
$timedOut = $false
$exitCode = 70
$stdout = ''
$stderr = ''
try {
    if (-not $process.Start()) {
        throw 'Official Codex child process did not start.'
    }
    $stdoutTask = $process.StandardOutput.ReadToEndAsync()
    $stderrTask = $process.StandardError.ReadToEndAsync()
    $process.StandardInput.Write($prompt)
    $process.StandardInput.Close()

    if (-not $process.WaitForExit($TimeoutSeconds * 1000)) {
        $timedOut = $true
        Stop-ChildProcessTree -Process $process
        $process.WaitForExit()
        $exitCode = 124
    }
    else {
        $process.WaitForExit()
        $exitCode = $process.ExitCode
    }
    $stdout = $stdoutTask.GetAwaiter().GetResult()
    $stderr = $stderrTask.GetAwaiter().GetResult()
}
finally {
    $process.Dispose()
}

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[IO.File]::WriteAllText($stdoutPath, $stdout, $utf8NoBom)
[IO.File]::WriteAllText($stderrPath, $stderr, $utf8NoBom)
if (-not $timedOut -and $exitCode -eq 0 -and -not (Test-Path -LiteralPath $resultPath -PathType Leaf)) {
    $exitCode = 66
}

[pscustomobject][ordered]@{
    action = 'completed'
    output_path = $resultPath
    stdout_path = $stdoutPath
    stderr_path = $stderrPath
    exit_code = $exitCode
    timeout = $timedOut
    provider = 'openai'
    model = $Model
}
