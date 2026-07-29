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
    latest_valid_session,
    validate_all_session_capsules,
    validate_session_capsule,
)


def git(root: Path, *arguments: str) -> str:
    completed = subprocess.run(["git", *arguments], cwd=root, check=True, capture_output=True, text=True)
    return completed.stdout.strip()


def make_repository(root: Path) -> tuple[str, str]:
    evidence = root / "evidence.md"
    evidence.write_text("historical evidence\n", encoding="utf-8")
    (root / "PLAN.md").write_text(
        "# Test plan\n\n### Task F1.1 - Reproduce test baseline\n- **Owner Gate:** G1 Reproduction\n",
        encoding="utf-8",
    )
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


def v2_capsule_payload(revision: str, evidence_hash: str, *, session_id: str) -> dict[str, object]:
    reference = {"path": "evidence.md", "sha256": evidence_hash, "locator": "entire file"}
    payload = capsule_payload(revision, evidence_hash)
    payload.update({
        "schema_version": "myis.research-session.v2",
        "session_id": session_id,
        "owner_approvals": [],
        "events": [{
            "event_id": "EV0001",
            "sequence": 1,
            "type": "claim",
            "provenance": "agent-observed",
            "summary": "Fixture evidence was verified.",
            "evidence_refs": [reference],
            "quantitative_claims": [{
                "claim_id": "QC0001",
                "statement": "Fixture count is one.",
                "value": 1,
                "unit": "file",
                "evidence_ref": reference,
            }],
        }],
        "execution_snapshot": {
            "phase_id": "F1", "task_id": "F1.1", "gate_id": "G1", "gate_status": "pending",
        },
        "owner_brief_th": "งานนี้ตรวจหลักฐานตัวอย่างและยังรอการอนุมัติจากเจ้าของงาน",
        "owner_actions": [{
            "action_id": "OA001", "priority": "required",
            "action_th": "ตรวจคำขอ Gate ก่อนอนุมัติ", "reason_th": "งานวิทยาศาสตร์ยังไม่เปิด",
            "blocking_gate": "G1",
        }],
        "gate_request": {
            "gate_id": "G1", "state": "draft", "summary_th": "เตรียมคำขอ Gate สำหรับการทำงานถัดไป",
            "blocking_reason_th": None, "evidence_refs": [],
        },
        "next_resources": {
            "status": "required",
            "items": [{
                "resource_id": "NR001", "description_th": "ต้องมีเอกสารอนุมัติ Gate",
                "purpose_th": "เพื่อเปิดขอบเขตงานที่อนุญาต",
            }],
        },
        "closeout": {
            "checks": [{"check_id": "CHK001", "status": "PASS", "summary": "fixture validated"}],
            "changed_files": [], "untouched_protected_surfaces": ["qrels", "confirmation membership"],
        },
        "corrections": [],
    })
    return payload


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

    def test_v2_requires_strict_closeout_and_binds_quantitative_claims(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            revision, evidence_hash = make_repository(root)
            path = root / SESSION_ROOT / "20260729T060001Z-v2-closeout.json"
            payload = v2_capsule_payload(revision, evidence_hash, session_id=path.stem)
            path.write_text(json.dumps(payload), encoding="utf-8")

            report = validate_session_capsule(path, root)

            self.assertEqual(report.schema_version, "myis.research-session.v2")
            self.assertEqual(report.reference_count, 1)
            payload["owner_brief_th"] = "English only"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(SessionCapsuleValidationError, "Thai text"):
                validate_session_capsule(path, root)

    def test_v2_rejects_unknown_fields_and_unbound_quantitative_claims(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            revision, evidence_hash = make_repository(root)
            path = root / SESSION_ROOT / "20260729T060002Z-v2-strict.json"
            payload = v2_capsule_payload(revision, evidence_hash, session_id=path.stem)
            payload["unexpected"] = True
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(SessionCapsuleValidationError, "v2 capsule keys"):
                validate_session_capsule(path, root)

            payload = v2_capsule_payload(revision, evidence_hash, session_id=path.stem)
            payload["events"][0]["quantitative_claims"][0]["evidence_ref"] = {
                "path": "evidence.md", "sha256": "a" * 64, "locator": "wrong",
            }
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(SessionCapsuleValidationError, "must bind"):
                validate_session_capsule(path, root)

    def test_validate_all_classifies_and_covers_invalid_v1(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            revision, evidence_hash = make_repository(root)
            legacy = root / SESSION_ROOT / "20260729T060003Z-invalid-v1.json"
            invalid = capsule_payload(revision, evidence_hash)
            invalid["session_id"] = legacy.stem
            invalid["events"][0]["evidence_refs"][0]["sha256"] = "a" * 64
            legacy.write_text(json.dumps(invalid), encoding="utf-8")
            initial = validate_all_session_capsules(root)
            self.assertEqual(initial["status"], "FAIL")

            correction = root / SESSION_ROOT / "20260729T060004Z-correction.json"
            payload = v2_capsule_payload(revision, evidence_hash, session_id=correction.stem)
            payload["corrections"] = [{
                "target_session_id": legacy.stem,
                "observed_validation_error": "evidence reference hash mismatch: evidence.md",
                "correction_th": "บันทึกข้อผิดพลาดของหลักฐานเดิมโดยไม่แก้ไฟล์ประวัติ",
            }]
            correction.write_text(json.dumps(payload), encoding="utf-8")
            audited = validate_all_session_capsules(root)
            self.assertEqual(audited["status"], "PASS")
            classifications = {item["session_id"]: item["classification"] for item in audited["records"]}
            self.assertEqual(classifications[legacy.stem], "CORRECTED_INVALID_V1")
            latest = latest_valid_session(root, phase_id="F1", task_id="F1.1", gate_id="G1")
            self.assertEqual(latest["session_id"], correction.stem)


if __name__ == "__main__":
    unittest.main()
