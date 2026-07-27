import json
import tempfile
import unittest
from pathlib import Path

from myis_research.adapters import AutoresearchAdapter, HyperResearchAdapter, Trial
from myis_research.brain_drive import run_brain_drive_demo
from myis_research.governance import AuthorizationError
from myis_research.mlflow_contract import AgentRun, AgentRunSpec, REQUIRED_ARTIFACTS
from myis_research.sources import register_source


class BrainDriveTests(unittest.TestCase):
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

    def test_hyperresearch_is_fail_closed(self) -> None:
        with self.assertRaises(AuthorizationError):
            HyperResearchAdapter(owner_approval="gate", provider="codex").validate()
        HyperResearchAdapter(owner_approval="gate", provider="claude").validate()

    def test_failed_run_preserves_complete_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run = AgentRun.start(Path(temp), AgentRunSpec(
                component="research", agent_id="test", experiment="failure",
                prompt_version="v1", skill_version="v1",
            ))
            run.progress("started")
            run_dir = run.fail("fixture failure")
            self.assertTrue(all((run_dir / name).exists() for name in REQUIRED_ARTIFACTS))
            self.assertEqual(json.loads((run_dir / "run.json").read_text())["status"], "FAILED")

    def test_autoresearch_mapping_preserves_required_fields(self) -> None:
        entry = AutoresearchAdapter().to_ledger_entry(Trial("h", "p", "cmd", "score", 0.5, "keep"))
        self.assertEqual(entry["metrics"]["score"], 0.5)
        self.assertIn("upstream_commit", entry)


if __name__ == "__main__":
    unittest.main()
