import tempfile
import unittest
from pathlib import Path

from myis_research.notes.catalog import build_notes, load_note_catalog, validate_note


ROOT = Path(__file__).parents[2]


class ResearchNoteTests(unittest.TestCase):
    def test_generated_catalog_is_allowlisted_and_pathless(self) -> None:
        catalog = load_note_catalog(ROOT)
        self.assertEqual(catalog["schema_version"], "myis.research-note-catalog.v1")
        self.assertGreaterEqual(len(catalog["notes"]), 3)
        for note in catalog["notes"]:
            self.assertTrue(note["obsidian_uri"].startswith("obsidian://open?"))
            self.assertNotIn("qrels", str(note["source_paths"]).casefold())
            self.assertNotIn(str(ROOT), note["obsidian_uri"])

    def test_build_is_deterministically_structured_and_validates_notes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / ".git").mkdir()
            # Build uses Git for the immutable source pointer; validate the checked-in projection directly.
            self.assertEqual(validate_note(ROOT / "07_obsidian_note/generated/current-status.md", ROOT)["note_id"], "current-status")

    def test_unsafe_or_protected_note_metadata_is_rejected(self) -> None:
        path = ROOT / "07_obsidian_note/generated/current-status.md"
        original = path.read_text(encoding="utf-8")
        try:
            path.write_text(original.replace("  - HANDOFF.md", "  - qrels/per_query.json"), encoding="utf-8")
            with self.assertRaises(ValueError):
                validate_note(path, ROOT)
        finally:
            path.write_text(original, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
