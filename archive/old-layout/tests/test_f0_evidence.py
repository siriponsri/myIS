import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]


def load_emitter():
    path = ROOT / "05_code/scripts/capture_f0_evidence.py"
    spec = importlib.util.spec_from_file_location("capture_f0_evidence", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


capture = load_emitter()


class F0EvidenceTests(unittest.TestCase):
    def test_absolute_local_paths_are_normalized_before_serialization(self) -> None:
        payload = capture.normalize_local_paths({"executable": r"C:\\runtime\\python.exe"})
        self.assertEqual(payload, {"executable": "<LOCAL_PATH>/python.exe"})
        capture.assert_no_absolute_local_paths(payload)
        with self.assertRaises(capture.EvidenceCaptureError):
            capture.assert_no_absolute_local_paths({"bad": r"C:\\runtime\\python.exe"})

    def test_append_json_rejects_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "record.json"
            first_hash = capture.append_json(path, {"record": 1})
            self.assertEqual(first_hash, capture.sha256_file(path))
            with self.assertRaises(FileExistsError):
                capture.append_json(path, {"record": 2})

    def test_task_evidence_ledger_chains_repeated_capture(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            task_root = root / "04_outputs/artifacts/task-evidence/F0.1"
            task_root.mkdir(parents=True)
            first = {
                "schema_version": "myis.task-evidence.v1",
                "record_id": "F0-1-first",
                "task_id": "F0.1",
                "plan_sha256": "a" * 64,
                "git_commit": "1" * 40,
                "acceptance_checks": [],
                "evidence_manifest_hashes": [],
                "prior_record_hash": None,
                "supersedes_record_id": None,
            }
            ledger = capture.ImmutableJsonLedger(
                task_root,
                prior_field="prior_record_hash",
                record_id_field="record_id",
                supersedes_field="supersedes_record_id",
            )
            ledger.append(first["record_id"], first)
            second = {**first, "record_id": "F0-1-second", "git_commit": "2" * 40, "prior_record_hash": ledger.head()}
            ledger.append(second["record_id"], second)
            self.assertEqual(ledger.validate_chain()["count"], 2)

    def test_task_evidence_ledger_reconciles_superseded_second_genesis(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            task_root = Path(directory)
            base = {
                "schema_version": "myis.task-evidence.v1",
                "task_id": "F0.1",
                "plan_sha256": "a" * 64,
                "git_commit": "1" * 40,
                "acceptance_checks": [],
                "evidence_manifest_hashes": [],
                "prior_record_hash": None,
                "supersedes_record_id": None,
            }
            first = {**base, "record_id": "F0-1-first"}
            malformed = {**base, "record_id": "F0-1-malformed", "git_commit": "2" * 40}
            capture.append_json(task_root / "F0-1-first.json", first)
            capture.append_json(task_root / "F0-1-malformed.json", malformed)
            ledger = capture.ImmutableJsonLedger(
                task_root,
                prior_field="prior_record_hash",
                record_id_field="record_id",
                supersedes_field="supersedes_record_id",
            )
            first_hash = next(digest for _, record, digest in ledger.records() if record["record_id"] == "F0-1-first")
            correction = {
                **malformed,
                "record_id": "F0-1-correction",
                "prior_record_hash": first_hash,
                "supersedes_record_id": "F0-1-malformed",
            }
            capture.append_json(task_root / "F0-1-correction.json", correction)
            chain = ledger.validate_chain()
            self.assertEqual(chain["count"], 2)
            self.assertEqual(chain["head"], next(digest for _, record, digest in ledger.records() if record["record_id"] == "F0-1-correction"))

    def test_authorized_output_root_rejects_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifacts = root / "04_outputs/artifacts"
            artifacts.mkdir(parents=True)
            external = root / "external"
            external.mkdir()
            link = artifacts / "f0-migration"
            try:
                link.symlink_to(external, target_is_directory=True)
            except OSError:
                self.skipTest("directory symlinks are unavailable")
            with self.assertRaises(capture.EvidenceCaptureError):
                capture._assert_regular_output_root(root, capture.AUTHORIZED_ROOTS[0])

    def test_f0_schema_payload_is_aggregate_only(self) -> None:
        capture.assert_aggregate_only({"schema_version": capture.F0_SCHEMA, "query_ids_hash": "a" * 64})
        with self.assertRaises(ValueError):
            capture.assert_aggregate_only({"query_id": "protected"})

    @unittest.skipUnless(os.name == "nt", "Windows Git Bash selection")
    def test_git_bash_does_not_select_wsl_system32_launcher(self) -> None:
        bash = capture._git_bash()
        self.assertIsNotNone(bash)
        self.assertNotIn("system32", str(bash).casefold())


if __name__ == "__main__":
    unittest.main()
