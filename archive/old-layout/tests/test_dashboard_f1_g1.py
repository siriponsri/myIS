import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from fastapi.testclient import TestClient

from myis_research.dashboard.app import create_app
from myis_research.dashboard.readiness import load_f1_g1_readiness


ROOT = Path(__file__).resolve().parents[2]


class DashboardF1G1Tests(TestCase):
    def test_missing_owner_store_is_safe_and_pending(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            root.mkdir()
            payload = load_f1_g1_readiness(root)
        self.assertFalse(payload["prepared"])
        self.assertEqual(payload["gate_status"], "pending")
        self.assertFalse(payload["scientific_run"])

    def test_presentation_endpoint_is_session_protected_and_thai_first(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for relative in (
                "00_governance/config/dashboard_topics.yaml",
                "06_frontend/dashboard/index.html",
                "06_frontend/dashboard/assets/tokens.css",
                "06_frontend/dashboard/assets/dashboard.css",
                "06_frontend/dashboard/assets/dashboard.js",
            ):
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / relative, target)
            (root / "00_governance/approvals").mkdir(parents=True)
            app = create_app(
                repository_root=root,
                actor_sid_override="S-1-5-21-f1-g1-test",
                test_mode=True,
            )
            client = TestClient(app, base_url="http://127.0.0.1:8765")
            self.assertEqual(client.get("/api/v1/presentation-topics").status_code, 401)
            client.get("/api/v1/session")
            response = client.get("/api/v1/presentation-topics")
            self.assertEqual(response.status_code, 200, response.text)
            topic = response.json()["topics"][0]
            self.assertEqual(topic["topic_id"], "dapfam")
            self.assertIn("ระดับตระกูล", topic["subtitle_th"])
            self.assertEqual(topic["data"]["gate_status"], "pending")
            self.assertNotIn(str(root), response.text)

    def test_notebook_source_has_no_stored_outputs(self) -> None:
        payload = json.loads((ROOT / "03_experiments/notebooks/Data_Review.ipynb").read_text(encoding="utf-8"))
        for cell in payload["cells"]:
            if cell["cell_type"] == "code":
                self.assertIsNone(cell["execution_count"])
                self.assertEqual(cell["outputs"], [])
        text = json.dumps(payload, ensure_ascii=False)
        self.assertIn("ยังไม่รัน - รอ G1", text)
        self.assertNotIn("Recall@100 =", text)
        self.assertEqual(payload["metadata"]["kernelspec"]["name"], "python3")

    def test_notebook_discovers_safe_batch_without_environment_override(self) -> None:
        payload = json.loads((ROOT / "03_experiments/notebooks/Data_Review.ipynb").read_text(encoding="utf-8"))
        first_code_cell = next(cell for cell in payload["cells"] if cell["cell_type"] == "code")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            safe_root = root / "01_Stores/00_myIS/owner-local/f1-g1/safe"
            batch_path = safe_root / "batches/fixture.json"
            projection_path = safe_root / "projections/current.json"
            batch_path.parent.mkdir(parents=True)
            projection_path.parent.mkdir(parents=True)
            batch_path.write_text(
                json.dumps(
                    {
                        "schema_version": "myis.g1-owner-value-batch.v1",
                        "gate_status": "pending",
                        "authorization": "NOT_AUTHORIZED",
                        "scientific_run": False,
                        "scientific_metric_count": 0,
                    }
                ),
                encoding="utf-8",
            )
            projection_path.write_text(
                json.dumps(
                    {
                        "schema_version": "myis.f1-g1-safe-projection.v1",
                        "safe_batch_id": batch_path.name,
                        "safe_batch_sha256": hashlib.sha256(batch_path.read_bytes()).hexdigest(),
                    }
                ),
                encoding="utf-8",
            )
            workdir = root / "workspace/repository"
            workdir.mkdir(parents=True)
            previous = Path.cwd()
            try:
                os.chdir(workdir)
                with patch.dict(os.environ, {"MYIS_F1G1_SAFE_BATCH": ""}):
                    namespace: dict[str, object] = {}
                    exec(compile("".join(first_code_cell["source"]), "Data_Review.ipynb", "exec"), namespace)
            finally:
                os.chdir(previous)
        self.assertEqual(namespace["safe_batch"], batch_path.resolve())

    def test_notebook_rejects_tampered_safe_batch(self) -> None:
        payload = json.loads((ROOT / "03_experiments/notebooks/Data_Review.ipynb").read_text(encoding="utf-8"))
        first_code_cell = next(cell for cell in payload["cells"] if cell["cell_type"] == "code")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            safe_root = root / "01_Stores/00_myIS/owner-local/f1-g1/safe"
            batch_path = safe_root / "batches/fixture.json"
            projection_path = safe_root / "projections/current.json"
            batch_path.parent.mkdir(parents=True)
            projection_path.parent.mkdir(parents=True)
            batch_path.write_text("{}", encoding="utf-8")
            projection_path.write_text(
                json.dumps(
                    {
                        "schema_version": "myis.f1-g1-safe-projection.v1",
                        "safe_batch_id": batch_path.name,
                        "safe_batch_sha256": "0" * 64,
                    }
                ),
                encoding="utf-8",
            )
            workdir = root / "workspace/repository"
            workdir.mkdir(parents=True)
            previous = Path.cwd()
            try:
                os.chdir(workdir)
                with patch.dict(os.environ, {"MYIS_F1G1_SAFE_BATCH": ""}):
                    with self.assertRaisesRegex(RuntimeError, "hash mismatch"):
                        exec(compile("".join(first_code_cell["source"]), "Data_Review.ipynb", "exec"), {})
            finally:
                os.chdir(previous)


if __name__ == "__main__":
    import unittest

    unittest.main()
