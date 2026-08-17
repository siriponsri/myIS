from __future__ import annotations

from copy import deepcopy

import pytest

from myis_research.armindex.a3_three_primary_owner_evaluator import (
    A3ThreePrimaryOwnerEvaluatorError,
    build_aggregate_safe_return_receipt,
    evaluate_remote_ranking_owner_local,
)
from myis_research.armindex.a3_three_primary_remote_retriever import (
    A3ThreePrimaryRemoteRetrieverError,
    build_remote_cell_request,
    run_remote_retrieval_cell,
    validate_remote_cell_request,
)
from myis_research.kernel.canonical import canonical_sha256


PRIMARY_ARMS = ("ARM-03", "ARM-04", "ARM-05")


def _self_hash(value: dict[str, object], field: str) -> dict[str, object]:
    value[field] = canonical_sha256({key: item for key, item in value.items() if key != field})
    return value


def _execution_contract() -> dict[str, object]:
    transfer_matrix = [
        {
            "source_arm_id": source,
            "target_arm_id": target,
            "post_admission_action": "reuse_self_winner" if source == target else "validate_cross_arm_transfer",
            "winner_program_sha256": "1" * 64,
            "target_adapter_sha256": "2" * 64,
            "result_scope": "aggregate_only",
        }
        for source in PRIMARY_ARMS
        for target in PRIMARY_ARMS
    ]
    return _self_hash(
        {
            "schema_version": "myis.armindex-a3-three-primary-execution-contract.v1",
            "status": "READY_FOR_POST_ADMISSION_EXECUTION",
            "runtime_bindings_sha256": "3" * 64,
            "transfer_matrix": transfer_matrix,
            "fixed_union_sha256": "4" * 64,
            "harness_batch_sha256s": ["5" * 64],
            "execution_order": ["transfer_matrix", "fixed_union_controls", "complete_harnessopt_batches"],
            "selection_permitted": False,
            "final_permitted": False,
            "provider_contact_performed": False,
            "remote_execution_performed": False,
            "execution_contract_sha256": "",
        },
        "execution_contract_sha256",
    )


def _assets() -> dict[str, object]:
    return {
        "corpus_sha256": "5" * 64,
        "queries_sha256": "6" * 64,
        "model_sha256s": {arm_id: str(index + 7) * 64 for index, arm_id in enumerate(PRIMARY_ARMS)},
    }


def _ranker(request: dict[str, object]) -> dict[str, object]:
    depth = max(request["output_depth_by_arm"].values())
    return {
        "rankings": {
            "Q-001": [
                {"family_token": f"F-{rank:03d}", "rank": rank, "score": 1.0 / rank}
                for rank in range(1, depth + 1)
            ],
            "Q-002": [
                {"family_token": f"F-{rank + 10:03d}", "rank": rank, "score": 1.0 / rank}
                for rank in range(1, depth + 1)
            ],
        },
        "coverage": {"expected_units": 2, "completed_units": 2},
        "latency": {"wall_seconds": 1.2, "search_p95_seconds": 0.7},
    }


def _metrics(_rankings: object) -> dict[str, str]:
    return {
        "recall_at_100/out": "0.5",
        "ndcg_at_100/out": "0.25",
        "ndcg_at_10/out": "0.125",
    }


def test_self_cross_and_fixed_union_route_only_to_owner_local_aggregate_evaluation() -> None:
    contract = _execution_contract()
    self_request = build_remote_cell_request(
        contract,
        operation_id="a3-self-03",
        operation_kind="transfer_cell",
        source_arm_id="ARM-03",
        target_arm_id="ARM-03",
        fixed_union_control_id=None,
        retrieval_arm_ids=["ARM-03"],
        output_depth_by_arm={"ARM-03": 3},
        remote_asset_sha256s=_assets(),
    )
    cross_request = build_remote_cell_request(
        contract,
        operation_id="a3-cross-03-04",
        operation_kind="transfer_cell",
        source_arm_id="ARM-03",
        target_arm_id="ARM-04",
        fixed_union_control_id=None,
        retrieval_arm_ids=["ARM-04"],
        output_depth_by_arm={"ARM-04": 3},
        remote_asset_sha256s=_assets(),
    )
    union_request = build_remote_cell_request(
        contract,
        operation_id="a3-commercial-union",
        operation_kind="fixed_union",
        source_arm_id=None,
        target_arm_id=None,
        fixed_union_control_id="commercial_only_fixed_union",
        retrieval_arm_ids=["ARM-04", "ARM-05"],
        output_depth_by_arm={"ARM-04": 3, "ARM-05": 3},
        remote_asset_sha256s=_assets(),
    )

    results = []
    for request in (self_request, cross_request, union_request):
        ranking_package = run_remote_retrieval_cell(request, ranker=_ranker)
        result = evaluate_remote_ranking_owner_local(
            request,
            ranking_package,
            evaluator_binding_sha256="a" * 64,
            evaluator_input_sha256="b" * 64,
            metric_evaluator=_metrics,
        )
        assert result["protected_payload_included"] is False
        assert result["per_query_outcomes_included"] is False
        results.append(result)
    safe_return = build_aggregate_safe_return_receipt(
        results, runtime_bindings_sha256=contract["runtime_bindings_sha256"]
    )
    assert safe_return["aggregate_result_count"] == 3
    assert safe_return["rankings_returned"] is False


def test_remote_request_and_union_fail_closed_on_protected_or_unequal_input() -> None:
    contract = _execution_contract()
    request = build_remote_cell_request(
        contract,
        operation_id="a3-union",
        operation_kind="fixed_union",
        source_arm_id=None,
        target_arm_id=None,
        fixed_union_control_id="commercial_only_fixed_union",
        retrieval_arm_ids=["ARM-04", "ARM-05"],
        output_depth_by_arm={"ARM-04": 3, "ARM-05": 3},
        remote_asset_sha256s=_assets(),
    )
    protected = deepcopy(request)
    protected["qrels"] = {"not": "allowed"}
    protected["request_sha256"] = canonical_sha256(
        {key: item for key, item in protected.items() if key != "request_sha256"}
    )
    with pytest.raises(A3ThreePrimaryRemoteRetrieverError, match="protected payload key"):
        validate_remote_cell_request(protected)

    with pytest.raises(A3ThreePrimaryRemoteRetrieverError, match="equal retrieval depth"):
        build_remote_cell_request(
            contract,
            operation_id="a3-bad-union",
            operation_kind="fixed_union",
            source_arm_id=None,
            target_arm_id=None,
            fixed_union_control_id="commercial_only_fixed_union",
            retrieval_arm_ids=["ARM-04", "ARM-05"],
            output_depth_by_arm={"ARM-04": 3, "ARM-05": 2},
            remote_asset_sha256s=_assets(),
        )


def test_remote_request_rejects_an_extended_contract_without_a_complete_batch() -> None:
    contract = _execution_contract()
    contract["harness_batch_sha256s"] = []
    contract["execution_contract_sha256"] = canonical_sha256(
        {key: item for key, item in contract.items() if key != "execution_contract_sha256"}
    )
    with pytest.raises(A3ThreePrimaryRemoteRetrieverError, match="one to three"):
        build_remote_cell_request(
            contract,
            operation_id="a3-no-batch",
            operation_kind="transfer_cell",
            source_arm_id="ARM-03",
            target_arm_id="ARM-03",
            fixed_union_control_id=None,
            retrieval_arm_ids=["ARM-03"],
            output_depth_by_arm={"ARM-03": 3},
            remote_asset_sha256s=_assets(),
        )


def test_safe_return_rejects_a_result_with_per_query_payload() -> None:
    contract = _execution_contract()
    request = build_remote_cell_request(
        contract,
        operation_id="a3-self-04",
        operation_kind="transfer_cell",
        source_arm_id="ARM-04",
        target_arm_id="ARM-04",
        fixed_union_control_id=None,
        retrieval_arm_ids=["ARM-04"],
        output_depth_by_arm={"ARM-04": 3},
        remote_asset_sha256s=_assets(),
    )
    result = evaluate_remote_ranking_owner_local(
        request,
        run_remote_retrieval_cell(request, ranker=_ranker),
        evaluator_binding_sha256="c" * 64,
        evaluator_input_sha256="d" * 64,
        metric_evaluator=_metrics,
    )
    result["per_query"] = []
    with pytest.raises(A3ThreePrimaryOwnerEvaluatorError, match="protected payload key"):
        build_aggregate_safe_return_receipt(
            [result], runtime_bindings_sha256=contract["runtime_bindings_sha256"]
        )
