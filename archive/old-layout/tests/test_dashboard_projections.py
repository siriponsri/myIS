import shutil
import tempfile
import unittest
from pathlib import Path

from myis_research.dashboard.progress import parse_plan
from myis_research.dashboard.projections import (
    load_evidence_catalog,
    load_governance_document_catalog,
    public_governance_catalog,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


class DashboardProjectionCatalogTests(unittest.TestCase):
    def test_public_catalog_aligns_plan_dashboard_linear_and_mlflow(self) -> None:
        plan = parse_plan(REPO_ROOT / "PLAN.md")
        payload = public_governance_catalog(REPO_ROOT, plan)
        self.assertEqual(payload["schema_version"], "myis.owner-governance-catalog.v1")
        self.assertEqual(len(payload["gates"]), 9)
        g4 = next(item for item in payload["gates"] if item["gate_id"] == "G4")
        g5 = next(item for item in payload["gates"] if item["gate_id"] == "G5")
        self.assertEqual(g4["opens_scope"]["phase_ids"], ["S0", "S1"])
        self.assertEqual(g5["opens_scope"]["phase_ids"], ["SF"])
        self.assertEqual(g4["title_en"], "Track S provider and baseline lock")
        self.assertEqual(payload["projection_alignment"]["plan"], {"phase_count": 13, "task_count": 22})
        self.assertEqual(payload["projection_alignment"]["linear"]["task_count"], 22)
        self.assertEqual(payload["projection_alignment"]["mlflow"]["document_count"], 11)
        self.assertEqual(len(payload["projection_alignment"]["mlflow"]["experiments"]), 6)
        self.assertGreaterEqual(len(payload["evidence_packages"]), 2)
        original = next(item for item in payload["evidence_packages"] if item["evidence_id"] == "f0-foundation-migration")
        revision = next(item for item in payload["evidence_packages"] if item["evidence_id"] == "f0-dashboard-mlflow-revision")
        self.assertEqual(original["gate_ids"], ["G0"])
        self.assertEqual(original["title_en"], "F0 foundation migration evidence")
        self.assertIn("protected-path comparison", original["summary_en"])
        self.assertEqual(revision["task_ids"], ["F0.3"])
        self.assertIn("English-first owner workflow", revision["summary_en"])
        external = next((item for item in payload["evidence_packages"] if item["evidence_id"] == "f1-g1-owner-value-batch"), None)
        if external is not None:
            self.assertEqual(external["gate_ids"], ["G1"])
            self.assertEqual(external["source"], "owner_local_f1_g1")
        self.assertNotIn(str(REPO_ROOT), str(payload))

    def test_governance_document_catalog_resolves_linear_issue_for_each_task(self) -> None:
        plan = parse_plan(REPO_ROOT / "PLAN.md")
        catalog = load_governance_document_catalog(REPO_ROOT, plan)
        canonical = next(item for item in catalog["documents"] if item["document_id"] == "canonical-plan")
        self.assertEqual(len(canonical["task_ids"]), 22)
        self.assertEqual(len(canonical["linear_issue_ids"]), 22)
        self.assertEqual(canonical["dashboard_content_id"], "canonical-plan")
        self.assertEqual(canonical["title_en"], "Canonical execution plan")

    def test_evidence_catalog_rejects_byte_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            paths = (
                "PLAN.md",
                "00_governance/config/evidence_catalog.yaml",
                "04_outputs/artifacts/f0-migration/F0-f32ac040efb5.json",
                "04_outputs/artifacts/f0-migration/F0-f5e00c80d990.json",
            )
            for relative in paths:
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(REPO_ROOT / relative, target)
            manifest = root / "04_outputs/artifacts/f0-migration/F0-f5e00c80d990.json"
            manifest.write_text(manifest.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "hash drifted"):
                load_evidence_catalog(root, parse_plan(root / "PLAN.md"))


if __name__ == "__main__":
    unittest.main()
