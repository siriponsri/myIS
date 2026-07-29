import hashlib
import shutil
import subprocess
import tempfile
from pathlib import Path
import unittest

from fastapi.testclient import TestClient

from myis_research.dashboard.app import create_app


REPO_ROOT = Path(__file__).resolve().parents[2]
CONTENT_FILES = (
    "PLAN.md",
    "FULL_RESEARCH_TRACK_PLAN.md",
    "LOCAL_RESEARCH_HARNESS_BUILD_PLAN.md",
    "AGENTS.md",
    "00_governance/OWNER_GATES.md",
    "00_governance/OPERATIONS.md",
    "00_governance/TOOLCHAIN.md",
    "00_governance/TOOL_BOOTSTRAP_STATUS.md",
    "00_governance/config/tools.lock.yaml",
    "00_governance/config/project.yaml",
    "00_governance/config/linear.yaml",
    "00_governance/config/evidence_catalog.yaml",
    "00_governance/config/dashboard_topics.yaml",
    "03_experiments/config/mlflow/governance_documents.yaml",
    "04_outputs/artifacts/f0-migration/F0-f32ac040efb5.json",
    "04_outputs/artifacts/f0-migration/F0-f5e00c80d990.json",
    "06_frontend/dashboard/content_registry.yaml",
    "06_frontend/dashboard/index.html",
    "06_frontend/dashboard/assets/tokens.css",
    "06_frontend/dashboard/assets/dashboard.css",
    "06_frontend/dashboard/assets/dashboard.js",
    "06_frontend/dashboard/diagrams/research-program.svg",
    "06_frontend/dashboard/diagrams/candidate-exposure.svg",
    "06_frontend/dashboard/diagrams/owner-gate.svg",
    "06_frontend/dashboard/diagrams/confirmation-boundary.svg",
    "06_frontend/dashboard/diagrams/harness-kernel.svg",
    "06_frontend/dashboard/diagrams/run-lifecycle.svg",
    "06_frontend/dashboard/diagrams/decision-ledger.svg",
    "06_frontend/dashboard/diagrams/mlflow-mirror.svg",
)


def make_fixture(root: Path, *, git_repository: bool = False) -> None:
    for relative in CONTENT_FILES:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / relative, target)
    (root / "00_governance/approvals").mkdir(parents=True, exist_ok=True)
    (root / ".gitignore").write_text("01_evidence/private/\n", encoding="utf-8")
    if git_repository:
        subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.invalid"],
            cwd=root,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Dashboard Test"], cwd=root, check=True
        )
        subprocess.run(["git", "add", "."], cwd=root, check=True)
        subprocess.run(
            ["git", "commit", "-m", "dashboard fixture"],
            cwd=root,
            check=True,
            capture_output=True,
        )


def session_client(root: Path) -> tuple[TestClient, str]:
    app = create_app(
        repository_root=root,
        port=8765,
        actor_sid_override="S-1-5-21-dashboard-test",
        test_mode=True,
    )
    client = TestClient(app, base_url="http://127.0.0.1:8765")
    csrf = client.get("/api/v1/session").json()["csrf_token"]
    return client, csrf


class DashboardFrontendTests(unittest.TestCase):
    def test_root_and_exact_static_assets_are_local_and_no_store(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_fixture(root)
            client, _ = session_client(root)

            index = client.get("/")
            self.assertEqual(index.status_code, 200)
            self.assertIn("myIS Owner Workbench", index.text)
            self.assertIn('<html lang="en">', index.text)
            self.assertIn("Connecting / กำลังเชื่อมต่อ", index.text)
            self.assertIn('id="flow-progress"', index.text)
            self.assertIn('data-plan-density="readable"', index.text)
            self.assertIn('data-plan-density="compact"', index.text)
            self.assertIn('id="overview-readiness"', index.text)
            self.assertIn('data-view="presentation"', index.text)
            self.assertIn('id="presentation-content"', index.text)
            self.assertEqual(index.headers["cache-control"], "no-store, max-age=0")
            self.assertEqual(client.get("/assets/dashboard.css").status_code, 200)
            self.assertEqual(client.get("/assets/tokens.css").status_code, 200)
            script = client.get("/assets/dashboard.js")
            self.assertEqual(script.status_code, 200)
            self.assertIn("AUTO_REFRESH_MS = 60000", script.text)
            self.assertIn("Completion requires canonical Task evidence", script.text)
            self.assertIn("item.title_en", script.text)
            self.assertIn("item.title_th", script.text)
            self.assertIn("renderReadiness", script.text)
            self.assertIn("renderPresentation", script.text)
            self.assertIn("bindFlowPan", script.text)
            self.assertIn("flow-toolbar", script.text)
            self.assertIn("aria-label\": \"Zoom in\"", script.text)
            self.assertIn("min-width: 960px", client.get("/assets/dashboard.css").text)
            self.assertEqual(client.get("/assets/unknown.js").status_code, 404)

    def test_response_policy_applies_to_html_static_json_and_svg(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_fixture(root)
            client, _ = session_client(root)
            detail = client.get("/api/v1/flows/research-program").json()
            responses = (
                client.get("/"),
                client.get("/assets/dashboard.css"),
                client.get("/assets/dashboard.js"),
                client.get("/api/v1/tools"),
                client.get(detail["image_url"]),
            )
            for response in responses:
                with self.subTest(content_type=response.headers.get("content-type")):
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.headers["cache-control"], "no-store, max-age=0")
                    self.assertEqual(response.headers["x-content-type-options"], "nosniff")
                    self.assertNotIn("access-control-allow-origin", response.headers)

    def test_projections_require_session_and_expose_no_filesystem_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_fixture(root)
            app = create_app(
                repository_root=root,
                port=8765,
                actor_sid_override="S-1-5-21-dashboard-test",
                test_mode=True,
            )
            client = TestClient(app, base_url="http://127.0.0.1:8765")
            self.assertEqual(client.get("/api/v1/content/process").status_code, 401)
            client.get("/api/v1/session")

            process = client.get("/api/v1/content/process")
            harness = client.get("/api/v1/content/harness")
            tools = client.get("/api/v1/tools")
            flows = client.get("/api/v1/flows")
            governance = client.get("/api/v1/governance-catalog")
            self.assertEqual(process.status_code, 200)
            self.assertEqual(harness.status_code, 200)
            self.assertEqual(tools.status_code, 200)
            self.assertEqual(flows.status_code, 200)
            self.assertEqual(governance.status_code, 200)
            combined = process.text + harness.text + tools.text + flows.text + governance.text
            self.assertNotIn(str(root), combined)
            self.assertNotIn('"path"', combined)
            tool_documents = tools.json()["documents"]
            self.assertEqual(
                [item["source_id"] for item in tool_documents],
                ["toolchain", "tool-bootstrap"],
            )

            flow = client.get("/api/v1/flows/research-program")
            image = client.get(flow.json()["image_url"])
            self.assertEqual(image.status_code, 200)
            self.assertTrue(image.headers["content-type"].startswith("image/svg+xml"))
            self.assertEqual(image.headers["cache-control"], "no-store, max-age=0")
            self.assertEqual(
                client.get(f"/api/v1/flows/not-allowlisted/image?sha256={'0' * 64}").status_code,
                404,
            )

    def test_all_current_flow_diagrams_are_structurally_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_fixture(root)
            client, _ = session_client(root)
            catalog = client.get("/api/v1/flows").json()["flows"]
            self.assertEqual(len(catalog), 8)
            for flow in catalog:
                with self.subTest(flow_id=flow["flow_id"]):
                    detail = client.get(flow["detail_url"])
                    self.assertEqual(detail.status_code, 200, detail.text)
                    image = client.get(detail.json()["image_url"])
                    self.assertEqual(image.status_code, 200, image.text)

    def test_flow_svg_rejects_external_references_scripts_and_css(self) -> None:
        malicious = (
            '<svg xmlns="http://www.w3.org/2000/svg"><a href=https://evil.invalid/x /></svg>',
            '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"><a xlink:href="javascript:alert(1)" /></svg>',
            '<svg xmlns="http://www.w3.org/2000/svg"><style>@import url(https://evil.invalid/x.css)</style></svg>',
            '<svg xmlns="http://www.w3.org/2000/svg"><script>1</script></svg>',
        )
        for payload in malicious:
            with self.subTest(payload=payload):
                with tempfile.TemporaryDirectory() as temp:
                    root = Path(temp)
                    make_fixture(root)
                    diagram = root / "06_frontend/dashboard/diagrams/research-program.svg"
                    diagram.write_text(payload, encoding="utf-8")
                    client, _ = session_client(root)
                    response = client.get("/api/v1/flows/research-program")
                    self.assertEqual(response.status_code, 409)

    def test_flow_image_is_hash_bound_and_serves_exact_validated_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_fixture(root)
            client, _ = session_client(root)
            detail = client.get("/api/v1/flows/research-program").json()
            diagram = root / "06_frontend/dashboard/diagrams/research-program.svg"
            replacement = b'<svg xmlns="http://www.w3.org/2000/svg"><text>changed</text></svg>\n'
            diagram.write_bytes(replacement)
            self.assertEqual(client.get(detail["image_url"]).status_code, 409)

            refreshed = client.get("/api/v1/flows/research-program").json()
            image = client.get(refreshed["image_url"])
            self.assertEqual(image.content, replacement)
            self.assertEqual(image.headers["x-content-sha256"], refreshed["sha256"])

    def test_registry_drift_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_fixture(root)
            registry = root / "06_frontend/dashboard/content_registry.yaml"
            registry.write_text(
                registry.read_text(encoding="utf-8").replace(
                    "PLAN.md", "../protected/confirmation-qrels.json", 1
                ),
                encoding="utf-8",
            )
            client, _ = session_client(root)
            response = client.get("/api/v1/content/process")
            self.assertEqual(response.status_code, 409)
            self.assertIn("registry drifted", response.json()["detail"])

    def test_missing_registry_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_fixture(root)
            (root / "06_frontend/dashboard/content_registry.yaml").unlink()
            client, _ = session_client(root)
            response = client.get("/api/v1/content/process")
            self.assertEqual(response.status_code, 409)
            self.assertIn("registry is missing", response.json()["detail"])

    def test_allowlisted_sources_reject_in_repo_symlinks(self) -> None:
        cases = (
            "PLAN.md",
            "06_frontend/dashboard/diagrams/research-program.svg",
            "00_governance/config/tools.lock.yaml",
        )
        for relative in cases:
            with self.subTest(relative=relative):
                with tempfile.TemporaryDirectory() as temp:
                    root = Path(temp)
                    make_fixture(root)
                    secret = root / "protected-confirmation-canary.txt"
                    secret.write_text("PROTECTED-CANARY", encoding="utf-8")
                    source = root / relative
                    source.unlink()
                    try:
                        source.symlink_to(secret)
                    except OSError as error:
                        self.skipTest(f"symlink creation is unavailable: {error}")
                    client, _ = session_client(root)
                    endpoint = (
                        "/api/v1/content/process"
                        if relative == "PLAN.md"
                        else "/api/v1/flows/research-program"
                        if relative.endswith(".svg")
                        else "/api/v1/tools"
                    )
                    response = client.get(endpoint)
                    self.assertEqual(response.status_code, 409)
                    self.assertNotIn("PROTECTED-CANARY", response.text)

    def test_owner_gate_preview_computes_scope_hash_and_actor_server_side(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_fixture(root, git_repository=True)
            client, csrf = session_client(root)
            scope = {
                "action": "approve_implementation",
                "phase_ids": ["F0"],
                "task_ids": ["F0.1"],
                "targets": [],
            }
            response = client.post(
                "/api/v1/owner-gates/preview",
                headers={
                    "origin": "http://127.0.0.1:8765",
                    "x-csrf-token": csrf,
                },
                json={
                    "gate_id": "G0",
                    "status": "approved",
                    "rationale": "Approve the exact fixture implementation scope.",
                    "evidence_manifest_hashes": [
                        hashlib.sha256(
                            (root / "04_outputs/artifacts/f0-migration/F0-f5e00c80d990.json").read_bytes()
                        ).hexdigest()
                    ],
                    "scope": scope,
                },
            )
            self.assertEqual(response.status_code, 200, response.text)
            record = response.json()["record"]
            expected = hashlib.sha256(
                b'{"action":"approve_implementation","phase_ids":["F0"],"targets":[],"task_ids":["F0.1"]}'
            ).hexdigest()
            self.assertEqual(record["scope_hash"], expected)
            self.assertEqual(len(record["actor"]), 64)
            self.assertNotIn("actor", scope)

    def test_owner_gate_approval_requires_verified_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_fixture(root, git_repository=True)
            client, csrf = session_client(root)
            response = client.post(
                "/api/v1/owner-gates/preview",
                headers={"origin": "http://127.0.0.1:8765", "x-csrf-token": csrf},
                json={
                    "gate_id": "G0",
                    "status": "approved",
                    "rationale": "Evidence is intentionally missing.",
                    "evidence_manifest_hashes": [],
                    "scope": {
                        "action": "approve_implementation",
                        "phase_ids": ["F0"],
                        "task_ids": ["F0.1"],
                        "targets": [],
                    },
                },
            )
            self.assertEqual(response.status_code, 422)
            self.assertIn("evidence", response.text)

    def test_owner_gates_endpoint_fails_closed_for_invalid_record(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_fixture(root)
            (root / "00_governance/approvals/bad.json").write_text(
                '{"decision_id":"bad","prior_record_hash":null}', encoding="utf-8"
            )
            client, _ = session_client(root)
            response = client.get("/api/v1/owner-gates")
            self.assertEqual(response.status_code, 409)
            self.assertIn("invalid Owner Gate record", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
