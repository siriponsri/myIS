import hashlib
import json
import sqlite3
import tempfile
from pathlib import Path
from unittest import TestCase

from pydantic import ValidationError

from myis_research.harness.candidate_ledger import RouteHit
from myis_research.harness.f1_baselines import (
    FrozenF1RunSpecV1,
    ModelArtifactCommitment,
    preflight_model_manifest,
    replay_fixture_baselines,
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
    def test_frozen_runspec_is_exact_and_rejects_unknown_fields(self) -> None:
        spec = FrozenF1RunSpecV1.model_validate(frozen_runspec_payload())
        self.assertEqual(spec.arms, ("B0", "B1", "B2"))
        invalid = frozen_runspec_payload()
        invalid["owner_decision_id"] = "circular-binding-is-forbidden"
        with self.assertRaises(ValidationError):
            FrozenF1RunSpecV1.model_validate(invalid)

    def test_source_free_baseline_replay_is_order_independent(self) -> None:
        fixtures = {
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
