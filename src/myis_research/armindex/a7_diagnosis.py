"""CPU-local, aggregate-safe diagnostics for the frozen A6 candidate pool.

This module intentionally consumes protected Owner Store inputs only in memory.
It writes no query/family identifiers, qrels, rankings, or per-query outcomes.
The diagnosis is descriptive: it cannot retrieve new candidates or change the
confirmed winner.
"""

from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping

import pyarrow as pa

from ..kernel.canonical import canonical_sha256, file_sha256
from ..protection import assert_aggregate_only


POPULATIONS = ("ALL", "IN", "OUT")
FORBIDDEN_EXPORT_TERMS = (
    "opaque_query_token", "opaque_family_token", "evidence_pointer",
    "qrels", "rankings", "per_query", "query_id", "family_id",
    "relevant_id", "domain_rel", "split_membership",
)


class A7DiagnosisError(ValueError):
    """Raised when frozen A6 inputs cannot support a safe diagnosis."""


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise A7DiagnosisError(f"JSON object required: {path}")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise A7DiagnosisError(f"JSONL object required: {path}")
                rows.append(value)
    return rows


def _round(value: float) -> float:
    return round(value, 12)


def _score(ranked: list[str], qrels: Mapping[str, int], cutoff: int) -> tuple[float, float]:
    relevant = set(qrels)
    recall = len(set(ranked[:cutoff]) & relevant) / len(relevant)
    dcg = sum(
        (2 ** qrels[family] - 1) / math.log2(position + 1)
        for position, family in enumerate(ranked[:cutoff], start=1)
        if family in qrels
    )
    ideal = sorted(qrels.values(), reverse=True)[:cutoff]
    idcg = sum((2 ** grade - 1) / math.log2(position + 1) for position, grade in enumerate(ideal, start=1))
    return recall, dcg / idcg if idcg else 0.0


def _summarize(
    rankings: Mapping[str, list[str]], qrels: Mapping[str, Mapping[str, int]], *, cutoff: int,
) -> dict[str, Any]:
    tokens = sorted(qrels)
    recalls: list[float] = []
    ndcgs: list[float] = []
    relevant_families = 0
    for token in tokens:
        if token not in rankings:
            raise A7DiagnosisError("relation and frozen-pool coverage differ")
        recall, ndcg = _score(rankings[token], qrels[token], cutoff)
        recalls.append(recall)
        ndcgs.append(ndcg)
        relevant_families += len(qrels[token])
    return {
        "judged_query_count": len(tokens),
        "relevant_family_count": relevant_families,
        f"Recall@{cutoff}": _round(sum(recalls) / len(recalls)) if recalls else None,
        f"nDCG@{cutoff}": _round(sum(ndcgs) / len(ndcgs)) if ndcgs else None,
    }


def _relations_from_owner_store(
    relations_path: Path, token_map_path: Path,
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any], set[str]]:
    family_tokens: dict[str, str] = {}
    for row in _read_jsonl(token_map_path):
        if row.get("role") == "corpus_family":
            family_tokens[str(row["source_id"])] = str(row["opaque_token"]).lower()

    table = pa.ipc.open_stream(relations_path.open("rb")).read_all()
    relations: dict[str, list[dict[str, Any]]] = defaultdict(list)
    integrity = Counter()
    seen_all: set[tuple[str, str]] = set()
    seen_by_domain: dict[str, set[tuple[str, str]]] = {"IN": set(), "OUT": set()}
    for raw in table.to_pylist():
        if float(raw["relevance_score"]) <= 0:
            continue
        family = family_tokens.get(str(raw["relevant_id"]))
        if family is None:
            integrity["unmapped_relevant_family_count"] += 1
            continue
        token = "q-" + hashlib.sha256(str(raw["query_id"]).encode("utf-8")).hexdigest()
        domain = str(raw["domain_rel"])
        if domain not in {"IN", "OUT"}:
            integrity["invalid_domain_relation_count"] += 1
            continue
        relation_key = (token, family)
        domain_relation_key = (token, family)
        integrity["family_collision_count"] += int(relation_key in seen_all)
        integrity[f"family_collision_count_{domain}"] += int(domain_relation_key in seen_by_domain[domain])
        seen_all.add(relation_key)
        seen_by_domain[domain].add(domain_relation_key)
        is_self_relation = str(raw["query_id"]) == str(raw["relevant_id"])
        relations[token].append({
            "family": family,
            "grade": max(1, int(round(float(raw["relevance_score"])))),
            "domain": domain,
            "is_raw_self_relation": is_self_relation,
        })
        integrity["positive_relation_row_count"] += 1
        integrity[f"positive_relation_row_count_{domain}"] += 1
        integrity["self_relation_count"] += int(is_self_relation)
    integrity["unique_family_relation_pair_count"] = len(seen_all)
    integrity["raw_to_family_deduplication_count"] = (
        integrity["positive_relation_row_count"] - integrity["unique_family_relation_pair_count"]
    )
    for domain in ("IN", "OUT"):
        integrity[f"unique_family_relation_pair_count_{domain}"] = len(seen_by_domain[domain])
        integrity[f"raw_to_family_deduplication_count_{domain}"] = (
            integrity[f"positive_relation_row_count_{domain}"]
            - integrity[f"unique_family_relation_pair_count_{domain}"]
        )
    return dict(relations), dict(integrity), set(family_tokens.values())


def _build_views(
    relations: Mapping[str, Iterable[Mapping[str, Any]]],
    *,
    exclude_raw_self_relations: bool = False,
) -> dict[str, dict[str, dict[str, int]]]:
    views = {population: {} for population in POPULATIONS}
    for query, values in relations.items():
        per_view = {population: {} for population in POPULATIONS}
        for item in values:
            if exclude_raw_self_relations and bool(item.get("is_raw_self_relation")):
                continue
            family, grade, domain = str(item["family"]), int(item["grade"]), str(item["domain"])
            per_view["ALL"][family] = max(grade, per_view["ALL"].get(family, 0))
            per_view[domain][family] = max(grade, per_view[domain].get(family, 0))
        for population in POPULATIONS:
            if per_view[population]:
                views[population][query] = per_view[population]
    return views


def _metric_delta(
    observed: Mapping[str, Any], sensitivity: Mapping[str, Any], *, metric: str,
) -> float | None:
    before, after = observed.get(metric), sensitivity.get(metric)
    if before is None or after is None:
        return None
    return _round(float(after) - float(before))


def _protocol_parity_matrix(
    config: Mapping[str, Any], *, metrics: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Emit conservative protocol metadata without inferring external parity."""

    unitization = config.get("unitization") if isinstance(config.get("unitization"), Mapping) else {}
    fields = config.get("field_order") if isinstance(config.get("field_order"), list) else []
    labels = config.get("field_labels") if isinstance(config.get("field_labels"), Mapping) else {}
    armindex_values = {
        "dataset_revision": f"source_sha256:{config.get('source_sha256', 'NOT_VERIFIED')}",
        "query_corpus_counts": f"1247_queries/{config.get('expected_document_count', 'NOT_VERIFIED')}_documents",
        "in_out_definition": (
            f"relation_scoped_IN:{metrics['IN']['judged_query_count']};"
            f"OUT:{metrics['OUT']['judged_query_count']}"
        ),
        "family_mapping": "hash_bound_corpus_family_tokens",
        "fields_prefixes": f"fields:{'+'.join(str(value) for value in fields) or 'NOT_VERIFIED'};labels:{json.dumps(labels, sort_keys=True)}",
        "passage_length_overlap": f"logical_size:{unitization.get('logical_size', 'NOT_VERIFIED')};overlap:{unitization.get('overlap', 'NOT_VERIFIED')}",
        "model_precision_normalization_similarity": (
            f"model:{config.get('model_id', 'NOT_VERIFIED')};precision:NOT_VERIFIED;"
            f"normalization:{config.get('normalization', 'NOT_VERIFIED')};"
            f"similarity:{config.get('index_kind', 'NOT_VERIFIED')}"
        ),
        "aggregation": str(config.get("family_aggregation", "NOT_VERIFIED")),
        "cutoff": "Recall@10/20/50/100/200;nDCG@10/100;Top-200_frozen_pool",
        "metric": "family_level_relevance_filtered_Recall_and_nDCG",
        "averaging": "macro_mean_across_judged_queries",
    }
    matrix = []
    for dimension, armindex in armindex_values.items():
        matrix.append({
            "dimension": dimension,
            "ArmIndex": armindex,
            "DAPFAM": "UNKNOWN_EXTERNAL_CONFIGURATION_NOT_FULLY_VERIFIED",
            "PatenTEB": "UNKNOWN_EXTERNAL_CONFIGURATION_NOT_FULLY_VERIFIED",
            "ArmIndex_vs_DAPFAM": "UNKNOWN",
            "ArmIndex_vs_PatenTEB": "UNKNOWN",
            "DAPFAM_vs_PatenTEB": "UNKNOWN",
        })
    return {
        "status": "BOUNDED_PASS" if config else "NOT_VERIFIED",
        "external_configuration_status": "UNKNOWN_NOT_INFERRED",
        "comparability_conclusion": "NOT_COMPARABLE_EXTERNAL_PROTOCOL_CONFIGURATION_NOT_FULLY_VERIFIED",
        "allowed_labels": ["EXACT", "FUNCTIONALLY_EQUIVALENT", "DIFFERENT_CONTROLLED", "NOT_COMPARABLE", "UNKNOWN"],
        "matrix": matrix,
        "selection_accesses": 0,
        "final_accesses": 0,
    }


def _oracle_ranking(
    ranked: list[str], qrels: Mapping[str, int], *, cutoff: int,
) -> list[str]:
    rank_index = {family: index for index, family in enumerate(ranked)}
    relevant = [family for family in ranked if family in qrels]
    relevant.sort(key=lambda family: (-qrels[family], rank_index[family]))
    non_relevant = [family for family in ranked if family not in qrels]
    return (relevant + non_relevant)[:cutoff]


def _read_rankings(pool_path: Path) -> tuple[dict[str, list[str]], dict[str, int]]:
    rows = _read_jsonl(pool_path)
    rankings: dict[str, list[tuple[int, str]]] = defaultdict(list)
    integrity = Counter(candidate_row_count=len(rows))
    for row in rows:
        try:
            query = str(row["opaque_query_token"])
            family = str(row["opaque_family_token"])
            rank = int(row["rank"])
            depth = int(row["pool_depth"])
        except (KeyError, TypeError, ValueError) as error:
            raise A7DiagnosisError("invalid frozen pool row") from error
        if depth != 200 or rank < 1 or rank > 200:
            raise A7DiagnosisError("frozen pool must remain exactly Top-200")
        rankings[query].append((rank, family))
    normalized: dict[str, list[str]] = {}
    for query, values in rankings.items():
        values.sort()
        families = [family for _, family in values]
        if [rank for rank, _ in values] != list(range(1, 201)):
            integrity["rank_continuity_failure_count"] += 1
        if len(set(families)) != 200:
            integrity["duplicate_family_within_query_count"] += 1
        normalized[query] = families
    integrity["pool_query_count"] = len(normalized)
    integrity["pool_depth"] = 200
    return normalized, dict(integrity)


def _safe_receipt(value: dict[str, Any]) -> dict[str, Any]:
    try:
        assert_aggregate_only(value)
    except ValueError as error:
        raise A7DiagnosisError("A7 aggregate receipt contains protected payload") from error
    encoded = json.dumps(value, ensure_ascii=True, sort_keys=True)
    lowered = encoded.casefold()
    leaked = [term for term in FORBIDDEN_EXPORT_TERMS if f'"{term}"' in lowered]
    if leaked:
        raise A7DiagnosisError(f"A7 aggregate receipt leaks protected fields: {leaked}")
    return {**value, "receipt_sha256": canonical_sha256(value)}


def diagnose(
    *, pool_path: Path, relations_path: Path, token_map_path: Path, evaluation_path: Path,
    execution_config_path: Path | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Calculate CPU-feasible A7 layers from hash-bound, frozen A6 inputs."""

    supplied_evaluation = _read_json(evaluation_path)
    rankings, pool_integrity = _read_rankings(pool_path)
    relations, relation_integrity, known_family_tokens = _relations_from_owner_store(relations_path, token_map_path)
    pool_integrity["unknown_pool_family_token_count"] = len(
        {family for ranked in rankings.values() for family in ranked} - known_family_tokens
    )
    # This check is deliberately restricted to relation labels that cannot be
    # mapped into the frozen corpus-family token space. Cross-split membership
    # is protected and is neither read nor inferred here.
    relation_integrity["leakage_count"] = relation_integrity.get("unmapped_relevant_family_count", 0)
    views = _build_views(relations)
    metrics = {population: _summarize(rankings, views[population], cutoff=100) for population in POPULATIONS}
    for population in POPULATIONS:
        expected_count = relation_integrity[
            "unique_family_relation_pair_count"
            if population == "ALL" else f"unique_family_relation_pair_count_{population}"
        ]
        relation_integrity[
            "denominator_discrepancy_count"
            if population == "ALL" else f"denominator_discrepancy_count_{population}"
        ] = abs(metrics[population]["relevant_family_count"] - expected_count)
    without_raw_self_views = _build_views(relations, exclude_raw_self_relations=True)
    without_raw_self_metrics = {
        population: _summarize(rankings, without_raw_self_views[population], cutoff=100)
        for population in POPULATIONS
    }
    expected = supplied_evaluation.get("populations", {})
    comparison: dict[str, Any] = {}
    for population in POPULATIONS:
        prior = expected.get(population, {})
        replay = metrics[population]
        comparison[population] = {
            "Recall@100_delta": _round(replay["Recall@100"] - float(prior["Recall@100"])) if replay["Recall@100"] is not None and prior.get("Recall@100") is not None else None,
            "nDCG@100_delta": _round(replay["nDCG@100"] - float(prior["nDCG@100"])) if replay["nDCG@100"] is not None and prior.get("nDCG@100") is not None else None,
            "query_count_match": replay["judged_query_count"] == prior.get("judged_query_count"),
        }
    l1_pass = all(
        (values["Recall@100_delta"] is None and values["nDCG@100_delta"] is None)
        or (values["Recall@100_delta"] == 0.0 and values["nDCG@100_delta"] == 0.0 and values["query_count_match"])
        for values in comparison.values()
    )

    pool_sets = {query: set(families) for query, families in rankings.items()}
    l6: dict[str, Any] = {}
    l7: dict[str, Any] = {}
    for population in POPULATIONS:
        qrels = views[population]
        aggregate = {cutoff: _summarize(rankings, qrels, cutoff=cutoff) for cutoff in (10, 20, 50, 100, 200)}
        top100_sets = {query: set(ranked[:100]) for query, ranked in rankings.items()}
        pool_hits = sum(len(pool_sets[query] & set(families)) for query, families in qrels.items())
        exposed_at_100 = sum(len(top100_sets[query] & set(families)) for query, families in qrels.items())
        deep_ranked = sum(
            len((pool_sets[query] - top100_sets[query]) & set(families))
            for query, families in qrels.items()
        )
        relevant = sum(len(families) for families in qrels.values())
        query_classes = Counter()
        for query, families in qrels.items():
            relevant_families = set(families)
            top100_hits = len(top100_sets[query] & relevant_families)
            deep_hits = len((pool_sets[query] - top100_sets[query]) & relevant_families)
            if top100_hits == len(relevant_families):
                query_classes["fully_exposed_at_100"] += 1
            elif top100_hits:
                query_classes["partially_exposed_at_100"] += 1
            elif deep_hits:
                query_classes["deep_only_101_to_200"] += 1
            else:
                query_classes["unretrieved_at_200"] += 1
        l6[population] = {
            "query_count": len(qrels), "relevant_family_count": relevant,
            "relevant_family_exposed_at_100": exposed_at_100,
            "relevant_family_deep_ranked_101_to_200": deep_ranked,
            "relevant_family_exposed_at_200": pool_hits,
            "relevant_family_not_exposed_at_200": relevant - pool_hits,
            "aggregate_query_classes": {
                "fully_exposed_at_100": query_classes["fully_exposed_at_100"],
                "partially_exposed_at_100": query_classes["partially_exposed_at_100"],
                "deep_only_101_to_200": query_classes["deep_only_101_to_200"],
                "unretrieved_at_200": query_classes["unretrieved_at_200"],
            },
            "curves": {
                str(cutoff): {
                    "Recall": aggregate[cutoff][f"Recall@{cutoff}"],
                    "nDCG": aggregate[cutoff][f"nDCG@{cutoff}"],
                }
                for cutoff in (10, 20, 50, 100, 200)
            },
        }
        oracle_at_100 = (
            sum(min(100, len(pool_sets[query] & set(families))) / len(families) for query, families in qrels.items()) / len(qrels)
            if qrels else None
        )
        oracle_ndcg = {
            cutoff: (
                sum(
                    _score(_oracle_ranking(rankings[query], families, cutoff=200), families, cutoff)[1]
                    for query, families in qrels.items()
                ) / len(qrels)
                if qrels else None
            )
            for cutoff in (10, 100)
        }
        l7[population] = {
            "query_count": len(qrels),
            "existing_top_200_oracle_Recall@100": _round(oracle_at_100) if oracle_at_100 is not None else None,
            "observed_Recall@100": metrics[population]["Recall@100"],
            "bounded_reranking_headroom_Recall@100": _round(oracle_at_100 - metrics[population]["Recall@100"])
            if oracle_at_100 is not None and metrics[population]["Recall@100"] is not None else None,
            "observed_nDCG@10": aggregate[10]["nDCG@10"],
            "bounded_top_200_oracle_nDCG@10": _round(oracle_ndcg[10]) if oracle_ndcg[10] is not None else None,
            "bounded_reranking_headroom_nDCG@10": _round(oracle_ndcg[10] - aggregate[10]["nDCG@10"])
            if oracle_ndcg[10] is not None and aggregate[10]["nDCG@10"] is not None else None,
            "observed_nDCG@100": aggregate[100]["nDCG@100"],
            "bounded_top_200_oracle_nDCG@100": _round(oracle_ndcg[100]) if oracle_ndcg[100] is not None else None,
            "bounded_reranking_headroom_nDCG@100": _round(oracle_ndcg[100] - aggregate[100]["nDCG@100"])
            if oracle_ndcg[100] is not None and aggregate[100]["nDCG@100"] is not None else None,
            "pool_expansion_performed": False,
        }

    config = _read_json(execution_config_path) if execution_config_path else {}
    fields = config.get("field_order") if isinstance(config.get("field_order"), list) else None
    source_hashes = {
        "pool_sha256": file_sha256(pool_path),
        "relations_sha256": file_sha256(relations_path),
        "token_map_sha256": file_sha256(token_map_path),
        "evaluation_file_sha256": file_sha256(evaluation_path),
    }
    l2_pass = not any(
        (
            relation_integrity.get("unmapped_relevant_family_count", 0),
            relation_integrity.get("invalid_domain_relation_count", 0),
            relation_integrity.get("denominator_discrepancy_count", 0),
            relation_integrity.get("leakage_count", 0),
            pool_integrity.get("rank_continuity_failure_count", 0),
            pool_integrity.get("duplicate_family_within_query_count", 0),
        )
    ) and set(rankings) == set(views["ALL"])
    self_match_sensitivity = {
        "status": "PASS_DESCRIPTIVE_SENSITIVITY",
        "removed_raw_self_relation_count": relation_integrity.get("self_relation_count", 0),
        "scope": "exclude_raw_relations_where_query_id_equals_relevant_id",
        "replayed_metrics_excluding_raw_self_relations": without_raw_self_metrics,
        "delta_vs_inclusive": {
            population: {
                "Recall@100_delta": _metric_delta(metrics[population], without_raw_self_metrics[population], metric="Recall@100"),
                "nDCG@100_delta": _metric_delta(metrics[population], without_raw_self_metrics[population], metric="nDCG@100"),
                "judged_query_count_delta": (
                    without_raw_self_metrics[population]["judged_query_count"]
                    - metrics[population]["judged_query_count"]
                ),
                "relevant_family_count_delta": (
                    without_raw_self_metrics[population]["relevant_family_count"]
                    - metrics[population]["relevant_family_count"]
                ),
            }
            for population in POPULATIONS
        },
        "conclusion": (
            "Sensitivity reported; raw identifier equality is not classified as cross-split leakage. "
            "No protected split membership was read or exported."
        ),
    }
    protocol_parity = _protocol_parity_matrix(config, metrics=metrics)
    receipt = {
        "schema_version": "myis.armindex-a7-seven-layer-diagnosis-receipt.v1",
        "status": "PASS_A7_CPU_LOCAL_DIAGNOSIS",
        "compute": "CPU_LOCAL",
        "claim_boundary": "post_confirmatory_diagnosis_only_no_winner_change_no_new_retrieval_no_pool_expansion_no_reranker",
        "frozen_input_hashes": source_hashes,
        "A7-L1_score_identity": {"status": "PASS" if l1_pass else "FAIL", "replayed_metrics": metrics, "delta_vs_A6": comparison},
        "A7-L2_family_relevance_integrity": {
            "status": "PASS" if l2_pass else "FAIL",
            "pool": pool_integrity, "relations": relation_integrity,
            "pool_relation_query_coverage_match": set(rankings) == set(views["ALL"]),
            "leakage_scope": "frozen_pool_to_corpus_family_mapping_only; protected_split_membership_not_inspected",
            "self_match_sensitivity": self_match_sensitivity,
        },
        "A7-L3_protocol_parity": protocol_parity,
        "A7-L3R_fixed_reference_reproduction": {"status": "NOT_RUN_NO_FRESH_GPU", "reason": "GPU instance destroyed; fresh admission absent"},
        "A7-L4_representation_attribution": {
            "status": "SUPPORTED_DESCRIPTIVE_ONLY" if fields else "NOT_AVAILABLE",
            "representation_fields": fields or [],
            "reason": "Frozen single-system evidence supports configuration attribution, not causal component ablation.",
            "unavailable_aggregate_record": {
                "status": "NOT_AVAILABLE",
                "reason": "No hash-bound component ablation or counterfactual representation run was supplied.",
            },
        },
        "A7-L5_query_rescue": {
            "status": "NOT_AVAILABLE",
            "reason": "No hash-bound comparator ranking was supplied; no comparison inferred.",
            "unavailable_aggregate_record": {
                "status": "NOT_AVAILABLE", "comparator_system_count": 0,
                "reason": "A frozen comparator ranking is required for query-rescue attribution.",
            },
        },
        "A7-L6_candidate_exposure_error_anatomy": {"status": "PASS", "populations": l6},
        "A7-L7_oracle_retrieval_boundary": {
            "status": "PASS",
            "definition": "oracle selection restricted to the existing frozen Top-200 candidates",
            "analytical_bound_only": True,
            "not_a_reranker_or_system_result": True,
            "populations": l7,
        },
        "claim_to_evidence": {
            "score_identity_replay": "SUPPORTED" if l1_pass else "FAILED",
            "family_relevance_and_leakage_integrity": "SUPPORTED" if l2_pass else "FAILED",
            "protocol_comparability": "NOT_COMPARABLE_EXTERNAL_CONFIGURATION_NOT_FULLY_VERIFIED",
            "representation_attribution": "DESCRIPTIVE_ONLY",
            "query_rescue_comparison": "NOT_AVAILABLE_NO_HASH_BOUND_COMPARATOR",
            "candidate_exposure_and_oracle_headroom": "SUPPORTED_WITHIN_TOP_200",
            "fixed_reference_gpu_reproduction": "NOT_RUN_NO_FRESH_GPU_ADMISSION",
            "winner_or_final_confirmation": "NOT_ESTABLISHED_BY_A7",
        },
        "protected_payload_included": False,
        "selection_accesses": 0,
        "final_accesses": 0,
    }
    csv_rows: list[dict[str, Any]] = []

    def add_numeric_rows(layer: str, population: str, value: Mapping[str, Any], prefix: str = "") -> None:
        for metric, item in value.items():
            label = f"{prefix}.{metric}" if prefix else str(metric)
            if isinstance(item, Mapping):
                add_numeric_rows(layer, population, item, label)
            elif isinstance(item, (int, float)) or item is None:
                csv_rows.append({"layer": layer, "population": population, "metric": label, "value": item})

    for layer, values in (("A7-L1", metrics), ("A7-L6", l6), ("A7-L7", l7)):
        for population, measures in values.items():
            add_numeric_rows(layer, population, measures)
    return _safe_receipt(receipt), csv_rows


def write_public_outputs(*, receipt: Mapping[str, Any], csv_rows: Iterable[Mapping[str, Any]], output_root: Path) -> None:
    """Write only the pre-validated aggregate-safe A7 receipt and metric table."""

    if "04_Owner_Stores" in output_root.parts or "protected" in {part.casefold() for part in output_root.parts}:
        raise A7DiagnosisError("A7 public output root must not be inside Owner Store or a protected directory")
    value = dict(receipt)
    _safe_receipt({key: item for key, item in value.items() if key != "receipt_sha256"})
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "a7-diagnosis-receipt.json").write_text(json.dumps(value, ensure_ascii=True, sort_keys=True, indent=2) + "\n", encoding="ascii")
    rows = list(csv_rows)
    headers = ("layer", "population", "metric", "value")
    lines = [",".join(headers)]
    for row in rows:
        lines.append(",".join("" if row.get(header) is None else str(row.get(header)) for header in headers))
    csv = "\n".join(lines) + "\n"
    if any(term in csv.casefold() for term in ("q-", "f-", "query_id", "family_id")):
        raise A7DiagnosisError("A7 metric CSV would leak protected identifiers")
    (output_root / "a7-layer-aggregate-metrics.csv").write_text(csv, encoding="ascii")


__all__ = ["A7DiagnosisError", "diagnose", "write_public_outputs"]
