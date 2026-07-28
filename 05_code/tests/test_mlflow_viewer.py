import hashlib
import importlib.util
import io
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from urllib.parse import quote

import mlflow.server


REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "06_forntend" / "mlflow" / "readonly_app.py"
SPEC = importlib.util.spec_from_file_location("myis_readonly_mlflow", MODULE_PATH)
assert SPEC and SPEC.loader
viewer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(viewer)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_store(root: Path, repository: Path) -> Path:
    store = root / "store"
    artifacts = store / "artifacts"
    database = store / "database" / "mlflow.db"
    artifacts.mkdir(parents=True)
    database.parent.mkdir(parents=True)
    safe_artifact = artifacts / "run" / "artifacts" / "metrics.json"
    safe_artifact.parent.mkdir(parents=True)
    safe_artifact.write_text('{"score": 0.1}\n', encoding="utf-8")
    connection = sqlite3.connect(database)
    try:
        connection.execute("CREATE TABLE experiments (experiment_id INTEGER, artifact_location TEXT)")
        connection.execute("CREATE TABLE runs (run_uuid TEXT, artifact_uri TEXT)")
        location = artifacts.as_uri()
        connection.execute("INSERT INTO experiments VALUES (?, ?)", (1, location))
        connection.execute("INSERT INTO runs VALUES (?, ?)", ("run", f"{location}/run/artifacts"))
        connection.commit()
    finally:
        connection.close()
    (store / "mlflow-bootstrap.json").write_text(
        json.dumps(
            {
                "schema_version": "myis.mlflow-bootstrap-report.v2",
                "status": "PASS",
                "stage": "bootstrap",
                "scientific_run": False,
                "store_root": str(store.resolve()),
            }
        ),
        encoding="utf-8",
    )
    return store


class FakeApp:
    def __init__(self, body=b'{"ok":true}', content_type="application/json"):
        self.body = body
        self.content_type = content_type
        self.calls = 0

    def __call__(self, _environ, start_response):
        self.calls += 1
        start_response(
            "200 OK",
            [
                ("Content-Type", self.content_type),
                ("Content-Length", str(len(self.body))),
                ("Cache-Control", "public, max-age=60"),
                ("Access-Control-Allow-Origin", "*"),
            ],
        )
        return [self.body]


def request(app, method: str, path: str, *, query: str = "", host: str = "127.0.0.1:5000", origin=None):
    captured = {}

    def start_response(status, headers, _exc_info=None):
        captured["status"] = status
        captured["headers"] = dict(headers)

    environ = {
        "REQUEST_METHOD": method,
        "SCRIPT_NAME": "",
        "PATH_INFO": path,
        "QUERY_STRING": query,
        "SERVER_NAME": "127.0.0.1",
        "SERVER_PORT": "5000",
        "SERVER_PROTOCOL": "HTTP/1.1",
        "wsgi.url_scheme": "http",
        "wsgi.version": (1, 0),
        "wsgi.input": io.BytesIO(b"{}"),
        "wsgi.errors": io.StringIO(),
        "wsgi.multithread": False,
        "wsgi.multiprocess": False,
        "wsgi.run_once": False,
        "REMOTE_ADDR": "127.0.0.1",
        "HTTP_HOST": host,
        "CONTENT_TYPE": "application/json",
        "CONTENT_LENGTH": "2",
    }
    if origin is not None:
        environ["HTTP_ORIGIN"] = origin
    body = b"".join(app(environ, start_response))
    return captured["status"], captured["headers"], body


class MLflowViewerTests(unittest.TestCase):
    def test_pinned_mlflow_route_contract_and_readonly_uri(self) -> None:
        self.assertEqual(mlflow.server.VERSION, viewer.MLFLOW_VERSION)
        viewer.validate_mlflow_contract(mlflow.server.app)
        with tempfile.TemporaryDirectory() as temp:
            database = Path(temp) / "mlflow.db"
            sqlite3.connect(database).close()
            uri = viewer.readonly_sqlite_uri(database)
            self.assertTrue(uri.startswith("sqlite+pysqlite:///file:"))
            self.assertTrue(uri.endswith("?mode=ro&uri=true"))

    def test_store_validation_rejects_repository_store_and_external_artifact_uri(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repository = root / "repo"
            repository.mkdir()
            with self.assertRaises(viewer.ViewerConfigurationError):
                viewer.validate_bootstrap_target(repository / "mlflow", repository)

            store = make_store(root, repository)
            state = viewer.validate_store(store, repository)
            self.assertEqual(Path(state["store_root"]), store.resolve())
            database = store / "database" / "mlflow.db"
            connection = sqlite3.connect(database)
            try:
                connection.execute("UPDATE experiments SET artifact_location = 'file:///C:/outside'")
                connection.commit()
            finally:
                connection.close()
            with self.assertRaises(viewer.ViewerConfigurationError):
                viewer.validate_store(store, repository)

    def test_negative_writes_never_reach_mlflow_or_change_store_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repository = root / "repo"
            repository.mkdir()
            store = make_store(root, repository)
            database = store / "database" / "mlflow.db"
            artifact = store / "artifacts" / "run" / "artifacts" / "metrics.json"
            before = (sha256(database), sha256(artifact))
            inner = FakeApp()
            app = viewer.ReadOnlyMLflowApp(inner, mlflow.server.app.url_map, port=5000)
            blocked = [
                ("POST", "/api/2.0/mlflow/experiments/create"),
                ("POST", "/api/2.0/mlflow/runs/log-batch"),
                ("PUT", "/api/2.0/mlflow-artifacts/artifacts/file.json"),
                ("POST", "/ajax-api/3.0/mlflow/gateway/secrets/create"),
                ("POST", "/ajax-api/3.0/mlflow/prompt-optimization/jobs"),
                ("POST", "/graphql"),
                ("POST", "/unknown-write"),
            ]
            for method, path in blocked:
                with self.subTest(method=method, path=path):
                    status, headers, _ = request(app, method, path)
                    self.assertEqual(status, "403 Forbidden")
                    self.assertEqual(headers["Cache-Control"], "no-store")
            self.assertEqual(inner.calls, 0)
            self.assertEqual((sha256(database), sha256(artifact)), before)

    def test_read_search_is_allowed_with_security_headers(self) -> None:
        inner = FakeApp()
        app = viewer.ReadOnlyMLflowApp(inner, mlflow.server.app.url_map, port=5000)
        status, headers, body = request(app, "POST", "/api/2.0/mlflow/runs/search")
        self.assertEqual(status, "200 OK")
        self.assertEqual(body, b'{"ok":true}')
        self.assertEqual(inner.calls, 1)
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(headers["X-Frame-Options"], "DENY")
        self.assertNotIn("Access-Control-Allow-Origin", headers)

    def test_ui_bootstrap_reads_are_synthetic_and_never_expose_identity_or_provider_config(self) -> None:
        inner = FakeApp()
        app = viewer.ReadOnlyMLflowApp(inner, mlflow.server.app.url_map, port=5000)
        expected = {
            "/ajax-api/2.0/mlflow/users/current": {},
            "/ajax-api/3.0/mlflow/assistant/config": {"enabled": False},
        }
        for path, payload in expected.items():
            with self.subTest(path=path):
                status, headers, body = request(app, "GET", path)
                self.assertEqual(status, "200 OK")
                self.assertEqual(json.loads(body), payload)
                self.assertEqual(headers["Cache-Control"], "no-store")
                self.assertNotIn("Access-Control-Allow-Origin", headers)
        self.assertEqual(inner.calls, 0)

        status, _, _ = request(
            app, "POST", "/ajax-api/3.0/mlflow/assistant/config"
        )
        self.assertEqual(status, "403 Forbidden")
        self.assertEqual(inner.calls, 0)

    def test_remote_host_origin_and_protected_artifacts_fail_closed(self) -> None:
        inner = FakeApp()
        app = viewer.ReadOnlyMLflowApp(inner, mlflow.server.app.url_map, port=5000)
        status, _, _ = request(app, "GET", "/health", host="research.example:5000")
        self.assertEqual(status, "400 Bad Request")
        status, _, _ = request(app, "GET", "/health", origin="http://research.example:5000")
        self.assertEqual(status, "403 Forbidden")
        status, _, _ = request(
            app,
            "GET",
            "/get-artifact",
            query=f"path={quote('confirmation/per_query.json')}",
        )
        self.assertEqual(status, "404 Not Found")
        self.assertEqual(inner.calls, 0)

    def test_artifact_listing_hides_protected_names(self) -> None:
        inner = FakeApp(
            json.dumps(
                {
                    "files": [
                        {"path": "metrics.json"},
                        {"path": "per_query_metrics.jsonl"},
                        {"path": "confirmation/outcomes.json"},
                    ]
                }
            ).encode("utf-8")
        )
        app = viewer.ReadOnlyMLflowApp(inner, mlflow.server.app.url_map, port=5000)
        status, headers, body = request(app, "GET", "/api/2.0/mlflow/artifacts/list")
        self.assertEqual(status, "200 OK")
        self.assertEqual(json.loads(body), {"files": [{"path": "metrics.json"}]})
        self.assertEqual(headers["Content-Length"], str(len(body)))


if __name__ == "__main__":
    unittest.main()
