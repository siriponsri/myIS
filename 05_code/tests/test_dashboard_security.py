import tempfile
from pathlib import Path
import unittest

from fastapi.testclient import TestClient
from pydantic import ValidationError

from datetime import datetime, timezone

from myis_research.dashboard.app import _decision_id, create_app
from myis_research.dashboard.artifacts import ArtifactCatalog
from myis_research.dashboard.contracts import DecisionPreviewRequest
from myis_research.dashboard.progress import parse_plan, validate_decision_scope
from myis_research.dashboard.security import WindowsSession, _validate_session_snapshot


class DashboardSecurityTests(unittest.TestCase):
    def test_decision_id_is_ledger_safe(self) -> None:
        value = _decision_id("MYIS-G0", datetime(2026, 7, 28, 1, 2, 3, 456789, tzinfo=timezone.utc))
        self.assertEqual(value, "MYIS-G0-20260728T010203456789Z")

    def test_superseded_is_not_a_decision_outcome(self) -> None:
        with self.assertRaises(ValidationError):
            DecisionPreviewRequest(
                gate_id="G0",
                status="superseded",
                rationale="correct an earlier record",
                evidence_manifest_hashes=(),
                scope={
                    "action": "approve_implementation",
                    "phase_ids": ["F0"],
                    "task_ids": [],
                    "targets": [],
                },
            )

    def test_session_snapshot_rejects_remote_and_multi_user_operation(self) -> None:
        _validate_session_snapshot([WindowsSession(1, "Console", 0, "owner", True)])
        with self.assertRaises(RuntimeError):
            _validate_session_snapshot([WindowsSession(1, "RDP-Tcp#1", 0, "owner", True)])
        with self.assertRaises(RuntimeError):
            _validate_session_snapshot(
                [
                    WindowsSession(1, "Console", 0, "owner", True),
                    WindowsSession(2, "RDP-Tcp#2", 4, "other", False),
                ]
            )

    def test_loopback_host_origin_session_and_headers(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "00_governance/approvals").mkdir(parents=True)
            app = create_app(
                repository_root=root,
                port=8765,
                actor_sid_override="S-1-5-21-test",
                test_mode=True,
            )
            client = TestClient(app, base_url="http://127.0.0.1:8765")
            health = client.get("/healthz")
            self.assertEqual(health.status_code, 200)
            self.assertEqual(health.headers["cache-control"], "no-store, max-age=0")
            self.assertEqual(health.json()["research_version"], "0.1")

            session = client.get("/api/v1/session")
            csrf = session.json()["csrf_token"]
            rejected = client.post(
                "/api/v1/owner-gates/preview",
                headers={"origin": "http://evil.invalid", "x-csrf-token": csrf},
                json={
                    "gate_id": "G0",
                    "status": "approved",
                    "rationale": "fixture approval",
                    "evidence_manifest_hashes": [],
                    "scope": {
                        "action": "approve_implementation",
                        "phase_ids": ["F0"],
                        "task_ids": [],
                        "targets": [],
                    },
                },
            )
            self.assertEqual(rejected.status_code, 403)

    def test_openapi_and_generic_mutation_routes_are_absent(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            app = create_app(
                repository_root=root,
                port=8765,
                actor_sid_override="S-1-5-21-test",
                test_mode=True,
            )
            client = TestClient(app, base_url="http://127.0.0.1:8765")
            self.assertEqual(client.get("/openapi.json").status_code, 404)
            self.assertEqual(
                client.put(
                    "/api/v1/artifacts/x",
                    headers={"origin": "http://127.0.0.1:8765"},
                ).status_code,
                404,
            )

    def test_protected_artifact_projection_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "catalog.json"
            path.write_text(
                '{"schema_version":"myis.dashboard-artifact-catalog.v1","artifacts":['
                '{"artifact_id":"q","title":"hidden","artifact_class":"result",'
                '"classification":"confirmation","sha256":"' + "a" * 64 + '",'
                '"size_bytes":1,"manifest_sha256":"' + "b" * 64 + '"}]}'
            )
            with self.assertRaises(PermissionError):
                ArtifactCatalog(path).public_entries()

    def test_gate_scope_rejects_tasks_and_phases_owned_by_another_gate(self) -> None:
        plan = parse_plan(Path(__file__).resolve().parents[2] / "PLAN.md")
        with self.assertRaisesRegex(ValueError, "not governed by G8"):
            validate_decision_scope(
                plan,
                "G8",
                {
                    "action": "authorize_publication",
                    "phase_ids": ("F0",),
                    "task_ids": ("F0.1",),
                    "targets": (),
                },
            )
        with self.assertRaisesRegex(ValueError, "not governed by G1"):
            validate_decision_scope(
                plan,
                "G1",
                {
                    "action": "authorize_reproduction",
                    "phase_ids": ("S1",),
                    "task_ids": ("S1.1",),
                    "targets": (),
                },
            )

    def test_confirmation_requires_q_phase_or_task_scope(self) -> None:
        plan = parse_plan(Path(__file__).resolve().parents[2] / "PLAN.md")
        with self.assertRaisesRegex(ValueError, "requires a governed phase or task"):
            validate_decision_scope(
                plan,
                "G6",
                {
                    "action": "authorize_joint_confirmation",
                    "phase_ids": (),
                    "task_ids": (),
                    "targets": ("04_outputs/confirmation-request.json",),
                },
            )
        validate_decision_scope(
            plan,
            "G6",
            {
                    "action": "authorize_joint_confirmation",
                "phase_ids": ("Q",),
                "task_ids": ("Q.1",),
                "targets": ("04_outputs/confirmation-request.json",),
            },
        )

    def test_transfer_target_only_scope_requires_exact_targets(self) -> None:
        plan = parse_plan(Path(__file__).resolve().parents[2] / "PLAN.md")
        with self.assertRaisesRegex(ValueError, "requires a named phase, task, or target|requires exact"):
            validate_decision_scope(
                plan,
                "G7",
                {
                    "action": "authorize_transfer",
                    "phase_ids": (),
                    "task_ids": (),
                    "targets": (),
                },
            )
        validate_decision_scope(
            plan,
            "G7",
            {
                "action": "authorize_transfer",
                "phase_ids": (),
                "task_ids": (),
                "targets": ("04_outputs/confirmation/request.json",),
            },
        )


if __name__ == "__main__":
    unittest.main()
