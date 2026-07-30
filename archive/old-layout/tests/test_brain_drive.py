import json
import tempfile
import unittest
from pathlib import Path

from myis_research.adapters import (
    AdapterOperation,
    AdapterProvenance,
    AdapterRequest,
    AdapterResponse,
    AutoresearchAdapter,
    HyperResearchAdapter,
    Trial,
    TypedAdapterBoundary,
)
from myis_research.brain_drive import run_brain_drive_demo
from myis_research.governance import AuthorizationError
from myis_research.sources import register_source


REQUIRED_ARTIFACTS = (
    "prompt.json",
    "flow.json",
    "progress.jsonl",
    "result.json",
    "metrics.json",
    "manifest.json",
)


class BrainDriveTests(unittest.TestCase):
    def test_typed_adapter_is_read_only_first_and_provenance_bound(self) -> None:
        digest = "a" * 64

        def handler(_: AdapterRequest) -> AdapterResponse:
            return AdapterResponse(
                metadata={"title": "fixture"},
                classification="internal",
                provenance=AdapterProvenance(
                    "source", digest, digest, "fixture-mcp", "1", "2026-07-28T00:00:00Z"
                ),
            )

        boundary = TypedAdapterBoundary(handler)
        request = AdapterRequest("brain", AdapterOperation.READ, "doc", "lookup", digest)
        self.assertEqual(boundary.execute(request).metadata["title"], "fixture")
        with self.assertRaises(PermissionError):
            boundary.execute(
                AdapterRequest(
                    "brain", AdapterOperation.WRITE, "doc", "update", digest,
                    owner_decision_id="IS1-BRAIN-WRITE",
                )
            )
        with self.assertRaises(PermissionError):
            AdapterResponse(
                metadata={"qrels": {}},
                classification="protected",
                provenance=AdapterProvenance(
                    "source", digest, digest, "fixture-mcp", "1", "2026-07-28T00:00:00Z"
                ),
            ).validate()

    def test_source_hash_and_offline_flow(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "paper.pdf"
            source.write_bytes(b"fixture")
            record = register_source(source, kind="pdf", title="Fixture")
            self.assertEqual(len(record.sha256), 64)
            result = run_brain_drive_demo(root / "demo", mlflow_root=root / "mlflow")
            run_dir = Path(result["run_dir"])
            self.assertTrue(all((run_dir / name).exists() for name in REQUIRED_ARTIFACTS))
            self.assertEqual(result["report"]["report_sha256"], json.loads((run_dir / "result.json").read_text())["report_sha256"])
            receipt = result["mlflow_receipt"]
            self.assertIn(receipt["status"], {"synced", "already_synced", "sync_deferred"})
            self.assertFalse(any("per_query" in path for path in receipt["artifact_hashes"]))

    def test_hyperresearch_is_fail_closed(self) -> None:
        with self.assertRaises(AuthorizationError):
            HyperResearchAdapter(owner_approval="gate", provider="codex").validate()
        HyperResearchAdapter(owner_approval="gate", provider="claude").validate()

    def test_autoresearch_mapping_preserves_required_fields(self) -> None:
        entry = AutoresearchAdapter().to_ledger_entry(Trial("h", "p", "cmd", "score", 0.5, "keep"))
        self.assertEqual(entry["metrics"]["score"], 0.5)
        self.assertIn("upstream_commit", entry)


if __name__ == "__main__":
    unittest.main()
