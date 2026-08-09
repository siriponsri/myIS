"""Deterministic Owner-local REP-DEV/HARNESS-DEV subdivision for A1.2.

Exact query membership is written only below ``MYIS_STORE``. Repository-safe
callers receive counts and SHA-256 commitments, never query identifiers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from ..dapfam_p1 import iter_arrow_rows, resolve_cache
from ..kernel.canonical import canonical_sha256, file_sha256
from ..protection import assert_aggregate_only


DECISION_PATH = Path("control/armindex/a1.2/rep-harness-split-decision.v1.json")
PARENT_SPLIT_FILE_SHA256 = "f56ad94e2a8d821ab8da556b39fcb60c30a970b9274dda4a40ddfc8f4364195c"
PARENT_SPLIT_SHA256 = "33a1818ff3c00775d43951182fdf769255c8ebfc591de183df4fbfdd3b039dc6"
ALGORITHM_ID = "hamilton-role-set-exact-relevance-sha256-order-v1"
PROTECTED_OUTPUT_NAME = "A1_2_REP_HARNESS_MEMBERSHIP_V1.json"
SAFE_RECEIPT_NAME = "A1_2_REP_HARNESS_SPLIT_RECEIPT_V1.json"


class RepHarnessSplitError(ValueError):
    """Fail-closed split error that never includes protected identifiers."""


def _json_text(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="ascii", newline="") as handle:
            handle.write(_json_text(value))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _read_json(path: Path, *, role: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RepHarnessSplitError(f"{role} is missing or invalid") from error
    if not isinstance(value, dict):
        raise RepHarnessSplitError(f"{role} must be a JSON object")
    return value


def validate_decision(repository_root: Path) -> dict[str, Any]:
    root = repository_root.resolve()
    decision = _read_json(root / DECISION_PATH, role="split decision")
    unsigned = {key: value for key, value in decision.items() if key != "decision_sha256"}
    expected = {
        "schema_version": "myis.armindex-a1.2-rep-harness-split-decision.v1",
        "decision_id": "a1.2-rep-harness-split-owner-decision-v1",
        "status": "AUTHORIZED_PRE_MEASUREMENT",
        "seed": 42,
        "parent": {
            "split_role": "Train-250",
            "count": 250,
            "split_sha256": PARENT_SPLIT_SHA256,
            "file_sha256": PARENT_SPLIT_FILE_SHA256,
        },
        "stratification": {
            "fields": ["canonical_in_out_role_set", "exact_positive_relevant_family_count"],
            "relevance_count_bins_allowed": False,
        },
        "allocation": {
            "method": "Hamilton largest remainder",
            "rep_dev_target": 150,
            "harness_dev_target": 100,
            "rep_dev_fraction": 0.6,
            "equal_remainder_tie_break": "lexical_stratum_key",
        },
        "within_stratum_order": {
            "algorithm": "SHA256(seed-colon-canonical-query-id), lexical query-id tie-break",
            "algorithm_id": "sha256-seed-colon-id-lexical-v1",
        },
        "grouping_policy": {
            "preserve_prior_frozen_constraints": True,
            "audit_result": "NO_PRIOR_FROZEN_SUBDIVISION_GROUPING_CONSTRAINT_FOUND",
            "constraints": [],
        },
        "privacy": {
            "exact_membership_owner_local_only": True,
            "repository_outputs": ["safe_hashes", "counts", "commitments"],
        },
        "safety": {
            "retrieval_results_inspected": False,
            "resampling_allowed": False,
            "optimization_allowed": False,
        },
    }
    for key, value in expected.items():
        if decision.get(key) != value:
            raise RepHarnessSplitError(f"split decision field drifted: {key}")
    if decision.get("algorithm", {}).get("id") != ALGORITHM_ID:
        raise RepHarnessSplitError("split algorithm identity drifted")
    if decision.get("algorithm", {}).get("source_uri") != Path(__file__).relative_to(root).as_posix():
        raise RepHarnessSplitError("split algorithm source URI drifted")
    if decision.get("algorithm", {}).get("source_sha256") != file_sha256(Path(__file__)):
        raise RepHarnessSplitError("split algorithm source SHA-256 drifted")
    if decision.get("decision_sha256") != canonical_sha256(unsigned):
        raise RepHarnessSplitError("split decision self-hash mismatch")
    return decision


def _stratum_key(role_set: Sequence[str], relevance_count: int) -> str:
    if not role_set or any(role not in {"IN", "OUT"} for role in role_set):
        raise RepHarnessSplitError("Train-250 query has no canonical positive IN/OUT role")
    return f"{'+'.join(sorted(role_set))}|{relevance_count:08d}"


def _stratum_order(key: str) -> tuple[str, int]:
    role, count = key.split("|", maxsplit=1)
    return role, int(count)


def _hamilton_rep_allocations(stratum_sizes: Mapping[str, int], target: int) -> dict[str, int]:
    total = sum(stratum_sizes.values())
    if total != 250 or target != 150:
        raise RepHarnessSplitError("Hamilton allocation requires frozen 150/250 targets")
    floors = {key: (size * target) // total for key, size in stratum_sizes.items()}
    remaining = target - sum(floors.values())
    ranked = sorted(
        stratum_sizes,
        key=lambda key: (
            -((stratum_sizes[key] * target) % total),
            key.split("|", maxsplit=1)[0],
            int(key.split("|", maxsplit=1)[1]),
        ),
    )
    for key in ranked[:remaining]:
        floors[key] += 1
    return floors


def derive_membership(
    parent_split: Mapping[str, Any],
    relation_rows: Iterable[Mapping[str, Any]],
    *,
    decision: Mapping[str, Any],
    algorithm_source_sha256: str,
    source_hashes: Mapping[str, str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    train = [str(item) for item in parent_split.get("train", [])]
    if (
        parent_split.get("schema_version") != "myis.protected-split.v1"
        or parent_split.get("seed") != 42
        or parent_split.get("algorithm") != "sha256-seed-colon-id-lexical-v1"
        or parent_split.get("split_sha256") != PARENT_SPLIT_SHA256
        or canonical_sha256({key: value for key, value in parent_split.items() if key != "split_sha256"})
        != PARENT_SPLIT_SHA256
        or len(train) != 250
        or len(set(train)) != 250
    ):
        raise RepHarnessSplitError("parent Train-250 commitment is invalid")
    train_set = set(train)
    positives: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for row in relation_rows:
        query_id = str(row.get("query_id", ""))
        if query_id not in train_set:
            continue
        score = row.get("relevance_score")
        role = str(row.get("domain_rel", ""))
        family_id = str(row.get("relevant_id", ""))
        if not isinstance(score, (int, float)) or score <= 0:
            continue
        if role not in {"IN", "OUT"} or not family_id:
            raise RepHarnessSplitError("positive Train-250 relation has an invalid canonical role or family")
        positives[query_id][role].add(family_id)
    if set(positives) != train_set:
        raise RepHarnessSplitError("not every Train-250 query has positive relevance relations")

    strata: dict[str, list[str]] = defaultdict(list)
    stratum_meta: dict[str, tuple[str, int]] = {}
    for query_id in train:
        role_map = positives[query_id]
        relevance_count = len(set().union(*role_map.values()))
        role_set = tuple(sorted(role_map))
        key = _stratum_key(role_set, relevance_count)
        strata[key].append(query_id)
        stratum_meta[key] = ("+".join(role_set), relevance_count)
    allocations = _hamilton_rep_allocations(
        {key: len(query_ids) for key, query_ids in strata.items()},
        150,
    )

    protected_strata: list[dict[str, Any]] = []
    safe_strata: list[dict[str, Any]] = []
    rep_dev: list[str] = []
    harness_dev: list[str] = []
    for key in sorted(strata, key=_stratum_order):
        ordered = sorted(
            strata[key],
            key=lambda value: (hashlib.sha256(f"42:{value}".encode("utf-8")).hexdigest(), value),
        )
        rep_count = allocations[key]
        rep_items, harness_items = ordered[:rep_count], ordered[rep_count:]
        role_set, relevance_count = stratum_meta[key]
        protected_strata.append(
            {
                "stratum_key": key,
                "role_set": role_set,
                "relevance_count": relevance_count,
                "rep_dev": rep_items,
                "harness_dev": harness_items,
            }
        )
        safe_strata.append(
            {
                "stratum_key": key,
                "role_set": role_set,
                "relevance_count": relevance_count,
                "parent_count": len(ordered),
                "rep_dev_count": len(rep_items),
                "harness_dev_count": len(harness_items),
            }
        )
        rep_dev.extend(rep_items)
        harness_dev.extend(harness_items)
    if len(rep_dev) != 150 or len(harness_dev) != 100 or set(rep_dev) & set(harness_dev):
        raise RepHarnessSplitError("subdivision did not produce exact disjoint 150/100 membership")
    if set(rep_dev) | set(harness_dev) != train_set:
        raise RepHarnessSplitError("subdivision does not cover the frozen Train-250 parent")

    membership_hashes = {
        "parent_train_membership_sha256": canonical_sha256(sorted(train_set)),
        "rep_dev_membership_sha256": canonical_sha256(sorted(rep_dev)),
        "harness_dev_membership_sha256": canonical_sha256(sorted(harness_dev)),
    }
    protected: dict[str, Any] = {
        "schema_version": "myis.armindex-a1.2-rep-harness-protected-membership.v1",
        "decision_id": decision["decision_id"],
        "decision_sha256": decision["decision_sha256"],
        "algorithm_id": ALGORITHM_ID,
        "algorithm_source_sha256": algorithm_source_sha256,
        "seed": 42,
        "parent_split_sha256": PARENT_SPLIT_SHA256,
        "parent_split_file_sha256": PARENT_SPLIT_FILE_SHA256,
        "source_hashes": dict(sorted(source_hashes.items())),
        **membership_hashes,
        "grouping_constraints": [],
        "strata": protected_strata,
        "rep_dev": rep_dev,
        "harness_dev": harness_dev,
    }
    protected["protected_membership_sha256"] = canonical_sha256(protected)
    safe: dict[str, Any] = {
        "schema_version": "myis.armindex-a1.2-rep-harness-split-receipt.v1",
        "receipt_id": "a1.2-rep-harness-split-receipt-v1",
        "status": "PASS",
        "scientific_authority": False,
        "claim_boundary": "Aggregate-safe pre-measurement split commitment only; no query identifiers, qrels, claim text, retrieval outcomes, rankings, provider values, or execution authorization are present.",
        "decision_id": decision["decision_id"],
        "decision_sha256": decision["decision_sha256"],
        "algorithm_id": ALGORITHM_ID,
        "algorithm_source_sha256": algorithm_source_sha256,
        "seed": 42,
        "parent_split_sha256": PARENT_SPLIT_SHA256,
        "parent_split_file_sha256": PARENT_SPLIT_FILE_SHA256,
        "source_hashes": dict(sorted(source_hashes.items())),
        "counts": {"parent_train": 250, "rep_dev": 150, "harness_dev": 100},
        "strata": safe_strata,
        **membership_hashes,
        "grouping_policy": {
            "audit_result": "NO_PRIOR_FROZEN_SUBDIVISION_GROUPING_CONSTRAINT_FOUND",
            "constraint_count": 0,
            "constraint_set_sha256": canonical_sha256([]),
        },
        "protected_membership_sha256": protected["protected_membership_sha256"],
        "safety": {
            "retrieval_results_inspected": False,
            "resampling_performed": False,
            "optimization_performed": False,
            "exact_membership_exported_to_repository": False,
            "launch_allowed": False,
            "adopted_for_execution": False,
            "measured_runs": 0,
        },
    }
    return protected, safe


def _safe_signature(value: Mapping[str, Any]) -> str:
    return canonical_sha256(
        {
            "strata": value["strata"],
            "parent_train_membership_sha256": value["parent_train_membership_sha256"],
            "rep_dev_membership_sha256": value["rep_dev_membership_sha256"],
            "harness_dev_membership_sha256": value["harness_dev_membership_sha256"],
            "protected_membership_sha256": value["protected_membership_sha256"],
        }
    )


def materialize(
    repository_root: Path,
    *,
    cache_root: Path,
    parent_split_relative_path: str,
    output_relative_directory: str,
) -> dict[str, Any]:
    root = repository_root.resolve()
    decision = validate_decision(root)
    raw_store = os.environ.get("MYIS_STORE")
    if not raw_store:
        raise RepHarnessSplitError("MYIS_STORE is required")
    store = Path(raw_store).resolve(strict=True)
    if store.is_symlink() or not store.is_dir() or store.is_relative_to(root):
        raise RepHarnessSplitError("MYIS_STORE must be an external regular directory")
    parent_path = (store / parent_split_relative_path).resolve(strict=True)
    if not parent_path.is_relative_to(store) or parent_path.is_symlink() or not parent_path.is_file():
        raise RepHarnessSplitError("parent split must be a regular MYIS_STORE file")
    if file_sha256(parent_path) != PARENT_SPLIT_FILE_SHA256:
        raise RepHarnessSplitError("parent split file SHA-256 mismatch")
    output_directory = (store / output_relative_directory).resolve(strict=False)
    if not output_directory.is_relative_to(store):
        raise RepHarnessSplitError("output directory must remain below MYIS_STORE")
    output_directory.mkdir(parents=True, exist_ok=True)
    if output_directory.is_symlink() or not output_directory.is_dir():
        raise RepHarnessSplitError("output directory is unsafe")

    layout = resolve_cache(cache_root, root)
    relation_paths = tuple(path for path in layout.files["relations"] if path.suffix == ".arrow")
    parent = _read_json(parent_path, role="parent split")
    rows = list(iter_arrow_rows(relation_paths, ("query_id", "relevant_id", "relevance_score", "domain_rel")))
    source_hashes = {
        "queries_arrow_sha256": layout.input_hashes["queries_000_sha256"],
        "relations_arrow_sha256": layout.input_hashes["relations_000_sha256"],
    }
    source_sha = file_sha256(Path(__file__))
    protected, safe = derive_membership(
        parent,
        rows,
        decision=decision,
        algorithm_source_sha256=source_sha,
        source_hashes=source_hashes,
    )
    _, repeated = derive_membership(
        parent,
        rows,
        decision=decision,
        algorithm_source_sha256=source_sha,
        source_hashes=source_hashes,
    )
    _, reversed_safe = derive_membership(
        parent,
        reversed(rows),
        decision=decision,
        algorithm_source_sha256=source_sha,
        source_hashes=source_hashes,
    )
    safe["deterministic_replay"] = {
        "forward_repeat_match": _safe_signature(safe) == _safe_signature(repeated),
        "reversed_relation_input_match": _safe_signature(safe) == _safe_signature(reversed_safe),
        "parent_commitment_held_immutable": True,
        "replay_signature_sha256": _safe_signature(safe),
    }
    if not all(
        safe["deterministic_replay"][key]
        for key in ("forward_repeat_match", "reversed_relation_input_match")
    ):
        raise RepHarnessSplitError("deterministic replay failed")
    safe["receipt_sha256"] = canonical_sha256(safe)
    assert_aggregate_only(safe)

    protected_path = output_directory / PROTECTED_OUTPUT_NAME
    receipt_path = output_directory / SAFE_RECEIPT_NAME
    protected_text, receipt_text = _json_text(protected), _json_text(safe)
    for path, text, value in (
        (protected_path, protected_text, protected),
        (receipt_path, receipt_text, safe),
    ):
        if path.exists():
            if path.is_symlink() or path.read_text(encoding="ascii") != text:
                raise RepHarnessSplitError("existing immutable split output differs")
        else:
            _atomic_json(path, value)
    return {
        "status": "PASS",
        "rep_dev_count": 150,
        "harness_dev_count": 100,
        "rep_dev_membership_sha256": safe["rep_dev_membership_sha256"],
        "harness_dev_membership_sha256": safe["harness_dev_membership_sha256"],
        "receipt_sha256": safe["receipt_sha256"],
        "receipt_file_sha256": file_sha256(receipt_path),
        "protected_membership_file_sha256": file_sha256(protected_path),
        "retrieval_results_inspected": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(prog="myis-a1.2-rep-harness-split-v1")
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    parser.add_argument("--cache-root", type=Path, required=True)
    parser.add_argument("--parent-split-relative", required=True)
    parser.add_argument("--output-relative", required=True)
    args = parser.parse_args()
    result = materialize(
        args.repository_root,
        cache_root=args.cache_root,
        parent_split_relative_path=args.parent_split_relative,
        output_relative_directory=args.output_relative,
    )
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
