from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re
import shutil
import subprocess
from types import SimpleNamespace

import pytest

from myis_research.kernel.canonical import canonical_sha256, file_sha256
import myis_research.p2.preflight as preflight_module
from myis_research.p2 import (
    P2_PREFLIGHT_RECEIPT_PATH,
    P2ContractError,
    run_p2_preflight as _run_p2_preflight,
    validate_p2_candidate_freeze_proposal,
    validate_p2_preflight_receipt,
    write_preflight_receipt,
)
from myis_research.p2.contracts import build_request, load_profile
from myis_research.p2_cli import main as p2_main
from myis_research.projections.read_model import (
    _p2_preflight_projection,
    _p2_readiness_projection,
    build_read_model,
)
from myis_research.report_records import build_report_records


ROOT = Path(__file__).resolve().parents[1]
PROPOSAL_PATH = ROOT / "campaigns/scope-autoindex-v1/proposals/p2-candidate-freeze-proposal.v1.json"
TRACKED_ARTIFACT_ROOTS = (
    "HANDOFF.md",
    "PLAN.md",
    "README.md",
    "campaigns",
    "control",
    "outputs",
    "projections",
    "obsidian_report",
    "mlflow",
)
OWNER_LOCAL_ABSOLUTE_PATH = re.compile(
    r"(?<![A-Za-z])[A-Za-z]:[\\/]+|/(?:Users|home)/[^/\s\"'`]+"
)


def run_p2_preflight(*args, **kwargs):
    """Exercise the preserved v1 path explicitly in historical tests."""

    kwargs.setdefault("allow_historical_request", True)
    return _run_p2_preflight(*args, **kwargs)


def _self_hash(payload: dict[str, object], field: str) -> dict[str, object]:
    payload.pop(field, None)
    payload[field] = canonical_sha256(payload)
    return payload


def _request_path(tmp_path: Path, repository_root: Path = ROOT) -> Path:
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    request = build_request(
        request_id="p2-preflight-test",
        git_commit=commit,
        execution_envelope_sha256=file_sha256(
            repository_root / "control/execution-envelope-p2.yaml"
        ),
        scope_hashes={
            "compiler": "1" * 64,
            "config": "2" * 64,
            "retriever": "3" * 64,
            "evaluator": "4" * 64,
        },
        input_hashes={"dataset": "5" * 64},
        frozen_controls=[f"control-{index}" for index in range(4)],
        repository_root=repository_root,
    )
    path = tmp_path / "request.json"
    path.write_text(json.dumps(request, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _passed_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    repository_root: Path = ROOT,
    *,
    output: Path | None = None,
) -> dict[str, object]:
    first = tmp_path / "myis-store"
    second = tmp_path / "myis-mlflow-store"
    first.mkdir(exist_ok=True)
    second.mkdir(exist_ok=True)
    monkeypatch.setenv("MYIS_STORE", str(first.resolve()))
    monkeypatch.setenv("MYIS_MLFLOW_STORE", str(second.resolve()))
    return run_p2_preflight(
        _request_path(tmp_path, repository_root),
        repository_root,
        output=output,
        required_free_space_bytes=0,
    )


def _control_repository(tmp_path: Path) -> Path:
    repository_root = tmp_path / "repo"
    for relative in (
        Path("control/budgets/p2-r1-primary-v1.yaml"),
        Path("control/execution-envelope-p2.yaml"),
        Path("control/campaigns/scope-autoindex-v1.yaml"),
        Path("control/decisions/D1_START_CAMPAIGN.yaml"),
        Path("control/decisions/ledger.jsonl"),
    ):
        target = repository_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    shutil.copytree(ROOT / "schemas", repository_root / "schemas")
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=repository_root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "p2-preflight@example.invalid"],
        cwd=repository_root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "P2 Preflight Test"],
        cwd=repository_root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "add", "."],
        cwd=repository_root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "fixture"],
        cwd=repository_root,
        check=True,
        capture_output=True,
    )
    return repository_root


def _candidate_ledger(repository_root: Path) -> dict[str, object]:
    profile = load_profile(repository_root)
    metric = {
        "schema_version": "myis.p2-train-metric.v1",
        "candidate_id": "candidate-0",
        "arm": "R1",
        "metric_name": "recall_at_100",
        "data_role": "train",
        "scope": "OUT",
        "evidence_role": "primary",
        "direction": "higher_is_better",
        "value": 0.1,
        "n": 1,
        "denominator": "macro_mean_per_query_relevant_families",
        "dataset_lineage_sha256": "1" * 64,
        "config_sha256": "2" * 64,
        "retriever_sha256": "3" * 64,
        "evaluator_sha256": "4" * 64,
    }
    body: dict[str, object] = {
        "schema_version": "myis.p2-candidate-ledger.v1",
        "request_id": "p2-stale-counter",
        "campaign_revision": profile.payload["campaign_revision"],
        "budget_profile_id": profile.profile_id,
        "budget_profile_sha256": profile.sha256,
        "baseline_commitment_sha256": "5" * 64,
        "candidate_count": 1,
        "candidates": [
            {
                "candidate_id": "candidate-0",
                "arm": "R1",
                "class": "preregistered_patent",
                "iteration": 0,
                "spec_sha256": "6" * 64,
                "status": "train_complete",
                "train_metric": metric,
                "index_build_count": 1,
                "selection_eligible": False,
            }
        ],
        "iterations": [
            {
                "iteration": iteration,
                "candidate_ids": [f"adaptive-{iteration}-{index}" for index in range(4)],
                "best_metric": metric,
                "status": "completed",
            }
            for iteration in range(1, 5)
        ],
    }
    body["ledger_sha256"] = canonical_sha256(body)
    return body


def test_candidate_freeze_proposal_is_valid_but_not_adopted() -> None:
    proposal = json.loads(PROPOSAL_PATH.read_text(encoding="utf-8"))

    validated = validate_p2_candidate_freeze_proposal(proposal, repository_root=ROOT)

    assert validated["status"] == "draft_owner_review"
    assert validated["adoption"] == "not_adopted"
    assert len(validated["frozen_controls"]) == 4
    assert len(validated["preregistered_candidates"]) == 8
    rows = [*validated["frozen_controls"], *validated["preregistered_candidates"]]
    assert all(item["registered"] is False and item["hash_locked"] is False for item in rows)
    assert all(item["purpose"].strip() and item["hypothesis"].strip() for item in rows)
    assert all(item["owner_approval_required"] for item in rows)
    assert len(validated["owner_approval_required"]) == 5
    assert set(validated["lineage_requirements"]) == {
        "dataset",
        "compiler",
        "config",
        "retriever",
        "evaluator",
    }
    assert all(
        lineage["proposed_sha256"] is not None or lineage["source_locations"]
        for lineage in validated["lineage_requirements"].values()
    )

    projection = _p2_readiness_projection(ROOT, {})
    assert projection["candidate_proposal"]["status"] == "draft_owner_review"
    assert projection["candidate_proposal"]["adoption"] == "not_adopted"
    assert projection["candidate_count"] == 0
    assert projection["shortlist_count"] == 0
    assert projection["selection_accesses"] == 0


def test_candidate_freeze_proposal_rejects_stale_source_binding() -> None:
    proposal = json.loads(PROPOSAL_PATH.read_text(encoding="utf-8"))
    proposal["source_bindings"][0]["sha256"] = "0" * 64
    _self_hash(proposal, "proposal_sha256")

    with pytest.raises(P2ContractError, match="source binding is stale"):
        validate_p2_candidate_freeze_proposal(proposal, repository_root=ROOT)


def test_candidate_freeze_proposal_rejects_unsafe_source_locator() -> None:
    proposal = json.loads(PROPOSAL_PATH.read_text(encoding="utf-8"))
    proposal["source_bindings"][0]["uri"] = "../PLAN.md"
    _self_hash(proposal, "proposal_sha256")

    with pytest.raises(P2ContractError, match="safe repository-relative URI"):
        validate_p2_candidate_freeze_proposal(proposal, repository_root=ROOT)


@pytest.mark.parametrize(
    ("field", "value"),
    (("registered", True), ("hash_locked", True)),
)
def test_candidate_freeze_proposal_cannot_register_or_hash_lock(
    field: str,
    value: bool,
) -> None:
    proposal = json.loads(PROPOSAL_PATH.read_text(encoding="utf-8"))
    proposal["preregistered_candidates"][0][field] = value
    _self_hash(proposal, "proposal_sha256")

    with pytest.raises(P2ContractError):
        validate_p2_candidate_freeze_proposal(proposal, repository_root=ROOT)


def test_preflight_passes_without_emitting_owner_local_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt = _passed_receipt(tmp_path, monkeypatch)

    assert receipt["status"] == "passed_pending_owner"
    assert receipt["measured_execution"] is False
    assert receipt["protected_data_accessed"] is False
    assert receipt["counters"] == {
        "measured_runs": 0,
        "candidate_count": 0,
        "shortlist_count": 0,
        "selection_accesses": 0,
        "baseline_commitment_present": False,
        "freeze_started": False,
    }
    encoded = json.dumps(receipt, ensure_ascii=True, sort_keys=True)
    assert str((tmp_path / "myis-store").resolve()) not in encoded
    assert str((tmp_path / "myis-mlflow-store").resolve()) not in encoded


def test_preflight_fails_closed_when_store_paths_overlap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = tmp_path / "shared-store"
    store.mkdir()
    monkeypatch.setenv("MYIS_STORE", str(store.resolve()))
    monkeypatch.setenv("MYIS_MLFLOW_STORE", str(store.resolve()))

    receipt = run_p2_preflight(
        _request_path(tmp_path),
        ROOT,
        required_free_space_bytes=0,
    )

    assert receipt["status"] == "failed"
    assert "store_path_overlap" in receipt["failure_codes"]
    assert receipt["measured_execution"] is False
    assert receipt["counters"]["selection_accesses"] == 0


def test_preflight_fails_closed_when_stores_are_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("MYIS_STORE", raising=False)
    monkeypatch.delenv("MYIS_MLFLOW_STORE", raising=False)

    receipt = run_p2_preflight(
        _request_path(tmp_path),
        ROOT,
        required_free_space_bytes=0,
    )

    assert receipt["status"] == "failed"
    assert {"store_myis_store", "store_myis_mlflow_store"} <= set(receipt["failure_codes"])
    assert all(store["status"] == "not_configured" for store in receipt["stores"].values())


def test_preflight_rejects_file_instead_of_store_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    file_store = tmp_path / "not-a-directory"
    file_store.write_text("store", encoding="utf-8")
    directory_store = tmp_path / "directory-store"
    directory_store.mkdir()
    monkeypatch.setenv("MYIS_STORE", str(file_store.resolve()))
    monkeypatch.setenv("MYIS_MLFLOW_STORE", str(directory_store.resolve()))

    receipt = run_p2_preflight(
        _request_path(tmp_path),
        ROOT,
        required_free_space_bytes=0,
    )

    assert receipt["status"] == "failed"
    assert receipt["stores"]["MYIS_STORE"]["exists"] is True
    assert receipt["stores"]["MYIS_STORE"]["is_directory"] is False


@pytest.mark.parametrize("store_path", (ROOT, ROOT.parent))
def test_preflight_rejects_store_inside_or_containing_a_worktree(
    store_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    other = tmp_path / "other-store"
    other.mkdir()
    monkeypatch.setenv("MYIS_STORE", str(store_path.resolve()))
    monkeypatch.setenv("MYIS_MLFLOW_STORE", str(other.resolve()))

    receipt = run_p2_preflight(
        _request_path(tmp_path),
        ROOT,
        required_free_space_bytes=0,
    )

    assert receipt["status"] == "failed"
    assert receipt["stores"]["MYIS_STORE"]["outside_all_worktrees"] is False
    assert receipt["stores"]["MYIS_STORE"]["writable_sentinel_created"] is False


def test_store_boundary_checks_every_linked_worktree(tmp_path: Path) -> None:
    first_worktree = tmp_path / "first-worktree"
    linked_worktree = tmp_path / "linked-worktree"
    store = linked_worktree / "store"
    first_worktree.mkdir()
    store.mkdir(parents=True)

    inspected = preflight_module._inspect_store(
        "MYIS_STORE",
        store,
        [first_worktree, linked_worktree],
    )

    assert inspected["status"] == "failed"
    assert inspected["outside_all_worktrees"] is False
    assert inspected["writable_sentinel_created"] is False


def test_preflight_rejects_symlinked_store(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "store-target"
    target.mkdir()
    link = tmp_path / "store-link"
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("directory symlinks are unavailable on this platform")
    other = tmp_path / "other-store"
    other.mkdir()
    monkeypatch.setenv("MYIS_STORE", str(link.absolute()))
    monkeypatch.setenv("MYIS_MLFLOW_STORE", str(other.resolve()))

    receipt = run_p2_preflight(
        _request_path(tmp_path),
        ROOT,
        required_free_space_bytes=0,
    )

    assert receipt["status"] == "failed"
    assert receipt["stores"]["MYIS_STORE"]["unsafe_link_or_junction"] is True


def test_windows_reparse_attribute_is_treated_as_a_junction() -> None:
    path = SimpleNamespace(
        is_symlink=lambda: False,
        lstat=lambda: SimpleNamespace(st_file_attributes=0x400),
    )

    assert preflight_module._is_link_or_junction(path) is True


def test_preflight_fails_when_writable_sentinel_cannot_be_created(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request_path = _request_path(tmp_path)
    first = tmp_path / "myis-store"
    second = tmp_path / "myis-mlflow-store"
    first.mkdir()
    second.mkdir()
    monkeypatch.setenv("MYIS_STORE", str(first.resolve()))
    monkeypatch.setenv("MYIS_MLFLOW_STORE", str(second.resolve()))
    original_open = preflight_module.os.open

    def blocked_open(path: object, *args: object, **kwargs: object) -> int:
        if ".myis-p2-preflight-" in str(path):
            raise PermissionError("blocked sentinel")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(preflight_module.os, "open", blocked_open)

    receipt = run_p2_preflight(
        request_path,
        ROOT,
        required_free_space_bytes=0,
    )

    assert receipt["status"] == "failed"
    assert all(store["writable_sentinel_created"] is False for store in receipt["stores"].values())


def test_preflight_fails_when_writable_sentinel_cannot_be_cleaned(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request_path = _request_path(tmp_path)
    first = tmp_path / "myis-store"
    second = tmp_path / "myis-mlflow-store"
    first.mkdir()
    second.mkdir()
    monkeypatch.setenv("MYIS_STORE", str(first.resolve()))
    monkeypatch.setenv("MYIS_MLFLOW_STORE", str(second.resolve()))
    original_unlink = Path.unlink

    def blocked_unlink(path: Path, *args: object, **kwargs: object) -> None:
        if path.name.startswith(".myis-p2-preflight-"):
            raise PermissionError("blocked cleanup")
        original_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", blocked_unlink)

    receipt = run_p2_preflight(
        request_path,
        ROOT,
        required_free_space_bytes=0,
    )

    assert receipt["status"] == "failed"
    assert all(store["writable_sentinel_created"] is True for store in receipt["stores"].values())
    assert all(store["writable_sentinel_cleaned"] is False for store in receipt["stores"].values())


def test_aggregate_free_space_counts_one_filesystem_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request_path = _request_path(tmp_path)
    first = tmp_path / "myis-store"
    second = tmp_path / "myis-mlflow-store"
    first.mkdir()
    second.mkdir()
    monkeypatch.setenv("MYIS_STORE", str(first.resolve()))
    monkeypatch.setenv("MYIS_MLFLOW_STORE", str(second.resolve()))
    usage_type = type(shutil.disk_usage(tmp_path))
    monkeypatch.setattr(
        preflight_module.shutil,
        "disk_usage",
        lambda path: usage_type(total=100, used=90, free=10),
    )
    monkeypatch.setattr(preflight_module, "_filesystem_identity", lambda path: "same-volume")

    receipt = run_p2_preflight(
        request_path,
        ROOT,
        required_free_space_bytes=15,
    )

    assert receipt["status"] == "failed"
    assert receipt["aggregate_free_space_bytes"] == 10
    assert "aggregate_free_space" in receipt["failure_codes"]


def test_preflight_receipt_rejects_stale_campaign_binding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt = _passed_receipt(tmp_path, monkeypatch)
    receipt["campaign_sha256"] = "0" * 64
    _self_hash(receipt, "receipt_sha256")

    with pytest.raises(P2ContractError, match="campaign binding is stale"):
        validate_p2_preflight_receipt(receipt, repository_root=ROOT)


def test_preflight_receipt_rejects_missing_required_check(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt = _passed_receipt(tmp_path, monkeypatch)
    receipt["checks"].pop()
    _self_hash(receipt, "receipt_sha256")

    with pytest.raises(P2ContractError, match="exact required check set"):
        validate_p2_preflight_receipt(receipt, repository_root=ROOT)


def test_preflight_receipt_rejects_stale_execution_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt = deepcopy(_passed_receipt(tmp_path, monkeypatch))
    receipt["git_commit"] = "f" * 40
    _self_hash(receipt, "receipt_sha256")

    with pytest.raises(P2ContractError, match="execution source commit is stale"):
        validate_p2_preflight_receipt(receipt, repository_root=ROOT)


def test_preflight_with_missing_execution_commit_returns_failed_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request_path = _request_path(tmp_path)
    request = json.loads(request_path.read_text(encoding="utf-8"))
    request["git_commit"] = "f" * 40
    request_path.write_text(
        json.dumps(request, ensure_ascii=True, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    first = tmp_path / "myis-store"
    second = tmp_path / "myis-mlflow-store"
    first.mkdir()
    second.mkdir()
    monkeypatch.setenv("MYIS_STORE", str(first.resolve()))
    monkeypatch.setenv("MYIS_MLFLOW_STORE", str(second.resolve()))

    receipt = run_p2_preflight(
        request_path,
        ROOT,
        required_free_space_bytes=0,
    )

    assert receipt["status"] == "failed"
    assert receipt["git_commit_exists"] is False
    assert "execution_source_commit" in receipt["failure_codes"]


@pytest.mark.parametrize(
    "field",
    ("execution_envelope_sha256", "budget_profile_sha256"),
)
def test_preflight_rejects_stale_request_binding_before_store_access(
    field: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request_path = _request_path(tmp_path)
    request = json.loads(request_path.read_text(encoding="utf-8"))
    request[field] = "0" * 64
    request_path.write_text(
        json.dumps(request, ensure_ascii=True, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        preflight_module,
        "_inspect_store",
        lambda *args, **kwargs: pytest.fail("stale request reached Owner-local store checks"),
    )

    with pytest.raises(P2ContractError):
        run_p2_preflight(request_path, ROOT, required_free_space_bytes=0)


def test_preflight_emits_failed_receipt_for_stale_campaign_binding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository_root = _control_repository(tmp_path)
    request_path = _request_path(tmp_path, repository_root)
    campaign_path = repository_root / "control/campaigns/scope-autoindex-v1.yaml"
    campaign_path.write_text(
        campaign_path.read_text(encoding="utf-8").replace(
            "p2_campaign_revision: scope-autoindex-v1-p2-r1-primary-v1",
            "p2_campaign_revision: stale-revision",
            1,
        ),
        encoding="utf-8",
    )
    first = tmp_path / "myis-store"
    second = tmp_path / "myis-mlflow-store"
    first.mkdir()
    second.mkdir()
    monkeypatch.setenv("MYIS_STORE", str(first.resolve()))
    monkeypatch.setenv("MYIS_MLFLOW_STORE", str(second.resolve()))

    receipt = run_p2_preflight(
        request_path,
        repository_root,
        required_free_space_bytes=0,
    )

    assert receipt["status"] == "failed"
    assert "canonical_campaign_binding" in receipt["failure_codes"]


def test_preflight_emits_failed_receipt_for_unsafe_d1_resource_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository_root = _control_repository(tmp_path)
    d1_path = repository_root / "control/decisions/D1_START_CAMPAIGN.yaml"
    d1_path.write_text(
        d1_path.read_text(encoding="utf-8").replace("  gpu: false", "  gpu: true", 1),
        encoding="utf-8",
    )
    first = tmp_path / "myis-store"
    second = tmp_path / "myis-mlflow-store"
    first.mkdir()
    second.mkdir()
    monkeypatch.setenv("MYIS_STORE", str(first.resolve()))
    monkeypatch.setenv("MYIS_MLFLOW_STORE", str(second.resolve()))

    receipt = run_p2_preflight(
        _request_path(tmp_path, repository_root),
        repository_root,
        required_free_space_bytes=0,
    )

    assert receipt["status"] == "failed"
    assert "gate_state" in receipt["failure_codes"]


@pytest.mark.parametrize(
    ("field", "message"),
    (
        ("execution_envelope_sha256", "execution envelope binding is stale"),
        ("budget_profile_sha256", "budget_profile_sha256 does not match"),
    ),
)
def test_preflight_receipt_rejects_stale_envelope_or_profile_binding(
    field: str,
    message: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt = _passed_receipt(tmp_path, monkeypatch)
    receipt[field] = "0" * 64
    _self_hash(receipt, "receipt_sha256")

    with pytest.raises(P2ContractError, match=message):
        validate_p2_preflight_receipt(receipt, repository_root=ROOT)


def test_failed_receipt_requires_exact_failure_codes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = tmp_path / "shared-store"
    store.mkdir()
    monkeypatch.setenv("MYIS_STORE", str(store.resolve()))
    monkeypatch.setenv("MYIS_MLFLOW_STORE", str(store.resolve()))
    receipt = run_p2_preflight(
        _request_path(tmp_path),
        ROOT,
        required_free_space_bytes=0,
    )
    receipt["failure_codes"] = []
    _self_hash(receipt, "receipt_sha256")

    with pytest.raises(P2ContractError, match="failure codes do not match"):
        validate_p2_preflight_receipt(receipt, repository_root=ROOT)


def test_receipt_rejects_aggregate_free_space_above_store_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt = _passed_receipt(tmp_path, monkeypatch)
    receipt["aggregate_free_space_bytes"] = (
        sum(store["free_space_bytes"] for store in receipt["stores"].values()) + 1
    )
    _self_hash(receipt, "receipt_sha256")

    with pytest.raises(P2ContractError, match="exceeds the store evidence"):
        validate_p2_preflight_receipt(receipt, repository_root=ROOT)


@pytest.mark.parametrize("decision_id", ("D2_OPEN_FINAL", "D3_SUBMIT_RELEASE"))
def test_passed_receipt_becomes_stale_when_owner_gate_changes(
    decision_id: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository_root = _control_repository(tmp_path)
    receipt = _passed_receipt(
        tmp_path,
        monkeypatch,
        repository_root,
        output=P2_PREFLIGHT_RECEIPT_PATH,
    )
    ledger_path = repository_root / "control/decisions/ledger.jsonl"
    ledger_path.write_text(
        ledger_path.read_text(encoding="utf-8")
        + json.dumps({"decision_id": decision_id, "status": "approved"})
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(P2ContractError, match="gate state is stale"):
        validate_p2_preflight_receipt(receipt, repository_root=repository_root)
    assert _p2_preflight_projection(repository_root)["status"] == "failed"


def test_passed_receipt_becomes_stale_when_d1_resource_state_changes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository_root = _control_repository(tmp_path)
    receipt = _passed_receipt(
        tmp_path,
        monkeypatch,
        repository_root,
        output=P2_PREFLIGHT_RECEIPT_PATH,
    )
    d1_path = repository_root / "control/decisions/D1_START_CAMPAIGN.yaml"
    d1_path.write_text(
        d1_path.read_text(encoding="utf-8").replace("  paid_api: false", "  paid_api: true", 1),
        encoding="utf-8",
    )

    with pytest.raises(P2ContractError, match="gate state is stale"):
        validate_p2_preflight_receipt(receipt, repository_root=repository_root)
    assert _p2_preflight_projection(repository_root)["status"] == "failed"


def test_passed_receipt_becomes_stale_when_candidate_ledger_appears(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository_root = _control_repository(tmp_path)
    receipt = _passed_receipt(
        tmp_path,
        monkeypatch,
        repository_root,
        output=P2_PREFLIGHT_RECEIPT_PATH,
    )
    ledger_path = (
        repository_root
        / "campaigns/scope-autoindex-v1/evidence/p2-stale-candidate-ledger.json"
    )
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(
        json.dumps(_candidate_ledger(repository_root), ensure_ascii=True, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(P2ContractError, match="counter state is stale"):
        validate_p2_preflight_receipt(receipt, repository_root=repository_root)
    assert _p2_preflight_projection(repository_root)["status"] == "failed"


def test_preflight_receipt_write_is_immutable_and_cannot_escape_repository(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository_root = _control_repository(tmp_path)
    receipt = _passed_receipt(tmp_path, monkeypatch, repository_root)
    relative = Path("campaigns/scope-autoindex-v1/preflight/immutable-receipt.json")

    write_preflight_receipt(repository_root, relative, receipt)
    with pytest.raises(P2ContractError, match="refusing to overwrite immutable"):
        write_preflight_receipt(repository_root, relative, receipt)
    with pytest.raises(P2ContractError, match="must remain in the repository"):
        write_preflight_receipt(repository_root, tmp_path / "outside-receipt.json", receipt)


def test_preflight_receipt_output_rejects_symlink_traversal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository_root = _control_repository(tmp_path)
    receipt = _passed_receipt(tmp_path, monkeypatch, repository_root)
    target = repository_root / "receipt-target"
    target.mkdir()
    link = repository_root / "receipt-link"
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("directory symlinks are unavailable on this platform")

    with pytest.raises(P2ContractError, match="symlink or junction"):
        write_preflight_receipt(repository_root, Path("receipt-link/receipt.json"), receipt)


def test_preflight_what_if_remains_not_started_and_does_not_inspect_stores(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        preflight_module,
        "_inspect_store",
        lambda *args, **kwargs: pytest.fail("what-if inspected an Owner-local store"),
    )

    payload = preflight_module.preflight_what_if(
        _request_path(tmp_path),
        ROOT,
        allow_historical_request=True,
    )

    assert payload["status"] == "not_started"
    assert payload["stores_checked"] is False
    assert payload["measured_execution"] is False
    assert payload["protected_data_accessed"] is False


def test_p2_cli_rejects_historical_v1_request_without_fallback(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    request_path = _request_path(tmp_path)
    base_args = [
        "preflight",
        "--request",
        str(request_path),
        "--repository-root",
        str(ROOT),
    ]

    with pytest.raises(SystemExit) as error:
        p2_main([*base_args, "--what-if"])
    assert error.value.code == 3
    assert "historical v1 fallback is forbidden" in capsys.readouterr().err


def test_p2_phase_and_task_reports_bind_completion_and_portability_repair_audits() -> None:
    records = build_report_records(ROOT, build_read_model(ROOT))
    p2_records = [
        record for record in records if record["phase_id"] == "P2_SCOPE_DEVELOPMENT"
    ]

    assert len(p2_records) == 2
    for record in p2_records:
        artifact_ids = {item["artifact_id"] for item in record["artifact_references"]}
        assert {
            "p2-preflight-completion-audit-initial",
            "p2-preflight-completion-audit-repair",
            "p2-preflight-report-byte-audit-initial",
            "p2-preflight-report-byte-audit-repair",
            "p2-preflight-projection-source-audit-initial",
            "p2-preflight-projection-source-audit-repair",
            "p2-preflight-tracked-owner-path-audit-initial",
            "p2-preflight-tracked-owner-path-audit-repair",
            "p2-v2-owner-local-preflight-blocker-audit",
            "p2-runtime-resilience-v2-linux-ci-failure-audit",
            "p2-runtime-resilience-v2-linux-ci-repair-audit",
            "p2-runtime-resilience-v2-clean-checkout-failure-audit",
            "p2-runtime-resilience-v2-clean-checkout-repair-audit",
            "p2-runtime-resilience-v2-independent-verifier-revise-audit",
            "p2-runtime-resilience-v2-independent-verifier-accept-audit",
        } <= artifact_ids
        assert any(
            item.get("status") == "repaired_and_validated"
            and item.get("counters_changed") is False
            and item.get("recovery_id") == "p2-preflight-report-byte-drift-repair-20260802"
            for item in record["failure_recovery_references"]
        )
        assert any(
            item.get("status") == "repaired_and_validated"
            and item.get("counters_changed") is False
            and item.get("recovery_id")
            == "p2-preflight-projection-source-hash-drift-repair-20260802"
            for item in record["failure_recovery_references"]
        )
        assert any(
            item.get("status") == "repaired_and_validated"
            and item.get("counters_changed") is False
            and item.get("recovery_id") == "p2-preflight-tracked-owner-path-repair-20260802"
            for item in record["failure_recovery_references"]
        )
        assert any(
            item.get("status") == "repaired_and_validated"
            and item.get("counters_changed") is False
            and item.get("recovery_id")
            == "p2-runtime-resilience-v2-linux-ci-repair-20260803"
            for item in record["failure_recovery_references"]
        )
        assert any(
            item.get("status") == "repaired_and_validated"
            and item.get("counters_changed") is False
            and item.get("failure_id")
            == "p2-runtime-resilience-v2-clean-checkout-drift-20260803"
            and item.get("recovery_id")
            == "p2-runtime-resilience-v2-clean-checkout-repair-20260803"
            for item in record["failure_recovery_references"]
        )
        assert any(
            item.get("status") == "repaired_and_validated"
            and item.get("counters_changed") is False
            and item.get("failure_id")
            == "p2-runtime-resilience-v2-independent-verifier-revise-20260803"
            and item.get("recovery_id")
            == "p2-runtime-resilience-v2-independent-verifier-accept-20260803"
            for item in record["failure_recovery_references"]
        )
        assert "no Owner-local preflight" in record["work_summary"]


def test_tracked_artifacts_do_not_embed_owner_local_absolute_paths() -> None:
    completed = subprocess.run(
        ["git", "ls-files", "-z", "--", *TRACKED_ARTIFACT_ROOTS],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    excluded_prefixes = (
        "obsidian_report/80_Owner_Notes/",
        "obsidian_report/.obsidian/",
    )
    offenders: list[str] = []
    for raw_path in completed.stdout.split(b"\0"):
        if not raw_path:
            continue
        relative = raw_path.decode("utf-8").replace("\\", "/")
        if relative.endswith(".canvas") or relative.startswith(excluded_prefixes):
            continue
        path = ROOT / relative
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        for line_number, line in enumerate(text.splitlines(), start=1):
            if OWNER_LOCAL_ABSOLUTE_PATH.search(line):
                offenders.append(f"{relative}:{line_number}")
    assert offenders == []
