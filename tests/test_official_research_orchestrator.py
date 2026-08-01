from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import subprocess

from jsonschema import Draft202012Validator
import pytest


ROOT = Path(__file__).resolve().parents[1]
INVOKE = ROOT / "scripts/orchestrator/invoke-official-research.ps1"
LOOP = ROOT / "scripts/orchestrator/run-research-loop.ps1"
SCHEMA = ROOT / "orchestration/schemas/official-research-result.schema.json"
OFFICIAL_HOME = Path(r"C:\Users\Siripon Sri\.codex-official")


def _valid_result(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": "1.0",
        "task_id": "official-research-0123456789abcdef",
        "round": 1,
        "verdict": "revise",
        "summary": "Bounded review summary.",
        "major_risks": ["One risk."],
        "publication_opportunities": ["One opportunity."],
        "required_changes": ["One required change."],
        "optional_changes": [],
        "evidence_gaps": ["One evidence gap."],
        "protected_data_accessed": False,
        "measured_execution_performed": False,
        "recommended_next_action": "Perform another read-only review.",
    }
    payload.update(overrides)
    return payload


def test_official_result_schema_is_strict_and_protected_false() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    validator.validate(_valid_result())

    assert list(validator.iter_errors(_valid_result(protected_data_accessed=True)))
    assert list(validator.iter_errors(_valid_result(measured_execution_performed=True)))
    assert list(validator.iter_errors(_valid_result(verdict="retry")))
    assert list(validator.iter_errors(_valid_result(extra_field="not allowed")))
    assert list(validator.iter_errors(_valid_result(round=4)))


def test_invoke_script_has_isolated_profile_and_only_safe_flags() -> None:
    text = INVOKE.read_text(encoding="utf-8")
    lowered = text.lower()

    assert r"C:\Users\Siripon Sri\.codex-official" in text
    assert "$startInfo.EnvironmentVariables['CODEX_HOME']" in text
    assert not re.search(r"\$env:CODEX_HOME\s*=", text, flags=re.IGNORECASE)
    assert "$startInfo.EnvironmentVariables.Remove('MYIS_STORE')" in text
    assert "$startInfo.EnvironmentVariables.Remove('MYIS_MLFLOW_STORE')" in text
    for flag in (
        "--ephemeral",
        "--ignore-user-config",
        "--sandbox",
        "read-only",
        "--output-schema",
        "--output-last-message",
    ):
        assert flag in text
    for forbidden in (
        "danger-full-access",
        "dangerously-bypass",
        "--add-dir",
        "--oss",
        "--local-provider",
        "auth.json",
        "copy-item",
        "codex login",
        "codex logout",
    ):
        assert forbidden not in lowered
    assert "[int]$TimeoutSeconds = 1800" in text
    assert text.index("if ($WhatIf)") < text.index("$process.Start()")


def test_loop_is_bounded_hash_guarded_and_carries_no_transcript() -> None:
    text = LOOP.read_text(encoding="utf-8")
    assert "[int]$MaxRounds = 2" in text
    assert "[ValidateRange(1, 3)]" in text
    assert "HashSet[string]" in text
    assert "seenPromptHashes.Add($promptHash)" in text
    for stop_reason in (
        "repeated_prompt_hash",
        "timeout",
        "nonzero_exit",
        "schema_failure",
        "blocked",
        "round_limit",
    ):
        assert stop_reason in text

    bounded_match = re.search(
        r"\$boundedPrior\s*=\s*\[ordered\]@\{(?P<body>.*?)\n\s*\}",
        text,
        flags=re.DOTALL,
    )
    assert bounded_match is not None
    bounded = bounded_match.group("body")
    assert "summary" in bounded
    assert "required_changes" in bounded
    assert "evidence_gaps" in bounded
    assert "recommended_next_action" in bounded
    assert "stdout" not in bounded.lower()
    assert "stderr" not in bounded.lower()
    assert "output_path" not in bounded.lower()

    loop_body = text[text.index("for ($round = 1;") :]
    assert loop_body.index("seenPromptHashes.Add($promptHash)") < loop_body.index(
        "& $invokeScript"
    )
    assert loop_body.count("& $invokeScript") == 1


def test_results_are_ignored_but_placeholder_is_tracked() -> None:
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "orchestration/results/*" in ignore
    assert "!orchestration/results/.gitkeep" in ignore
    assert (ROOT / "orchestration/results/.gitkeep").exists()
    assert (ROOT / "orchestration/prompts/.gitkeep").exists()


def _powershell() -> str:
    executable = shutil.which("powershell") or shutil.which("pwsh")
    if executable is None:
        pytest.skip("PowerShell is unavailable")
    return executable


def _require_windows_official_profile() -> None:
    if os.name != "nt":
        pytest.skip("The orchestrator intentionally pins a Windows Official profile")
    if not OFFICIAL_HOME.is_dir() or not (OFFICIAL_HOME / "config.toml").is_file():
        pytest.skip("The fixed Official Codex profile is not installed")


def _ps_literal(value: Path | str) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def _make_mock_codex(mock_bin: Path) -> Path:
    mock_bin.mkdir(parents=True)
    script = mock_bin / "codex.ps1"
    script.write_text(
        r"""$ErrorActionPreference = 'Stop'
$prompt = [Console]::In.ReadToEnd()
$count = 0
if (Test-Path -LiteralPath $env:MOCK_CODEX_COUNT) {
    $count = [int](Get-Content -Raw -LiteralPath $env:MOCK_CODEX_COUNT)
}
$count++
[IO.File]::WriteAllText($env:MOCK_CODEX_COUNT, [string]$count)
$record = [ordered]@{
    args = @($args)
    codex_home = $env:CODEX_HOME
    has_myis_store = [bool](Test-Path Env:MYIS_STORE)
    has_myis_mlflow_store = [bool](Test-Path Env:MYIS_MLFLOW_STORE)
    prompt = $prompt
}
[IO.File]::AppendAllText(
    $env:MOCK_CODEX_TRACE,
    (($record | ConvertTo-Json -Depth 5 -Compress) + [Environment]::NewLine)
)
if ($env:MOCK_CODEX_SLEEP_SECONDS) {
    Start-Sleep -Seconds ([int]$env:MOCK_CODEX_SLEEP_SECONDS)
}
$resultPath = ''
for ($index = 0; $index -lt $args.Count - 1; $index++) {
    if ($args[$index] -eq '--output-last-message') {
        $resultPath = $args[$index + 1]
        break
    }
}
if (-not $resultPath) { exit 64 }
if ($env:MOCK_CODEX_INVALID_RESULT -eq '1') {
    [IO.File]::WriteAllText($resultPath, '{"schema_version":"1.0"}')
}
else {
    $taskMatch = [regex]::Match($prompt, 'Required task_id: (?<value>[A-Za-z0-9._-]+)')
    $roundMatch = [regex]::Match($prompt, 'Required round: (?<value>\d+)')
    $taskId = if ($taskMatch.Success) { $taskMatch.Groups['value'].Value } else { 'mock-task' }
    $round = if ($roundMatch.Success) { [int]$roundMatch.Groups['value'].Value } else { 1 }
    $verdicts = @($env:MOCK_CODEX_VERDICTS -split ',')
    $verdict = if ($count -le $verdicts.Count -and $verdicts[$count - 1]) { $verdicts[$count - 1] } else { 'accept' }
    $result = [ordered]@{
        schema_version = '1.0'
        task_id = $taskId
        round = $round
        verdict = $verdict
        summary = "summary-$count"
        major_risks = @("risk-$count")
        publication_opportunities = @("opportunity-$count")
        required_changes = @("required-$count")
        optional_changes = @("optional-$count")
        evidence_gaps = @("gap-$count")
        protected_data_accessed = $false
        measured_execution_performed = $false
        recommended_next_action = "next-$count"
    }
    [IO.File]::WriteAllText($resultPath, ($result | ConvertTo-Json -Depth 5 -Compress))
}
Write-Output 'mock-final-output'
$exitCode = if ($env:MOCK_CODEX_EXIT_CODE) { [int]$env:MOCK_CODEX_EXIT_CODE } else { 0 }
exit $exitCode
""",
        encoding="utf-8",
    )
    return script


def _mock_environment(tmp_path: Path, mock_bin: Path, **updates: str) -> dict[str, str]:
    environment = os.environ.copy()
    environment.update(
        {
            "PATH": str(mock_bin) + os.pathsep + environment.get("PATH", ""),
            "CODEX_HOME": "parent-profile-must-remain",
            "MYIS_STORE": "PROTECTED_STORE_SENTINEL",
            "MYIS_MLFLOW_STORE": "PROTECTED_MLFLOW_SENTINEL",
            "MOCK_CODEX_TRACE": str(tmp_path / "mock-trace.jsonl"),
            "MOCK_CODEX_COUNT": str(tmp_path / "mock-count.txt"),
            "MOCK_CODEX_VERDICTS": "accept",
        }
    )
    environment.update(updates)
    return environment


def _run_harness(
    tmp_path: Path,
    target: Path,
    arguments: list[tuple[str, Path | str | int | None]],
    environment: dict[str, str],
) -> subprocess.CompletedProcess[str]:
    argument_text = []
    for name, value in arguments:
        argument_text.append(name)
        if value is not None:
            argument_text.append(_ps_literal(str(value)))
    harness = tmp_path / "test harness.ps1"
    harness.write_text(
        "\n".join(
            [
                "$ErrorActionPreference = 'Stop'",
                f"$result = & {_ps_literal(target)} {' '.join(argument_text)}",
                "$payload = [ordered]@{",
                "  result = $result",
                "  parent_state_preserved = (",
                "    $env:CODEX_HOME -eq 'parent-profile-must-remain' -and",
                "    $env:MYIS_STORE -eq 'PROTECTED_STORE_SENTINEL' -and",
                "    $env:MYIS_MLFLOW_STORE -eq 'PROTECTED_MLFLOW_SENTINEL'",
                "  )",
                "}",
                "$payload | ConvertTo-Json -Depth 8 -Compress",
            ]
        ),
        encoding="utf-8",
    )
    return subprocess.run(
        [
            _powershell(),
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "RemoteSigned",
            "-File",
            str(harness),
        ],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )


def _parse_harness_result(completed: subprocess.CompletedProcess[str]) -> dict[str, object]:
    assert completed.returncode == 0, completed.stderr
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    return json.loads(lines[-1])


@pytest.mark.skipif(os.name != "nt", reason="Windows-only mocked PowerShell execution")
def test_whatif_validates_paths_without_invoking_codex(tmp_path: Path) -> None:
    _require_windows_official_profile()
    mock_bin = tmp_path / "mock bin"
    _make_mock_codex(mock_bin)
    working = tmp_path / "working directory with spaces"
    output = tmp_path / "output directory with spaces"
    working.mkdir()
    output.mkdir()
    prompt = tmp_path / "prompt with spaces.txt"
    prompt.write_text("Read-only review.", encoding="utf-8")
    environment = _mock_environment(tmp_path, mock_bin)

    completed = _run_harness(
        tmp_path,
        INVOKE,
        [
            ("-PromptFile", prompt),
            ("-WorkingDirectory", working),
            ("-OutputDirectory", output),
            ("-WhatIf", None),
        ],
        environment,
    )
    payload = _parse_harness_result(completed)
    result = payload["result"]
    assert result["action"] == "validated"
    assert not Path(environment["MOCK_CODEX_TRACE"]).exists()
    assert list(output.iterdir()) == []
    assert "PROTECTED_STORE_SENTINEL" not in completed.stdout + completed.stderr


@pytest.mark.skipif(os.name != "nt", reason="Windows-only mocked PowerShell execution")
def test_mocked_invoke_isolates_profile_env_and_supports_spaces(tmp_path: Path) -> None:
    _require_windows_official_profile()
    mock_bin = tmp_path / "mock bin"
    _make_mock_codex(mock_bin)
    working = tmp_path / "working directory with spaces"
    output = tmp_path / "output directory with spaces"
    working.mkdir()
    output.mkdir()
    prompt = tmp_path / "prompt with spaces.txt"
    prompt.write_text("Read-only review.", encoding="utf-8")
    environment = _mock_environment(tmp_path, mock_bin)

    completed = _run_harness(
        tmp_path,
        INVOKE,
        [
            ("-PromptFile", prompt),
            ("-WorkingDirectory", working),
            ("-OutputDirectory", output),
        ],
        environment,
    )
    payload = _parse_harness_result(completed)
    result = payload["result"]
    assert result["exit_code"] == 0
    assert result["timeout"] is False
    assert payload["parent_state_preserved"] is True

    trace = json.loads(Path(environment["MOCK_CODEX_TRACE"]).read_text(encoding="utf-8"))
    assert trace["codex_home"] == str(OFFICIAL_HOME)
    assert trace["has_myis_store"] is False
    assert trace["has_myis_mlflow_store"] is False
    args = trace["args"]
    assert args[0] == "exec"
    for flag in (
        "--ephemeral",
        "--ignore-user-config",
        "--sandbox",
        "read-only",
        "-C",
        str(working.resolve()),
        "-m",
        "gpt-5.6-sol",
        "--output-schema",
        "--output-last-message",
    ):
        assert flag in args
    assert args[-1] == "-"
    assert not set(args).intersection(
        {"danger-full-access", "--dangerously-bypass-approvals-and-sandbox", "--add-dir"}
    )
    assert Path(result["output_path"]).is_file()
    assert Path(result["stdout_path"]).is_file()
    assert Path(result["stderr_path"]).is_file()
    assert "PROTECTED_STORE_SENTINEL" not in completed.stdout + completed.stderr


@pytest.mark.skipif(os.name != "nt", reason="Windows-only mocked PowerShell execution")
def test_mocked_invoke_enforces_timeout(tmp_path: Path) -> None:
    _require_windows_official_profile()
    mock_bin = tmp_path / "mock-bin"
    _make_mock_codex(mock_bin)
    working = tmp_path / "work"
    output = tmp_path / "output"
    working.mkdir()
    output.mkdir()
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("Read-only timeout test.", encoding="utf-8")
    environment = _mock_environment(tmp_path, mock_bin, MOCK_CODEX_SLEEP_SECONDS="3")

    completed = _run_harness(
        tmp_path,
        INVOKE,
        [
            ("-PromptFile", prompt),
            ("-WorkingDirectory", working),
            ("-OutputDirectory", output),
            ("-TimeoutSeconds", 1),
        ],
        environment,
    )
    result = _parse_harness_result(completed)["result"]
    assert result["timeout"] is True
    assert result["exit_code"] == 124


@pytest.mark.skipif(os.name != "nt", reason="Windows-only mocked PowerShell execution")
def test_mocked_loop_stops_at_three_unique_rounds_without_transcripts(tmp_path: Path) -> None:
    _require_windows_official_profile()
    mock_bin = tmp_path / "mock-bin"
    _make_mock_codex(mock_bin)
    working = tmp_path / "working directory"
    output = tmp_path / "loop output"
    working.mkdir()
    output.mkdir()
    prompt = tmp_path / "loop prompt.txt"
    prompt.write_text("Perform the bounded repository review.", encoding="utf-8")
    environment = _mock_environment(
        tmp_path,
        mock_bin,
        MOCK_CODEX_VERDICTS="revise,revise,revise",
    )

    completed = subprocess.run(
        [
            _powershell(),
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "RemoteSigned",
            "-File",
            str(LOOP),
            "-PromptFile",
            str(prompt),
            "-WorkingDirectory",
            str(working),
            "-OutputDirectory",
            str(output),
            "-MaxRounds",
            "3",
        ],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    trace_lines = Path(environment["MOCK_CODEX_TRACE"]).read_text(encoding="utf-8").splitlines()
    traces = [json.loads(line) for line in trace_lines]
    assert len(traces) == 3
    assert "Bounded prior-round result (not a transcript)" in traces[1]["prompt"]
    assert "summary-1" in traces[1]["prompt"]
    assert "mock-final-output" not in traces[1]["prompt"]

    summaries = list(output.glob("research-loop-*.summary.json"))
    assert len(summaries) == 1
    summary = json.loads(summaries[0].read_text(encoding="utf-8"))
    assert summary["stop_reason"] == "round_limit"
    assert len(summary["rounds"]) == 3
    assert len({item["prompt_hash"] for item in summary["rounds"]}) == 3
    assert all(item["provider"] == "openai" for item in summary["rounds"])
    assert all(item["model"] == "gpt-5.6-sol" for item in summary["rounds"])


@pytest.mark.skipif(os.name != "nt", reason="Windows-only mocked PowerShell execution")
def test_mocked_loop_stops_after_schema_failure(tmp_path: Path) -> None:
    _require_windows_official_profile()
    mock_bin = tmp_path / "mock-bin"
    _make_mock_codex(mock_bin)
    working = tmp_path / "work"
    output = tmp_path / "output"
    working.mkdir()
    output.mkdir()
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("Perform a bounded review.", encoding="utf-8")
    environment = _mock_environment(tmp_path, mock_bin, MOCK_CODEX_INVALID_RESULT="1")

    completed = subprocess.run(
        [
            _powershell(),
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "RemoteSigned",
            "-File",
            str(LOOP),
            "-PromptFile",
            str(prompt),
            "-WorkingDirectory",
            str(working),
            "-OutputDirectory",
            str(output),
            "-MaxRounds",
            "3",
        ],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert Path(environment["MOCK_CODEX_COUNT"]).read_text(encoding="utf-8") == "1"
    summary_path = next(output.glob("research-loop-*.summary.json"))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["stop_reason"] == "schema_failure"
    assert summary["rounds"][0]["verdict"] == "schema_failure"


@pytest.mark.skipif(os.name != "nt", reason="Windows-only mocked PowerShell execution")
def test_loop_rejects_more_than_three_rounds_before_codex_call(tmp_path: Path) -> None:
    _require_windows_official_profile()
    mock_bin = tmp_path / "mock-bin"
    _make_mock_codex(mock_bin)
    working = tmp_path / "work"
    output = tmp_path / "output"
    working.mkdir()
    output.mkdir()
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("Perform a bounded review.", encoding="utf-8")
    environment = _mock_environment(tmp_path, mock_bin)

    completed = subprocess.run(
        [
            _powershell(),
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "RemoteSigned",
            "-File",
            str(LOOP),
            "-PromptFile",
            str(prompt),
            "-WorkingDirectory",
            str(working),
            "-OutputDirectory",
            str(output),
            "-MaxRounds",
            "4",
        ],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        timeout=15,
        check=False,
    )
    assert completed.returncode != 0
    assert not Path(environment["MOCK_CODEX_TRACE"]).exists()
