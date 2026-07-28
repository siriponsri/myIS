import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]


def load_validator():
    path = ROOT / "05_code/scripts/validate_restructure.py"
    spec = importlib.util.spec_from_file_location("validate_restructure", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


validate_restructure = load_validator()


class RestructureValidatorTests(unittest.TestCase):
    def test_local_markdown_target_ignores_external_and_anchor_links(self) -> None:
        self.assertIsNone(validate_restructure.local_markdown_target("#phase-c0"))
        self.assertIsNone(validate_restructure.local_markdown_target("https://example.test/path"))
        self.assertEqual(
            validate_restructure.local_markdown_target("<docs/track c.md> 'title'"),
            "docs/track c.md",
        )
        self.assertEqual(
            validate_restructure.local_markdown_target("docs/track.md#section"),
            "docs/track.md",
        )

    def test_markdown_link_check_accepts_existing_local_targets(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text(
                "[plan](PLAN.md) [anchor](#local) [remote](https://example.test)\n",
                encoding="utf-8",
            )
            (root / "PLAN.md").write_text("# Plan\n", encoding="utf-8")

            self.assertEqual(validate_restructure.markdown_link_failures(root), [])

    def test_markdown_link_check_rejects_missing_and_escaping_targets(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text(
                "[missing](MISSING.md) [escape](../outside.md)\n", encoding="utf-8"
            )

            failures = validate_restructure.markdown_link_failures(root)

            self.assertTrue(any("broken Markdown link" in failure for failure in failures))
            self.assertTrue(any("Markdown link escapes repository" in failure for failure in failures))

    def test_active_context_excludes_protected_and_legacy_roots(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text("IS1 Research V0.1\n", encoding="utf-8")
            protected = root / "01_evidence/literature/frozen.md"
            protected.parent.mkdir(parents=True)
            protected.write_text("IS1 Research V0.1\n", encoding="utf-8")
            legacy = root / "02_tracks/99_legacy/01_R_ranking_evidence/history.md"
            legacy.parent.mkdir(parents=True)
            legacy.write_text("Track R\n", encoding="utf-8")
            demo = root / "03_experiments/V01_brain_drive_agent_demo/README.md"
            demo.parent.mkdir(parents=True)
            demo.write_text("is1-research\n", encoding="utf-8")

            failures = validate_restructure.active_context_failures(root)

            self.assertEqual(failures, ["legacy active-context reference (IS1 Research V0.1): README.md"])

    def test_repository_restructure_contract_is_valid(self) -> None:
        self.assertEqual(validate_restructure.validate(), [])


if __name__ == "__main__":
    unittest.main()
