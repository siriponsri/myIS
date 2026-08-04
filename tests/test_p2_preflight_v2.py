from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile

import pytest

from myis_research.kernel.canonical import canonical_sha256, file_sha256
from myis_research.p2 import (
    P2ContractError,
    active_p2_source_uris,
    build_evaluator_compatibility_evidence,
    build_measured_request,
    load_evaluator_compatibility,
    load_measured_request,
    validate_p2_artifact,
    validate_p2_preflight_receipt,
)
from myis_research.p2.measured_adapter import (
    baseline_expectation,
    current_scope_hashes,
)
from myis_research.p2.measured_contracts import (
    git_identity,
    load_envelope_uri,
    load_profile_uri,
    load_referenced_measured_artifact,
)
from myis_research.p2.preflight import P2_LIFECYCLE_SCHEMAS
from myis_research.p2_cli import main as p2_main


ROOT = Path(__file__).resolve().parents[1]
PROFILE_URI = "control/budgets/p2-r1-primary-v2.yaml"
ENVELOPE_URI = "control/execution-envelope-p2-v2.yaml"
BASE_SET_URI = "control/p2/p2-base-candidate-set-r1-v2.json"
POLICY_URI = "control/p2/p2-adaptive-policy-r1-v2.json"
PROPOSER_URI = "control/p2/p2-proposer-contract-r1-v2.json"


def _request_payload(repository_root: Path) -> dict[str, object]:
    root = Path(repository_root).resolve()
    profile, profile_sha256 = load_profile_uri(root, PROFILE_URI)
    envelope, envelope_sha256 = load_envelope_uri(root, ENVELOPE_URI)
    base_set = load_referenced_measured_artifact(root, BASE_SET_URI)
    policy = load_referenced_measured_artifact(root, POLICY_URI)
    proposer = load_referenced_measured_artifact(root, PROPOSER_URI)
    identity = git_identity(root)
    return {
        "schema_version": "myis.p2-measured-request.v1",
        "request_id": "p2-v2-preflight-regression",
        "phase_id": "P2_SCOPE_DEVELOPMENT",
        "arm": "R1",
        "stage": "train_selection",
        "campaign_id": "scope-autoindex-v1",
        "campaign_revision": profile["campaign_revision"],
        "budget_profile_id": profile["profile_id"],
        "budget_profile_uri": PROFILE_URI,
        "budget_profile_sha256": profile_sha256,
        "execution_envelope_id": envelope["envelope_id"],
        "execution_envelope_uri": ENVELOPE_URI,
        "execution_envelope_sha256": envelope_sha256,
        "base_candidate_set_id": base_set["candidate_set_id"],
        "base_candidate_set_uri": BASE_SET_URI,
        "base_candidate_set_sha256": base_set["candidate_set_sha256"],
        "adaptive_policy_id": policy["policy_id"],
        "adaptive_policy_uri": POLICY_URI,
        "adaptive_policy_sha256": policy["policy_sha256"],
        "proposer_contract_id": proposer["contract_id"],
        "proposer_contract_uri": PROPOSER_URI,
        "proposer_contract_sha256": proposer["contract_sha256"],
        "proposer_identity": {
            "provider": "sanitized-test-provider",
            "model": "test-model",
            "revision": "test-revision",
            "effort": "test",
            "tool_version": "test",
            "instructions_sha256": "1" * 64,
            "output_schema_sha256": "2" * 64,
            "seed": 0,
            "fallback": False,
        },
        "execution_source_commit": identity["commit"],
        "execution_source_tree": identity["tree"],
        "worktree_clean": True,
        "input_hashes": {"dataset_lineage_sha256": "3" * 64},
        "scope_hashes": current_scope_hashes(root),
        "global_counters": {
            "measured_runs": 0,
            "candidate_count": 0,
            "shortlist_count": 0,
            "selection_accesses": 0,
        },
        "protected_boundary": {
            "output_mode": "aggregate_hash_count_only",
            "train_selection_only": True,
            "final_split_open": False,
            "d2_open_final": False,
            "d3_submit_release": False,
            "gpu": False,
            "paid_api": False,
            "network_model_download": False,
            "provider_fallback": False,
        },
    }


def test_evaluator_compatibility_reproduces_committed_proof() -> None:
    manifest = load_evaluator_compatibility(ROOT)
    evidence = build_evaluator_compatibility_evidence(
        ROOT,
        baseline_revision=manifest["baseline"]["source_commit"],
        current_revision="HEAD",
    )

    assert evidence["baseline_evaluator_sha256"] == manifest["baseline"]["evaluator_sha256"]
    assert evidence["current_evaluator_sha256"] == manifest["current"]["evaluator_sha256"]
    assert evidence["source_diff_sha256"] == manifest["proof"]["source_diff_sha256"]
    assert evidence["normalized_ast_sha256"] == manifest["proof"]["normalized_ast_sha256"]
    assert evidence["differential_case_count"] == 4
    assert evidence["differential_proof_sha256"] == manifest["proof"]["differential_proof_sha256"]
    assert manifest["baseline"]["evaluator_sha256"] != manifest["current"]["evaluator_sha256"]
    assert manifest["baseline"]["accepted_receipt_sha256"] == file_sha256(
        ROOT / manifest["baseline"]["accepted_receipt_uri"]
    )
    assert manifest["proof"]["independent_verification"] == "runtime_reproduction_required"
    assert manifest["proof"]["verification_test_uri"] == "tests/test_p2_preflight_v2.py"


def test_shared_registry_validates_measured_request_and_excludes_request_from_counters() -> None:
    request = _request_payload(ROOT)

    validated = validate_p2_artifact(request, repository_root=ROOT)

    assert validated["schema_version"] == "myis.p2-measured-request.v1"
    assert validated["budget_profile_id"] == "p2-r1-primary-v2"
    assert "myis.p2-measured-request.v1" not in P2_LIFECYCLE_SCHEMAS
    assert "myis.p2-request.v1" not in P2_LIFECYCLE_SCHEMAS


def test_measured_request_rejects_mixed_v1_binding_and_invalid_compatibility(
    tmp_path: Path,
) -> None:
    request = _request_payload(ROOT)
    request["budget_profile_uri"] = "control/budgets/p2-r1-primary-v1.yaml"
    path = tmp_path / "mixed-request.json"
    path.write_text(json.dumps(request, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(P2ContractError, match="active P2 budget profile"):
        load_measured_request(path, ROOT, require_current_git=False)

    request = _request_payload(ROOT)
    request["scope_hashes"]["evaluator_compatibility_sha256"] = "0" * 64
    path = tmp_path / "invalid-compatibility-request.json"
    path.write_text(json.dumps(request, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(P2ContractError, match="compatibility hash is stale"):
        load_measured_request(path, ROOT, require_current_git=False)


def test_measured_request_rejects_tree_that_does_not_belong_to_commit(
    tmp_path: Path,
) -> None:
    request = _request_payload(ROOT)
    request["execution_source_tree"] = "0" * 40
    path = tmp_path / "wrong-tree-request.json"
    path.write_text(json.dumps(request, sort_keys=True) + "\n", encoding="utf-8")

    with pytest.raises(P2ContractError, match="tree does not match its commit"):
        load_measured_request(path, ROOT, require_current_git=False)


def test_active_source_resolution_has_no_v1_fallback(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    source = root / "control/source-of-truth.yaml"
    source.parent.mkdir(parents=True)
    source.write_text(
        "schema_version: myis.source-of-truth.v2\nrecords: []\n",
        encoding="utf-8",
    )

    with pytest.raises(P2ContractError, match="missing required records"):
        active_p2_source_uris(root)


def test_baseline_expectation_accepts_only_explicit_hash_pair() -> None:
    request = _request_payload(ROOT)

    expectation = baseline_expectation(request=request, repository_root=ROOT)

    manifest = load_evaluator_compatibility(ROOT)
    assert expectation["expected_metric"]["evaluator_sha256"] == manifest["current"]["evaluator_sha256"]
    assert expectation["prior_artifact_uri"].endswith(".receipt.json")


def test_cli_requires_explicit_store_check_opt_in(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    request_path = tmp_path / "request.json"
    request_path.write_text(json.dumps(_request_payload(ROOT)) + "\n", encoding="utf-8")

    with pytest.raises(SystemExit) as error:
        p2_main([
            "preflight",
            "--request",
            str(request_path),
            "--repository-root",
            str(ROOT),
        ])

    assert error.value.code == 3
    assert "--require-stores is required" in capsys.readouterr().err


def test_clean_clone_cli_preflight_reaches_passed_pending_owner(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    if subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout:
        pytest.skip("clean committed checkout required for the end-to-end binding test")

    clone_parent = Path(tempfile.mkdtemp(prefix="p2v2-"))
    clone = clone_parent / "repository"
    try:
        subprocess.run(
            ["git", "clone", "--quiet", "--no-hardlinks", str(ROOT), str(clone)],
            check=True,
            capture_output=True,
        )
        scope_hashes = current_scope_hashes(clone)
        request = build_measured_request(
            repository_root=clone,
            request_id="p2-v2-clean-clone-preflight",
            budget_profile_uri=PROFILE_URI,
            execution_envelope_uri=ENVELOPE_URI,
            base_candidate_set_uri=BASE_SET_URI,
            adaptive_policy_uri=POLICY_URI,
            proposer_contract_uri=PROPOSER_URI,
            proposer_identity={
                "provider": "sanitized-test-provider",
                "model": "test-model",
                "revision": "test-revision",
                "effort": "test",
                "tool_version": "test",
                "instructions_sha256": "1" * 64,
                "output_schema_sha256": "2" * 64,
                "seed": 0,
                "fallback": False,
            },
            input_hashes={"dataset_lineage_sha256": "3" * 64},
            scope_hashes=scope_hashes,
            global_counters={
                "measured_runs": 0,
                "candidate_count": 0,
                "shortlist_count": 0,
                "selection_accesses": 0,
            },
        )
        request_path = tmp_path / "owner-local-preflight-request.json"
        request_path.write_text(json.dumps(request, sort_keys=True) + "\n", encoding="utf-8")
        first = tmp_path / "owner-store"
        second = tmp_path / "mlflow-store"
        first.mkdir()
        second.mkdir()
        monkeypatch.setenv("MYIS_STORE", str(first.resolve()))
        monkeypatch.setenv("MYIS_MLFLOW_STORE", str(second.resolve()))

        exit_code = p2_main([
            "preflight",
            "--request",
            str(request_path),
            "--repository-root",
            str(clone),
            "--require-stores",
            "--required-free-space-bytes",
            "0",
        ])
        encoded = capsys.readouterr().out
        receipt = json.loads(encoded)

        assert exit_code == 0
        assert receipt["status"] == "passed_pending_owner"
        assert receipt["schema_version"] == "myis.p2-preflight-receipt.v2"
        assert all(item["status"] == "passed" for item in receipt["checks"])
        assert receipt["request_schema_version"] == "myis.p2-measured-request.v1"
        assert receipt["request_sha256"] == canonical_sha256(request)
        assert receipt["git_commit"] == request["execution_source_commit"]
        assert receipt["git_tree"] == request["execution_source_tree"]
        assert receipt["evaluator_compatibility_sha256"] == scope_hashes["evaluator_compatibility_sha256"]
        assert receipt["execution_envelope_sha256"] == request["execution_envelope_sha256"]
        assert receipt["safe_path_boundary"]["stores_disjoint"] is True
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
        assert receipt["gates"]["D2_OPEN_FINAL"] == "waiting_owner"
        assert receipt["gates"]["D3_SUBMIT_RELEASE"] == "waiting_owner"
        assert receipt["final_split_open"] is False
        assert str(first.resolve()) not in encoded
        assert str(second.resolve()) not in encoded
        assert validate_p2_preflight_receipt(receipt, repository_root=clone) == receipt
        assert not (clone / "campaigns/scope-autoindex-v1/preflight/p2-preflight-receipt.json").exists()
        assert not any((clone / "campaigns/scope-autoindex-v1/requests").glob("*p2-v2-clean-clone*"))
    finally:
        shutil.rmtree(clone_parent, ignore_errors=False)
