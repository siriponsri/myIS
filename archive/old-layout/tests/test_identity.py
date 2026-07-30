import tempfile
from pathlib import Path
import unittest

from myis_research import __version__ as package_version
from myis_research.identity import (
    DISPLAY_NAME,
    PROGRAM_ID,
    PROTOCOL_FAMILY_ID,
    PROTOCOL_VERSION,
    RESEARCH_VERSION,
    IdentityValidationError,
    ResearchIdentity,
    assert_canonical_identity,
    load_research_identity,
    validate_full_git_commit,
)


ROOT = Path(__file__).resolve().parents[2]


class ResearchIdentityTests(unittest.TestCase):
    def test_myis_identity_is_canonical(self) -> None:
        identity = load_research_identity(ROOT)

        assert_canonical_identity(identity)
        self.assertEqual(identity.program_id, PROGRAM_ID)
        self.assertEqual(identity.display_name, DISPLAY_NAME)
        self.assertEqual(identity.protocol_version, PROTOCOL_VERSION)
        self.assertEqual(identity.research_version, RESEARCH_VERSION)
        self.assertEqual(identity.protocol_family_id, PROTOCOL_FAMILY_ID)
        self.assertIn("historical-program-label", identity.legacy_aliases)

    def test_package_version_is_independent(self) -> None:
        identity = load_research_identity(ROOT)

        self.assertEqual(package_version, "0.1.0")
        self.assertEqual(identity.research_version, "0.1")
        self.assertNotEqual(package_version, identity.research_version)

    def test_invalid_display_name_fails_closed(self) -> None:
        value = {
            "program_id": PROGRAM_ID,
            "display_name": "Paper E",
            "research_version": RESEARCH_VERSION,
            "protocol_version": PROTOCOL_VERSION,
            "version_class": "protocol_major",
            "protocol_family_id": PROTOCOL_FAMILY_ID,
            "legacy_aliases": ["Paper E"],
        }

        with self.assertRaises(IdentityValidationError):
            ResearchIdentity.from_mapping(value)

    def test_missing_project_mapping_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "00_governance/config"
            path.mkdir(parents=True)
            (path / "project.yaml").write_text("authority: {}\n", encoding="utf-8")

            with self.assertRaises(IdentityValidationError):
                load_research_identity(root)

    def test_full_git_commit_rejects_abbreviated_or_noncanonical_values(self) -> None:
        commit = "a" * 40
        self.assertEqual(validate_full_git_commit(commit), commit)
        self.assertEqual(validate_full_git_commit("b" * 64), "b" * 64)
        for invalid in ("a" * 12, "A" * 40, "g" * 40, ""):
            with self.subTest(invalid=invalid), self.assertRaises(IdentityValidationError):
                validate_full_git_commit(invalid)


if __name__ == "__main__":
    unittest.main()
