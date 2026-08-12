"""Owner-local production adapter for one frozen A2 representation program.

The adapter is intentionally a narrow boundary.  It verifies that a requested
program is byte-for-byte one of the frozen A2 programs, binds the invocation
to the immutable A1 v16 runtime/model/data/evaluator lineage, and permits only
one aggregate-safe result object on stdout.  The retriever/evaluator itself is
an Owner-local command named in the input manifest; no protected inputs,
provider configuration, or verbose output enter this repository.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from ..kernel.canonical import canonical_sha256, file_sha256
from ..protection import assert_aggregate_only
from .a2_execution_readiness import frozen_candidates

_HASH = re.compile(r"^[a-f0-9]{64}$")
_ATTEMPT = re.compile(r"^a2-[a-z0-9-]{7,63}$")
_FORBIDDEN_PATH = re.compile(
    r"(?:qrels|membership|query[_-]?ids?|credential|secret|token[_-]?map|"
    r"embedding|provider[_-]?payload|model[_-]?weights?)",
    re.IGNORECASE,
)
_FIXTURE = re.compile(r"(?:fixture|synthetic|compiler\.py)", re.IGNORECASE)
_RESULT_FIELDS = frozenset(
    {
        "schema_version",
        "attempt_id",
        "candidate_id",
        "arm_id",
        "program_sha256",
        "executor_output_sha256",
        "evaluator_input_sha256",
        "evaluator_sha256",
        "code_sha256",
        "model_sha256",
        "data_sha256",
        "primary_metric",
        "secondary_metrics",
        "latency",
        "cost",
        "coverage",
        "resume_count",
        "failure_count",
        "reserve_activation_passed",
        "reserve_activation_evidence_sha256",
        "train_only",
        "rep_dev_measured",
        "protected_payload_included",
        "per_query_outcomes_included",
    }
)
_A1_RUNTIME = Path("control/armindex/a1.2/runtime-lock.direct-base.v5.json")
_A1_LOCKSET = Path("control/armindex/a1.2/model-lockset.v1.json")
_A1_TERMINAL = Path(
    "campaigns/armindex-multiretriever-v2/evidence/a1.2-terminal-attempts/"
    "a12-v16-20260811-r15.receipt.v16.json"
)
_A1_SUMMARY = Path(
    "campaigns/armindex-multiretriever-v2/evidence/a1.2-result-summaries/"
    "a12-v16-20260811-r15.summary.v16.json"
)
_A1_CELL_EDA = Path(
    "campaigns/armindex-multiretriever-v2/evidence/a1.2-cell-eda/"
    "a12-v16-20260811-r15.eda.v16.json"
)
_A1_PROGRAMS = Path("control/armindex/a1.2/common-program-set.v11.json")
_A1_HANDOFF_REQUEST = Path("control/owner-local/a1.2-evaluator-handoff-request.v11.json")


class A2MeasuredAdapterError(ValueError):
    """Raised when the Owner-local measured adapter cannot prove its inputs."""


def _load_json(path: Path, *, role: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise A2MeasuredAdapterError(f"{role} is missing or invalid") from error
    if not isinstance(value, dict):
        raise A2MeasuredAdapterError(f"{role} must be a JSON object")
    return value


def _hash(value: object, *, role: str) -> str:
    if not isinstance(value, str) or _HASH.fullmatch(value) is None:
        raise A2MeasuredAdapterError(f"{role} hash is invalid")
    return value


def _safe_relative_file(
    root: Path, relative: object, *, role: str, protected: bool = False
) -> Path:
    if (
        not isinstance(relative, str)
        or not relative
        or Path(relative).is_absolute()
        or ".." in Path(relative).parts
        or (not protected and _FORBIDDEN_PATH.search(relative))
    ):
        raise A2MeasuredAdapterError(f"{role} path is unsafe")
    candidate = root / relative
    try:
        resolved = candidate.resolve(strict=True)
        metadata = candidate.lstat()
    except OSError as error:
        raise A2MeasuredAdapterError(f"{role} is unavailable") from error
    if (
        candidate.is_symlink()
        or not resolved.is_file()
        or not resolved.is_relative_to(root)
        or metadata.st_mode & 0o170000 != 0o100000
    ):
        raise A2MeasuredAdapterError(f"{role} path is unsafe")
    return resolved


def _a1_v16_bindings(repository_root: Path) -> dict[str, str]:
    root = repository_root.resolve()
    _load_json(root / _A1_RUNTIME, role="frozen A1 runtime lock")
    _load_json(root / _A1_LOCKSET, role="frozen A1 model lockset")
    terminal = _load_json(root / _A1_TERMINAL, role="frozen A1 terminal receipt")
    _load_json(root / _A1_SUMMARY, role="frozen A1 summary")
    expected = {
        # Source artifact commitments are file hashes.  The evaluator receipt
        # is additionally bound to its canonical receipt hash from A1 v16.
        "runtime_lock_sha256": file_sha256(root / _A1_RUNTIME),
        "model_lockset_sha256": file_sha256(root / _A1_LOCKSET),
        "data_handoff_sha256": file_sha256(root / _A1_SUMMARY),
        "evaluator_receipt_sha256": terminal.get("evaluator_receipt_sha256"),
    }
    return {key: _hash(value, role=f"A1 v16 {key}") for key, value in expected.items()}


def canonical_a1_incumbents(repository_root: Path) -> dict[str, dict[str, str]]:
    """Derive the three A2 incumbents from immutable A1 v16 aggregate evidence."""

    root = repository_root.resolve()
    eda = _load_json(root / _A1_CELL_EDA, role="A1 v16 cell EDA")
    programs = _load_json(root / _A1_PROGRAMS, role="A1 v16 common programs")
    if (
        eda.get("status") != "PASS"
        or eda.get("attempt_id") != "a12-v16-20260811-r15"
        or eda.get("scientific_authority") is not True
    ):
        raise A2MeasuredAdapterError("A1 v16 incumbent evidence is not authoritative")
    program_hashes = {
        row["program_key"]: row["program_spec_sha256"] for row in programs["programs"]
    }
    result: dict[str, dict[str, str]] = {}
    for arm_id in ("ARM-03", "ARM-05", "ARM-04"):
        rows = [row for row in eda["cells"] if row.get("arm_id") == arm_id]
        if len(rows) != 5:
            raise A2MeasuredAdapterError("A1 v16 incumbent coverage drift")
        best = min(
            rows,
            key=lambda row: (-float(row["out_recall_at_100"]), str(row["program_id"])),
        )
        result[arm_id] = {
            "candidate_id": str(best["program_id"]),
            "program_sha256": _hash(
                program_hashes.get(str(best["program_id"])), role=f"{arm_id} incumbent program"
            ),
            "primary_metric": str(best["out_recall_at_100"]),
        }
    return result


def _verify_model_manifest(
    repository_root: Path, *, arm_id: str, model_root: Path, manifest_path: Path
) -> None:
    manifest = _load_json(manifest_path, role="Owner-local model file manifest")
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        raise A2MeasuredAdapterError("Owner-local model file manifest is incomplete")
    lock = _load_json(
        repository_root / "control" / "armindex" / "a1.2" / "model-locks" / f"{arm_id}.v1.json",
        role=f"frozen {arm_id} model lock",
    )
    if (
        manifest.get("arm_id") != arm_id
        or manifest.get("model_lock_sha256") != lock.get("lock_sha256")
        or manifest.get("model_id") != lock.get("model_id")
        or manifest.get("resolved_revision") != lock.get("resolved_revision")
    ):
        raise A2MeasuredAdapterError("Owner-local model manifest binding drift")
    critical = lock.get("critical_artifacts")
    if not isinstance(critical, list) or any(
        not isinstance(row, Mapping)
        or not isinstance(row.get("path"), str)
        or not isinstance(row.get("sha256"), str)
        for row in critical
    ):
        raise A2MeasuredAdapterError("frozen model lock is incomplete")
    expected_critical = {str(row["path"]): str(row["sha256"]) for row in critical}
    expected: set[str] = set()
    for row in files:
        if not isinstance(row, Mapping):
            raise A2MeasuredAdapterError("Owner-local model file manifest is invalid")
        path = _safe_relative_file(model_root, row.get("path"), role="model file", protected=True)
        if file_sha256(path) != row.get("sha256"):
            raise A2MeasuredAdapterError("Owner-local model file hash drift")
        expected.add(path.relative_to(model_root).as_posix())
    actual = {
        path.relative_to(model_root).as_posix()
        for path in model_root.rglob("*")
        if path.is_file() and not path.is_symlink()
    }
    if actual != expected:
        raise A2MeasuredAdapterError("Owner-local model file set drift")
    observed = {str(row["path"]): str(row["sha256"]) for row in files if isinstance(row, Mapping)}
    if any(observed.get(path) != digest for path, digest in expected_critical.items()):
        raise A2MeasuredAdapterError("Owner-local model critical artifact drift")


def _runtime_python_identity(root: Path, executable: Path) -> None:
    runtime = _load_json(root / _A1_RUNTIME, role="frozen A1 runtime lock")
    try:
        process = subprocess.run(
            [str(executable), "-c", "import json,platform,torch;print(json.dumps({'python':platform.python_version(),'pytorch':torch.__version__,'cuda':torch.version.cuda}))"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30,
            env={"PATH": os.environ.get("PATH", ""), "PYTHONDONTWRITEBYTECODE": "1"},
        )
        identity = json.loads(process.stdout) if process.returncode == 0 else None
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as error:
        raise A2MeasuredAdapterError("frozen runtime interpreter cannot be verified") from error
    if (
        not isinstance(identity, Mapping)
        or not str(identity.get("python", "")).startswith("3.11.")
        or identity.get("pytorch") != runtime["pytorch"]
        or identity.get("cuda") != runtime["cuda"]
    ):
        raise A2MeasuredAdapterError("frozen runtime interpreter identity drift")


def _validate_schema(repository_root: Path, value: Mapping[str, Any]) -> None:
    schema = _load_json(
        repository_root / "schemas/armindex/a2-owner-local-measured-input.v1.json",
        role="A2 owner-local input schema",
    )
    errors = sorted(
        Draft202012Validator(schema).iter_errors(dict(value)),
        key=lambda error: tuple(str(item) for item in error.absolute_path),
    )
    if errors:
        raise A2MeasuredAdapterError(f"A2 owner-local input validation failed: {errors[0].message}")


def validate_owner_local_input(
    repository_root: Path, *, owner_root: Path, manifest_relative_path: str
) -> dict[str, Any]:
    """Validate an A2 input manifest without opening protected artifact contents."""

    root = repository_root.resolve()
    try:
        local_root = owner_root.resolve(strict=True)
    except OSError as error:
        raise A2MeasuredAdapterError("Owner-local root is unavailable") from error
    if owner_root.is_symlink() or not local_root.is_dir():
        raise A2MeasuredAdapterError("Owner-local root is unsafe")
    manifest_path = _safe_relative_file(
        local_root, manifest_relative_path, role="Owner-local input manifest"
    )
    manifest = _load_json(manifest_path, role="Owner-local input manifest")
    _validate_schema(root, manifest)
    body = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    if manifest.get("manifest_sha256") != canonical_sha256(body):
        raise A2MeasuredAdapterError("Owner-local input manifest self-hash mismatch")
    if manifest.get("status") != "READY" or _ATTEMPT.fullmatch(str(manifest.get("attempt_id"))) is None:
        raise A2MeasuredAdapterError("Owner-local input manifest is not READY")
    if manifest.get("a1_v16_bindings") != _a1_v16_bindings(root):
        raise A2MeasuredAdapterError("frozen A1 v16 binding drift")
    if manifest["arm_incumbents"] != canonical_a1_incumbents(root):
        raise A2MeasuredAdapterError("Owner-local A1 incumbent binding drift")
    artifacts = manifest["owner_artifacts"]
    expected_bindings = _a1_v16_bindings(root)
    binding_names = {
        "runtime": "runtime_lock_sha256",
        "model_lockset": "model_lockset_sha256",
        "data_handoff": "data_handoff_sha256",
        "evaluator": "evaluator_receipt_sha256",
    }
    for name in ("runtime", "model_lockset", "data_handoff", "evaluator"):
        item = artifacts[name]
        artifact = _safe_relative_file(
            local_root, item["path"], role=f"{name} artifact", protected=True
        )
        if file_sha256(artifact) != item["sha256"]:
            raise A2MeasuredAdapterError(f"{name} artifact hash drift")
        if item["binding_sha256"] != expected_bindings[binding_names[name]]:
            raise A2MeasuredAdapterError(f"{name} A1 v16 binding drift")
    for name in ("corpus", "queries", "qrels", "membership"):
        item = artifacts[name]
        artifact = _safe_relative_file(
            local_root, item["path"], role=f"{name} artifact", protected=True
        )
        if file_sha256(artifact) != item["sha256"]:
            raise A2MeasuredAdapterError(f"{name} artifact hash drift")
        _hash(item["binding_sha256"], role=f"{name} binding")
    handoff_request = _load_json(root / _A1_HANDOFF_REQUEST, role="A1 handoff contract")
    data_receipt = _load_json(
        _safe_relative_file(local_root, artifacts["data_handoff"]["path"], role="data handoff", protected=True),
        role="Owner-local data handoff",
    )
    if (
        data_receipt.get("status") != "PASS"
        or data_receipt.get("source_contract_sha256")
        != handoff_request["handoff_contract_sha256"]
        or data_receipt.get("split_role") != "REP-DEV"
        or data_receipt.get("query_count") != 150
        or data_receipt.get("reserved_harness_dev_count") != 100
        or any(
            data_receipt.get(field) != artifacts[name]["binding_sha256"]
            for field, name in (
                ("corpus_bundle_sha256", "corpus"),
                ("query_bundle_sha256", "queries"),
                ("qrels_commitment_sha256", "qrels"),
                ("split_commitment_sha256", "membership"),
                ("evaluator_sha256", "evaluator"),
            )
        )
    ):
        raise A2MeasuredAdapterError("Owner-local REP-DEV data handoff drift")
    engine = manifest["engine"]
    argv = engine["argv"]
    if not argv or any(not isinstance(item, str) or not item for item in argv):
        raise A2MeasuredAdapterError("Owner-local retriever/evaluator argv is invalid")
    if any(_FIXTURE.search(item) for item in argv):
        raise A2MeasuredAdapterError("fixture adapter is forbidden for measured A2")
    if "{program_path}" not in argv:
        raise A2MeasuredAdapterError("Owner-local retriever/evaluator must receive the frozen program")
    python_executable = Path(engine["python_executable"])
    if argv[:3] != [
        str(python_executable),
        "-m",
        "myis_research.armindex.a2_owner_local_engine",
    ]:
        raise A2MeasuredAdapterError("measured A2 requires the production Owner-local engine")
    _runtime_python_identity(root, python_executable)
    if engine["device_by_arm"] != {
        "ARM-02": "cuda:0",
        "ARM-03": "cuda:1",
        "ARM-04": "cuda:2",
        "ARM-05": "cuda:3",
    }:
        raise A2MeasuredAdapterError("frozen dense-arm device topology drift")
    for arm_id, relative in engine["model_directories"].items():
        model = local_root / relative
        if arm_id not in {"ARM-02", "ARM-03", "ARM-04", "ARM-05"} or model.is_symlink():
            raise A2MeasuredAdapterError("Owner-local model directory is unsafe")
        try:
            resolved = model.resolve(strict=True)
        except OSError as error:
            raise A2MeasuredAdapterError("Owner-local model directory is unavailable") from error
        if not resolved.is_dir() or not resolved.is_relative_to(local_root):
            raise A2MeasuredAdapterError("Owner-local model directory is unsafe")
        manifest_relative = engine["model_manifests"][arm_id]
        model_manifest = _safe_relative_file(
            local_root, manifest_relative, role=f"{arm_id} model manifest", protected=True
        )
        _verify_model_manifest(
            root, arm_id=arm_id, model_root=resolved, manifest_path=model_manifest
        )
    output_root = local_root / engine["output_root"]
    output_root.mkdir(parents=True, exist_ok=True)
    if output_root.is_symlink() or not output_root.resolve().is_relative_to(local_root):
        raise A2MeasuredAdapterError("Owner-local output root is unsafe")
    _hash(engine["code_sha256"], role="Owner-local retriever/evaluator code")
    return manifest


def frozen_program_for_candidate(repository_root: Path, candidate_id: str) -> dict[str, Any]:
    """Return the exact manifest program after checking its schema and commitment."""

    root = repository_root.resolve()
    candidates = frozen_candidates(root)
    candidate = candidates.get(candidate_id)
    if candidate is None:
        raise A2MeasuredAdapterError("candidate is outside frozen A2 membership")
    program = candidate.get("program")
    if not isinstance(program, Mapping):
        raise A2MeasuredAdapterError("frozen candidate program is missing")
    schema = _load_json(
        root / "schemas/armindex/representation-program.v1.json",
        role="representation program schema",
    )
    errors = sorted(
        Draft202012Validator(schema).iter_errors(dict(program)),
        key=lambda error: tuple(str(item) for item in error.absolute_path),
    )
    if errors:
        raise A2MeasuredAdapterError(f"frozen candidate program is invalid: {errors[0].message}")
    unsigned = {key: value for key, value in program.items() if key != "program_sha256"}
    if (
        program.get("program_id") != candidate_id
        or program.get("program_sha256") != canonical_sha256(unsigned)
        or program.get("program_sha256") != candidate.get("program_sha256")
    ):
        raise A2MeasuredAdapterError("frozen candidate program hash drift")
    return dict(program)


def _validate_result(
    result: Mapping[str, Any],
    *,
    candidate_id: str,
    candidate: Mapping[str, Any],
    manifest: Mapping[str, Any],
) -> dict[str, Any]:
    row = dict(result)
    if set(row) != _RESULT_FIELDS:
        raise A2MeasuredAdapterError("retriever/evaluator result fields are not allowlisted")
    try:
        assert_aggregate_only(row)
    except ValueError as error:
        raise A2MeasuredAdapterError("retriever/evaluator output crosses protected boundary") from error
    if (
        row.get("schema_version") != "myis.armindex-a2-external-candidate-result.v1"
        or row.get("attempt_id") != manifest["attempt_id"]
        or row.get("candidate_id") != candidate_id
        or row.get("arm_id") != candidate["arm_id"]
        or row.get("program_sha256") != candidate["program_sha256"]
    ):
        raise A2MeasuredAdapterError("retriever/evaluator result identity drift")
    artifacts = manifest["owner_artifacts"]
    expected = {
        "evaluator_sha256": artifacts["evaluator"]["binding_sha256"],
        "model_sha256": artifacts["model_lockset"]["binding_sha256"],
        "data_sha256": artifacts["data_handoff"]["binding_sha256"],
        "code_sha256": manifest["engine"]["code_sha256"],
    }
    for name, value in expected.items():
        if row.get(name) != value:
            raise A2MeasuredAdapterError(f"retriever/evaluator {name} drift")
    for name in ("executor_output_sha256", "evaluator_input_sha256"):
        _hash(row.get(name), role=name)
    if (
        row.get("train_only") is not False
        or row.get("rep_dev_measured") is not True
        or row.get("protected_payload_included") is not False
        or row.get("per_query_outcomes_included") is not False
    ):
        raise A2MeasuredAdapterError("retriever/evaluator result crosses the protected boundary")
    return row


def run_candidate_adapter(
    repository_root: Path,
    *,
    owner_root: Path,
    manifest_relative_path: str,
    candidate_id: str,
    timeout_seconds: int = 21600,
) -> dict[str, Any]:
    """Run one explicit Owner-local retriever/evaluator command and return its result."""

    if timeout_seconds <= 0:
        raise A2MeasuredAdapterError("adapter timeout is invalid")
    manifest = validate_owner_local_input(
        repository_root, owner_root=owner_root, manifest_relative_path=manifest_relative_path
    )
    program = frozen_program_for_candidate(repository_root, candidate_id)
    candidate = frozen_candidates(repository_root.resolve())[candidate_id]
    if (
        os.environ.get("MYIS_A2_ARM_ID") != candidate["arm_id"]
        or os.environ.get("MYIS_A2_PROGRAM_SHA256") != candidate["program_sha256"]
    ):
        raise A2MeasuredAdapterError("candidate environment identity drift")
    owner = owner_root.resolve(strict=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="ascii", suffix=".a2-program.json", prefix=".a2-", dir=owner,
        delete=False,
    ) as handle:
        program_path = Path(handle.name)
        handle.write(json.dumps(program, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
        handle.write("\n")
    try:
        substitutions = {
            "{candidate_id}": candidate_id,
            "{arm_id}": str(candidate["arm_id"]),
            "{program_sha256}": str(candidate["program_sha256"]),
            "{program_path}": str(program_path),
        }
        command = [
            substitutions.get(item, item)
            for item in manifest["engine"]["argv"]
        ]
        command = [
            (
                str(_safe_relative_file(owner, item, role="Owner-local engine argument"))
                if index > 0
                and not Path(item).is_absolute()
                and (owner / item).exists()
                else item
            )
            for index, item in enumerate(command)
        ]
        environment = {
            "PATH": os.environ.get("PATH", ""),
            "PYTHONDONTWRITEBYTECODE": "1",
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "PIP_NO_INDEX": "1",
            "MYIS_A2_CANDIDATE_ID": candidate_id,
            "MYIS_A2_ARM_ID": str(candidate["arm_id"]),
            "MYIS_A2_PROGRAM_SHA256": str(candidate["program_sha256"]),
            "MYIS_A2_REPOSITORY_ROOT": str(repository_root.resolve()),
            "MYIS_A2_OWNER_ROOT": str(owner),
            "MYIS_A2_OWNER_INPUT_MANIFEST": manifest_relative_path,
        }
        process = subprocess.run(
            command,
            check=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="strict",
            env=environment,
            cwd=owner,
            timeout=timeout_seconds,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise A2MeasuredAdapterError("Owner-local retriever/evaluator did not complete") from error
    finally:
        program_path.unlink(missing_ok=True)
    if process.returncode != 0:
        raise A2MeasuredAdapterError("Owner-local retriever/evaluator failed")
    if not process.stdout.endswith("\n") or process.stdout.count("\n") != 1:
        raise A2MeasuredAdapterError("retriever/evaluator must emit exactly one JSON object")
    try:
        result = json.loads(process.stdout)
    except json.JSONDecodeError as error:
        raise A2MeasuredAdapterError("retriever/evaluator stdout is invalid JSON") from error
    if not isinstance(result, dict):
        raise A2MeasuredAdapterError("retriever/evaluator stdout must be an object")
    return _validate_result(
        result, candidate_id=candidate_id, candidate=candidate, manifest=manifest
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="myis-a2-measured-adapter")
    parser.add_argument("--repository-root", required=True, type=Path)
    parser.add_argument("--owner-root", required=True, type=Path)
    parser.add_argument("--input-manifest", required=True)
    parser.add_argument("--timeout-seconds", type=int, default=21600)
    args = parser.parse_args(argv)
    candidate_id = os.environ.get("MYIS_A2_CANDIDATE_ID", "")
    try:
        result = run_candidate_adapter(
            args.repository_root,
            owner_root=args.owner_root,
            manifest_relative_path=args.input_manifest,
            candidate_id=candidate_id,
            timeout_seconds=args.timeout_seconds,
        )
    except A2MeasuredAdapterError as error:
        print(json.dumps({"status": "FAILED_CLOSED", "error": str(error)}, sort_keys=True))
        return 2
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return 0


__all__ = [
    "A2MeasuredAdapterError",
    "frozen_program_for_candidate",
    "canonical_a1_incumbents",
    "run_candidate_adapter",
    "validate_owner_local_input",
]
