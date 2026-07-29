import json
import shutil
import tempfile
from pathlib import Path
from unittest import TestCase

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


if __name__ == "__main__":
    import unittest

    unittest.main()
