import hashlib
import json
import sqlite3
import tempfile
from pathlib import Path
from unittest import TestCase

from pydantic import ValidationError

from myis_research.harness.candidate_ledger import RouteHit
from myis_research.harness.f1_baselines import (
    CLOUD_TRANSFER_POLICY_V2,
    COMPUTE_SPRINT_RECEIPT_V1,
    MODEL_ARTIFACT_MANIFEST_V2,
    MODEL_SOURCE_MANIFEST_V1,
    RUNTIME_MAP_V1,
    CloudTransferPolicyV2,
    FrozenF1RunSpecV1,
    ModelArtifactCommitment,
    ModelArtifactManifestV2,
    RuntimeMapV1,
    create_compute_sprint_receipt,
    execute_cpu_fixture_adapter,
    preflight_model_manifest,
    replay_fixture_baselines,
    validate_compute_sprint_receipt,
)
from myis_research.harness.sparse import Fts5SchemaContract, inspect_fts5_database


def frozen_runspec_payload() -> dict[str, object]:
    return {
        "schema_version": "myis.frozen-f1-runspec.v1",
        "status": "frozen",
        "executable": True,
        "gate": "G1",
        "authorization": "F1.1_B0_B1_B2_ONLY",
        "track": "C",
        "phase": "F1",
        "task": "F1.1",
        "arms": ["B0", "B1", "B2"],
        "git_commit": "a" * 40,
        "owner_value_batch_sha256": "b" * 64,
        "proposal_sha256": "c" * 64,
        "source_sha256": {
            role: hashlib.sha256(role.encode()).hexdigest()
            for role in ("corpus", "queries", "qrels", "family", "evaluator", "field_protocol")
        },
        "split_membership_sha256": {
            role: hashlib.sha256(role.encode()).hexdigest()
            for role in ("train", "selection", "joint_test")
        },
        "environment_sha256": {
            role: hashlib.sha256(role.encode()).hexdigest()
            for role in ("uv_lock", "python", "code")
        },
        "model": {
            "model_id": "Llama-Embed-Nemotron-8B",
            "revision": "aa3b43a495a9b280d1bdb716da37c54bb495d630",
            "artifact_sha256": "d" * 64,
            "manifest_sha256": "e" * 64,
        },
        "protocol": {
            "B0": {"view": "TAC", "dense_top_k": 400, "final_family_k": 100},
            "B1": {
                "view": "TAC",
                "dense_top_k": 400,
                "bm25_top_k": 400,
                "fusion": "minmax_weighted",
                "dense_weight": 0.7,
                "bm25_weight": 0.3,
                "final_family_k": 100,
            },
            "B2": {
                "views": ["TAC", "Abstract", "Claim1"],
                "fusion": "rrf",
                "rrf_k": 60,
                "final_family_k": 100,
            },
        },
        "budget": {
            "compute_class": "local_cpu",
            "max_threads": 12,
            "max_wall_seconds": 3600,
            "max_temp_bytes": 1_000_000,
            "max_cost_usd": 0,
        },
        "runtime": {
            "python_version": "3.11.9",
            "uv_version": "0.8.0",
            "os": "Windows-11",
            "architecture": "AMD64",
            "accelerator": "cpu",
            "cuda_stack": None,
            "selected_groups": [],
            "selected_extras": ["dashboard", "tracking", "notebook", "test"],
        },
        "access": {
            "provider": "local",
            "endpoint_class": "local",
            "network_access": "none",
            "data_egress": False,
            "fallback": "forbidden",
            "parameter_dropping": False,
        },
    }


def hit(route: str, view: str, family: str, rank: int, score: float) -> RouteHit:
    return RouteHit("q-fixture", route, view, family, f"pub-{family}", rank, score)


class F1CpuScaffoldTests(TestCase):
    @staticmethod
    def fixture_hits() -> dict[str, tuple[RouteHit, ...]]:
        return {
            "B0": (hit("dense", "tac", "f1", 1, 0.9), hit("dense", "tac", "f2", 2, 0.8)),
            "B1": (
                hit("dense", "tac", "f1", 1, 0.9),
                hit("dense", "tac", "f2", 2, 0.1),
                hit("bm25", "tac", "f1", 2, -1.0),
                hit("bm25", "tac", "f2", 1, -3.0),
            ),
            "B2": (
                hit("tac", "tac", "f1", 1, 1.0),
                hit("abstract", "abstract", "f2", 1, 1.0),
                hit("claim1", "claim1", "f1", 2, 1.0),
            ),
        }

    def test_frozen_runspec_is_exact_and_rejects_unknown_fields(self) -> None:
        spec = FrozenF1RunSpecV1.model_validate(frozen_runspec_payload())
        self.assertEqual(spec.arms, ("B0", "B1", "B2"))
        invalid = frozen_runspec_payload()
        invalid["owner_decision_id"] = "circular-binding-is-forbidden"
        with self.assertRaises(ValidationError):
            FrozenF1RunSpecV1.model_validate(invalid)

    def test_source_free_baseline_replay_is_order_independent(self) -> None:
        fixtures = self.fixture_hits()
        first = replay_fixture_baselines(fixtures)
        replay = replay_fixture_baselines({arm: tuple(reversed(rows)) for arm, rows in fixtures.items()})
        self.assertEqual(
            {arm: result.ledger_sha256 for arm, result in first.items()},
            {arm: result.ledger_sha256 for arm, result in replay.items()},
        )
        self.assertEqual(first["B2"].candidates[0].family_id, "f1")

    def test_fixture_replay_rejects_protocol_drift(self) -> None:
        fixtures = {
            "B0": (hit("dense", "tac", "f1", 401, 0.9),),
            "B1": (hit("dense", "tac", "f1", 1, 0.9), hit("bm25", "tac", "f1", 1, 1.0)),
            "B2": (hit("tac", "tac", "f1", 1, 1.0),),
        }
        with self.assertRaisesRegex(ValueError, "top-400"):
            replay_fixture_baselines(fixtures)

        fixtures["B0"] = (hit("dense", "tac", "f1", 1, 0.9),)
        with self.assertRaisesRegex(ValueError, "every protocol route"):
            replay_fixture_baselines(fixtures)

    def test_model_preflight_never_loads_or_downloads_model_bytes(self) -> None:
        payload = {
            "schema_version": "myis.model-artifact.v1",
            "model_id": "Llama-Embed-Nemotron-8B",
            "revision": "aa3b43a495a9b280d1bdb716da37c54bb495d630",
            "artifact_sha256": "d" * 64,
        }
        encoded = json.dumps(payload, sort_keys=True).encode()
        commitment = ModelArtifactCommitment(
            model_id="Llama-Embed-Nemotron-8B",
            revision="aa3b43a495a9b280d1bdb716da37c54bb495d630",
            artifact_sha256="d" * 64,
            manifest_sha256=hashlib.sha256(encoded).hexdigest(),
        )
        self.assertEqual(preflight_model_manifest(None, commitment).status, "RESOURCE_BLOCKED")
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest = Path(temp_dir) / "manifest.json"
            manifest.write_bytes(encoded)
            result = preflight_model_manifest(manifest, commitment)
        self.assertEqual(result.status, "PASS")
        self.assertFalse(result.model_loaded)
        self.assertEqual(result.network_access, "none")

    def test_v2_model_manifest_binds_source_without_loading_model_bytes(self) -> None:
        source = {
            "schema_version": MODEL_SOURCE_MANIFEST_V1,
            "source_id": "nemotron-local-cache",
            "source_kind": "local_preprovisioned",
            "repository": "nvidia/llama-embed-nemotron-8b",
            "revision": "aa3b43a495a9b280d1bdb716da37c54bb495d630",
            "license": "NVIDIA Open Model License",
            "source_manifest_sha256": "a" * 64,
            "network_access": "none",
            "data_egress": False,
        }
        source_hash = hashlib.sha256(
            json.dumps(source, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8")
        ).hexdigest()
        payload = {
            "schema_version": MODEL_ARTIFACT_MANIFEST_V2,
            "model_id": "Llama-Embed-Nemotron-8B",
            "revision": "aa3b43a495a9b280d1bdb716da37c54bb495d630",
            "artifact_sha256": "d" * 64,
            "source": source,
            "source_manifest_sha256": source_hash,
        }
        encoded = json.dumps(payload, sort_keys=True).encode()
        commitment = ModelArtifactCommitment(
            model_id="Llama-Embed-Nemotron-8B",
            revision="aa3b43a495a9b280d1bdb716da37c54bb495d630",
            artifact_sha256="d" * 64,
            manifest_sha256=hashlib.sha256(encoded).hexdigest(),
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest = Path(temp_dir) / "manifest.json"
            manifest.write_bytes(encoded)
            result = preflight_model_manifest(manifest, commitment)
        self.assertEqual(result.status, "PASS")
        self.assertFalse(result.model_loaded)
        self.assertEqual(result.network_access, "none")
        self.assertEqual(result.source_manifest_sha256, source_hash)

        payload["source_manifest_sha256"] = "b" * 64
        with self.assertRaises(ValidationError):
            ModelArtifactManifestV2.model_validate(payload)

    def test_compute_sprint_receipt_stays_fixture_only_and_blocks_cloud_transfer(self) -> None:
        fixture_result = execute_cpu_fixture_adapter(self.fixture_hits())
        runtime = RuntimeMapV1(
            schema_version=RUNTIME_MAP_V1,
            runtime_id="owner-local-cpu",
            compute_class="local_cpu",
            python_version="3.11.9",
            uv_version="0.8.0",
            os="Windows-11",
            architecture="AMD64",
            accelerator="cpu",
            logical_cpu_count=12,
            memory_bytes=15_700_000_000,
            available_temp_bytes=1_000_000,
            network_access="none",
            gpu_access="none",
        )
        policy = CloudTransferPolicyV2(
            schema_version=CLOUD_TRANSFER_POLICY_V2,
            status="blocked",
            authorization="NOT_AUTHORIZED",
            target_compute_class="approved_cloud_gpu",
            provider="none",
            network_access="none",
            data_egress=False,
            gpu_access="none",
            fallback="forbidden",
            reason="G1 remains pending",
        )
        blocked = preflight_model_manifest(None, ModelArtifactCommitment(
            model_id="Llama-Embed-Nemotron-8B",
            revision="aa3b43a495a9b280d1bdb716da37c54bb495d630",
            artifact_sha256="d" * 64,
            manifest_sha256="e" * 64,
        ))
        receipt = create_compute_sprint_receipt(
            sprint_id="f1-fixture-sprint",
            runtime_map=runtime,
            cloud_transfer_policy=policy,
            model_preflight=blocked,
            fixture_result=fixture_result,
        )
        self.assertEqual(receipt.schema_version, COMPUTE_SPRINT_RECEIPT_V1)
        self.assertEqual(receipt.status, "RESOURCE_BLOCKED")
        self.assertEqual(receipt.gate_status, "pending")
        self.assertFalse(receipt.scientific_run)
        self.assertEqual(receipt.dataset_access, "none")
        self.assertEqual(receipt.scientific_metric_count, 0)
        self.assertEqual(validate_compute_sprint_receipt(receipt.model_dump(mode="json")), receipt)

        invalid_policy = policy.model_dump(mode="json")
        invalid_policy["status"] = "enabled"
        with self.assertRaises(ValidationError):
            CloudTransferPolicyV2.model_validate(invalid_policy)
        invalid_receipt = receipt.model_dump(mode="json")
        invalid_receipt["fixture_ledger_sha256"].pop("B2")
        with self.assertRaises(ValidationError):
            validate_compute_sprint_receipt(invalid_receipt)

    def test_fts_inspection_uses_regular_read_only_database(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database = Path(temp_dir) / "fixture.sqlite"
            connection = sqlite3.connect(database)
            try:
                connection.execute(
                    "CREATE VIRTUAL TABLE docs USING fts5(text, unit_id UNINDEXED, patent_id UNINDEXED, tokenize='unicode61')"
                )
                connection.commit()
            finally:
                connection.close()
            inspection = inspect_fts5_database(
                database, Fts5SchemaContract("docs", "text", ("unit_id", "patent_id"))
            )
        self.assertTrue(inspection.compatible, inspection.issues)


if __name__ == "__main__":
    import unittest

    unittest.main()
