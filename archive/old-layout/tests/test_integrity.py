import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]


def load_script(name: str):
    path = ROOT / "05_code/scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


capture_environment = load_script("capture_environment")
validate_integrity = load_script("validate_integrity")


class IntegrityTests(unittest.TestCase):
    def test_import_hashes_match_worktree_and_git_index(self) -> None:
        self.assertEqual(validate_integrity.validate(), [])

    def test_semantic_parsers_ignore_line_ending_representation(self) -> None:
        json_lf = b'{"value": [1, 2]}\n'
        json_crlf = b'{"value": [1, 2]}\r\n'
        csv_lf = b"key,value\na,1\n"
        csv_crlf = b"key,value\r\na,1\r\n"

        self.assertEqual(
            validate_integrity.semantic_value("value.json", json_lf),
            validate_integrity.semantic_value("value.json", json_crlf),
        )
        self.assertEqual(
            validate_integrity.semantic_value("value.csv", csv_lf),
            validate_integrity.semantic_value("value.csv", csv_crlf),
        )

    def test_environment_capture_binds_uv_lock_and_selections(self) -> None:
        payload = capture_environment.build_environment(
            ["test", "test"], ["tracking"]
        )
        lock_bytes = (ROOT / "uv.lock").read_bytes()

        self.assertEqual(payload["schema_version"], "myis.environment.v1")
        self.assertEqual(payload["selected_groups"], ["test"])
        self.assertEqual(payload["selected_extras"], ["tracking"])
        self.assertEqual(
            payload["pyproject_sha256"],
            hashlib.sha256((ROOT / "pyproject.toml").read_bytes()).hexdigest().upper(),
        )
        self.assertEqual(
            payload["uv_lock_sha256"], hashlib.sha256(lock_bytes).hexdigest().upper()
        )
        self.assertRegex(payload["python"]["version"], r"^3\.11\.[0-9]+$")
        self.assertIsNotNone(payload["uv_version"])

    def test_environment_json_is_canonicalizable(self) -> None:
        payload = capture_environment.build_environment([], [])
        encoded = json.dumps(payload, ensure_ascii=True, sort_keys=True)
        self.assertEqual(json.loads(encoded), payload)


if __name__ == "__main__":
    unittest.main()
