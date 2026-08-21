"""Stage a fresh A4 Selection-125 root from immutable remote retrieval assets.

This is an operational transport path.  It never copies prior requests,
workers, caches, receipts, or outputs.  The seed contributes only frozen
corpus/program/model bytes; the fresh root receives a new code bundle,
Selection query package, scope, inventory, and runtime binding.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shlex
import subprocess
from typing import Any

from myis_research.armindex.a4_asset_bundle import _asset_hashes
from myis_research.armindex.a4_remote_ranker import _profile_registry, _runtime_bindings, _scope
from myis_research.armindex.a4_selection_materializer import validate_selection_input_materialization
from myis_research.kernel.canonical import canonical_json, canonical_sha256, file_sha256


_ATTEMPT = re.compile(r"^a4-goal001-[0-9]{8}T[0-9]{6}Z-[a-z0-9]{4,24}$")
_ROOT = re.compile(r"^/opt/myis/a4-goal001-[0-9]{8}T[0-9]{6}Z-[a-z0-9]{4,24}$")


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"invalid JSON object: {path}")
    return value


def _write(path: Path, value: dict[str, Any]) -> None:
    if path.exists() or path.is_symlink():
        raise ValueError(f"write-once path already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(value) + "\n", encoding="utf-8")


def _run(args: list[str]) -> str:
    return subprocess.run(args, check=True, capture_output=True, text=True, timeout=180).stdout


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--attempt-id", required=True)
    parser.add_argument("--remote-root", required=True)
    parser.add_argument("--seed-root", required=True)
    parser.add_argument("--source-package", type=Path, required=True)
    parser.add_argument("--selection-input", type=Path, required=True)
    parser.add_argument("--profile-registry", type=Path, required=True)
    parser.add_argument("--code-bundle", type=Path, required=True)
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--key", type=Path, required=True)
    parser.add_argument("--known-hosts", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if not _ATTEMPT.fullmatch(args.attempt_id) or not _ROOT.fullmatch(args.remote_root) or not _ROOT.fullmatch(args.seed_root):
        raise ValueError("attempt/root identity is invalid")
    if not args.remote_root.endswith(args.attempt_id) or args.remote_root == args.seed_root:
        raise ValueError("fresh remote root is invalid")
    source = args.source_package.resolve(strict=True)
    source_assets = (source / "assets").resolve(strict=True)
    query_root = args.selection_input.resolve(strict=True)
    selection = validate_selection_input_materialization(query_root, expected_attempt_id=_load(query_root / "A4_SELECTION_INPUT_MATERIALIZATION_RECEIPT.json")["attempt_id"])
    query_file = (query_root / "protected" / "selection-125-queries.jsonl").resolve(strict=True)
    if query_file.is_symlink() or len([line for line in query_file.read_text(encoding="utf-8").splitlines() if line.strip()]) != 125:
        raise ValueError("Selection query package must contain exactly 125 rows")
    registry = _profile_registry(_load(args.profile_registry.resolve(strict=True)), attempt_id=args.attempt_id)
    code = args.code_bundle.resolve(strict=True)
    if code.is_symlink() or not code.is_file():
        raise ValueError("code bundle is unsafe")

    stage = args.output.resolve()
    if stage.exists() or stage.is_symlink():
        raise ValueError("stage receipt root already exists")
    scope_body = {
        "schema_version": "myis.armindex-a4-selection-scope.v1",
        "scope": "Selection-125",
        "population": "OUT",
        "query_count": 125,
        "parent_split_sha256": selection["parent_split_sha256"],
        "selection_input_receipt_sha256": selection["receipt_sha256"],
        "query_bundle_sha256": file_sha256(query_file),
        "selection_accesses": 0,
        "final_accesses": 0,
        "protected_payload_included": False,
    }
    scope = {**scope_body, "scope_sha256": canonical_sha256(scope_body)}
    _write(stage / "selection-scope.json", scope)
    # The remote root contains precisely these copied seed files plus these
    # two fresh query/scope files, so local hashes are a complete expected map.
    copied = {
        relative: digest
        for relative, digest in _asset_hashes(source_assets, exclude={"A4_RUNTIME_ASSETS.json", "hdev-scope.json", "queries.jsonl"}).items()
    }
    copied["queries.jsonl"] = file_sha256(query_file)
    copied["selection-scope.json"] = file_sha256(stage / "selection-scope.json")
    inventory_body = {
        "schema_version": "myis.armindex-a4-runtime-assets-inventory.v1",
        "attempt_id": args.attempt_id,
        "asset_sha256s": dict(sorted(copied.items())),
        "selection_scope_sha256": scope["scope_sha256"],
        "profile_registry_sha256": registry["registry_sha256"],
        "selection_input_receipt_sha256": selection["receipt_sha256"],
        "protected_payload_included": False,
    }
    inventory = {**inventory_body, "inventory_sha256": canonical_sha256(inventory_body)}
    _write(stage / "A4_RUNTIME_ASSETS.json", inventory)
    runtime_body = {
        "schema_version": "myis.armindex-a4-runtime-bindings.v1",
        "attempt_id": args.attempt_id,
        "predecessor_binding_sha256": registry["predecessor_binding_sha256"],
        "profile_registry_sha256": registry["registry_sha256"],
        "selection_scope_sha256": scope["scope_sha256"],
        "asset_inventory_sha256": inventory["inventory_sha256"],
        "winner_program_sha256s": _load(source / "A4_RUNTIME_BINDINGS.json")["winner_program_sha256s"],
        "primary_arm_scope": ["ARM-03", "ARM-04", "ARM-05"],
        "protected_payload_included": False,
    }
    runtime = {**runtime_body, "runtime_bindings_sha256": canonical_sha256(runtime_body)}
    _write(stage / "A4_RUNTIME_BINDINGS.json", runtime)
    _write(stage / "profile-registry.json", registry)

    known_hosts = args.known_hosts.resolve(strict=True)
    key = args.key.resolve(strict=True)
    known_hosts_option = f'UserKnownHostsFile="{known_hosts}"'
    ssh = ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", known_hosts_option, "-o", "ServerAliveInterval=30", "-o", "ServerAliveCountMax=6", "-i", str(key), "-p", str(args.port), f"root@{args.host}"]
    scp = ["scp", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", known_hosts_option, "-o", "ServerAliveInterval=30", "-o", "ServerAliveCountMax=6", "-i", str(key), "-P", str(args.port)]
    remote = f"root@{args.host}"
    root, seed = shlex.quote(args.remote_root), shlex.quote(args.seed_root)
    _run([*ssh, f"set -eu; test ! -e {root}; test -d {seed}/assets; mkdir -p {root}/incoming {root}/current {root}/assets {root}/requests {root}/receipts {root}/output {root}/checkpoints; cp -a --reflink=auto {seed}/assets/corpus.jsonl {root}/assets/; cp -a --reflink=auto {seed}/assets/programs {root}/assets/; cp -a --reflink=auto {seed}/assets/models {root}/assets/"])
    uploads = {
        "code.tar.gz": code,
        "queries.jsonl": query_file,
        "selection-scope.json": stage / "selection-scope.json",
        "A4_RUNTIME_ASSETS.json": stage / "A4_RUNTIME_ASSETS.json",
        "A4_RUNTIME_BINDINGS.json": stage / "A4_RUNTIME_BINDINGS.json",
        "profile-registry.json": stage / "profile-registry.json",
    }
    for name, path in uploads.items():
        _run([*scp, str(path), f"{remote}:{args.remote_root}/incoming/{name}"])
    verification = (
        "import json,sys; from pathlib import Path; "
        f"sys.path.insert(0,{args.remote_root!r}+'/current/src'); "
        "from myis_research.armindex.a4_remote_ranker import _inventory,_runtime_bindings,_scope,_profile_registry; "
        f"root=Path({args.remote_root!r}); assets=root/'assets'; "
        "inventory=_inventory(json.loads((assets/'A4_RUNTIME_ASSETS.json').read_text()),assets); "
        f"runtime=_runtime_bindings(json.loads((root/'A4_RUNTIME_BINDINGS.json').read_text()),attempt_id={args.attempt_id!r}); "
        f"scope=_scope(json.loads((assets/'selection-scope.json').read_text()),selection=True); "
        f"registry=_profile_registry(json.loads((root/'receipts/profile-registry.json').read_text()),attempt_id={args.attempt_id!r}); "
        "assert runtime['asset_inventory_sha256']==inventory['inventory_sha256']; "
        "assert runtime['selection_scope_sha256']==scope['scope_sha256']; "
        "assert runtime['profile_registry_sha256']==registry['registry_sha256']"
    )
    _run([*ssh, f"set -eu; tar -xzf {root}/incoming/code.tar.gz -C {root}/current; cp {root}/incoming/queries.jsonl {root}/assets/queries.jsonl; cp {root}/incoming/selection-scope.json {root}/assets/selection-scope.json; cp {root}/incoming/A4_RUNTIME_ASSETS.json {root}/assets/A4_RUNTIME_ASSETS.json; cp {root}/incoming/A4_RUNTIME_BINDINGS.json {root}/A4_RUNTIME_BINDINGS.json; cp {root}/incoming/profile-registry.json {root}/receipts/profile-registry.json; PYTHONPATH={root}/current/src python3 -c {shlex.quote(verification)}; sha256sum {root}/incoming/* > {root}/receipts/staged.sha256"])
    body = {
        "schema_version": "myis.armindex-a4-selection-verified-seed-stage-receipt.v1",
        "status": "PASS_A4_SELECTION_VERIFIED_SEED_STAGED",
        "attempt_id": args.attempt_id,
        "remote_root": args.remote_root,
        "seed_root": args.seed_root,
        "code_bundle_sha256": file_sha256(code),
        "runtime_bindings_sha256": runtime["runtime_bindings_sha256"],
        "profile_registry_sha256": registry["registry_sha256"],
        "selection_scope_sha256": scope["scope_sha256"],
        "asset_inventory_sha256": inventory["inventory_sha256"],
        "reused_worker": False,
        "reused_cache": False,
        "reused_request": False,
        "reused_output": False,
        "selection_accesses": 0,
        "final_accesses": 0,
        "protected_payload_included": False,
    }
    _write(stage / "stage-receipt.json", {**body, "receipt_sha256": canonical_sha256(body)})
    print(canonical_json({"status": body["status"], "attempt_id": args.attempt_id, "remote_root": args.remote_root, "stage_receipt_sha256": canonical_sha256(body)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
