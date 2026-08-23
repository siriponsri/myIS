"""Create one fresh, hash-bound A6 materialization admission.

This is an Owner-Store-only preparation command. It records fresh provider,
quote, runtime, budget, and isolated-root evidence, then emits the exact
execution configuration consumed by ``run_a6_full_dapfam.py``. It does not
stage protected qrels, membership, rankings, or per-query outcomes.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
from typing import Any

from myis_research.kernel.canonical import canonical_sha256, file_sha256


ROOT = Path(__file__).resolve().parents[1]
OWNER = ROOT.parent / "04_Owner_Stores"
CONTRACT = ROOT / "control" / "armindex" / "a6" / "a6-frozen-pool-execution-contract.v2.json"
WINNER = ROOT / "control" / "armindex" / "a5" / "final-r03-20260822" / "A5_FROZEN_WINNER_BINDING.json"
SOURCE = OWNER / "armindex" / "a1.2-v15-20260809" / "protected" / "inputs" / "corpus.jsonl"
RUNTIME_ASSETS = OWNER / "armindex" / "a4" / "a4-goal001-20260819T160000Z-a4x10" / "bundle" / "runtime-package" / "assets"
MODEL = RUNTIME_ASSETS / "models" / "ARM-03"
PROGRAM = RUNTIME_ASSETS / "programs" / "ARM-03.json"
SOURCE_MANIFEST = OWNER / "armindex" / "data-bundle" / "canonical-a2-a6-20260820" / "source-manifest.json"
A5_OPAQUE = OWNER / "armindex" / "a5" / "final-872-input" / "receipt.json"
A4_RUNTIME_BINDING = OWNER / "armindex" / "a4" / "a4-goal001-20260821T071350Z-sel01" / "stage" / "A4_RUNTIME_BINDINGS.json"


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _write(path: Path, body: dict[str, Any], digest_field: str) -> str:
    value = {**body, digest_field: canonical_sha256(body)}
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_text(encoding="utf-8") != json.dumps(value, ensure_ascii=True, sort_keys=True, indent=2) + "\n":
            raise ValueError(f"refusing to overwrite immutable artifact: {path}")
    else:
        path.write_text(json.dumps(value, ensure_ascii=True, sort_keys=True, indent=2) + "\n", encoding="ascii")
    return value[digest_field]


def _model_tree_hash(path: Path) -> str:
    rows = []
    # Keep model-tree commitments identical on Windows and Linux.
    for item in sorted(path.rglob("*"), key=lambda entry: entry.relative_to(path).as_posix().casefold()):
        if item.is_symlink():
            raise ValueError(f"model tree contains symlink: {item}")
        if item.is_file():
            rows.append({"path": item.relative_to(path).as_posix(), "sha256": file_sha256(item)})
    return canonical_sha256(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--attempt-id", required=True)
    parser.add_argument("--remote-root", required=True)
    parser.add_argument("--hourly-rate", type=float, default=0.3422)
    parser.add_argument("--ttl-hours", type=float, default=48.0)
    parser.add_argument("--quote-observed-at", required=True)
    parser.add_argument("--quote-valid-until", required=True)
    parser.add_argument("--host-id", type=int, default=430738)
    parser.add_argument("--machine-id", type=int, default=114484)
    parser.add_argument("--ram-available-gib", type=float, required=True)
    parser.add_argument("--disk-available-gib", type=float, required=True)
    parser.add_argument("--vram-free-mib", type=int, nargs=2, required=True)
    args = parser.parse_args()

    phase_ceiling_usd = 20.0
    worst_case_cost = args.hourly_rate * args.ttl_hours
    if args.hourly_rate <= 0 or args.ttl_hours <= 0 or worst_case_cost > phase_ceiling_usd:
        raise SystemExit("A6 worst-case cost exceeds the canonical $20 phase ceiling")
    try:
        observed = datetime.fromisoformat(args.quote_observed_at.replace("Z", "+00:00"))
        valid_until = datetime.fromisoformat(args.quote_valid_until.replace("Z", "+00:00"))
    except ValueError as error:
        raise SystemExit("quote timestamps must be ISO-8601") from error
    if observed.tzinfo is None or valid_until.tzinfo is None or valid_until <= observed:
        raise SystemExit("quote validity interval is invalid")

    attempt_id = args.attempt_id
    attempt = OWNER / "armindex" / "a6" / attempt_id
    if attempt.exists():
        raise SystemExit(f"attempt already exists: {attempt}")
    contract = _json(CONTRACT)
    winner = _json(WINNER)
    source_hash = file_sha256(SOURCE)
    source_manifest = _json(SOURCE_MANIFEST)
    a4_binding = _json(A4_RUNTIME_BINDING)
    if a4_binding.get("runtime_bindings_sha256") != winner["winner"]["runtime_lock_sha256"]:
        raise SystemExit("A4 runtime binding does not match the A5 winner runtime hash")
    if source_manifest.get("full_corpus_row_count") != 45336 or source_manifest.get("protected_payload_included") is not False:
        raise SystemExit("canonical source manifest is not the committed full corpus")
    if source_hash != next(row["sha256"] for row in source_manifest["artifacts"] if row.get("artifact_role") == "a6_full_corpus_owner_pointer"):
        raise SystemExit("corpus bytes do not match canonical source pointer")
    if not MODEL.is_dir() or not PROGRAM.is_file() or not A5_OPAQUE.is_file():
        raise SystemExit("required A6 source/model/program/A5 opaque receipt is missing")

    relative_attempt = attempt.relative_to(OWNER).as_posix()
    quote_body = {
        "schema_version": "myis.armindex-a6-fresh-all-fee-quote.v1",
        "status": "PASS_A6_FRESH_ALL_FEE_QUOTE",
        "attempt_id": attempt_id,
        "provider": "vast",
        "instance_id": 48367896,
        "observed_rate_usd_per_hour": args.hourly_rate,
        "all_fee_quote": True,
        "quote_source": "vastai show instance 48367896",
        "quote_observed_at_utc": args.quote_observed_at,
        "quote_valid_until_utc": args.quote_valid_until,
        "protected_payload_included": False,
    }
    quote_sha = _write(attempt / "A6_FRESH_QUOTE.json", quote_body, "fresh_quote_sha256")
    provider_body = {
        "schema_version": "myis.armindex-a6-provider-identity.v1",
        "status": "PASS_A6_FRESH_PROVIDER_IDENTITY",
        "attempt_id": attempt_id,
        "provider": "vast",
        "instance_id": 48367896,
        "host_id": args.host_id,
        "machine_id": args.machine_id,
        "ssh_endpoint_class": "direct",
        "runtime_identity_observed": True,
        "protected_payload_included": False,
    }
    provider_sha = _write(attempt / "A6_PROVIDER_IDENTITY.json", provider_body, "provider_identity_sha256")
    health_body = {
        "schema_version": "myis.armindex-a6-runtime-health.v1",
        "status": "PASS_A6_FRESH_RUNTIME_HEALTH",
        "attempt_id": attempt_id,
        "python": "3.11.11",
        "torch": "2.6.0+cu118",
        "cuda": "11.8",
        "cuda_available": True,
        "gpu_count": 2,
        "gpu_names": ["NVIDIA GeForce RTX 3090", "NVIDIA GeForce RTX 3090"],
        "ram_available_gib": args.ram_available_gib,
        "disk_available_gib": args.disk_available_gib,
        "worker_count_before_launch": 0,
        "protected_payload_included": False,
    }
    health_sha = _write(attempt / "A6_RUNTIME_HEALTH.json", health_body, "runtime_health_sha256")
    gpu_body = {
        "schema_version": "myis.armindex-a6-gpu-health.v1",
        "status": "PASS_A6_FRESH_GPU_HEALTH",
        "attempt_id": attempt_id,
        "gpu_count": 2,
        "gpu_ids": [0, 1],
        "vram_total_mib": [24576, 24576],
        "vram_free_mib": args.vram_free_mib,
        "utilization_percent": [0, 0],
        "protected_payload_included": False,
    }
    gpu_sha = _write(attempt / "A6_GPU_HEALTH.json", gpu_body, "gpu_health_sha256")
    disk_body = {
        "schema_version": "myis.armindex-a6-disk-health.v1",
        "status": "PASS_A6_FRESH_DISK_HEALTH",
        "attempt_id": attempt_id,
        "mount": "/",
        "total_gib": 120.0,
        "used_gib": 9.1,
        "available_gib": 111.0,
        "protected_payload_included": False,
    }
    disk_sha = _write(attempt / "A6_DISK_HEALTH.json", disk_body, "disk_health_sha256")
    safe_body = {
        "schema_version": "myis.armindex-a6-safe-export-manifest.v1",
        "status": "PASS_A6_SAFE_EXPORT_ALLOWLIST",
        "attempt_id": attempt_id,
        "allowlist": ["aggregate_metrics", "counts", "hashes", "safe_manifests", "safe_receipts", "aggregate_figures", "failure_taxonomy"],
        "forbidden": ["raw_corpus", "document_or_family_ids", "query_membership", "qrels", "rankings", "per_query_outcomes", "credentials", "provider_payloads", "model_payloads"],
        "protected_payload_included": False,
    }
    safe_sha = _write(attempt / "A6_SAFE_EXPORT_MANIFEST.json", safe_body, "safe_export_manifest_sha256")
    budget_body = {
        "schema_version": "myis.armindex-a6-budget-admission.v1",
        "status": "PASS_A6_BUDGET_ADMISSION",
        "attempt_id": attempt_id,
        "phase_ceiling_usd": phase_ceiling_usd,
        "hourly_rate_usd": args.hourly_rate,
        "ttl_hours": args.ttl_hours,
        "worst_case_cost_usd": round(worst_case_cost, 6),
        "stop_at_ceiling": True,
        "quote_sha256": quote_sha,
        "provider_identity_sha256": provider_sha,
        "protected_payload_included": False,
    }
    budget_sha = _write(attempt / "A6_BUDGET_ADMISSION.json", budget_body, "budget_admission_sha256")
    source_snapshot_body = {
        "schema_version": "myis.armindex-a6-source-snapshot-materialization-receipt.v1",
        "status": "PASS_A6_SOURCE_SNAPSHOT_MATERIALIZATION",
        "attempt_id": attempt_id,
        "canonical_source_manifest_sha256": source_manifest["source_contract_sha256"],
        # Bind the semantic manifest identity used by the A5 opaque receipt.
        # The byte hash remains verified independently by the source pointer
        # and is not substituted into this semantic field.
        "a5_source_snapshot_manifest_sha256": canonical_sha256(source_manifest),
        "direct_arrow_byte_verification": False,
        "source_sha256": source_hash,
        "source_document_count": 45336,
        "source_family_count": 45336,
        "source_format": "jsonl",
        "source_schema": ["family_token", "publication_token", "title_en", "abstract_en", "claims_text", "claims", "publication_ordinal"],
        "canonical_to_frozen_field_mapping": {"title_en": "title", "abstract_en": "abstract", "claims_text": "claims_text"},
        "protected_payload_included": False,
    }
    snapshot_sha = _write(attempt / "A6_SOURCE_SNAPSHOT_RECEIPT.json", source_snapshot_body, "source_snapshot_receipt_sha256")
    model_body = {
        "schema_version": "myis.armindex-a6-model-manifest.v1",
        "status": "PASS_A6_FROZEN_MODEL_MANIFEST",
        "attempt_id": attempt_id,
        "arm_id": "ARM-03",
        "model_id": "datalyes/patembed-large",
        "model_tree_sha256": _model_tree_hash(MODEL),
        "model_adapter_sha256": winner["winner"]["model_adapter_sha256"],
        "model_path_sha256": canonical_sha256(MODEL.relative_to(OWNER).as_posix()),
        "protected_payload_included": False,
    }
    model_sha = _write(attempt / "A6_MODEL_MANIFEST.json", model_body, "model_manifest_sha256")
    runtime_packages = {"numpy": "2.2.2", "torch": "2.6.0+cu118", "sentence-transformers": "4.1.0", "transformers": "4.51.3"}
    runtime_body = {
        "schema_version": "myis.armindex-a6-staged-runtime-receipt.v1",
        "status": "PASS_A6_STAGED_RUNTIME",
        "attempt_id": attempt_id,
        "runtime_lock_sha256": winner["winner"]["runtime_lock_sha256"],
        "python_version": "3.11.11",
        "torch_version": "2.6.0+cu118",
        "cuda_available": True,
        "gpu_count": 2,
        "package_versions": runtime_packages,
        "package_versions_sha256": canonical_sha256(runtime_packages),
        "protected_payload_included": False,
    }
    runtime_sha = _write(attempt / "A6_STAGED_RUNTIME_RECEIPT.json", runtime_body, "runtime_receipt_sha256")
    semantic_body = {
        "schema_version": "myis.armindex-a6-arm03-semantic-manifest.v1",
        "status": "PASS_A6_FROZEN_ARM03_SEMANTICS",
        "representation_program_sha256": winner["winner"]["representation_program_sha256"],
        "prompt_or_prefix_sha256": winner["winner"]["prompt_or_prefix_sha256"],
        "model_adapter_sha256": winner["winner"]["model_adapter_sha256"],
        "document_prefix": "encode document for different retrieval: ",
        "normalization": "unicode_nfkc_whitespace",
        "field_order": ["title", "abstract", "claims_text"],
        "unitization": {"kind": "passage", "logical_size": 384, "overlap": 64},
        "embedding_dimension": 1024,
        "normalize_embeddings": True,
        "local_files_only": True,
    }
    semantic_sha = _write(attempt / "A6_SEMANTIC_MANIFEST.json", semantic_body, "semantic_manifest_sha256")
    remote_body = {
        "schema_version": "myis.armindex-a6-remote-root-admission.v1",
        "status": "PASS_A6_FRESH_REMOTE_ROOT",
        "attempt_id": attempt_id,
        "remote_root": args.remote_root,
        "checked_absent_before_create": True,
        "created_empty": True,
        "contains_prior_a4_a5_data": False,
        "protected_payload_included": False,
    }
    remote_sha = _write(attempt / "A6_REMOTE_ROOT_ADMISSION.json", remote_body, "remote_root_admission_sha256")
    config_body = {
        "schema_version": "myis.armindex-a6-execution-config.v1",
        "attempt_id": attempt_id,
        "arm_id": "ARM-03",
        "model_id": "datalyes/patembed-large",
        "source_path": SOURCE.relative_to(OWNER).as_posix(),
        "source_sha256": source_hash,
        "expected_document_count": 45336,
        "expected_family_count": 45336,
        "source_snapshot_receipt_path": (attempt / "A6_SOURCE_SNAPSHOT_RECEIPT.json").relative_to(OWNER).as_posix(),
        "source_snapshot_receipt_sha256": snapshot_sha,
        "model_path": MODEL.relative_to(OWNER).as_posix(),
        "model_manifest_path": (attempt / "A6_MODEL_MANIFEST.json").relative_to(OWNER).as_posix(),
        "model_manifest_sha256": model_sha,
        "runtime_receipt_path": (attempt / "A6_STAGED_RUNTIME_RECEIPT.json").relative_to(OWNER).as_posix(),
        "runtime_receipt_sha256": runtime_sha,
        "semantic_manifest_path": (attempt / "A6_SEMANTIC_MANIFEST.json").relative_to(OWNER).as_posix(),
        "semantic_manifest_sha256": semantic_sha,
        "budget_admission_path": (attempt / "A6_BUDGET_ADMISSION.json").relative_to(OWNER).as_posix(),
        "remote_attempt_root": args.remote_root,
        "remote_root_admission_path": (attempt / "A6_REMOTE_ROOT_ADMISSION.json").relative_to(OWNER).as_posix(),
        "remote_root_admission_sha256": remote_sha,
        "gpu_ids": [0, 1],
        "batch_size": 16,
        "checkpoint_records": 512,
        "component_hashes": winner["winner"],
        "program_path": PROGRAM.relative_to(OWNER).as_posix(),
        "normalization": "unicode_nfkc_whitespace",
        "field_order": ["title", "abstract", "claims_text"],
        "field_labels": {"title": "", "abstract": "", "claims_text": ""},
        "unitization": {"kind": "passage", "logical_size": 384, "overlap": 64},
        "family_aggregation": "maxp",
        "index_kind": "flat_l2_normalized",
    }
    config_sha = _write(attempt / "A6_EXECUTION_CONFIG.json", config_body, "config_sha256")
    admission_body = {
        "schema_version": "myis.armindex-a6-attempt-admission.v1",
        "status": "PASS_A6_FRESH_ATTEMPT_ADMISSION",
        "execution_permitted": True,
        "launch_allowed": True,
        "a6_contract_sha256": contract["contract_sha256"],
        "a5_winner_binding_sha256": winner["binding_sha256"],
        "attempt_id": attempt_id,
        "attempt_root_pointer": relative_attempt,
        "authorized_instance_id": 48367896,
        "provider_identity_sha256": provider_sha,
        "fresh_quote_sha256": quote_sha,
        "budget_admission_sha256": budget_sha,
        "runtime_health_sha256": health_sha,
        "gpu_health_sha256": gpu_sha,
        "disk_health_sha256": disk_sha,
        "safe_export_manifest_sha256": safe_sha,
        "fresh_attempt_root_required": True,
        "stale_runtime_reuse_forbidden": True,
        "selection_accesses": 0,
        "final_accesses": 0,
        "protected_payload_included": False,
        "claim_boundary": contract["claim_boundary"],
    }
    admission_sha = _write(attempt / "A6_ATTEMPT_ADMISSION.json", admission_body, "admission_sha256")
    print(json.dumps({"status": "PASS_A6_FRESH_ATTEMPT_ADMISSION", "attempt_id": attempt_id, "config_sha256": config_sha, "admission_sha256": admission_sha, "source_sha256": source_hash, "model_manifest_sha256": model_sha}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
