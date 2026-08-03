"""Deterministic builders for the adopted P2 base search contract."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

from ..kernel.canonical import canonical_sha256, file_sha256
from .measured_contracts import committed_blob_sha256, scientific_payload_sha256


SOURCE_CONTRACT_URI = "control/assets/dapfam-p1-source.v1.json"
COMPILER_URI = "src/myis_research/scope/compiler.py"
BASE_SET_URI = "control/p2/p2-base-candidate-set-r1-v2.json"
ADAPTIVE_POLICY_URI = "control/p2/p2-adaptive-policy-r1-v2.json"
PROPOSER_CONTRACT_URI = "control/p2/p2-proposer-contract-r1-v2.json"
CAMPAIGN_REVISION = "scope-autoindex-v1-p2-r1-primary-v2"


def build_base_candidate_set(repository_root: Path, *, committed_hashes: bool = True) -> dict[str, Any]:
    root = Path(repository_root).resolve()
    hash_reader = committed_blob_sha256 if committed_hashes else _working_sha256
    controls = [
        _candidate(
            "p2-control-r0-flat-bm25", "frozen_control", "R0", "baseline",
            "Full TAC family document reproduces the flat P1 lexical baseline.",
            "unitization", None, _scope_spec("r0-flat", 1, "document", ("title_en", "abstract_en", "claims_text"), "joined_document"),
            _axes(fields="title_abstract_claims", unitization="document", span=0, stride=0, composition="single", duplicate="family_first"),
            aggregation="family_first",
        ),
        _candidate(
            "p2-control-r0-window-maxp", "frozen_control", "R0-W", "control",
            "Non-overlapping 512-token full TAC windows reproduce the P1 incumbent.",
            "unitization", "p2-control-r0-flat-bm25", _scope_spec("r0-window", 2, "passage", ("title_en", "abstract_en", "claims_text"), "token_passages", window_tokens=512, stride_tokens=512),
            _axes(fields="title_abstract_claims", unitization="passage", span=512, stride=512, composition="single", duplicate="family_maxp"),
            aggregation="family_maxp",
        ),
        _candidate(
            "p2-control-r1-document-grounded", "frozen_control", "R1", "control",
            "A grounded one-unit R1 document isolates representation metadata from retrieval changes.",
            "unitization", "p2-control-r1-passage-maxp", _scope_spec("r1-doc-control", 3, "document", ("title_en", "abstract_en", "claims_text"), "joined_document"),
            _axes(fields="title_abstract_claims", unitization="document", span=0, stride=0, composition="single", duplicate="family_first"),
            aggregation="family_first",
        ),
        _candidate(
            "p2-control-r1-passage-maxp", "frozen_control", "R1", "matched_ablation",
            "A grounded 512-token R1 passage view tests the unitization axis against the document control.",
            "unitization", "p2-control-r1-document-grounded", _scope_spec("r1-passage-control", 4, "passage", ("title_en", "abstract_en", "claims_text"), "token_passages", window_tokens=512, stride_tokens=512),
            _axes(fields="title_abstract_claims", unitization="passage", span=512, stride=512, composition="single", duplicate="family_maxp"),
            aggregation="family_maxp",
        ),
    ]
    candidates = [
        _candidate("p2-r1-tac-document", "preregistered_patent", "R1", "candidate", "A canonical grounded TAC document may retain useful family evidence.", "unitization", "p2-control-r1-passage-maxp", _scope_spec("r1-tac-doc", 5, "document", ("title_en", "abstract_en", "claims_text"), "joined_document"), _axes(fields="title_abstract_claims", unitization="document", span=0, stride=0, composition="single", duplicate="family_first"), aggregation="family_first"),
        _candidate("p2-r1-title-abstract", "preregistered_patent", "R1", "candidate", "Removing claim boilerplate may improve lexical exposure for descriptive patent concepts.", "source_fields", "p2-r1-tac-document", _scope_spec("r1-title-abstract", 6, "document", ("title_en", "abstract_en"), "joined_document"), _axes(fields="title_abstract", unitization="document", span=0, stride=0, composition="single", duplicate="family_first"), aggregation="family_first"),
        _candidate("p2-r1-claim-view", "preregistered_patent", "R1", "candidate", "A claims-only document may concentrate limitation-bearing language.", "source_fields", "p2-r1-tac-document", _scope_spec("r1-claim-view", 7, "claim", ("claims_text",), "joined_document"), _axes(fields="claims", unitization="document", span=0, stride=0, composition="single", duplicate="family_first"), aggregation="family_first"),
        _candidate("p2-r1-section-view", "preregistered_patent", "R1", "candidate", "Separate title, abstract, and claims units may expose matches hidden by document length.", "unitization", "p2-r1-tac-document", _scope_spec("r1-section-view", 8, "section", ("title_en", "abstract_en", "claims_text"), "field_sections"), _axes(fields="title_abstract_claims", unitization="section", span=0, stride=0, composition="single", duplicate="family_maxp"), aggregation="family_maxp"),
        _candidate("p2-r1-claim-element-view", "preregistered_patent", "R1", "candidate", "Deterministic claim elements may expose limitation matches more directly than a claims document.", "unitization", "p2-r1-claim-view", _scope_spec("r1-claim-elements", 9, "claim", ("claims_text",), "claim_elements"), _axes(fields="claims", unitization="claim_element", span=0, stride=0, composition="single", duplicate="family_maxp"), aggregation="family_maxp"),
        _candidate("p2-r1-passage-256-maxp", "preregistered_patent", "R1", "candidate", "Short 256-token passages may increase local lexical exposure.", "passage_span", "p2-r1-passage-512-maxp", _scope_spec("r1-passage-256", 10, "passage", ("title_en", "abstract_en", "claims_text"), "token_passages", window_tokens=256, stride_tokens=256), _axes(fields="title_abstract_claims", unitization="passage", span=256, stride=256, composition="single", duplicate="family_maxp"), aggregation="family_maxp"),
        _candidate("p2-r1-passage-512-maxp", "preregistered_patent", "R1", "matched_ablation", "The P1-aligned 512-token passage span is the matched span ablation.", "passage_span", "p2-r1-passage-256-maxp", _scope_spec("r1-passage-512", 11, "passage", ("title_en", "abstract_en", "claims_text"), "token_passages", window_tokens=512, stride_tokens=512), _axes(fields="title_abstract_claims", unitization="passage", span=512, stride=512, composition="single", duplicate="family_maxp"), aggregation="family_maxp"),
        _candidate("p2-r1-multiview-maxp", "preregistered_patent", "R1", "candidate", "A title-abstract view plus a claims view may preserve complementary evidence within the four-unit limit.", "view_composition", "p2-r1-section-view", _scope_spec("r1-multiview", 12, "section", ("title_en", "abstract_en", "claims_text"), "multiview", field_groups=(("title_en", "abstract_en"), ("claims_text",))), _axes(fields="title_abstract_claims", unitization="section", span=0, stride=0, composition="title_abstract_plus_claims", duplicate="family_maxp"), aggregation="family_maxp"),
    ]
    body: dict[str, Any] = {
        "schema_version": "myis.p2-base-candidate-set.v1",
        "candidate_set_id": "p2-base-candidate-set-r1-v2",
        "phase_id": "P2_SCOPE_DEVELOPMENT",
        "campaign_id": "scope-autoindex-v1",
        "campaign_revision": CAMPAIGN_REVISION,
        "status": "adopted_hash_locked",
        "adoption_authority": "D1_START_CAMPAIGN_plus_owner_authored_goal",
        "source_contract_uri": SOURCE_CONTRACT_URI,
        "source_contract_sha256": hash_reader(root, SOURCE_CONTRACT_URI),
        "compiler_uri": COMPILER_URI,
        "compiler_sha256": hash_reader(root, COMPILER_URI),
        "adapter_rule": {
            "family_id_source": "relevant_id",
            "publication_id_source": "relevant_id",
            "max_searchable_units_per_family": 4,
            "overflow_policy": "first_last_balanced_with_explicit_offsets",
        },
        "frozen_controls": controls,
        "preregistered_candidates": candidates,
        "protected_boundary": _boundary(),
    }
    body["candidate_set_sha256"] = canonical_sha256(body)
    return body


def build_adaptive_policy() -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema_version": "myis.p2-adaptive-policy.v1",
        "policy_id": "p2-adaptive-policy-r1-v2",
        "campaign_revision": CAMPAIGN_REVISION,
        "status": "adopted_hash_locked",
        "candidates_per_iteration": 4,
        "batch_roles": ["exploit", "matched_ablation", "orthogonal", "diversity"],
        "allowed_axes": ["source_fields", "unitization", "passage_span", "passage_stride", "view_composition", "duplicate_handling", "normalization"],
        "forbidden_axes": ["query_view", "qrels", "split_membership", "per_query_outcomes", "selection_feedback", "evaluator", "metric", "top_k", "retriever_family", "tie_policy", "dense_model", "llm_summary", "external_data", "paid_api", "gpu", "network_download", "compiler_code"],
        "candidate_id_pattern": "^p2-r1-r[0-9]{2}-i[0-9]{2}-c0[1-4]$",
        "scientific_identity_exclusions": ["spec_id", "parent_spec_id", "hypothesis_id", "description", "created_at", "artifact_uri"],
        "admission": {
            "full_batch_frozen_before_measurement": True,
            "schema_valid": True,
            "grounded_source_fields_only": True,
            "compiler_determinism_required": True,
            "matched_ablation_single_axis_required": True,
            "independent_verifier_required": True,
        },
        "stopping": {
            "minimum_completed_iterations": 4,
            "no_improvement_patience": 2,
            "ties_are_improvement": False,
            "development_impact_gate_may_stop": True,
            "wall_time_admission_required": True,
        },
    }
    body["policy_sha256"] = canonical_sha256(body)
    return body


def build_proposer_contract() -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema_version": "myis.p2-proposer-contract.v1",
        "contract_id": "p2-proposer-contract-r1-v2",
        "status": "adopted_hash_locked",
        "input_schema": "myis.p2-adaptive-feedback.v1",
        "output_schema": "myis.p2-scope-candidate-batch.v1",
        "batch_size": 4,
        "allowed_input": ["aggregate_train_metrics", "aggregate_deltas", "failure_categories", "remaining_axes", "budget_counters", "lineage_hashes", "literature_pointers"],
        "forbidden_input": ["query_ids", "qrels", "membership", "rankings", "per_query_outcomes", "raw_corpus_text", "raw_query_text", "selection", "final_872", "credentials", "owner_store_paths"],
        "environment_removed": [
            "MYIS_STORE",
            "MYIS_MLFLOW_STORE",
            "credential_like_environment_variables",
        ],
        "command": ["codex", "exec", "--ephemeral", "--sandbox", "read-only", "--output-schema"],
        "provider_identity_frozen_at_preflight": True,
        "attempts_per_batch": 2,
        "retry_limit": 1,
        "measured_execution_performed": False,
        "protected_data_accessed": False,
    }
    body["contract_sha256"] = canonical_sha256(body)
    return body


def _candidate(
    candidate_id: str,
    candidate_class: str,
    arm: str,
    role: str,
    hypothesis: str,
    declared_axis: str,
    matched_ablation_id: str | None,
    scope_spec: Mapping[str, Any],
    axis_values: Mapping[str, Any],
    *,
    aggregation: str,
) -> dict[str, Any]:
    spec = deepcopy(dict(scope_spec))
    return {
        "candidate_id": candidate_id,
        "candidate_class": candidate_class,
        "arm": arm,
        "role": role,
        "hypothesis": hypothesis,
        "declared_axis": declared_axis,
        "matched_ablation_id": matched_ablation_id,
        "scope_spec": spec,
        "spec_sha256": canonical_sha256(spec),
        "scientific_payload_sha256": scientific_payload_sha256(spec),
        "axis_values": dict(axis_values),
        "retrieval": {
            "scorer": "sqlite_fts5_bm25_v1",
            "query_operator": "OR",
            "top_k": 100,
            "family_aggregation": aggregation,
            "fts_tokenizer": "unicode61 remove_diacritics 2",
            "lexical_tokenizer": "python-re-unicode-word-casefold-v1",
        },
    }


def _scope_spec(
    suffix: str,
    hypothesis_number: int,
    kind: str,
    source_fields: tuple[str, ...],
    mode: str,
    *,
    window_tokens: int | None = None,
    stride_tokens: int | None = None,
    field_groups: tuple[tuple[str, ...], ...] | None = None,
) -> dict[str, Any]:
    policy: dict[str, Any] = {"mode": mode, "max_units": 4, "overflow_policy": "first_last_balanced"}
    if window_tokens is not None:
        policy["window_tokens"] = window_tokens
    if stride_tokens is not None:
        policy["stride_tokens"] = stride_tokens
    if field_groups is not None:
        policy["source_field_groups"] = [list(group) for group in field_groups]
    aggregation = "family_first" if mode == "joined_document" else "family_maxp"
    return {
        "schema_version": "myis.scope-dsl.v1",
        "spec_id": f"spec-{suffix}-v01",
        "parent_spec_id": None,
        "hypothesis_id": f"hyp-i00-{hypothesis_number:03d}",
        "compiler_api_version": "1.1.0",
        "description": {"title": suffix, "purpose": "P2 frozen base candidate"},
        "fields": [
            {"field_id": "family_id", "source": "relevant_id", "role": "identity"},
            {"field_id": "publication_id", "source": "relevant_id", "role": "identity"},
            {"field_id": "title_en", "source": "title_en", "role": "text"},
            {"field_id": "abstract_en", "source": "abstract_en", "role": "text"},
            {"field_id": "claims_text", "source": "claims_text", "role": "text"},
        ],
        "claims": {"claim_boundary": "retrieval_evidence_only", "source": "claims_text"},
        "graph": {"unitization": {"primary": policy}},
        "views": [{
            "view_id": "primary",
            "kind": kind,
            "source_fields": list(source_fields),
            "family_field": "family_id",
            "publication_field": "publication_id",
            "span_scheme": "dapfam-source-offset-v1",
            "compiler_version": "1.1.0",
            "normalization_version": "1.0.0",
            "searchable": True,
            "aggregation": aggregation,
            "deterministic_order": "source",
        }],
        "aggregation": {"unit": "family", "rule": aggregation, "tie_policy": "lexical_unit_id"},
        "constraints": {
            "require_source_grounding": True,
            "abstractive_summaries": False,
            "query_specific_vocabulary": False,
            "adapter_limits": {"dapfam": 4},
        },
    }


def _axes(*, fields: str, unitization: str, span: int, stride: int, composition: str, duplicate: str) -> dict[str, Any]:
    return {
        "source_fields": fields,
        "unitization": unitization,
        "passage_span": span,
        "passage_stride": stride,
        "view_composition": composition,
        "duplicate_handling": duplicate,
        "normalization": "python-re-unicode-word-casefold-v1",
    }


def _boundary() -> dict[str, bool]:
    return {
        "final_split_open": False,
        "d2_open_final": False,
        "d3_submit_release": False,
        "gpu": False,
        "paid_api": False,
        "network_model_download": False,
        "provider_fallback": False,
    }


def _working_sha256(repository_root: Path, uri: str) -> str:
    return file_sha256(Path(repository_root) / uri)
