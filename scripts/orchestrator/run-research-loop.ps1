[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$PromptFile,

    [string]$WorkingDirectory = (Join-Path $PSScriptRoot '..\..'),

    [string]$OutputDirectory = (Join-Path $PSScriptRoot '..\..\orchestration\results'),

    [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9._-]*$')]
    [string]$Model = 'gpt-5.6-sol',

    [ValidateRange(1, 86400)]
    [int]$TimeoutSeconds = 1800,

    [ValidateRange(1, 3)]
    [int]$MaxRounds = 2,

    [switch]$WhatIf
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'

$invokeScript = Join-Path $PSScriptRoot 'invoke-official-research.ps1'
$expectedProperties = @(
    'schema_version', 'task_id', 'round', 'verdict', 'summary',
    'major_risks', 'publication_opportunities', 'required_changes',
    'optional_changes', 'evidence_gaps', 'protected_data_accessed',
    'measured_execution_performed', 'recommended_next_action'
)

function Get-TextSha256 {
    param([Parameter(Mandatory = $true)][string]$Text)

    $sha256 = [Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [Text.Encoding]::UTF8.GetBytes($Text)
        return ([BitConverter]::ToString($sha256.ComputeHash($bytes))).Replace('-', '').ToLowerInvariant()
    }
    finally {
        $sha256.Dispose()
    }
}

function Test-StringArray {
    param(
        $Value,
        [int]$MaximumItems = 20,
        [int]$MaximumItemLength = 2000
    )

    if ($null -eq $Value -or $Value -is [string]) { return $false }
    $items = @($Value)
    if ($items.Count -gt $MaximumItems) { return $false }
    foreach ($item in $items) {
        if ($item -isnot [string] -or [string]::IsNullOrWhiteSpace($item) -or $item.Length -gt $MaximumItemLength) {
            return $false
        }
    }
    return $true
}

function Test-OfficialResult {
    param(
        [Parameter(Mandatory = $true)]$Result,
        [Parameter(Mandatory = $true)][string]$TaskId,
        [Parameter(Mandatory = $true)][int]$Round
    )

    $actualProperties = @($Result.PSObject.Properties.Name)
    if (@(Compare-Object -ReferenceObject $expectedProperties -DifferenceObject $actualProperties).Count -ne 0) {
        return $false
    }
    if ($Result.schema_version -isnot [string] -or $Result.schema_version -ne '1.0') {
        return $false
    }
    if ($Result.task_id -isnot [string] -or $Result.task_id -ne $TaskId) {
        return $false
    }
    if (($Result.round -isnot [int] -and $Result.round -isnot [long]) -or $Result.round -ne $Round) {
        return $false
    }
    if ($Result.verdict -isnot [string] -or $Result.verdict -notin @('accept', 'revise', 'blocked')) { return $false }
    if ($Result.summary -isnot [string] -or [string]::IsNullOrWhiteSpace($Result.summary) -or $Result.summary.Length -gt 4000) { return $false }
    if ($Result.recommended_next_action -isnot [string] -or [string]::IsNullOrWhiteSpace($Result.recommended_next_action) -or $Result.recommended_next_action.Length -gt 2000) { return $false }
    foreach ($name in @('major_risks', 'publication_opportunities', 'required_changes', 'optional_changes', 'evidence_gaps')) {
        if (-not (Test-StringArray -Value $Result.$name)) { return $false }
    }
    if ($Result.protected_data_accessed -isnot [bool] -or $Result.protected_data_accessed) { return $false }
    if ($Result.measured_execution_performed -isnot [bool] -or $Result.measured_execution_performed) { return $false }
    return $true
}

function New-RoundPrompt {
    param(
        [Parameter(Mandatory = $true)][string]$BasePrompt,
        [Parameter(Mandatory = $true)][string]$TaskId,
        [Parameter(Mandatory = $true)][int]$Round,
        $PreviousResult
    )

    $priorContext = 'No prior round context.'
    if ($null -ne $PreviousResult) {
        $boundedPrior = [ordered]@{
            verdict = $PreviousResult.verdict
            summary = $PreviousResult.summary
            required_changes = @($PreviousResult.required_changes)
            evidence_gaps = @($PreviousResult.evidence_gaps)
            recommended_next_action = $PreviousResult.recommended_next_action
        }
        $priorContext = 'Bounded prior-round result (not a transcript): ' + ($boundedPrior | ConvertTo-Json -Depth 4 -Compress)
    }

    return @"
$BasePrompt

<official_research_orchestration>
This is a read-only engineering research review, not a P2 candidate iteration.
Do not run measured harnesses, access protected stores or protected DAPFAM data,
open D2/D3, use GPU, download a model, change providers, or modify repository files.
Required task_id: $TaskId
Required round: $Round
$priorContext
Return only the JSON object required by the supplied output schema. Keep
protected_data_accessed=false and measured_execution_performed=false; otherwise
return verdict=blocked without attempting the prohibited action.
</official_research_orchestration>
"@
}

if (-not (Test-Path -LiteralPath $invokeScript -PathType Leaf)) {
    throw "Official invocation script is missing: $invokeScript"
}
if (-not (Test-Path -LiteralPath $PromptFile -PathType Leaf)) {
    throw "Prompt file is missing: $PromptFile"
}
if (-not (Test-Path -LiteralPath $WorkingDirectory -PathType Container)) {
    throw "Working directory is missing: $WorkingDirectory"
}
if (-not (Test-Path -LiteralPath $OutputDirectory -PathType Container)) {
    throw "Output directory is missing: $OutputDirectory"
}

$resolvedPrompt = (Resolve-Path -LiteralPath $PromptFile).ProviderPath
$resolvedWorkingDirectory = (Resolve-Path -LiteralPath $WorkingDirectory).ProviderPath
$resolvedOutputDirectory = (Resolve-Path -LiteralPath $OutputDirectory).ProviderPath
$basePrompt = Get-Content -Raw -Encoding UTF8 -LiteralPath $resolvedPrompt
if ([string]::IsNullOrWhiteSpace($basePrompt)) {
    throw "Prompt file is empty: $resolvedPrompt"
}

if ($WhatIf) {
    $validation = & $invokeScript `
        -PromptFile $resolvedPrompt `
        -WorkingDirectory $resolvedWorkingDirectory `
        -OutputDirectory $resolvedOutputDirectory `
        -Model $Model `
        -TimeoutSeconds $TimeoutSeconds `
        -WhatIf
    [pscustomobject][ordered]@{
        action = 'validated'
        max_rounds = $MaxRounds
        provider = $validation.provider
        model = $validation.model
    }
    return
}

$baseHash = Get-TextSha256 -Text $basePrompt
$taskId = 'official-research-' + $baseHash.Substring(0, 16)
$runToken = '{0}-{1}' -f (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssfffZ'), ([guid]::NewGuid().ToString('N').Substring(0, 8))
$summaryPath = Join-Path $resolvedOutputDirectory ("research-loop-$runToken.summary.json")
$seenPromptHashes = New-Object 'System.Collections.Generic.HashSet[string]'
$roundSummaries = New-Object System.Collections.Generic.List[object]
$previousResult = $null
$stopReason = 'round_limit'
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)

for ($round = 1; $round -le $MaxRounds; $round++) {
    $roundPrompt = New-RoundPrompt -BasePrompt $basePrompt -TaskId $taskId -Round $round -PreviousResult $previousResult
    $promptHash = Get-TextSha256 -Text $roundPrompt
    if (-not $seenPromptHashes.Add($promptHash)) {
        $stopReason = 'repeated_prompt_hash'
        break
    }

    $roundPromptPath = Join-Path $resolvedOutputDirectory ("research-loop-$runToken-round-$round.prompt.txt")
    [IO.File]::WriteAllText($roundPromptPath, $roundPrompt, $utf8NoBom)

    try {
        $invocation = & $invokeScript `
            -PromptFile $roundPromptPath `
            -WorkingDirectory $resolvedWorkingDirectory `
            -OutputDirectory $resolvedOutputDirectory `
            -Model $Model `
            -TimeoutSeconds $TimeoutSeconds
    }
    catch {
        $invocation = [pscustomobject]@{
            output_path = ''
            exit_code = 70
            timeout = $false
            provider = 'openai'
            model = $Model
        }
    }

    $verdict = 'unavailable'
    $validatedResult = $null
    if ($invocation.timeout) {
        $stopReason = 'timeout'
    }
    elseif ($invocation.exit_code -ne 0) {
        $stopReason = 'nonzero_exit'
    }
    else {
        try {
            $validatedResult = Get-Content -Raw -Encoding UTF8 -LiteralPath $invocation.output_path | ConvertFrom-Json
            if (-not (Test-OfficialResult -Result $validatedResult -TaskId $taskId -Round $round)) {
                throw 'Official result did not satisfy the local schema contract.'
            }
            $verdict = $validatedResult.verdict
        }
        catch {
            $validatedResult = $null
            $verdict = 'schema_failure'
            $stopReason = 'schema_failure'
        }
    }

    $roundSummary = [pscustomobject][ordered]@{
        round = $round
        prompt_hash = $promptHash
        output_path = $invocation.output_path
        exit_code = [int]$invocation.exit_code
        timeout = [bool]$invocation.timeout
        verdict = $verdict
        provider = $invocation.provider
        model = $invocation.model
    }
    $roundSummaries.Add($roundSummary)
    Write-Output ($roundSummary | ConvertTo-Json -Compress)

    if ($null -eq $validatedResult) { break }
    if ($validatedResult.verdict -eq 'blocked') {
        $stopReason = 'blocked'
        break
    }
    if ($validatedResult.verdict -eq 'accept') {
        $stopReason = 'accept'
        break
    }
    $previousResult = $validatedResult
}

$loopSummary = [ordered]@{
    schema_version = '1.0'
    task_id = $taskId
    max_rounds = $MaxRounds
    stop_reason = $stopReason
    rounds = $roundSummaries.ToArray()
}
[IO.File]::WriteAllText($summaryPath, ($loopSummary | ConvertTo-Json -Depth 5), $utf8NoBom)
Write-Output ("summary_path={0}; stop_reason={1}" -f $summaryPath, $stopReason)
