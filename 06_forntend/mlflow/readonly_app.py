"""Fail-closed read-only WSGI boundary for the local MLflow mirror.

This application intentionally exposes only the small MLflow surface required
to browse experiments, runs, metrics, and allowlisted artifacts. Git and the
validated repository artifacts remain canonical.
"""

from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import os
import re
import socket
import sqlite3
import stat
import sys
from pathlib import Path
from typing import Callable, Iterable, Mapping, Sequence
from urllib.parse import unquote, urlparse


MLFLOW_VERSION = "3.14.0"
MLFLOW_ROUTE_MAP_SHA256 = "4deb3ebd20d1ee769c6d5c5541b04c637288fc8cbb2da1f8100aa2edbca85f16"
DEFAULT_PORT = 5000

_ALLOWED_ENDPOINT_METHODS: Mapping[str, frozenset[str]] = {
    "static": frozenset({"GET", "HEAD"}),
    "serve_static_file": frozenset({"GET", "HEAD"}),
    "serve": frozenset({"GET", "HEAD"}),
    "health": frozenset({"GET", "HEAD"}),
    "version": frozenset({"GET", "HEAD"}),
    "_get_experiment_by_name": frozenset({"GET", "HEAD"}),
    "_search_experiments": frozenset({"GET", "HEAD", "POST"}),
    "_get_experiment": frozenset({"GET", "HEAD"}),
    "_get_run": frozenset({"GET", "HEAD"}),
    "_search_runs": frozenset({"POST"}),
    "_list_artifacts": frozenset({"GET", "HEAD"}),
    "_get_metric_history": frozenset({"GET", "HEAD"}),
    "get_metric_history_bulk_interval_handler": frozenset({"GET", "HEAD"}),
    "serve_get_metric_history_bulk": frozenset({"GET", "HEAD"}),
    "serve_get_metric_history_bulk_interval": frozenset({"GET", "HEAD"}),
    "_download_artifact": frozenset({"GET", "HEAD"}),
    "_list_artifacts_mlflow_artifacts": frozenset({"GET", "HEAD"}),
    "_get_presigned_download_url": frozenset({"GET", "HEAD"}),
    "serve_artifacts": frozenset({"GET", "HEAD"}),
    "_get_server_info": frozenset({"GET", "HEAD"}),
    "serve_search_datasets": frozenset({"POST"}),
    "serve_get_ui_telemetry": frozenset({"GET", "HEAD"}),
}
_ARTIFACT_ENDPOINTS = frozenset(
    {
        "_list_artifacts",
        "_download_artifact",
        "_list_artifacts_mlflow_artifacts",
        "_get_presigned_download_url",
        "serve_artifacts",
    }
)
_ARTIFACT_LIST_ENDPOINTS = frozenset({"_list_artifacts", "_list_artifacts_mlflow_artifacts"})
_SYNTHETIC_UI_READS: Mapping[str, object] = {
    "/ajax-api/2.0/mlflow/users/current": {},
    "/ajax-api/3.0/mlflow/assistant/config": {"enabled": False},
}
_PROTECTED_ARTIFACT_RE = re.compile(
    r"(?:^|[._/\\-])(qrels?|confirmation|heldout|held-out|membership|per[_-]?query|"
    r"credentials?|secrets?|provider[_-]?payload)(?:[._/\\-]|$)",
    re.IGNORECASE,
)


class ViewerConfigurationError(RuntimeError):
    """Raised when the viewer cannot establish a read-only local boundary."""


def readonly_sqlite_uri(database: Path) -> str:
    """Return the required SQLAlchemy SQLite URI with immutable read semantics."""

    path = database.resolve(strict=True).as_posix()
    return f"sqlite+pysqlite:///file:{path}?mode=ro&uri=true"


def default_store(repository_root: Path) -> Path:
    """Resolve the numbered shared store from the canonical Research layout."""

    root = repository_root.resolve(strict=True)
    if root.name != "01_Research" or len(root.parents) < 3:
        raise ViewerConfigurationError(
            "cannot resolve the shared MLflow store; set MYIS_MLFLOW_STORE"
        )
    return root.parents[2] / "01_Stores" / "00_myIS" / "mlflow"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _is_link_or_reparse(path: Path) -> bool:
    if path.is_symlink():
        return True
    try:
        attributes = path.stat(follow_symlinks=False).st_file_attributes
    except (AttributeError, OSError):
        return False
    return bool(attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(root.resolve(strict=True))
    except (OSError, ValueError):
        return False
    return True


def validate_bootstrap_target(store_root: Path, repository_root: Path) -> Path:
    """Validate a not-yet-created store target without creating it."""

    if not store_root.is_absolute():
        raise ViewerConfigurationError("MYIS_MLFLOW_STORE must be an absolute path")
    repository = repository_root.resolve(strict=True)
    target = store_root.resolve(strict=False)
    if _inside(target, repository):
        raise ViewerConfigurationError("MLflow store must remain outside the Git repository")
    for ancestor in (target, *target.parents):
        if ancestor.exists() and _is_link_or_reparse(ancestor):
            raise ViewerConfigurationError("MLflow store path must not cross a reparse point")
        git_marker = ancestor / ".git"
        if git_marker.is_file() or (git_marker.is_dir() and (git_marker / "HEAD").is_file()):
            raise ViewerConfigurationError("MLflow store must remain outside every Git worktree")
    existing = target
    while not existing.exists() and existing != existing.parent:
        existing = existing.parent
    if not existing.exists() or _is_link_or_reparse(existing):
        raise ViewerConfigurationError("MLflow store parent is missing or uses a reparse point")
    return target


def _artifact_location_path(value: str) -> Path:
    parsed = urlparse(value)
    if parsed.scheme.lower() != "file" or parsed.netloc not in {"", "localhost"}:
        raise ViewerConfigurationError("MLflow artifact locations must use local file URIs")
    raw = unquote(parsed.path)
    if re.fullmatch(r"/[A-Za-z]:/.*", raw):
        raw = raw[1:]
    return Path(raw)


def _validate_database_artifact_locations(database: Path, artifacts: Path) -> None:
    connection = sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True)
    try:
        rows: list[tuple[str]] = []
        for table, column in (("experiments", "artifact_location"), ("runs", "artifact_uri")):
            exists = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
            ).fetchone()
            if exists:
                rows.extend(connection.execute(f"SELECT {column} FROM {table} WHERE {column} IS NOT NULL"))
        for (value,) in rows:
            if not _inside(_artifact_location_path(str(value)), artifacts):
                raise ViewerConfigurationError("MLflow database references artifacts outside the approved root")
    finally:
        connection.close()


def validate_store(store_root: Path, repository_root: Path) -> dict[str, str]:
    """Validate the persistent mirror layout and return its resolved paths."""

    root = validate_bootstrap_target(store_root, repository_root)
    if not root.is_dir() or _is_link_or_reparse(root):
        raise ViewerConfigurationError("MLflow store root is missing or unsafe")
    database = root / "database" / "mlflow.db"
    artifacts = root / "artifacts"
    report = root / "mlflow-bootstrap.json"
    for path in (database, artifacts, report):
        if not path.exists() or _is_link_or_reparse(path):
            raise ViewerConfigurationError(f"required MLflow store path is missing or unsafe: {path.name}")
        if not _inside(path, root):
            raise ViewerConfigurationError("MLflow store path escapes the approved root")
    if not database.is_file() or database.read_bytes()[:16] != b"SQLite format 3\x00":
        raise ViewerConfigurationError("MLflow database is not a valid SQLite file")
    if not artifacts.is_dir() or not report.is_file():
        raise ViewerConfigurationError("MLflow artifacts/report layout is invalid")
    for path in artifacts.rglob("*"):
        if _is_link_or_reparse(path) or not _inside(path, artifacts):
            raise ViewerConfigurationError("MLflow artifact tree contains an unsafe link")

    try:
        bootstrap = json.loads(report.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ViewerConfigurationError("MLflow bootstrap report is invalid") from exc
    expected = {
        "schema_version": "myis.mlflow-bootstrap-report.v2",
        "status": "PASS",
        "stage": "bootstrap",
        "scientific_run": False,
    }
    if any(bootstrap.get(key) != value for key, value in expected.items()):
        raise ViewerConfigurationError("MLflow bootstrap report did not pass the governed bootstrap")
    try:
        reported_root = Path(str(bootstrap["store_root"])).resolve(strict=True)
    except (KeyError, OSError) as exc:
        raise ViewerConfigurationError("MLflow bootstrap report has no valid store root") from exc
    if reported_root != root:
        raise ViewerConfigurationError("MLflow bootstrap report points to a different store")

    _validate_database_artifact_locations(database, artifacts)
    return {
        "store_root": str(root),
        "database": str(database),
        "artifacts": str(artifacts),
        "database_sha256": _sha256(database),
    }


def route_map_sha256(url_map: object) -> str:
    rows = sorted(
        (
            rule.rule,
            rule.endpoint,
            sorted(method for method in rule.methods if method not in {"HEAD", "OPTIONS"}),
        )
        for rule in url_map.iter_rules()
    )
    payload = json.dumps(rows, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_mlflow_contract(app: object) -> None:
    import mlflow

    if mlflow.__version__ != MLFLOW_VERSION:
        raise ViewerConfigurationError(
            f"MLflow version drift: expected {MLFLOW_VERSION}, found {mlflow.__version__}"
        )
    actual = route_map_sha256(app.url_map)
    if actual != MLFLOW_ROUTE_MAP_SHA256:
        raise ViewerConfigurationError(
            f"MLflow route-map drift: expected {MLFLOW_ROUTE_MAP_SHA256}, found {actual}"
        )
    endpoints = {rule.endpoint for rule in app.url_map.iter_rules()}
    missing = sorted(set(_ALLOWED_ENDPOINT_METHODS).difference(endpoints))
    if missing:
        raise ViewerConfigurationError(f"required read endpoints are missing: {missing}")


def _forbidden_artifact_reference(path: str, query: str) -> bool:
    return bool(_PROTECTED_ARTIFACT_RE.search(unquote(f"{path}?{query}")))


def _filter_artifact_listing(value: object) -> object:
    if not isinstance(value, dict) or not isinstance(value.get("files"), list):
        return value
    filtered = []
    for item in value["files"]:
        if isinstance(item, dict) and _PROTECTED_ARTIFACT_RE.search(str(item.get("path", ""))):
            continue
        filtered.append(item)
    return {**value, "files": filtered}


def _response(
    start_response: Callable[..., object],
    status: str,
    code: str,
    message: str,
) -> list[bytes]:
    body = json.dumps({"error": code, "message": message}, ensure_ascii=True).encode("utf-8")
    headers = [
        ("Content-Type", "application/json"),
        ("Content-Length", str(len(body))),
        ("Cache-Control", "no-store"),
        ("Pragma", "no-cache"),
        ("X-Frame-Options", "DENY"),
        ("X-Content-Type-Options", "nosniff"),
        ("Referrer-Policy", "no-referrer"),
    ]
    start_response(status, headers)
    return [body]


def _json_response(
    start_response: Callable[..., object], payload: object, *, head_only: bool = False
) -> list[bytes]:
    body = json.dumps(payload, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    headers = _secure_headers(
        [("Content-Type", "application/json")], content_length=len(body)
    )
    start_response("200 OK", headers)
    return [] if head_only else [body]


def _secure_headers(headers: Sequence[tuple[str, str]], content_length: int | None = None) -> list[tuple[str, str]]:
    rejected = {
        "access-control-allow-origin",
        "access-control-allow-credentials",
        "access-control-allow-methods",
        "access-control-allow-headers",
        "cache-control",
        "pragma",
        "expires",
        "x-frame-options",
        "content-length" if content_length is not None else "",
    }
    result = [(key, value) for key, value in headers if key.lower() not in rejected]
    if content_length is not None:
        result.append(("Content-Length", str(content_length)))
    result.extend(
        [
            ("Cache-Control", "no-store"),
            ("Pragma", "no-cache"),
            ("Expires", "0"),
            ("X-Frame-Options", "DENY"),
            ("X-Content-Type-Options", "nosniff"),
            ("Referrer-Policy", "no-referrer"),
            ("Content-Security-Policy", "frame-ancestors 'none'; object-src 'none'"),
        ]
    )
    return result


class ReadOnlyMLflowApp:
    """WSGI middleware that resolves and authorizes every MLflow route."""

    def __init__(self, inner_app: Callable[..., Iterable[bytes]], route_map: object, *, port: int):
        self.inner_app = inner_app
        self.route_map = route_map
        self.port = port
        self.allowed_hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}

    def __call__(self, environ: dict[str, object], start_response: Callable[..., object]) -> Iterable[bytes]:
        remote = str(environ.get("REMOTE_ADDR", ""))
        if remote not in {"127.0.0.1", "::1"}:
            return _response(start_response, "403 Forbidden", "remote_access_denied", "loopback access only")
        host = str(environ.get("HTTP_HOST", ""))
        if host.lower() not in self.allowed_hosts:
            return _response(start_response, "400 Bad Request", "invalid_host", "Host is not allowlisted")
        origin = str(environ.get("HTTP_ORIGIN", ""))
        if origin and origin.lower() not in {f"http://{item}" for item in self.allowed_hosts}:
            return _response(start_response, "403 Forbidden", "invalid_origin", "Origin is not same-origin")

        method = str(environ.get("REQUEST_METHOD", "GET")).upper()
        path = str(environ.get("PATH_INFO", ""))
        if path in _SYNTHETIC_UI_READS:
            if method not in {"GET", "HEAD"}:
                return _response(
                    start_response, "403 Forbidden", "route_blocked", "route is not read-allowlisted"
                )
            return _json_response(
                start_response, _SYNTHETIC_UI_READS[path], head_only=method == "HEAD"
            )
        try:
            adapter = self.route_map.bind_to_environ(environ)
            endpoint, _ = adapter.match(method=method)
        except Exception:
            return _response(start_response, "403 Forbidden", "route_blocked", "route is not read-allowlisted")
        if method not in _ALLOWED_ENDPOINT_METHODS.get(endpoint, frozenset()):
            return _response(start_response, "403 Forbidden", "route_blocked", "route is not read-allowlisted")

        query = str(environ.get("QUERY_STRING", ""))
        if endpoint in _ARTIFACT_ENDPOINTS and _forbidden_artifact_reference(path, query):
            return _response(start_response, "404 Not Found", "artifact_not_available", "artifact is not exposed")

        if endpoint in _ARTIFACT_LIST_ENDPOINTS:
            return self._filtered_listing(environ, start_response)

        def secured_start(status: str, headers: list[tuple[str, str]], exc_info: object = None) -> object:
            return start_response(status, _secure_headers(headers), exc_info)

        return self.inner_app(environ, secured_start)

    def _filtered_listing(
        self, environ: dict[str, object], start_response: Callable[..., object]
    ) -> Iterable[bytes]:
        captured: dict[str, object] = {}

        def capture(status: str, headers: list[tuple[str, str]], exc_info: object = None) -> Callable[[bytes], object]:
            captured["status"] = status
            captured["headers"] = headers
            captured["exc_info"] = exc_info
            return lambda _chunk: None

        body = b"".join(self.inner_app(environ, capture))
        try:
            payload = json.loads(body)
            body = json.dumps(_filter_artifact_listing(payload), ensure_ascii=True, separators=(",", ":")).encode(
                "utf-8"
            )
        except (UnicodeDecodeError, json.JSONDecodeError):
            return _response(start_response, "502 Bad Gateway", "invalid_upstream", "artifact listing was not JSON")
        start_response(
            str(captured.get("status", "200 OK")),
            _secure_headers(captured.get("headers", []), len(body)),
            captured.get("exc_info"),
        )
        return [body]


def create_application(store_root: Path, repository_root: Path, *, port: int) -> ReadOnlyMLflowApp:
    state = validate_store(store_root, repository_root)
    database = Path(state["database"])
    artifacts = Path(state["artifacts"])
    database_hash = state["database_sha256"]
    backend_uri = readonly_sqlite_uri(database)

    os.environ["MLFLOW_BACKEND_STORE_URI"] = backend_uri
    os.environ["MLFLOW_REGISTRY_STORE_URI"] = backend_uri
    os.environ["MLFLOW_DEFAULT_ARTIFACT_ROOT"] = artifacts.as_uri()
    os.environ["MLFLOW_SERVER_ENABLE_JOB_EXECUTION"] = "false"
    os.environ["MLFLOW_ENABLE_WORKSPACES"] = "false"

    import mlflow.server
    from mlflow.server import handlers

    validate_mlflow_contract(mlflow.server.app)
    handlers.initialize_backend_stores(
        backend_store_uri=backend_uri,
        registry_store_uri=backend_uri,
        default_artifact_root=artifacts.as_uri(),
    )
    if _sha256(database) != database_hash:
        raise ViewerConfigurationError("MLflow backend initialization changed the canonical database")
    return ReadOnlyMLflowApp(mlflow.server.app, mlflow.server.app.url_map, port=port)


def _port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(0.35)
        return probe.connect_ex(("127.0.0.1", port)) == 0


def _viewer_status(port: int) -> str:
    if not _port_open(port):
        return "stopped"
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=1.0)
    try:
        connection.request("GET", "/health", headers={"Host": f"127.0.0.1:{port}"})
        health = connection.getresponse()
        health_body = health.read()
        health_cache = health.getheader("Cache-Control")
        connection.request("GET", "/version", headers={"Host": f"127.0.0.1:{port}"})
        version = connection.getresponse()
        version_body = version.read().decode("utf-8")
        if (
            health.status == 200
            and health_body == b"OK"
            and health_cache == "no-store"
            and version.status == 200
            and version_body == MLFLOW_VERSION
        ):
            return "running"
    except OSError:
        pass
    finally:
        connection.close()
    return "occupied"


def _port(value: str) -> int:
    try:
        port = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("port must be an integer") from exc
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("port must be between 1 and 65535")
    return port


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only local MLflow viewer")
    parser.add_argument("command", choices=("target", "doctor", "serve", "status", "url"))
    parser.add_argument("--store-root", type=Path)
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--port", type=_port, default=DEFAULT_PORT)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        configured_store = os.environ.get("MYIS_MLFLOW_STORE")
        store_root = args.store_root or (
            Path(configured_store) if configured_store else default_store(args.repository_root)
        )
        if args.command == "url":
            print(f"http://127.0.0.1:{args.port}")
            return 0
        if args.command == "status":
            print(json.dumps({"status": _viewer_status(args.port), "url": f"http://127.0.0.1:{args.port}"}))
            return 0
        if args.command == "target":
            target = validate_bootstrap_target(store_root, args.repository_root)
            print(json.dumps({"status": "PASS", "store_root": str(target)}, ensure_ascii=True))
            return 0
        if sys.version_info[:2] != (3, 11):
            raise ViewerConfigurationError(f"Python 3.11 is required; found {sys.version.split()[0]}")
        application = create_application(store_root, args.repository_root, port=args.port)
        if args.command == "doctor":
            print(
                json.dumps(
                    {
                        "status": "PASS",
                        "mlflow_version": MLFLOW_VERSION,
                        "route_map_sha256": MLFLOW_ROUTE_MAP_SHA256,
                        "store_root": str(store_root.resolve()),
                        "database_uri": readonly_sqlite_uri(store_root / "database" / "mlflow.db"),
                        "url": f"http://127.0.0.1:{args.port}",
                    },
                    ensure_ascii=True,
                )
            )
            return 0
        if _port_open(args.port):
            raise ViewerConfigurationError(f"port {args.port} is already in use")
        try:
            from waitress import serve
        except ImportError as exc:
            raise ViewerConfigurationError("waitress is missing; replay the locked tracking environment") from exc
        print(f"Read-only MLflow viewer: http://127.0.0.1:{args.port}", flush=True)
        serve(application, host="127.0.0.1", port=args.port, threads=1, ident="myis-mlflow-readonly")
        return 0
    except ViewerConfigurationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
