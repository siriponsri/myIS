import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from myis_research.dashboard.progress import (
    _dependency_annotations,
    _dependency_ids,
    _gate_readiness,
    build_owner_inbox,
    build_dashboard_snapshot,
    parse_plan,
    scope_sha256,
)
from myis_research.ledger import ImmutableJsonLedger


REPO_ROOT = Path(__file__).resolve().parents[2]


def git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True, text=True
    )
    return completed.stdout.strip()


def make_repository(root: Path) -> str:
    shutil.copy2(REPO_ROOT / "PLAN.md", root / "PLAN.md")
    (root / "00_governance/config").mkdir(parents=True)
    shutil.copy2(
        REPO_ROOT / "00_governance/config/linear.yaml",
        root / "00_governance/config/linear.yaml",
    )
    (root / "00_governance/approvals").mkdir(parents=True)
    (root / "04_outputs/artifacts/task-evidence").mkdir(parents=True)
    (root / ".gitignore").write_text("01_evidence/private/\n", encoding="utf-8")
    git(root, "init")
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "config", "user.name", "Dashboard Test")
    git(root, "add", "PLAN.md", ".gitignore", "00_governance/config/linear.yaml")
    git(root, "commit", "-m", "plan fixture")
    return git(root, "rev-parse", "HEAD")


class DashboardProgressTests(unittest.TestCase):
    def test_dependency_parser_ignores_parallel_and_independent_annotations(self) -> None:
        self.assertEqual(
            _dependency_ids("S0; parallel with S1.1 and S1.3", "S1.2"),
            ["S0"],
        )
        self.assertEqual(
            _dependency_annotations("S0; parallel with S1.1 and S1.3", "S1.2"),
            {"parallel_with": ["S1.1", "S1.3"], "independent_of": []},
        )
        self.assertEqual(
            _dependency_ids("CF and SF; independent of Q/PC/PS", "CT.1"),
            ["CF", "SF"],
        )
        self.assertEqual(
            _dependency_annotations("CF and SF; independent of Q/PC/PS", "CT.1"),
            {"parallel_with": [], "independent_of": ["Q", "PC", "PS"]},
        )

    def test_dependency_range_expands_inclusive(self) -> None:
        self.assertEqual(
            _dependency_ids("S1.1-S1.3", "SF.1"),
            ["S1.1", "S1.2", "S1.3"],
        )

    def test_phase_dependency_with_sentence_punctuation_is_not_dropped(self) -> None:
        self.assertEqual(_dependency_ids("F1.", "D0.1"), ["F1"])
        self.assertEqual(_dependency_ids("F1.1", "D0.1"), ["F1.1"])

    def test_snapshot_exposes_validated_graph_and_owner_focus(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_repository(root)
            snapshot = build_dashboard_snapshot(root)
            self.assertEqual(len(snapshot["plan_graph"]["task_edges"]), 27)
            self.assertEqual(len(snapshot["plan_graph"]["groups"]), 5)
            self.assertEqual(snapshot["plan_graph"]["source_bindings"]["authority"], "PLAN.md")
            self.assertIn("mode", snapshot["owner_focus"])
            s1_annotations = [
                item for item in snapshot["plan_graph"]["annotations"] if item["task_id"] == "S1.2"
            ]
            self.assertEqual(s1_annotations[0]["parallel_with"], ["S1.1", "S1.3"])

    def test_plan_projection_preserves_current_phase_and_task_order(self) -> None:
        plan = parse_plan(REPO_ROOT / "PLAN.md")
        self.assertEqual(len(plan.phases), 13)
        self.assertEqual(sum(len(phase.tasks) for phase in plan.phases), 22)
        self.assertEqual(plan.phases[0].phase_id, "F0")
        self.assertEqual(plan.phases[-1].phase_id, "PS")

    def test_current_pre_f1_readiness_is_a_projection_of_verified_phase_and_gate_state(self) -> None:
        snapshot = build_dashboard_snapshot(REPO_ROOT)
        self.assertEqual(
            snapshot["readiness"],
            {
                "f0": "closed",
                "g0": "approved",
                "f1": "waiting_gate",
                "g1": "pending",
                "project": "f1_g1_preparation_only",
                "project_label": "F1/G1 preparation only",
            },
        )
        self.assertTrue(snapshot["gate_readiness"]["G1"]["ready"])
        self.assertEqual(snapshot["gate_readiness"]["G1"]["waiting_for"], [])
        self.assertFalse(snapshot["gate_readiness"]["G2"]["ready"])
        self.assertEqual(snapshot["gate_readiness"]["G2"]["waiting_for"], ["F1"])
        self.assertFalse(snapshot["gate_readiness"]["G4"]["ready"])
        self.assertEqual(snapshot["gate_readiness"]["G4"]["waiting_for"], ["CF"])

    def test_owner_inbox_requests_g1_from_pre_f1_prerequisites(self) -> None:
        with patch("myis_research.dashboard.progress.latest_valid_session", return_value=None) as latest:
            inbox = build_owner_inbox(REPO_ROOT)
        self.assertEqual(inbox["gate"]["gate_id"], "G1")
        self.assertTrue(inbox["gate"]["ready"])
        self.assertEqual(inbox["task"]["task_id"], "F1.1")
        self.assertEqual(inbox["scientific_results"], "NOT_RUN")
        latest.assert_called_once_with(
            REPO_ROOT,
            phase_id="F1",
            task_id="F1.1",
            gate_id="G1",
        )

    def test_later_gate_requires_all_prior_gates_even_when_phase_evidence_is_complete(self) -> None:
        snapshot = build_dashboard_snapshot(REPO_ROOT)
        phases = json.loads(json.dumps(snapshot["phases"]))
        next(phase for phase in phases if phase["phase_id"] == "F1")["evidence_state"] = "complete"
        readiness = _gate_readiness(phases, snapshot["gate_states"])
        self.assertEqual(readiness["G2"]["waiting_for"], [])
        self.assertEqual(readiness["G2"]["prior_gates_pending"], ["G1"])
        self.assertFalse(readiness["G2"]["ready"])

    def test_successful_activity_without_task_evidence_is_not_complete(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_repository(root)
            snapshot = build_dashboard_snapshot(root)
            task = snapshot["phases"][0]["tasks"][0]
            self.assertEqual(task["evidence_state"], "not_recorded")
            self.assertEqual(task["governance_state"], "pending")
            self.assertEqual(task["project_state"], "verification_needed")
            self.assertEqual(snapshot["progress"]["completed_task_count"], 0)
            self.assertEqual(snapshot["progress"]["completion_authority"], "canonical_task_evidence")

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
            self.assertEqual(task["project_state"], "complete")
            self.assertEqual(snapshot["phases"][0]["project_state"], "in_progress")

    def test_superseding_correction_reconciles_a_second_genesis(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source_commit = make_repository(root)
            plan_sha256 = hashlib.sha256((root / "PLAN.md").read_bytes()).hexdigest()
            evidence_root = root / "04_outputs/artifacts/task-evidence/F0.1"
            evidence_root.mkdir()
            base = {
                "schema_version": "myis.task-evidence.v1",
                "task_id": "F0.1",
                "plan_sha256": plan_sha256,
                "git_commit": source_commit,
                "acceptance_checks": [
                    {"check_id": "validators", "status": "passed", "evidence_sha256": "a" * 64}
                ],
                "evidence_manifest_hashes": ["b" * 64],
                "prior_record_hash": None,
                "supersedes_record_id": None,
            }
            first = {**base, "record_id": "F0-1-first"}
            malformed = {**base, "record_id": "F0-1-malformed"}
            (evidence_root / "F0-1-first.json").write_text(json.dumps(first), encoding="utf-8")
            (evidence_root / "F0-1-malformed.json").write_text(json.dumps(malformed), encoding="utf-8")
            ledger = ImmutableJsonLedger(
                evidence_root,
                prior_field="prior_record_hash",
                record_id_field="record_id",
                supersedes_field="supersedes_record_id",
            )
            first_hash = next(digest for _, payload, digest in ledger.records() if payload["record_id"] == "F0-1-first")
            correction = {
                **malformed,
                "record_id": "F0-1-correction",
                "prior_record_hash": first_hash,
                "supersedes_record_id": "F0-1-malformed",
            }
            (evidence_root / "F0-1-correction.json").write_text(json.dumps(correction), encoding="utf-8")
            git(root, "add", "04_outputs")
            git(root, "commit", "-m", "repair evidence chain")

            snapshot = build_dashboard_snapshot(root)
            task = snapshot["phases"][0]["tasks"][0]
            self.assertEqual(task["evidence_state"], "complete")
            self.assertEqual(task["evidence"]["record_id"], "F0-1-correction")

    def test_linear_done_without_canonical_evidence_needs_verification(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_repository(root)
            linear_path = root / "00_governance/config/linear.yaml"
            linear_text = linear_path.read_text(encoding="utf-8").replace(
                "task_id: F0.1, phase: F0, external_id: SIR-5, status: In Progress",
                "task_id: F0.1, phase: F0, external_id: SIR-5, status: Done",
            )
            linear_path.write_text(linear_text, encoding="utf-8")
            snapshot = build_dashboard_snapshot(root)
            task = snapshot["phases"][0]["tasks"][0]
            self.assertEqual(task["evidence_state"], "not_recorded")
            self.assertEqual(task["project_state"], "verification_needed")

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
