import hashlib
import shutil
import subprocess
import tempfile
from pathlib import Path
import unittest

from myis_research.dashboard.progress import build_dashboard_snapshot, parse_plan, scope_sha256
from myis_research.ledger import ImmutableJsonLedger


REPO_ROOT = Path(__file__).resolve().parents[2]


def git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True, text=True
    )
    return completed.stdout.strip()


def make_repository(root: Path) -> str:
    shutil.copy2(REPO_ROOT / "PLAN.md", root / "PLAN.md")
    (root / "00_governance/approvals").mkdir(parents=True)
    (root / "04_outputs/artifacts/task-evidence").mkdir(parents=True)
    (root / ".gitignore").write_text("01_evidence/private/\n", encoding="utf-8")
    git(root, "init")
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "config", "user.name", "Dashboard Test")
    git(root, "add", "PLAN.md", ".gitignore")
    git(root, "commit", "-m", "plan fixture")
    return git(root, "rev-parse", "HEAD")


class DashboardProgressTests(unittest.TestCase):
    def test_plan_projection_preserves_current_phase_and_task_order(self) -> None:
        plan = parse_plan(REPO_ROOT / "PLAN.md")
        self.assertEqual(len(plan.phases), 12)
        self.assertEqual(sum(len(phase.tasks) for phase in plan.phases), 15)
        self.assertEqual(plan.phases[0].phase_id, "F0")
        self.assertEqual(plan.phases[-1].phase_id, "P")

    def test_successful_activity_without_task_evidence_is_not_complete(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_repository(root)
            snapshot = build_dashboard_snapshot(root)
            task = snapshot["phases"][0]["tasks"][0]
            self.assertEqual(task["evidence_state"], "not_recorded")
            self.assertEqual(task["governance_state"], "pending")

    def test_passed_evidence_is_complete_but_owner_gate_remains_pending(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source_commit = make_repository(root)
            plan_sha256 = hashlib.sha256((root / "PLAN.md").read_bytes()).hexdigest()
            evidence_root = root / "04_outputs/artifacts/task-evidence/F0.1"
            ledger = ImmutableJsonLedger(evidence_root, prior_field="prior_record_hash")
            ledger.append(
                "F0-1-pass",
                {
                    "schema_version": "myis.task-evidence.v1",
                    "record_id": "F0-1-pass",
                    "task_id": "F0.1",
                    "plan_sha256": plan_sha256,
                    "git_commit": source_commit,
                    "acceptance_checks": [
                        {
                            "check_id": "validators",
                            "status": "passed",
                            "evidence_sha256": "a" * 64,
                        }
                    ],
                    "evidence_manifest_hashes": ["b" * 64],
                    "prior_record_hash": None,
                    "supersedes_record_id": None,
                },
            )
            git(root, "add", "04_outputs")
            git(root, "commit", "-m", "record evidence")

            snapshot = build_dashboard_snapshot(root)
            task = snapshot["phases"][0]["tasks"][0]
            self.assertEqual(task["evidence_state"], "complete")
            self.assertEqual(task["governance_state"], "pending")

    def test_plan_hash_drift_marks_existing_evidence_stale(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source_commit = make_repository(root)
            evidence_root = root / "04_outputs/artifacts/task-evidence/F0.1"
            ImmutableJsonLedger(evidence_root, prior_field="prior_record_hash").append(
                "F0-1-stale",
                {
                    "schema_version": "myis.task-evidence.v1",
                    "record_id": "F0-1-stale",
                    "task_id": "F0.1",
                    "plan_sha256": "c" * 64,
                    "git_commit": source_commit,
                    "acceptance_checks": [
                        {"check_id": "tests", "status": "passed", "evidence_sha256": "d" * 64}
                    ],
                    "evidence_manifest_hashes": [],
                    "prior_record_hash": None,
                    "supersedes_record_id": None,
                },
            )
            git(root, "add", "04_outputs")
            git(root, "commit", "-m", "record stale evidence")
            snapshot = build_dashboard_snapshot(root)
            self.assertEqual(snapshot["phases"][0]["tasks"][0]["evidence_state"], "stale")

    def test_scoped_gate_decision_does_not_authorize_sibling_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source_commit = make_repository(root)
            approvals = ImmutableJsonLedger(
                root / "00_governance/approvals", prior_field="prior_record_hash"
            )
            scope = {
                "action": "approve_implementation",
                "phase_ids": [],
                "task_ids": ["F0.1"],
                "targets": [],
            }
            approvals.append(
                "G0-F0-1-only",
                {
                    "schema_version": "myis.owner-gate-decision.v2",
                    "decision_id": "G0-F0-1-only",
                    "gate_id": "G0",
                    "status": "approved",
                    "rationale": "Approve only the first integrity task.",
                    "timestamp": "2026-07-28T00:00:00+00:00",
                    "actor": "a" * 64,
                    "display_label": None,
                    "evidence_manifest_hashes": [],
                    "git_commit": source_commit,
                    "scope": scope,
                    "scope_hash": scope_sha256(scope),
                    "prior_record_hash": None,
                    "supersedes_decision_id": None,
                },
            )

            snapshot = build_dashboard_snapshot(root)
            tasks = snapshot["phases"][0]["tasks"]
            self.assertEqual(tasks[0]["governance_state"], "approved")
            self.assertEqual(tasks[1]["governance_state"], "pending")
            self.assertEqual(tasks[2]["governance_state"], "pending")
            self.assertEqual(snapshot["gate_states"]["G0"], "partial")

    def test_scope_hash_mismatch_cannot_authorize_task(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source_commit = make_repository(root)
            scope = {
                "action": "approve_implementation",
                "phase_ids": [],
                "task_ids": ["F0.1"],
                "targets": [],
            }
            ImmutableJsonLedger(
                root / "00_governance/approvals", prior_field="prior_record_hash"
            ).append(
                "G0-invalid-scope-hash",
                {
                    "schema_version": "myis.owner-gate-decision.v2",
                    "decision_id": "G0-invalid-scope-hash",
                    "gate_id": "G0",
                    "status": "approved",
                    "rationale": "This malformed record must fail closed.",
                    "timestamp": "2026-07-28T00:00:00+00:00",
                    "actor": "a" * 64,
                    "display_label": None,
                    "evidence_manifest_hashes": [],
                    "git_commit": source_commit,
                    "scope": scope,
                    "scope_hash": "b" * 64,
                    "prior_record_hash": None,
                    "supersedes_decision_id": None,
                },
            )
            with self.assertRaisesRegex(ValueError, "scope_hash"):
                build_dashboard_snapshot(root)

    def test_owner_gate_filename_must_match_decision_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source_commit = make_repository(root)
            scope = {
                "action": "approve_implementation",
                "phase_ids": [],
                "task_ids": ["F0.1"],
                "targets": [],
            }
            ImmutableJsonLedger(
                root / "00_governance/approvals", prior_field="prior_record_hash"
            ).append(
                "wrong-filename",
                {
                    "schema_version": "myis.owner-gate-decision.v2",
                    "decision_id": "G0-canonical-id",
                    "gate_id": "G0",
                    "status": "approved",
                    "rationale": "The filename must preserve immutable identity.",
                    "timestamp": "2026-07-28T00:00:00+00:00",
                    "actor": "a" * 64,
                    "display_label": None,
                    "evidence_manifest_hashes": [],
                    "git_commit": source_commit,
                    "scope": scope,
                    "scope_hash": scope_sha256(scope),
                    "prior_record_hash": None,
                    "supersedes_decision_id": None,
                },
            )
            with self.assertRaisesRegex(ValueError, "filename"):
                build_dashboard_snapshot(root)


if __name__ == "__main__":
    unittest.main()
