import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from myis_research.session_capsules import (
    SESSION_ROOT,
    SessionCapsuleValidationError,
    assert_append_only_session_target,
    validate_session_capsule,
)


def git(root: Path, *arguments: str) -> str:
    completed = subprocess.run(["git", *arguments], cwd=root, check=True, capture_output=True, text=True)
    return completed.stdout.strip()


def make_repository(root: Path) -> tuple[str, str]:
    evidence = root / "evidence.md"
    evidence.write_text("historical evidence\n", encoding="utf-8")
    (root / SESSION_ROOT).mkdir(parents=True)
    git(root, "init")
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "config", "user.name", "Session Capsule Test")
    git(root, "add", "evidence.md")
    git(root, "commit", "-m", "historical evidence")
    revision = git(root, "rev-parse", "HEAD")
    blob = subprocess.run(
        ["git", "show", f"{revision}:evidence.md"], cwd=root, check=True, capture_output=True
    ).stdout
    return revision, hashlib.sha256(blob).hexdigest()


def capsule_payload(revision: str, evidence_hash: str) -> dict[str, object]:
    return {
        "schema_version": "myis.research-session.v1",
        "session_id": "20260729T060000Z-closeout",
        "run_id": None,
        "goal_id": None,
        "started_at_utc": None,
        "ended_at_utc": "2026-07-29T06:00:00Z",
        "scope": "Validate an append-only closeout capsule.",
        "provenance": "agent-observed",
        "owner_approvals": [{"gate": "G0", "source": "approval.json#/decision_id", "scope": "F0 only"}],
        "repository": {"path": ".", "revision": revision, "dirty_paths": []},
        "events": [{
            "event_id": "EV0001",
            "sequence": 1,
            "type": "observation",
            "provenance": "agent-observed",
            "summary": "Historical evidence was verified at its recorded revision.",
            "evidence_refs": [{"path": "evidence.md", "sha256": evidence_hash, "locator": "entire file"}],
        }],
        "run_artifacts": {
            "prompt": None, "flow": None, "progress": None, "result": None, "metrics": None,
            "runtime": None, "per_query_metrics": None, "validation_report": None, "manifest": None,
            "mlflow_receipts": [],
        },
        "open_threads": [],
        "integrity": {
            "all_refs_exist": True,
            "all_hashes_match": True,
            "contains_protected_payload": False,
            "contains_secrets": False,
        },
    }


class SessionCapsuleTests(unittest.TestCase):
    def test_validates_historical_reference_at_recorded_revision(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            revision, evidence_hash = make_repository(root)
            path = root / SESSION_ROOT / "20260729T060000Z-closeout.json"
            path.write_text(json.dumps(capsule_payload(revision, evidence_hash)), encoding="utf-8")
            (root / "evidence.md").write_text("current file changed\n", encoding="utf-8")

            report = validate_session_capsule(path, root)

            self.assertEqual(report.session_id, "20260729T060000Z-closeout")
            self.assertEqual(report.reference_count, 1)

    def test_rejects_tampered_hash_and_protected_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            revision, evidence_hash = make_repository(root)
            path = root / SESSION_ROOT / "20260729T060000Z-closeout.json"
            payload = capsule_payload(revision, evidence_hash)
            payload["events"][0]["evidence_refs"][0]["sha256"] = "a" * 64
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(SessionCapsuleValidationError, "hash mismatch"):
                validate_session_capsule(path, root)

            payload = capsule_payload(revision, evidence_hash)
            payload["events"][0]["query_id"] = "protected"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(SessionCapsuleValidationError, "protected payload key"):
                validate_session_capsule(path, root)

    def test_append_only_target_requires_new_safe_name(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repository(root)
            target = root / SESSION_ROOT / "20260729T060000Z-closeout.json"
            self.assertEqual(assert_append_only_session_target(target, root), target.resolve())
            target.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(SessionCapsuleValidationError, "already exists"):
                assert_append_only_session_target(target, root)
            with self.assertRaises(SessionCapsuleValidationError):
                assert_append_only_session_target(root / "outside.json", root)


if __name__ == "__main__":
    unittest.main()
