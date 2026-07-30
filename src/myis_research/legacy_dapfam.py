"""Read-only discovery and owner-local adapter for the legacy DAPFAM tree.

The discovery surface is metadata-only by default.  The owner-local execution
path may open protected query/qrels/split bytes, but it emits only hashes,
counts, aggregate metrics, and lineage.  No legacy file is moved, overwritten,
regenerated, or copied into Git.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator

from .kernel.canonical import canonical_sha256, file_sha256


PROTECTED_NAME_RE = re.compile(r"(?:qrel|query|split|membership|per[_-]?query|outcome|^ids(?:_|\.jsonl$))", re.I)
PAPER_EXPOSURE_NAMES = ("paper-a", "paper-b", "paper-d")
ACTIVE_SPLIT_SEED = 42
ACTIVE_SPLIT_ALGORITHM = "seeded-sha256-query-membership-v1"
LEGACY_ASSET_ID = "APP-DAPFAM-PROTECTED"
LEGACY_REQUEST_ID = "legacy-dapfam-p1-cpu-s42-commitment-v2"


@dataclass(frozen=True)
class LegacyAsset:
    path: str
    bytes: int
    kind: str
    disposition: str
    sha256: str | None
    note: str

    def as_safe_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "bytes": self.bytes,
            "kind": self.kind,
            "disposition": self.disposition,
            "sha256": self.sha256,
            "note": self.note,
        }


def is_protected_path(path: Path) -> bool:
    return bool(PROTECTED_NAME_RE.search(path.name) or PROTECTED_NAME_RE.search(str(path.parent)))


def classify_path(relative: str) -> tuple[str, str, str]:
    lower = relative.casefold().replace("\\", "/")
    name = lower.rsplit("/", 1)[-1]
    if name in {"patents.jsonl", "chunks_doc.jsonl"}:
        return ("processed_corpus", "reusable-after-certification", "safe corpus candidate")
    if name in {"chunks_section.jsonl", "chunks_claim.jsonl"}:
        return ("representation", "historical-reference", "not an active P1 corpus candidate")
    if name == "chunks_element.jsonl":
        return ("representation", "incompatible", "2,234,841 rows exceed the DAPFAM four-unit R1 limit")
    if name in {"qrels.tsv", "qrels_domain.tsv", "queries.jsonl", "queries_tac.jsonl"}:
        return ("protected_evaluator_input", "reusable-after-certification", "owner-local process only")
    if name == "dev_test_split.json":
        return ("historical_split_commitment", "historical-reference", "historically exposed Paper-D split")
    if name == "index.sqlite":
        return ("bm25_index", "reusable-after-certification", "reuse only after full lineage match")
    if name.endswith("embedding_manifest.json") or "embedding_manifest__" in name:
        return ("embedding_manifest", "historical-reference", "not used by P1 lexical baseline")
    if name.endswith(".npy") or name.endswith(".arrow"):
        return ("raw_or_embedding_cache", "reference_only", "read-only source bytes")
    if name == "manifest.json" or name.endswith("validation_summary.json"):
        return ("manifest", "reusable-after-certification", "metadata/provenance only")
    if "paper" in lower or "results" in lower or "test-997" in lower:
        return ("historical_reference", "historical-reference", "Paper A/B/D evidence is exposed history")
    if name.endswith(".md") or name.endswith(".csv"):
        return ("documentation_or_table", "historical-reference", "not a P1 numeric source")
    return ("other", "reference_only", "not selected by the active P1 adapter")


def discover_legacy(root: Path, *, include_protected_hashes: bool = False) -> dict[str, Any]:
    """Inventory a legacy root without reading protected payload contents."""

    root = root.resolve()
    if not root.is_dir() or root.is_symlink():
        raise ValueError("legacy root must be a regular directory")
    assets: list[LegacyAsset] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(root).as_posix()
        kind, disposition, note = classify_path(relative)
        protected = is_protected_path(path)
        digest = file_sha256(path) if (include_protected_hashes or not protected) else None
        if protected and not include_protected_hashes:
            note = f"{note}; hash withheld outside owner-local process"
        assets.append(LegacyAsset(relative, path.stat().st_size, kind, disposition, digest, note))
    candidates = {
        "patents": _first_existing(root, ("processed/dapfam/patents.jsonl",)),
        "queries": _first_existing(root, ("processed/dapfam/queries.jsonl", "processed/retrieval/dapfam_citation_controlled_tac512/queries_tac.jsonl")),
        "qrels": _first_existing(root, ("processed/dapfam/qrels.tsv",)),
        "qrels_domain": _first_existing(root, ("processed/retrieval/dapfam_citation_controlled_tac512/qrels_domain.tsv", "processed/retrieval/dapfam_citation_controlled_tac512_v2/qrels_domain.tsv")),
        "chunks_doc": _first_existing(root, ("processed/dapfam/chunks_doc.jsonl",)),
        "chunks_tac": _first_existing(root, ("processed/retrieval/dapfam_citation_controlled_tac512/corpus_tac_passages.jsonl", "processed/retrieval/dapfam_citation_controlled_tac512_v2/corpus_tac_passages.jsonl")),
    }
    found = {key: value for key, value in candidates.items() if value is not None}
    safe_hashes = {asset.path: asset.sha256 for asset in assets if asset.sha256 is not None}
    return {
        "schema_version": "myis.legacy-dapfam-inventory.v1",
        "root": LEGACY_ASSET_ID,
        "asset_count": len(assets),
        "assets": [asset.as_safe_dict() for asset in assets],
        "candidates": found,
        "safe_file_hashes": safe_hashes,
        "protected_assets_owner_local_only": [asset.path for asset in assets if asset.sha256 is None],
        "paper_d_copies": _paper_d_copy_inventory(root),
        "paper_history": {
            "paper_a": "historically_exposed",
            "paper_b": "historically_exposed",
            "paper_d": "historically_exposed",
            "paper_d_test_997": "historically_exposed",
            "active_final_872_global_untouched": "not_claimable",
        },
    }


def build_input_hashes(root: Path, inventory: dict[str, Any], *, include_protected: bool = True) -> dict[str, str]:
    """Hash discovered input files inside the owner-local process."""

    hashes: dict[str, str] = {}
    for key, relative in sorted((inventory.get("candidates") or {}).items()):
        path = (root / str(relative)).resolve()
        path.relative_to(root.resolve())
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"discovered input is missing or unsafe: {key}")
        if include_protected or not is_protected_path(path):
            hashes[f"{key}_sha256"] = file_sha256(path)
    return hashes


def build_request_scope(root: Path, inventory: dict[str, Any], repository_root: Path) -> dict[str, str]:
    """Build hash-only request bindings inside the owner-local process.

    The active and historical split memberships are read only to construct
    SHA-256 commitments. Their member IDs never leave this function.
    """

    root = root.resolve()
    repository_root = repository_root.resolve()
    candidates = inventory.get("candidates") or {}
    queries_relative = candidates.get("queries")
    if not isinstance(queries_relative, str):
        raise ValueError("legacy query source is required for the active split commitment")
    query_path = _contained_regular_file(root, queries_relative)
    return {
        "campaign_sha256": file_sha256(repository_root / "control" / "campaigns" / "scope-autoindex-v1.yaml"),
        "envelope_sha256": file_sha256(repository_root / "control" / "execution-envelope.yaml"),
        "inventory_sha256": canonical_sha256(inventory),
        "active_seed42_split_membership_sha256": _active_split_commitment(query_path),
        "paper_d_split_membership_sha256": _paper_d_split_commitment(root),
        "legacy_adapter_code_sha256": file_sha256(repository_root / "src" / "myis_research" / "legacy_dapfam.py"),
        "legacy_cli_code_sha256": file_sha256(repository_root / "src" / "myis_research" / "legacy_dapfam_cli.py"),
        "legacy_certifier_code_sha256": file_sha256(repository_root / "scripts" / "legacy_dapfam_certify.py"),
        "owner_local_runner_code_sha256": file_sha256(repository_root / "src" / "myis_research" / "owner_local_runner.py"),
        "p1_evaluator_code_sha256": file_sha256(repository_root / "src" / "myis_research" / "kernel" / "p1.py"),
        "request_schema_sha256": file_sha256(repository_root / "control" / "owner-local" / "request.schema.json"),
        "receipt_schema_sha256": file_sha256(repository_root / "control" / "owner-local" / "receipt.schema.json"),
    }


def build_legacy_p1_request(root: Path, repository_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build the one supported legacy P1 request from current local bytes."""

    root = root.resolve()
    repository_root = repository_root.resolve()
    inventory = discover_legacy(root, include_protected_hashes=False)
    owner_inventory = discover_legacy(root, include_protected_hashes=True)
    request = {
        "schema_version": "myis.owner-local-request.v2",
        "request_id": LEGACY_REQUEST_ID,
        "decision_id": "P1_CPU_EXECUTION_ENVELOPE",
        "phase_id": "P1_CPU_BASELINE",
        "stage": "train_selection",
        "scope": build_request_scope(root, inventory, repository_root),
        "git_commit": current_git_commit(repository_root),
        "input_hashes": dict(sorted(build_input_hashes(root, owner_inventory, include_protected=True).items())),
    }
    assert_legacy_p1_request_current(request, root, repository_root)
    return inventory, request


def assert_legacy_p1_request_current(request: dict[str, Any], root: Path, repository_root: Path) -> None:
    """Fail closed unless every request binding exactly matches current bytes."""

    root = root.resolve()
    repository_root = repository_root.resolve()
    inventory = discover_legacy(root, include_protected_hashes=False)
    owner_inventory = discover_legacy(root, include_protected_hashes=True)
    expected_scope = build_request_scope(root, inventory, repository_root)
    expected_input_hashes = dict(sorted(build_input_hashes(root, owner_inventory, include_protected=True).items()))
    if request.get("request_id") != LEGACY_REQUEST_ID:
        raise ValueError("legacy request ID is not current")
    if request.get("git_commit") != current_git_commit(repository_root):
        raise ValueError("legacy request git_commit does not match HEAD")
    if request.get("scope") != expected_scope:
        raise ValueError("legacy request scope does not match current bindings")
    if request.get("input_hashes") != expected_input_hashes:
        raise ValueError("legacy request input hashes do not match current files")


def current_git_commit(repository_root: Path) -> str:
    try:
        commit = subprocess.check_output(
            ["git", "-C", str(repository_root.resolve()), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError) as error:
        raise ValueError("legacy request requires an accessible Git HEAD") from error
    if not re.fullmatch(r"[a-f0-9]{40}", commit):
        raise ValueError("legacy request Git HEAD is invalid")
    return commit


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"invalid JSONL at {path}:{number}") from error
            if not isinstance(value, dict):
                raise ValueError(f"JSONL row must be an object at {path}:{number}")
            yield value


def pick(row: dict[str, Any], names: Iterable[str], *, required: bool = True) -> str:
    for name in names:
        value = row.get(name)
        if value is not None and str(value).strip():
            return str(value).strip()
    if required:
        raise ValueError(f"legacy row missing required field candidates: {tuple(names)}")
    return ""


def text_value(row: dict[str, Any], names: Iterable[str]) -> str:
    values: list[str] = []
    for name in names:
        value = row.get(name)
        if isinstance(value, list):
            values.extend(str(item) for item in value if str(item).strip())
        elif value is not None and str(value).strip():
            values.append(str(value))
    return "\n".join(values).strip()


def _first_existing(root: Path, candidates: Iterable[str]) -> str | None:
    for relative in candidates:
        path = root / relative
        if path.is_file() and not path.is_symlink():
            return relative.replace("\\", "/")
    return None


def legacy_project_root(root: Path) -> Path:
    root = root.resolve()
    if root.name == "data" and root.parent.name == "shared":
        return root.parents[1]
    return root


def _paper_d_root(root: Path) -> Path:
    return legacy_project_root(root) / "paper-d"


def _paper_d_copy_inventory(root: Path) -> dict[str, Any]:
    """Summarize Paper-D copies without hashing or opening their payloads."""

    paper_d_root = _paper_d_root(root)
    if not paper_d_root.is_dir() or paper_d_root.is_symlink():
        return {
            "status": "not_found",
            "disposition": "historical-reference",
            "content_hashes": "owner_local_only",
        }
    file_count = 0
    byte_count = 0
    protected_named_file_count = 0
    split_named_file_count = 0
    for path in paper_d_root.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        file_count += 1
        byte_count += path.stat().st_size
        if is_protected_path(path):
            protected_named_file_count += 1
        if "split" in path.name.casefold():
            split_named_file_count += 1
    return {
        "status": "present",
        "path": "paper-d",
        "file_count": file_count,
        "bytes": byte_count,
        "protected_named_file_count": protected_named_file_count,
        "split_named_file_count": split_named_file_count,
        "disposition": "historical-reference",
        "content_hashes": "owner_local_only",
    }


def _contained_regular_file(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError as error:
        raise ValueError("discovered path escapes legacy root") from error
    if not path.is_file() or path.is_symlink():
        raise ValueError("discovered input is missing or unsafe")
    return path


def _active_split_commitment(query_path: Path) -> str:
    query_ids = [pick(row, ("query_id", "qid", "id")) for row in iter_jsonl(query_path)]
    ordered = sorted(set(query_ids), key=lambda value: hashlib.sha256(f"{ACTIVE_SPLIT_SEED}:{value}".encode("utf-8")).hexdigest())
    return canonical_sha256({
        "algorithm": ACTIVE_SPLIT_ALGORITHM,
        "seed": ACTIVE_SPLIT_SEED,
        "train": ordered[:250],
        "selection": ordered[250:375],
        "final": ordered[375:],
    })


def _paper_d_split_commitment(root: Path) -> str:
    paper_d_root = _paper_d_root(root)
    split_paths = []
    if paper_d_root.is_dir() and not paper_d_root.is_symlink():
        split_paths = [
            path for path in sorted((paper_d_root / "config").glob("*split*.json"))
            if path.is_file() and not path.is_symlink()
        ] if (paper_d_root / "config").is_dir() else []
    return canonical_sha256({
        "algorithm": "paper-d-raw-split-file-set-v1",
        "files": {
            path.relative_to(legacy_project_root(root)).as_posix(): file_sha256(path)
            for path in split_paths
        },
    })
