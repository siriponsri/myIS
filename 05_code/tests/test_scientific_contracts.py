import hashlib
import unittest

from myis_research.confirmation import (
    AGGREGATE_SCHEMA,
    AggregateComparison,
    ComparisonFamilyMetadata,
    ConfirmationAggregatePackage,
    ConfirmationRequest,
    validate_confirmation_aggregate,
)
from myis_research.harness.benchmark import (
    CandidateExposureComparison,
    ConfirmationClassification,
    FrozenPoolRankingComparison,
    SharedSplitCommitment,
    SelectionDecision,
    SplitFreezeCommitment,
    TrackCRankingDiagnostic,
    classify_confirmation,
    deterministic_stratified_split,
)
from myis_research.harness.candidate_ledger import (
    GroundedQueryView,
    GroundingSpan,
    RouteHit,
    build_family_ledger,
    candidate_ledger_bytes,
    freeze_candidate_pool,
)
from myis_research.harness.manifest import MANIFEST_V2, MANIFEST_V3
from myis_research.harness.models import EndpointClass, ProviderExecution, ResearchVersionSpec
from myis_research.harness.policy import (
    CandidateBudget,
    FusionContract,
    HarnessPolicy,
    QueryViewPolicy,
    RoutePolicy,
)
from myis_research.harness.statistics import holm_adjust, paired_statistics
from myis_research.harness.validation import ValidationError, validate_manifest_payload
from myis_research.protection import PatchSurfacePolicy, assert_aggregate_only
from myis_research.providers import (
    LunaUse,
    ModelCalibrationProtocol,
    OptimizerProtocol,
    assert_matched_track_s_optimizer_protocols,
    assert_matched_optimizer_protocols,
    validate_luna_use,
)


def sha(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


class ScientificContractTests(unittest.TestCase):
    def test_split_rejects_duplicate_query_ids(self) -> None:
        with self.assertRaises(ValueError):
            deterministic_stratified_split(
                [("q1", "A"), ("q1", "B")], seed=7, ratios=(0.60, 0.20, 0.20)
            )

    def test_split_freeze_binds_sensitivity_counts_and_qrels_snapshot(self) -> None:
        freeze = SplitFreezeCommitment(
            seed=7,
            ratios=(0.60, 0.20, 0.20),
            membership_hashes={name: sha(name) for name in ("adaptation", "selection", "confirmation")},
            qrels_snapshot_sha256=sha("qrels"),
            query_counts={"adaptation": 12, "selection": 4, "confirmation": 4},
            out_positive_counts={"adaptation": 8, "selection": 2, "confirmation": 1},
            out_positive_available={"adaptation": True, "selection": True, "confirmation": True},
            prospective_sensitivity_report_sha256=sha("mde-report"),
            owner_decision_id="IS1-V0.1-SPLIT-FREEZE",
        )
        self.assertEqual(len(freeze.sha256), 64)
        with self.assertRaises(ValueError):
            SplitFreezeCommitment(
                **{**freeze.__dict__, "out_positive_available": {**freeze.out_positive_available, "confirmation": False}}
            ).validate()

    def test_shared_split_requires_locked_counts_and_independent_firewalls(self) -> None:
        commitment = SharedSplitCommitment(
            seed=42,
            membership_hashes={name: sha(name) for name in ("train", "selection", "joint_test")},
            qrels_snapshot_sha256=sha("qrels"),
            c_firewall_sha256=sha("c-firewall"),
            s_firewall_sha256=sha("s-firewall"),
            owner_decision_id="MYIS-G2-SPLIT",
        )
        self.assertEqual(len(commitment.sha256), 64)
        with self.assertRaises(ValueError):
            SharedSplitCommitment(
                **{**commitment.__dict__, "seed": 7}
            ).validate()
        with self.assertRaises(ValueError):
            SharedSplitCommitment(
                **{**commitment.__dict__, "s_firewall_sha256": commitment.c_firewall_sha256}
            ).validate()

    def test_strict_selection_rejects_ties(self) -> None:
        better = SelectionDecision.decide(
            candidate_id="c1", incumbent_id="c0", primary_metric="out_recall_at_100",
            candidate_score=0.200000000002, incumbent_score=0.2,
        )
        numeric_tie = SelectionDecision.decide(
            candidate_id="c2", incumbent_id="c1", primary_metric="out_recall_at_100",
            candidate_score=0.2000000000001, incumbent_score=0.2,
        )
        self.assertTrue(better.accepted)
        self.assertEqual(numeric_tie.status, "rejected_tie")

    def test_track_c_ranking_is_a_frozen_pool_diagnostic(self) -> None:
        gate_c = CandidateExposureComparison.compare(
            baseline_id="hybrid", candidate_id="crossroute",
            baseline_scores=[0.1, 0.2, 0.3], candidate_scores=[0.2, 0.3, 0.4],
            bootstrap_seed="C", resamples=200,
        )
        pool_hash = sha("pool")
        gate_r = FrozenPoolRankingComparison.compare(
            baseline_id="no-rerank", candidate_id="ranker",
            baseline_pool_sha256=pool_hash, candidate_pool_sha256=pool_hash,
            baseline_scores=[0.3, 0.4, 0.5], candidate_scores=[0.2, 0.3, 0.4],
            bootstrap_seed="R", resamples=200,
        )
        self.assertEqual(gate_c.gate_id, "C")
        self.assertEqual(gate_r.track_id, "C")
        self.assertEqual(gate_r.diagnostic_id, "C_DIAGNOSTIC")
        self.assertNotEqual(gate_c.classification, gate_r.classification)
        with self.assertRaises(ValueError):
            FrozenPoolRankingComparison.compare(
                baseline_id="no-rerank", candidate_id="ranker",
                baseline_pool_sha256=pool_hash, candidate_pool_sha256=sha("other"),
                baseline_scores=[0.3], candidate_scores=[0.4], bootstrap_seed="R", resamples=10,
            )
        diagnostic = TrackCRankingDiagnostic(
            candidate_pool_sha256=pool_hash,
            no_rerank_id="c1-no-rerank",
            reranker_id="frozen-reranker",
            no_rerank_ndcg_at_100=0.30,
            reranked_ndcg_at_100=0.35,
            oracle_ndcg_at_100=0.55,
            reachable_ndcg_at_100=0.50,
            promotions=4,
            demotions=2,
            failure_layer="ranking",
        )
        diagnostic.validate()

    def test_confirmation_classification_uses_point_delta_not_ci_as_gate(self) -> None:
        self.assertEqual(
            classify_confirmation(0.006, -0.001),
            ConfirmationClassification.HIGHER_MEASURED_SCORE_UNCERTAIN_SUPERIORITY,
        )
        self.assertEqual(
            classify_confirmation(0.006, 0.001),
            ConfirmationClassification.STATISTICALLY_SUPPORTED_SUPERIORITY,
        )
        self.assertEqual(
            classify_confirmation(0.0, -0.001),
            ConfirmationClassification.NO_OBSERVED_IMPROVEMENT,
        )

    def test_grounded_policy_and_candidate_ledger_are_deterministic(self) -> None:
        policy = HarnessPolicy(
            "crossroute",
            query_views=(QueryViewPolicy("claims", ("claims",)),),
            routes=(RoutePolicy("claim-bm25", "lexical", ("claims",), depth=20, quota=10),),
            candidate_budget=CandidateBudget(final_k=2, max_total_retrieved=20),
            fusion_contract=FusionContract("rrf", 30, {"claim-bm25": 1.0}),
        )
        policy.validate({"lexical", "dense"})
        view = GroundedQueryView(
            "q1", "claims", "claim text", (GroundingSpan("claims", 0, 10, sha("claims")),)
        )
        view.validate()
        with self.assertRaises(ValueError):
            GroundedQueryView("q1", "bad", "generated", ()).validate()

        hits = [
            RouteHit("q1", "claim-bm25", "claims", "f2", "p2", 1, 2.0),
            RouteHit("q1", "claim-bm25", "claims", "f1", "p1", 1, 2.0),
            RouteHit("q1", "claim-bm25", "claims", "f1", "p1b", 2, 1.0),
        ]
        ledger_a = build_family_ledger(hits, fusion_k=30, final_k=2)
        ledger_b = build_family_ledger(reversed(hits), fusion_k=30, final_k=2)
        self.assertEqual(candidate_ledger_bytes(ledger_a), candidate_ledger_bytes(ledger_b))
        self.assertEqual([row.family_id for row in ledger_a], ["f1", "f2"])
        pool = freeze_candidate_pool(ledger_a, policy_sha256=policy.sha256, final_k=2)
        self.assertTrue(pool.frozen)

    def test_statistics_report_wlt_effect_bootstrap_and_holm(self) -> None:
        stats = paired_statistics([0.1, 0.2, 0.3], [0.2, 0.2, 0.1], seed="fixture")
        self.assertEqual(stats.ci95.resamples, 10_000)
        self.assertEqual(stats.counts.n, 3)
        self.assertEqual((stats.counts.wins, stats.counts.losses, stats.counts.ties), (1, 1, 1))
        self.assertEqual(stats.rank_biserial_effect, -0.333333333333)
        self.assertEqual(holm_adjust([0.01, 0.04, 0.03]), (0.03, 0.06, 0.06))

    def test_provider_fallback_and_a2_a3_drift_are_rejected(self) -> None:
        provider = ProviderExecution("gpt-5.6-sol", "gpt-5.6-sol", "openai", "medium")
        protocol = OptimizerProtocol(provider, sha("budget"), sha("initial"), sha("eval"), sha("stop"))
        assert_matched_optimizer_protocols(protocol, protocol, stage="selection")
        assert_matched_track_s_optimizer_protocols(protocol, protocol, protocol, stage="selection")
        fallback = ProviderExecution(
            "gpt-5.6-sol", "gpt-5.6-sol", "proxy", "medium",
            endpoint_class=EndpointClass.THIRD_PARTY, fallback_used=True,
        )
        with self.assertRaises(ValueError):
            OptimizerProtocol(fallback, sha("budget"), sha("initial"), sha("eval"), sha("stop")).validate(
                stage="selection"
            )
        with self.assertRaises(ValueError):
            ProviderExecution(
                "qwen/qwen3-30b-a3b-instruct-2507",
                "qwen/qwen3-30b-a3b-instruct-2507",
                "openrouter-coreweave",
                "non-thinking",
                endpoint_class=EndpointClass.THIRD_PARTY,
                routing_used=True,
            ).validate(measured=True)

    def test_model_calibration_and_luna_roles_are_explicit(self) -> None:
        implementation = ProviderExecution("gpt-5.6-sol", "gpt-5.6-sol", "openai", "high")
        medium = ProviderExecution("gpt-5.6-sol", "gpt-5.6-sol", "openai", "medium")
        ModelCalibrationProtocol(implementation, medium, medium).validate()
        high = ProviderExecution("gpt-5.6-sol", "gpt-5.6-sol", "openai", "high")
        with self.assertRaises(ValueError):
            ModelCalibrationProtocol(implementation, medium, high).validate()
        ModelCalibrationProtocol(
            implementation,
            medium,
            high,
            qrels_blind_calibration_failed=True,
            calibration_report_sha256=sha("calibration"),
            escalation_owner_decision_id="IS1-V0.1-MODEL-ESCALATION",
        ).validate()
        luna = ProviderExecution("gpt-5.6-luna", "gpt-5.6-luna", "openai", "medium")
        validate_luna_use(luna, use=LunaUse.SUPPORT_TASK, main_a2_a3=False)
        with self.assertRaises(ValueError):
            validate_luna_use(luna, use=LunaUse.COST_ABLATION, main_a2_a3=True)

    def test_patch_and_aggregate_boundaries_fail_closed(self) -> None:
        surfaces = PatchSurfacePolicy((".agents/skills/study",), ("data/qrels", "confirmation"))
        surfaces.validate_changed_paths([".agents/skills/study/SKILL.md"])
        with self.assertRaises(PermissionError):
            surfaces.validate_changed_paths(["data/qrels/out.json"])
        with self.assertRaises(ValueError):
            assert_aggregate_only({"per_query": [{"query_id": "q1"}]})

    def test_confirmation_request_and_aggregate_are_hash_only(self) -> None:
        request = ConfirmationRequest(
            "request-1", "2026-07-28T00:00:00Z", "f" * 40,
            {"C": sha("submission")}, {"C": sha("config")}, {"analysis": sha("analysis")},
        )
        request.validate()
        comparison = AggregateComparison(
            track_id="C", gate_id="C", primary_metric="out_recall_at_100", baseline_id="hybrid", candidate_id="crossroute",
            n=3, baseline_point_estimate=0.2, candidate_point_estimate=0.206, paired_delta=0.006,
            ci95_lower=-0.001, ci95_upper=0.013, effect_size_name="rank_biserial", effect_size_value=0.2,
            wins=2, losses=1, ties=0,
            classification=ConfirmationClassification.HIGHER_MEASURED_SCORE_UNCERTAIN_SUPERIORITY,
            comparison_family=ComparisonFamilyMetadata("gate-c-primary", "primary", "none", 1),
        )
        package = ConfirmationAggregatePackage(
            "package-1", "2026-07-28T01:00:00Z", request.sha256,
            {"request": request.sha256}, {"aggregate": sha("aggregate")}, (comparison,),
        )
        package.validate(expected_request_sha256=request.sha256)
        payload = package.as_dict()
        payload["schema_version"] = AGGREGATE_SCHEMA
        self.assertEqual(validate_confirmation_aggregate(payload).comparisons[0].n, 3)
        payload["per_query"] = [{"query_id": "q1"}]
        with self.assertRaises(ValueError):
            validate_confirmation_aggregate(payload)
        payload.pop("per_query")
        payload["unexpected"] = "field"
        with self.assertRaises(ValueError):
            validate_confirmation_aggregate(payload)

    def test_manifest_v2_is_read_only_and_v3_contract_validates(self) -> None:
        base = {
            "schema_version": MANIFEST_V2,
            "identity": {"phase": "fixture"}, "lifecycle": {},
            "method": {},
            "inputs": {
                "dataset_manifest_hash": sha("dataset"),
                "split_query_ids_hash": sha("split"),
            },
            "evaluator": {"hash": sha("evaluator")},
            "budget": {}, "metrics": {}, "artifacts": [],
        }
        self.assertTrue(validate_manifest_payload(base)["read_only_legacy"])
        v3 = {
            **base,
            "schema_version": MANIFEST_V3,
            "method": {"provider": None},
            "identity": {
                "phase": "fixture", "arm": "C0",
                "research": {
                    "program_id": "myis-research", "display_name": "myIS Research",
                    "protocol_version": "1.0", "track_id": "C", "track_version": "0.1",
                    "package_version": "0.1.0", "research_version": "0.1",
                    "protocol_family_id": "crossroute-frozen-c1-skillopt-v1", "revision_id": "fixture",
                },
            },
            "environment": {
                "python_version": "3.11.9", "uv_version": "0.8.0", "os": "Windows",
                "architecture": "AMD64", "accelerator": "cpu", "uv_lock_sha256": sha("uv.lock")
            },
            "statistics": None,
            "surfaces": None,
            "isolation": None,
            "candidate_pool": None,
            "declared_artifact_hashes": {},
        }
        self.assertFalse(validate_manifest_payload(v3)["read_only_legacy"])
        legacy_v3 = {
            **v3,
            "identity": {
                **v3["identity"],
                "research": {**v3["identity"]["research"], "program_id": "is1-research"},
            },
        }
        self.assertTrue(validate_manifest_payload(legacy_v3)["read_only_legacy"])
        with self.assertRaises(ValueError):
            ResearchVersionSpec(program_id="is1-research").validate()

        measured = {
            **v3,
            "identity": {**v3["identity"], "phase": "C1"},
            "method": {
                "provider": {
                    "requested_model": "gpt-5.6-sol", "resolved_model": "gpt-5.6-sol",
                    "provider": "openai", "effort": "medium", "endpoint_class": "official",
                    "fallback_allowed": False, "fallback_used": False,
                }
            },
            "isolation": {
                "network_mode": "offline",
                "network_guard_sha256": sha("network-guard"),
                "cached_inputs_sha256": sha("cached-inputs"),
                "data_scopes": ["adaptation", "selection"],
                "dependency_replay_command": "uv sync --locked",
                "confirmation_access": False,
            },
            "inputs": {
                **v3["inputs"],
                "shared_split_commitment_sha256": sha("shared-split"),
                "track_firewall_sha256": sha("c-firewall"),
            },
        }
        self.assertFalse(validate_manifest_payload(measured)["read_only_legacy"])
        measured["method"] = {"provider": None}
        with self.assertRaises(ValidationError):
            validate_manifest_payload(measured)


if __name__ == "__main__":
    unittest.main()
