from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
from typing import Any

from myis_research.kernel.canonical import file_sha256
from myis_research.owner_local import validate_receipt
from myis_research.p2.base_candidates import (
    build_adaptive_policy,
    build_base_candidate_set,
    build_proposer_contract,
)
from myis_research.p2.measured_adapter import current_scope_hashes
from myis_research.p2.measured_contracts import build_measured_request
from myis_research.p2.proposer import PROPOSER_INSTRUCTIONS_SHA256


ROOT = Path(__file__).resolve().parents[1]
PRIOR_URI = Path(
    "campaigns/scope-autoindex-v1/evidence/"
    "dapfam-p1-fulltext-c058a3aa7357c782.receipt.json"
)
BASELINE_COMMIT = "947d9a132f2272774dcd8b4ab6e831e0734ec7d3"


def _git(repository: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _copy(relative: str, repository: Path) -> None:
    source = ROOT / relative
    target = repository / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def prepare_v2_repository(
    repository: Path,
    *,
    request_id: str,
    dataset_lineage_sha256: str | None = None,
) -> tuple[Path, dict[str, Any]]:
    """Build a minimal, hash-complete v2 repository for runtime tests."""

    (repository / "schemas").mkdir(parents=True)
    (repository / "control" / "budgets").mkdir(parents=True)
    (repository / "control" / "p2").mkdir(parents=True)
    for schema in (ROOT / "schemas").glob("p2-*.json"):
        shutil.copy2(schema, repository / "schemas" / schema.name)
    for relative in (
        ".gitattributes",
        "control/source-of-truth.yaml",
        "control/campaigns/scope-autoindex-p2-r1-primary-v2.yaml",
        "control/budgets/p2-r1-primary-v2.yaml",
        "control/execution-envelope-p2-v2.yaml",
        "control/p2/p2-evaluator-compatibility-v1.json",
        "src/myis_research/kernel/p1.py",
        "src/myis_research/scope/compiler.py",
        "src/myis_research/p2/measured_adapter.py",
        "tests/test_p2_preflight_v2.py",
    ):
        _copy(relative, repository)
    prior_target = repository / PRIOR_URI
    prior_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / PRIOR_URI, prior_target)

    _git(repository, "init")
    _git(repository, "config", "core.autocrlf", "true")
    _git(repository, "config", "user.email", "p2-v2-fixture@example.invalid")
    _git(repository, "config", "user.name", "P2 v2 fixture")
    _git(repository, "add", ".")
    _git(repository, "commit", "-m", "synthetic v2 authority fixture")
    _git(repository, "fetch", "--quiet", str(ROOT), BASELINE_COMMIT)

    artifacts = {
        "p2-base-candidate-set-r1-v2.json": build_base_candidate_set(
            ROOT,
            committed_hashes=True,
        ),
        "p2-adaptive-policy-r1-v2.json": build_adaptive_policy(),
        "p2-proposer-contract-r1-v2.json": build_proposer_contract(),
    }
    for name, payload in artifacts.items():
        (repository / "control" / "p2" / name).write_text(
            json.dumps(payload, ensure_ascii=True, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    _git(repository, "add", ".")
    _git(repository, "commit", "-m", "synthetic v2 measured controls")

    prior = validate_receipt(json.loads(prior_target.read_text(encoding="utf-8")))
    dataset_hash = dataset_lineage_sha256 or str(
        prior["lineage_hashes"]["dataset_sha256"]
    )
    scope_hashes = current_scope_hashes(repository)
    request = build_measured_request(
        repository_root=repository,
        request_id=request_id,
        budget_profile_uri="control/budgets/p2-r1-primary-v2.yaml",
        execution_envelope_uri="control/execution-envelope-p2-v2.yaml",
        base_candidate_set_uri="control/p2/p2-base-candidate-set-r1-v2.json",
        adaptive_policy_uri="control/p2/p2-adaptive-policy-r1-v2.json",
        proposer_contract_uri="control/p2/p2-proposer-contract-r1-v2.json",
        proposer_identity={
            "provider": "synthetic",
            "model": "synthetic",
            "revision": "synthetic",
            "effort": "none",
            "tool_version": "synthetic",
            "instructions_sha256": PROPOSER_INSTRUCTIONS_SHA256,
            "output_schema_sha256": file_sha256(
                repository / "schemas" / "p2-scope-candidate-batch.v1.json"
            ),
            "seed": 42,
            "fallback": False,
        },
        input_hashes={
            "synthetic_input_sha256": "a" * 64,
            "dataset_lineage_sha256": dataset_hash,
        },
        scope_hashes=scope_hashes,
        global_counters={
            "measured_runs": 0,
            "candidate_count": 0,
            "shortlist_count": 0,
            "selection_accesses": 0,
        },
    )
    request_path = repository.parent / f"{request_id}.json"
    request_path.write_text(
        json.dumps(request, ensure_ascii=True, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return request_path, prior
