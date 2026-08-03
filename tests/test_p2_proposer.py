from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from myis_research.kernel.canonical import canonical_sha256, file_sha256
from myis_research.p2.base_candidates import (
    build_base_candidate_set,
    build_proposer_contract,
)
from myis_research.p2.measured_contracts import scientific_payload_sha256
from myis_research.p2.measured_state import MeasuredRunJournal
from myis_research.p2.proposer import (
    PROPOSER_INSTRUCTIONS_SHA256,
    ProposerRecoveryRequired,
    invoke_codex_proposer,
    sanitized_proposer_environment,
)
from myis_research.p2.runtime_environment import sanitized_runtime_environment


ROOT = Path(__file__).resolve().parents[1]


def test_detached_runtime_environment_drops_stores_and_credentials() -> None:
    source = {
        "PATH": "safe-path",
        "SYSTEMROOT": "safe-root",
        "MYIS_STORE": "protected-store",
        "MYIS_MLFLOW_STORE": "tracking-store",
        "OPENAI_API_KEY": "secret-value",
        "SESSION_TOKEN": "secret-session",
        "UNRELATED": "not-allowlisted",
    }
    environment = sanitized_runtime_environment(source)
    assert environment["PATH"] == "safe-path"
    assert environment["SYSTEMROOT"] == "safe-root"
    assert "MYIS_STORE" not in environment
    assert "MYIS_MLFLOW_STORE" not in environment
    assert "OPENAI_API_KEY" not in environment
    assert "SESSION_TOKEN" not in environment
    assert "UNRELATED" not in environment


def _request() -> dict:
    return {
        "schema_version": "myis.p2-measured-request.v1",
        "request_id": "p2-proposer-test",
        "campaign_revision": "scope-autoindex-v1-p2-r1-primary-v2",
        "budget_profile_id": "p2-r1-primary-v2",
        "budget_profile_sha256": "b" * 64,
        "execution_source_commit": "c" * 40,
        "execution_source_tree": "d" * 40,
        "proposer_identity": {
            "provider": "openai",
            "model": "gpt-test",
            "revision": "revision-test",
            "effort": "high",
            "tool_version": "codex-test",
            "instructions_sha256": PROPOSER_INSTRUCTIONS_SHA256,
            "output_schema_sha256": file_sha256(
                ROOT / "schemas" / "p2-scope-candidate-batch.v1.json"
            ),
            "seed": 42,
            "fallback": False,
        },
    }


def _feedback() -> dict:
    feedback = {
        "schema_version": "myis.p2-adaptive-feedback.v1",
        "feedback_id": "feedback-i01",
        "request_id": "p2-proposer-test",
        "campaign_revision": "scope-autoindex-v1-p2-r1-primary-v2",
        "iteration": 1,
        "lineage_hashes": {"dataset_sha256": "a" * 64},
        "aggregate_candidates": [],
        "failure_categories": [],
        "remaining_axes": ["source_fields", "unitization"],
        "budget_counters": {"candidate_count": 12, "remaining_candidates": 20},
        "selection_exposures": 0,
        "protected_data_accessed": False,
    }
    feedback["feedback_sha256"] = canonical_sha256(feedback)
    return feedback


def _batch() -> dict:
    base = build_base_candidate_set(ROOT, committed_hashes=False)
    definitions = (
        ("exploit", base["preregistered_candidates"][0], "p2-r1-r02-i01-c02", "source_fields"),
        ("matched_ablation", base["preregistered_candidates"][1], "p2-r1-r02-i01-c01", "source_fields"),
        ("orthogonal", base["preregistered_candidates"][4], None, "unitization"),
        ("diversity", base["preregistered_candidates"][7], None, "view_composition"),
    )
    candidates = []
    for index, (role, definition, matched, axis) in enumerate(definitions, start=1):
        spec = deepcopy(definition["scope_spec"])
        spec["spec_id"] = f"spec-r02-i01-c{index:02d}-v01"
        spec["hypothesis_id"] = f"hyp-i01-{index:03d}"
        candidates.append(
            {
                "candidate_id": f"p2-r1-r02-i01-c{index:02d}",
                "parent_candidate_id": definition["candidate_id"],
                "hypothesis_id": spec["hypothesis_id"],
                "hypothesis": definition["hypothesis"],
                "role": role,
                "declared_axis": axis,
                "matched_ablation_id": matched,
                "scope_spec": spec,
                "spec_sha256": canonical_sha256(spec),
                "scientific_payload_sha256": scientific_payload_sha256(spec),
                "axis_values": definition["axis_values"],
            }
        )
    batch = {
        "schema_version": "myis.p2-scope-candidate-batch.v1",
        "batch_id": "p2-r1-r02-i01",
        "request_id": "p2-proposer-test",
        "campaign_revision": "scope-autoindex-v1-p2-r1-primary-v2",
        "iteration": 1,
        "feedback_sha256": _feedback()["feedback_sha256"],
        "proposer_invocation_sha256": "0" * 64,
        "status": "frozen_before_measurement",
        "candidates": candidates,
    }
    batch["batch_sha256"] = canonical_sha256(batch)
    return batch


def test_proposer_environment_drops_protected_and_credential_variables() -> None:
    environment = sanitized_proposer_environment(
        {
            "PATH": "safe-path",
            "MYIS_STORE": "protected-root",
            "MYIS_MLFLOW_STORE": "protected-mlflow",
            "OPENAI_API_KEY": "secret",
            "PASSWORD": "secret",
            "SYSTEMROOT": "system-root",
        }
    )
    assert environment == {"PATH": "safe-path", "SYSTEMROOT": "system-root"}


def test_valid_proposer_output_is_rebound_to_invocation_receipt(tmp_path: Path) -> None:
    journal = MeasuredRunJournal(tmp_path / "run")
    journal.initialize(
        run_id="p2-proposer-test",
        request=_request(),
        owner_paths={"run_root": str(tmp_path / "run")},
    )
    captured: list[dict] = []

    def runner(command: list[str], **kwargs: object) -> SimpleNamespace:
        captured.append({"command": command, **kwargs})
        output = Path(command[command.index("--output-last-message") + 1])
        output.write_text(json.dumps(_batch()), encoding="utf-8")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    batch, invocation = invoke_codex_proposer(
        feedback=_feedback(),
        request=_request(),
        proposer_contract=build_proposer_contract(),
        repository_root=ROOT,
        run_root=tmp_path / "run",
        journal=journal,
        runner=runner,
        base_environment={
            "PATH": "safe-path",
            "MYIS_STORE": "protected-root",
            "OPENAI_API_KEY": "secret",
        },
    )
    assert batch["proposer_invocation_sha256"] == invocation["invocation_sha256"]
    assert batch["batch_sha256"] == canonical_sha256(
        {key: value for key, value in batch.items() if key != "batch_sha256"}
    )
    assert captured[0]["env"] == {"PATH": "safe-path"}
    assert "protected-root" not in captured[0]["input"]
    assert (journal.artifact_root / "adaptive-batch-i01.json").is_file()


def test_two_invalid_attempts_stop_before_batch_and_preserve_budget(tmp_path: Path) -> None:
    journal = MeasuredRunJournal(tmp_path / "run")
    journal.initialize(
        run_id="p2-proposer-test",
        request=_request(),
        owner_paths={"run_root": str(tmp_path / "run")},
    )
    prompts: list[str] = []

    def runner(command: list[str], **kwargs: object) -> SimpleNamespace:
        prompts.append(str(kwargs["input"]))
        output = Path(command[command.index("--output-last-message") + 1])
        output.write_text("{}\n", encoding="utf-8")
        return SimpleNamespace(returncode=0, stdout="", stderr="invalid")

    with pytest.raises(ProposerRecoveryRequired, match="recovery"):
        invoke_codex_proposer(
            feedback=_feedback(),
            request=_request(),
            proposer_contract=build_proposer_contract(),
            repository_root=ROOT,
            run_root=tmp_path / "run",
            journal=journal,
            runner=runner,
            base_environment={"PATH": "safe"},
        )
    assert len(prompts) == 2
    assert prompts[0] == prompts[1]
    state = journal.load()
    assert state["stage"] == "awaiting_proposer_recovery"
    assert not (journal.artifact_root / "adaptive-batch-i01.json").exists()
    receipt = json.loads(
        (journal.artifact_root / "proposer-failure-i01.json").read_text(
            encoding="utf-8"
        )
    )
    assert receipt["candidate_budget_consumed"] == 0
    assert receipt["measurement_started"] is False
