import copy
import hashlib
import tempfile
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from unittest import TestCase

from myis_research.harness.dapfam_contracts import (
    OWNER_VALUE_BATCH_SCHEMA,
    SPLIT_ALIASES,
    GeneratorIdentity,
    OwnerValueBatchV1,
    SourceCommitment,
    ValidationReceipt,
    proposal_hash,
)
from myis_research.harness.g1_preparation import hamilton_allocation, prepare_shared_split
from myis_research.mlflow_mirror import MirrorSpec, MirrorStage, MirrorValidationError


def synthetic_batch() -> OwnerValueBatchV1:
    split = prepare_shared_split(
        {f"q{index:04d}": f"bucket-{index % 7}" for index in range(1247)},
        out_positive_query_ids={f"q{index:04d}" for index in range(905)},
    ).commitment
    now = datetime.now(timezone.utc)
    payload = {
        "schema_version": OWNER_VALUE_BATCH_SCHEMA,
        "document_kind": "g1_owner_value_batch",
        "status": "proposal",
        "executable": False,
        "gate": "G1",
        "gate_status": "pending",
        "authorization": "NOT_AUTHORIZED",
        "scientific_run": False,
        "dataset_access": "owner_local_read_only",
        "scientific_metric_count": 0,
        "track": "C",
        "phase": "F1",
        "task": "F1.1",
        "generated_at_utc": now,
        "generator": GeneratorIdentity(
            program_id="myis-research",
            protocol_version="1.0",
            research_version="0.1",
            package_version="0.1.0",
            git_commit="a" * 40,
            python_version="3.11.9",
            platform="test",
        ).model_dump(mode="json"),
        "sources": [
            SourceCommitment(
                role=role,
                source_id=f"dapfam-{role}",
                relative_path=f"processed/{role}.dat",
                bytes=1,
                sha256=hashlib.sha256(role.encode()).hexdigest(),
            ).model_dump(mode="json")
            for role in ("corpus", "queries", "qrels", "out_strata", "validation")
        ],
        "inventory_counts": {"corpus": 45336, "queries": 1247, "qrels": 49869},
        "qrels_domain_distribution": {"IN": 19736, "OUT": 5193, "NC": 24940},
        "family_commitment_sha256": "b" * 64,
        "evaluator": {
            "evaluator_id": "dapfam-family-retrieval-v1",
            "unit": "patent_family",
            "relevance_rule": "grade_gt_0",
            "primary_metric": "recall_at_100",
            "claim_boundary": "retrieval_relevance_not_legal_truth",
        },
        "field_protocol": {"B0": "fixture", "B1": "fixture", "B2": "fixture"},
        "published_targets": {
            "encoder": "Llama-Embed-Nemotron-8B",
            "encoder_revision": "aa3b43a495a9b280d1bdb716da37c54bb495d630",
            "arms": ["B0", "B1", "B2"],
        },
        "split": split.model_dump(mode="json"),
        "validation": ValidationReceipt(
            status="PASS", validated_at_utc=now, checks={"fixture": True}
        ).model_dump(mode="json"),
        "unresolved_owner_decisions": ["final_G1_immutable_decision"],
        "owner_decision_sha256": None,
        "mlflow": None,
    }
    payload["proposal_sha256"] = proposal_hash(payload)
    return OwnerValueBatchV1.model_validate(payload)


class F1G1PreparationTests(TestCase):
    def test_hamilton_allocation_is_exact_and_stable(self) -> None:
        sizes = {"a": 100, "b": 100, "c": 47}
        self.assertEqual(sum(hamilton_allocation(sizes, 51).values()), 51)
        self.assertEqual(hamilton_allocation(sizes, 51), hamilton_allocation(dict(reversed(list(sizes.items()))), 51))

    def test_shared_split_is_exact_disjoint_and_replays(self) -> None:
        strata = {f"q{index:04d}": f"bucket-{index % 9}" for index in range(1247)}
        positives = {f"q{index:04d}" for index in range(905)}
        first = prepare_shared_split(strata, out_positive_query_ids=positives)
        replay = prepare_shared_split(dict(reversed(list(strata.items()))), out_positive_query_ids=reversed(sorted(positives)))
        self.assertEqual(first, replay)
        self.assertEqual({key: len(value) for key, value in first.membership.items()}, {"train": 250, "selection": 125, "joint_test": 872})
        self.assertEqual(sum(first.commitment.out_positive_counts.values()), 905)
        self.assertEqual(first.commitment.aliases, SPLIT_ALIASES)

    def test_duplicate_or_wrong_query_count_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "1,247"):
            prepare_shared_split({"q1": "OUT"}, out_positive_query_ids={"q1"})

    def test_proposal_hash_excludes_operational_linkage(self) -> None:
        batch = synthetic_batch()
        payload = batch.model_dump(mode="json")
        changed = copy.deepcopy(payload)
        changed["generated_at_utc"] = "2030-01-01T00:00:00Z"
        changed["mlflow"] = {"run_id": "later"}
        changed["validation"]["safe_batch_sha256"] = "c" * 64
        self.assertEqual(proposal_hash(payload), proposal_hash(changed))
        changed["field_protocol"]["B0"] = "drift"
        self.assertNotEqual(proposal_hash(payload), proposal_hash(changed))

    def test_batch_rejects_raw_membership(self) -> None:
        payload = synthetic_batch().model_dump(mode="json")
        payload["split"]["membership"] = {"train": ["q1"]}
        payload["proposal_sha256"] = proposal_hash(payload)
        with self.assertRaises(ValueError):
            OwnerValueBatchV1.model_validate(payload)

    def test_preparation_mlflow_stage_forbids_metrics_and_artifacts(self) -> None:
        spec = MirrorSpec(
            stage=MirrorStage.F1_G1_PREPARATION,
            run_name="fixture",
            git_commit="a" * 40,
            canonical_source_sha256="b" * 64,
            track="C",
            arm="G1_PREPARATION",
            phase="F1",
            data_role="preparation",
            tags={"scientific_run": "false"},
            metrics={},
        )
        spec.validate(())
        with self.assertRaisesRegex(MirrorValidationError, "metrics"):
            replace(spec, metrics={"recall": 1.0}).validate(())


if __name__ == "__main__":
    import unittest

    unittest.main()
