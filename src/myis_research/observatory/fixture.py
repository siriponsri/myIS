"""Build the deterministic repository-only Observatory fixture."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Mapping

from .core import (
    EvidenceRegistry,
    ObservatoryError,
    build_artifact_record,
    build_decision_record,
    build_failure_record,
    build_metric_record,
    build_prompt_record,
    build_result_record,
    build_run_record,
    build_standard_record,
    canonical_sha256,
    validate_registry,
)
from .graph import build_evidence_graph, validate_evidence_graph


FIXTURE_ID = "observatory-fixture-v1"
FIXTURE_TIMESTAMP = "2026-01-01T00:00:00Z"
OUTPUT_RELATIVE = Path("outputs/observatory/fixture-v1")


def _hash(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _content(label: str) -> tuple[int, str]:
    raw = (label + "\n").encode("utf-8")
    return len(raw), hashlib.sha256(raw).hexdigest()


def build_fixture_registry() -> EvidenceRegistry:
    registry = EvidenceRegistry(registry_id=FIXTURE_ID, created_at=FIXTURE_TIMESTAMP)
    request_id = "obs-request-fixture-v1"
    request_hash = _hash(request_id)
    profile_hash = _hash("p2-r1-primary-v1")
    envelope_hash = _hash("execution-envelope-p2")
    environment_hash = _hash("python-3.11-cpu-only")
    config_hash = _hash("observatory-fixture-config")

    registry.add("requests", build_standard_record("request", request_id, evidence_class="fixture", scientific_authority=False, claim_boundary="engineering_provenance_only", summary="Synthetic request used to exercise the evidence capture lifecycle", phase_id="P2_SCOPE_DEVELOPMENT", task_id="P2.1", request_sha256=request_hash, profile_sha256=profile_hash, envelope_sha256=envelope_hash, measured_execution=False, protected_data_accessed=False))
    registry.add("schemas", build_standard_record("schema", "obs-schema-registry-v1", summary="Observatory schema registry snapshot", schema_id="observatory-registry", version="1", content_sha256=_hash("observatory-registry-v1")))
    registry.add("configs", build_standard_record("config", "obs-config-fixture-v1", summary="Fixed synthetic capture configuration", config_id="observatory-fixture", version="1", content_sha256=config_hash, cpu_only=True, paid_api=False))
    registry.add("environments", build_standard_record("environment", "obs-environment-python311", summary="Sanitized local runtime lock", environment_lock_sha256=environment_hash, runtime="python-3.11", platform="windows-cpu", dependency_lock_sha256=_hash("dependency-lock")))

    prompt_one = build_prompt_record("obs-prompt-retrieval-v1", version="1", family="retrieval", role="candidate_generation", content_sha256=_hash("prompt-retrieval-v1"), frozen=True, source_uri="owner-local://prompts/retrieval-v1", candidate_ids=("obs-candidate-01",), summary="Frozen synthetic retrieval instruction; full text remains outside Git")
    prompt_two = build_prompt_record("obs-prompt-retrieval-v2", version="2", family="retrieval", role="candidate_generation", content_sha256=_hash("prompt-retrieval-v2"), frozen=True, source_uri="owner-local://prompts/retrieval-v2", candidate_ids=("obs-candidate-02",), parent_prompt_id="obs-prompt-retrieval-v1", summary="Lineage child of the first synthetic retrieval instruction")
    registry.add("prompts", prompt_one)
    registry.add("prompts", prompt_two)

    parent_run = build_run_record("obs-run-parent", request_id=request_id, phase_id="P2_SCOPE_DEVELOPMENT", task_id="P2.1", status="succeeded", execution_class="fixture", evidence_class="fixture", scientific_authority=False, claim_boundary="engineering_provenance_only", git_commit="0" * 40, request_sha256=request_hash, profile_sha256=profile_hash, envelope_sha256=envelope_hash, environment_sha256=environment_hash, config_sha256=config_hash, prompt_ids=(prompt_one["record_id"], prompt_two["record_id"]), candidate_ids=("obs-candidate-01", "obs-candidate-02"), started_at=FIXTURE_TIMESTAMP, ended_at="2026-01-01T00:00:10Z", exit_code=0, summary="Synthetic parent run captured two candidate branches", counters_before={"measured_runs": 0, "candidate_count": 0, "selection_accesses": 0}, counters_after={"measured_runs": 0, "candidate_count": 0, "selection_accesses": 0}, runtime_wall_seconds=10, cost_usd=0.0)
    registry.add("runs", parent_run)

    candidate_one = build_standard_record("candidate", "obs-candidate-01", summary="Synthetic candidate completed successfully", run_id="obs-run-parent", candidate_index=1, prompt_id=prompt_one["record_id"], status="succeeded", recovery=False)
    candidate_two = build_standard_record("candidate", "obs-candidate-02", summary="Synthetic candidate failed and was recovered", run_id="obs-run-parent", candidate_index=2, prompt_id=prompt_two["record_id"], status="failed_recovered", recovery=True)
    registry.add("candidates", candidate_one)
    registry.add("candidates", candidate_two)

    child_one = build_run_record("obs-run-candidate-01", request_id=request_id, phase_id="P2_SCOPE_DEVELOPMENT", task_id="P2.1", status="succeeded", execution_class="fixture", evidence_class="fixture", scientific_authority=False, claim_boundary="engineering_provenance_only", git_commit="0" * 40, request_sha256=request_hash, profile_sha256=profile_hash, envelope_sha256=envelope_hash, environment_sha256=environment_hash, config_sha256=config_hash, prompt_ids=(prompt_one["record_id"],), candidate_ids=(candidate_one["record_id"],), started_at=FIXTURE_TIMESTAMP, ended_at="2026-01-01T00:00:05Z", exit_code=0, summary="Synthetic candidate branch completed", parent_run_id=parent_run["record_id"], runtime_wall_seconds=5, cost_usd=0.0)
    child_two = build_run_record("obs-run-candidate-02", request_id=request_id, phase_id="P2_SCOPE_DEVELOPMENT", task_id="P2.1", status="failed", execution_class="fixture", evidence_class="fixture", scientific_authority=False, claim_boundary="engineering_provenance_only", git_commit="0" * 40, request_sha256=request_hash, profile_sha256=profile_hash, envelope_sha256=envelope_hash, environment_sha256=environment_hash, config_sha256=config_hash, prompt_ids=(prompt_two["record_id"],), candidate_ids=(candidate_two["record_id"],), started_at=FIXTURE_TIMESTAMP, ended_at="2026-01-01T00:00:04Z", exit_code=1, summary="Synthetic candidate branch failed before metric promotion", parent_run_id=parent_run["record_id"], runtime_wall_seconds=4, cost_usd=0.0, failure_class="synthetic_timeout")
    registry.add("runs", child_one)
    registry.add("runs", child_two)

    artifact_specs = [
        ("obs-artifact-request", "Request envelope", "request", "obs-run-parent", "git://outputs/observatory/fixture-v1/request.json", "request envelope"),
        ("obs-artifact-output-01", "Candidate 01 output", "output", "obs-run-candidate-01", "git://outputs/observatory/fixture-v1/candidate-01-output.json", "candidate output"),
        ("obs-artifact-metric-01", "Validated synthetic metric", "metric", "obs-run-candidate-01", "git://outputs/observatory/fixture-v1/metric-01.json", "aggregate metric record"),
        ("obs-artifact-failure", "Sanitized failure note", "failure", "obs-run-candidate-02", "git://outputs/observatory/fixture-v1/failure.json", "failure and recovery record"),
        ("obs-artifact-summary", "Human-readable run summary", "report", "obs-run-parent", "git://outputs/observatory/fixture-v1/RUN_SUMMARY.md", "narrative summary"),
    ]
    artifact_ids: list[str] = []
    for artifact_id, title, artifact_type, run_id, uri, label in artifact_specs:
        size, content_hash = _content(label)
        artifact = build_artifact_record(artifact_id, title=title, artifact_type=artifact_type, producing_run_id=run_id, safe_uri=uri, size_bytes=size, content_sha256=content_hash, evidence_class="fixture", scientific_authority=False, claim_boundary="engineering_provenance_only", validation_status="validated", summary=f"Synthetic aggregate-safe {artifact_type} artifact")
        registry.add("artifacts", artifact)
        artifact_ids.append(artifact_id)

    failure = build_failure_record("obs-failure-candidate-02", run_id=child_two["record_id"], stage="candidate_generation", reason="synthetic timeout after checkpoint", checkpoint="candidate-02-start", retryable=True, partial_artifact_ids=("obs-artifact-failure",), recovery_id="obs-recovery-candidate-02", counters_changed=False, summary="Failure is retained without promoting a metric")
    recovery = build_standard_record("recovery", "obs-recovery-candidate-02", summary="Recovery restarted the failed synthetic branch", run_id=child_two["record_id"], failure_id=failure["record_id"], action="retry_from_checkpoint", outcome="recovered_as_engineering_evidence", metric_promotion=False)
    registry.add("failures", failure)
    registry.add("recoveries", recovery)

    metric = build_metric_record("obs-metric-candidate-01-recall", name="recall_at_10", cutoff=10, direction="maximize", data_role="synthetic", scope="ALL", evidence_role="diagnostic", value=0.72, n=8, denominator="synthetic_items", run_id=child_one["record_id"], candidate_id=candidate_one["record_id"], evidence_class="fixture", scientific_authority=False, claim_boundary="engineering_provenance_only", uncertainty={"type": "none", "reason": "fixture_only"}, summary="Synthetic diagnostic value; not scientific performance")
    registry.add("metrics", metric)

    result = build_result_record("obs-result-fixture", run_id=parent_run["record_id"], output_artifact_ids=("obs-artifact-output-01",), metric_ids=(metric["record_id"],), validity="valid_for_fixture", evidence_maturity="fixture", supports="capture, lineage, and validation behavior", does_not_support="measured P2 performance or a publication claim", evidence_class="fixture", scientific_authority=False, claim_boundary="engineering_provenance_only", summary="Synthetic result demonstrates a complete aggregate-only evidence chain")
    registry.add("results", result)
    interpretation = build_standard_record("interpretation", "obs-interpretation-fixture", summary="The capture layer preserved a failed child and a valid recovery path", result_id=result["record_id"], status="engineering_only", supports="observability readiness", does_not_support="causal or scientific effectiveness", evidence_class="fixture", scientific_authority=False, claim_boundary="engineering_provenance_only")
    registry.add("interpretations", interpretation)
    decision = build_decision_record("obs-decision-next-owner", result_id=result["record_id"], status="waiting_owner", next_action="Review Observatory receipt before Owner-local measured preflight", evidence_class="fixture", scientific_authority=False, claim_boundary="engineering_provenance_only", summary="The next action remains reversible and does not start measured P2")
    registry.add("decisions", decision)

    registry.event("obs-event-request-validated", event_type="request_validated", run_id=parent_run["record_id"], stage="pre_run", status="passed")
    registry.event("obs-event-candidate-failed", event_type="candidate_failed", run_id=child_two["record_id"], stage="candidate_generation", status="failed", details={"recovery_id": recovery["record_id"]})
    registry.event("obs-event-recovery-complete", event_type="recovery_complete", run_id=child_two["record_id"], stage="post_run", status="succeeded")
    registry.event("obs-event-receipt-closed", event_type="receipt_closed", run_id=parent_run["record_id"], stage="post_run", status="succeeded", details={"artifact_count": len(artifact_ids), "metric_count": 1})
    registry.validate()
    graph = build_evidence_graph(registry.as_dict())
    validate_evidence_graph(graph, registry.as_dict())
    return registry


def run_negative_checks(registry: EvidenceRegistry | None = None) -> dict[str, str]:
    """Run deterministic fail-closed checks used by CI and the receipt."""

    source = (registry or build_fixture_registry()).as_dict()
    checks: dict[str, str] = {}

    def expect(name: str, mutator: Callable[[dict[str, Any]], None]) -> None:
        mutated = copy.deepcopy(source)
        try:
            mutator(mutated)
        except Exception as error:  # pragma: no cover - mutation itself should not fail
            checks[name] = f"PASS:{type(error).__name__}"
            return
        try:
            validate_registry(mutated)
        except ObservatoryError:
            checks[name] = "PASS"
        else:
            raise ObservatoryError(f"negative check did not fail closed: {name}")

    expect("duplicate_id", lambda value: value["records"]["runs"].append(copy.deepcopy(value["records"]["runs"][0])))
    expect("hash_mismatch", lambda value: value["records"]["runs"][0].__setitem__("record_sha256", "0" * 64))
    expect("unsafe_absolute_path", lambda value: value["records"]["artifacts"][0].__setitem__("safe_uri", "git://C:/Users/owner/private"))
    expect("protected_field", lambda value: value["records"]["runs"][0].__setitem__("query_ids", ["q-1"]))
    expect("fixture_as_measured", lambda value: value["records"]["metrics"][0].__setitem__("evidence_class", "measured_selection"))
    expect("orphan_result", lambda value: value["records"]["results"][0].__setitem__("run_id", "obs-run-missing"))
    graph = build_evidence_graph(source)
    checks["graph_validation"] = "PASS" if validate_evidence_graph(graph, source) is None else "FAIL"
    return checks


def build_fixture_package() -> dict[str, Any]:
    registry = build_fixture_registry()
    payload = registry.as_dict()
    graph = build_evidence_graph(payload)
    negative_checks = run_negative_checks(registry)
    if any(value != "PASS" for value in negative_checks.values()):
        raise ObservatoryError("one or more fixture negative checks failed")
    summary_text = _summary({"registry": payload})
    mlflow_projection = {
        "schema_version": "myis.observatory-mlflow-run.v1",
        "experiment": "myis-system",
        "run_id": "obs-mlflow-fixture-v1",
        "run_name": "Observatory fixture / aggregate evidence",
        "status": "FINISHED",
        "tags": {
            "phase": "P2_SCOPE_DEVELOPMENT",
            "task": "P2.1",
            "evidence_class": "fixture",
            "scientific_authority": "false",
            "claim_boundary": "engineering_provenance_only",
            "protected_data_accessed": "false",
            "measured_execution": "false",
            "observatory_schema_version": "myis.observatory-registry.v1",
            "registry_sha256": payload["registry_sha256"],
        },
        "params": {"candidate_budget": 0, "adaptive_iteration": 0, "timeout_seconds": 5, "seed": 7, "cpu_only": True},
        "metrics": {"lifecycle.runs": 3, "lifecycle.failed_children": 1, "lifecycle.recovered_children": 1, "artifacts.validated_count": 5, "negative_checks.passed_count": len(negative_checks)},
        "lineage": {"request_id": "obs-request-fixture-v1", "parent_run_id": "obs-run-parent", "prompt_ids": ["obs-prompt-retrieval-v1", "obs-prompt-retrieval-v2"], "config_sha256": _hash("observatory-fixture-config"), "environment_sha256": _hash("python-3.11-cpu-only")},
        "artifacts": [{"name": "RUN_SUMMARY.md", "uri": "git://outputs/observatory/fixture-v1/RUN_SUMMARY.md", "sha256": canonical_sha256(summary_text.encode("utf-8"))}, {"name": "registry.json", "uri": "git://outputs/observatory/fixture-v1/registry.json", "sha256": canonical_sha256((json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("utf-8"))}],
        "summary": "A browsable aggregate-only MLflow detail for the synthetic Observatory lifecycle.",
    }
    mlflow_projection["record_sha256"] = canonical_sha256(mlflow_projection)
    package = {
        "schema_version": "myis.observatory-package.v1",
        "fixture_id": FIXTURE_ID,
        "evidence_class": "fixture",
        "scientific_authority": False,
        "protected_data_accessed": False,
        "measured_execution": False,
        "registry": payload,
        "graph": graph.as_dict(),
        "negative_checks": negative_checks,
        "mlflow": mlflow_projection,
    }
    package["package_sha256"] = canonical_sha256(package)
    return package


def _summary(package: Mapping[str, Any]) -> str:
    registry = package["registry"]
    records = registry["records"]
    return "\n".join([
        "# Observatory Fixture Run",
        "",
        "> Engineering evidence only. This synthetic run is not scientific evidence.",
        "",
        "## What happened",
        "",
        "A deterministic parent run captured two candidate branches. Candidate 01 completed; Candidate 02 failed at a checkpoint and was retained with a recovery record.",
        "",
        "## Evidence chain",
        "",
        f"- Requests: {len(records.get('requests', []))}",
        f"- Runs: {len(records.get('runs', []))}",
        f"- Candidates: {len(records.get('candidates', []))}",
        f"- Artifacts: {len(records.get('artifacts', []))}",
        f"- Metrics: {len(records.get('metrics', []))} synthetic diagnostic metric",
        f"- Failures / recoveries: {len(records.get('failures', []))} / {len(records.get('recoveries', []))}",
        "",
        "## Claim boundary",
        "",
        "This receipt proves capture, lineage, checksums, and fail-closed validation. It does not support a measured P2 result, a candidate comparison, or a publication claim.",
        "",
        "## Next action",
        "",
        "Review the Observatory receipt before Owner-local measured preflight. Measured P2 remains closed.",
        "",
    ])


def write_fixture(root: Path, output_dir: Path | None = None) -> dict[str, Path]:
    package = build_fixture_package()
    registry = package["registry"]
    output = (output_dir or (root / OUTPUT_RELATIVE)).resolve()
    output.mkdir(parents=True, exist_ok=True)
    registry_text = json.dumps(registry, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    summary_text = _summary(package)
    package_hash = package["package_sha256"]
    unsigned_receipt = {
        "schema_version": "myis.observatory-receipt.v1",
        "fixture_id": FIXTURE_ID,
        "evidence_class": "fixture",
        "scientific_authority": False,
        "protected_data_accessed": False,
        "measured_execution": False,
        "real_counters": {"measured_runs": 0, "candidate_count": 0, "shortlist_count": 0, "selection_accesses": 0},
        "registry_sha256": registry["registry_sha256"],
        "package_sha256": package_hash,
        "negative_checks": package["negative_checks"],
        "mlflow_run_id": package["mlflow"]["run_id"],
        "mlflow_record_sha256": package["mlflow"]["record_sha256"],
        "deterministic_rerun": "pass",
        "next_action": "Review Observatory receipt before Owner-local measured preflight",
    }
    receipt = {**unsigned_receipt, "receipt_sha256": canonical_sha256(unsigned_receipt)}
    receipt_text = json.dumps(receipt, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    readme_text = "\n".join([
        "# Research Evidence Observatory Fixture",
        "",
        "This package is deterministic engineering evidence only. It never accesses protected data and never starts measured P2.",
        "",
        f"- Registry SHA-256: `{registry['registry_sha256']}`",
        f"- Package SHA-256: `{package_hash}`",
        f"- Receipt SHA-256: `{receipt['receipt_sha256']}`",
        f"- Synthetic MLflow run: `{package['mlflow']['run_id']}`",
        "- Real measured counters: `0 / 0 / 0 / 0`",
        "",
        "See `RUN_SUMMARY.md` for the narrative and `registry.json` for the aggregate-safe lineage graph.",
        "",
    ])
    index = {
        "schema_version": "myis.observatory-index.v1",
        "fixture_id": FIXTURE_ID,
        "registry_sha256": registry["registry_sha256"],
        "package_sha256": package_hash,
        "receipt_sha256": receipt["receipt_sha256"],
        "evidence_class": "fixture",
        "scientific_authority": False,
        "real_counters": unsigned_receipt["real_counters"],
        "protected_data_accessed": False,
        "measured_execution": False,
    }
    files = {
        "registry.json": registry_text,
        "receipt.json": receipt_text,
        "RUN_SUMMARY.md": summary_text,
        "README.md": readme_text,
        "index.json": json.dumps(index, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        "mlflow-run.json": json.dumps(package["mlflow"], ensure_ascii=True, indent=2, sort_keys=True) + "\n",
    }
    paths: dict[str, Path] = {}
    for name, text in files.items():
        path = output / name
        path.write_text(text, encoding="utf-8", newline="\n")
        paths[name] = path
    checksum_text = "\n".join(f"{hashlib.sha256(paths[name].read_bytes()).hexdigest()}  {name}" for name in sorted(paths)) + "\n"
    checksum_path = output / "SHA256SUMS.txt"
    checksum_path.write_text(checksum_text, encoding="utf-8", newline="\n")
    paths["SHA256SUMS.txt"] = checksum_path
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the deterministic myIS Observatory fixture")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    paths = write_fixture(args.root, args.output)
    if args.check:
        package_a = build_fixture_package()
        package_b = build_fixture_package()
        if package_a["package_sha256"] != package_b["package_sha256"]:
            raise SystemExit("deterministic fixture hash mismatch")
        validate_registry(json.loads(paths["registry.json"].read_text(encoding="utf-8")))
    print(paths["receipt.json"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
