"""Aggregate-safe Hybrid Codex proposer for adaptive P2 batches."""

from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import re
import subprocess
import time
from typing import Any, Callable, Mapping, Sequence

from ..kernel.canonical import canonical_json, canonical_sha256, file_sha256
from .contracts import P2ContractError
from .measured_contracts import validate_measured_artifact
from .measured_state import MeasuredRunJournal


PROPOSER_INSTRUCTIONS = """Generate exactly one four-candidate SCOPE batch.
Use only the aggregate-safe feedback object. Preserve the requested campaign,
iteration, stable IDs, four roles, grounded source fields, deterministic
compiler constraints, and matched single-axis ablation. Do not request or emit
qrels, membership, query IDs, rankings, per-query outcomes, raw text,
credentials, protected paths, selection feedback, final data, external data,
paid APIs, GPUs, downloads, retriever changes, evaluator changes, or fallback.
Return only the JSON object required by myis.p2-scope-candidate-batch.v1."""
PROPOSER_INSTRUCTIONS_SHA256 = canonical_sha256({"instructions": PROPOSER_INSTRUCTIONS})

_ALLOWED_ENVIRONMENT = frozenset(
    {
        "APPDATA",
        "CODEX_HOME",
        "COMSPEC",
        "HOME",
        "LANG",
        "LC_ALL",
        "LOCALAPPDATA",
        "PATH",
        "PATHEXT",
        "SYSTEMDRIVE",
        "SYSTEMROOT",
        "TEMP",
        "TMP",
        "USERPROFILE",
        "WINDIR",
    }
)
_CREDENTIAL_KEY = re.compile(
    r"(?:API[_-]?KEY|ACCESS[_-]?KEY|SECRET|TOKEN|PASSWORD|PASSWD|CREDENTIAL|AUTH|COOKIE|SESSION)",
    re.IGNORECASE,
)


class ProposerRecoveryRequired(P2ContractError):
    """Raised after both identical proposer attempts fail closed."""


def sanitized_proposer_environment(
    source: Mapping[str, str] | None = None,
    *,
    explicitly_removed: Sequence[str] = (),
) -> dict[str, str]:
    values = dict(os.environ if source is None else source)
    removed = {str(item).upper() for item in explicitly_removed}
    environment: dict[str, str] = {}
    for key in sorted(values):
        upper = key.upper()
        if upper not in _ALLOWED_ENVIRONMENT:
            continue
        if upper in removed or upper in {"MYIS_STORE", "MYIS_MLFLOW_STORE"}:
            continue
        if _CREDENTIAL_KEY.search(upper):
            continue
        environment[key] = str(values[key])
    return environment


def invoke_codex_proposer(
    *,
    feedback: Mapping[str, Any],
    request: Mapping[str, Any],
    proposer_contract: Mapping[str, Any],
    repository_root: Path,
    run_root: Path,
    journal: MeasuredRunJournal,
    runner: Callable[..., Any] = subprocess.run,
    timeout_seconds: int = 900,
    base_environment: Mapping[str, str] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    root = Path(repository_root).resolve()
    owner_run_root = Path(run_root).resolve()
    validated_feedback = validate_measured_artifact(feedback, root)
    validated_contract = validate_measured_artifact(proposer_contract, root)
    request_payload = dict(request)
    request_payload.pop("_resolved", None)
    identity = dict(request_payload["proposer_identity"])
    output_schema = root / "schemas" / "p2-scope-candidate-batch.v1.json"
    if identity["instructions_sha256"] != PROPOSER_INSTRUCTIONS_SHA256:
        raise P2ContractError("measured request proposer instructions hash is stale")
    if identity["output_schema_sha256"] != file_sha256(output_schema):
        raise P2ContractError("measured request proposer output schema hash is stale")
    feedback_json = canonical_json(validated_feedback)
    prompt = (
        PROPOSER_INSTRUCTIONS
        + "\n\nFrozen request identity:\n"
        + canonical_json(
            {
                "request_id": request_payload["request_id"],
                "campaign_revision": request_payload["campaign_revision"],
                "iteration": validated_feedback["iteration"],
                "seed": identity["seed"],
            }
        )
        + "\n\nAggregate-safe feedback:\n"
        + feedback_json
    )
    prompt_sha256 = canonical_sha256({"prompt": prompt})
    environment = sanitized_proposer_environment(
        base_environment,
        explicitly_removed=validated_contract["environment_removed"],
    )
    proposer_root = owner_run_root / "proposer"
    proposer_root.mkdir(parents=True, exist_ok=True)
    failures: list[dict[str, Any]] = []
    max_attempts = int(validated_contract["attempts_per_batch"])
    for attempt in range(max_attempts):
        completed: Any | None = None
        output_path = proposer_root / (
            f"iteration-{int(validated_feedback['iteration']):02d}-attempt-{attempt + 1:02d}.json"
        )
        output_path.unlink(missing_ok=True)
        command = [
            "codex",
            "exec",
            "--ephemeral",
            "--sandbox",
            "read-only",
            "--output-schema",
            str(output_schema),
            "--output-last-message",
            str(output_path),
            "-",
        ]
        started = time.monotonic()
        try:
            completed = runner(
                command,
                cwd=root,
                env=environment,
                input=prompt,
                text=True,
                capture_output=True,
                timeout=timeout_seconds,
                check=False,
            )
            return_code = int(completed.returncode)
            if return_code != 0:
                raise P2ContractError(f"codex proposer exited with code {return_code}")
            raw = _json_file(output_path)
            provisional = deepcopy(raw)
            provisional["proposer_invocation_sha256"] = "0" * 64
            provisional.pop("batch_sha256", None)
            provisional["batch_sha256"] = canonical_sha256(provisional)
            validate_measured_artifact(provisional, root)
            output_sha256 = canonical_sha256(raw)
            invocation = {
                "schema_version": "myis.p2-proposer-invocation.v1",
                "invocation_id": (
                    f"{request_payload['request_id']}-i{int(validated_feedback['iteration']):02d}"
                    f"-a{attempt + 1:02d}"
                ),
                "request_sha256": canonical_sha256(request_payload),
                "execution_source_commit": request_payload["execution_source_commit"],
                "contract_sha256": validated_contract["contract_sha256"],
                "instructions_sha256": identity["instructions_sha256"],
                "prompt_sha256": prompt_sha256,
                "feedback_sha256": validated_feedback["feedback_sha256"],
                "output_schema_sha256": identity["output_schema_sha256"],
                "provider": identity["provider"],
                "model": identity["model"],
                "revision": identity["revision"],
                "effort": identity["effort"],
                "tool_version": identity["tool_version"],
                "seed": identity["seed"],
                "output_sha256": output_sha256,
                "retry_count": attempt,
                "environment_removed": list(validated_contract["environment_removed"]),
                "protected_data_accessed": False,
                "measured_execution_performed": False,
            }
            invocation["invocation_sha256"] = canonical_sha256(invocation)
            invocation = validate_measured_artifact(invocation, root)
            batch = deepcopy(raw)
            batch["proposer_invocation_sha256"] = invocation["invocation_sha256"]
            batch.pop("batch_sha256", None)
            batch["batch_sha256"] = canonical_sha256(batch)
            batch = validate_measured_artifact(batch, root)
            journal.write_artifact(
                f"proposer-invocation-i{int(validated_feedback['iteration']):02d}.json",
                invocation,
            )
            journal.write_artifact(
                f"adaptive-batch-i{int(validated_feedback['iteration']):02d}.json",
                batch,
            )
            output_path.unlink(missing_ok=True)
            return batch, invocation
        except (OSError, subprocess.TimeoutExpired, P2ContractError, json.JSONDecodeError) as error:
            elapsed = time.monotonic() - started
            stdout = getattr(completed, "stdout", "")
            stderr = getattr(completed, "stderr", "")
            failure = {
                "attempt": attempt + 1,
                "category": _failure_category(error),
                "elapsed_seconds": round(elapsed, 6),
                "stdout_sha256": canonical_sha256({"stdout": str(stdout)}),
                "stderr_sha256": canonical_sha256({"stderr": str(stderr)}),
            }
            failures.append(failure)
            output_path.unlink(missing_ok=True)
    failure_receipt = {
        "schema_version": "myis.p2-proposer-failure.v1",
        "request_id": request_payload["request_id"],
        "campaign_revision": request_payload["campaign_revision"],
        "iteration": validated_feedback["iteration"],
        "prompt_sha256": prompt_sha256,
        "feedback_sha256": validated_feedback["feedback_sha256"],
        "output_schema_sha256": identity["output_schema_sha256"],
        "attempts": failures,
        "status": "awaiting_proposer_recovery",
        "candidate_budget_consumed": 0,
        "measurement_started": False,
        "protected_data_accessed": False,
    }
    failure_receipt["failure_sha256"] = canonical_sha256(failure_receipt)
    journal.write_artifact(
        f"proposer-failure-i{int(validated_feedback['iteration']):02d}.json",
        failure_receipt,
    )
    state = journal.load()
    state["stage"] = "awaiting_proposer_recovery"
    state["failure"] = {
        "category": "proposer_failure",
        "receipt_sha256": failure_receipt["failure_sha256"],
    }
    journal.append_transition(
        state,
        event_type="proposer_recovery_required",
        idempotency_key=(
            f"proposer-recovery:{validated_feedback['feedback_sha256']}:"
            f"{identity['output_schema_sha256']}"
        ),
    )
    raise ProposerRecoveryRequired(
        "two identical proposer attempts failed; recovery is required before batch creation"
    )


def _failure_category(error: BaseException) -> str:
    if isinstance(error, subprocess.TimeoutExpired):
        return "timeout"
    if isinstance(error, OSError):
        return "infrastructure"
    message = str(error).lower()
    if "schema" in message or "single" in message or "batch" in message:
        return "invalid_output"
    return "proposer_error"


def _json_file(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise P2ContractError("proposer did not return one valid JSON object") from error
    if not isinstance(value, dict):
        raise P2ContractError("proposer output must be one JSON object")
    return value
