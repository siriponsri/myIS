from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from myis_research import asset_cli
from myis_research.asset_registry import (
    MAP_RELATIVE_PATH,
    canonical_json,
    load_registry,
    parse_plan_tasks,
    query_assets,
    render_asset_map,
    validate_sources,
)


ROOT = Path(__file__).resolve().parents[2]
PLAN_SHA256 = "54d3e820ee1abfdf05f5478db553e506805265355e62c7b4e2dd112fc8ed2700"


class AssetRegistryTests(unittest.TestCase):
    def test_registry_schema_ids_and_task_coverage(self) -> None:
        registry = load_registry(ROOT)
        assets = registry["assets"]
        self.assertEqual(len(assets), 15)
        self.assertEqual(len({asset["asset_id"] for asset in assets}), len(assets))
        plan_tasks = {task.task_id for task in parse_plan_tasks(ROOT / "PLAN.md")}
        covered = {task_id for asset in assets for task_id in asset["task_ids"]}
        self.assertEqual(covered, plan_tasks)

    def test_dapfam_core_has_metadata_only_huggingface_provenance(self) -> None:
        registry = load_registry(ROOT)
        asset = next(item for item in registry["assets"] if item["asset_id"] == "APP-DAPFAM-CORE")
        upstream = asset["source"]["upstream_huggingface"]
        self.assertEqual(upstream["dataset_id"], "datalyes/DAPFAM_patent")
        self.assertEqual(upstream["configs"], ["corpus", "queries", "relations"])
        self.assertTrue(upstream["metadata_only"])
        self.assertFalse(upstream["live_fetch_allowed"])

    def test_query_filters_and_outputs_are_deterministic(self) -> None:
        registry = load_registry(ROOT)
        selected = query_assets(registry, task_id="F1.1", disposition="reuse")
        self.assertEqual(
            [asset["asset_id"] for asset in selected],
            ["APP-DAPFAM-CORE", "APP-DAPFAM-PAPER-VIEWS", "APP-PATEMBED-CONTROL"],
        )
        self.assertEqual(canonical_json(list(selected)), canonical_json(list(selected)))
        original = Path.cwd()
        try:
            os.chdir(ROOT)
            first = StringIO()
            second = StringIO()
            with redirect_stdout(first):
                self.assertEqual(asset_cli.main(["query", "--task", "F1.1", "--json"]), 0)
            with redirect_stdout(second):
                self.assertEqual(asset_cli.main(["query", "--task", "F1.1", "--json"]), 0)
            self.assertEqual(first.getvalue(), second.getvalue())
            json.loads(first.getvalue())
        finally:
            os.chdir(original)

    def test_generated_map_exactly_matches_registry(self) -> None:
        registry = load_registry(ROOT)
        expected = render_asset_map(registry, ROOT)
        self.assertEqual((ROOT / MAP_RELATIVE_PATH).read_text(encoding="utf-8"), expected)
        for task in parse_plan_tasks(ROOT / "PLAN.md"):
            self.assertIn(f"| `{task.task_id}` |", expected)

    def test_protected_full_validation_refuses_before_source_read(self) -> None:
        registry = load_registry(ROOT)
        with patch("myis_research.asset_registry._hash_file") as hash_file:
            with self.assertRaises(PermissionError):
                validate_sources(
                    registry,
                    ROOT,
                    mode="full",
                    asset_ids=["APP-DAPFAM-CORE"],
                )
        hash_file.assert_not_called()

    def test_unrelated_head_advancement_warns_but_registered_change_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            self._git(source, "init")
            self._git(source, "config", "user.email", "test@example.invalid")
            self._git(source, "config", "user.name", "Registry Test")
            registered = source / "registered.txt"
            other = source / "other.txt"
            registered.write_text("stable\n", encoding="utf-8")
            other.write_text("one\n", encoding="utf-8")
            self._git(source, "add", ".")
            self._git(source, "commit", "-m", "initial")
            initial = self._git(source, "rev-parse", "HEAD")
            registry = self._minimal_registry(initial, registered)

            other.write_text("two\n", encoding="utf-8")
            self._git(source, "add", "other.txt")
            self._git(source, "commit", "-m", "unrelated")
            report = validate_sources(registry, root, mode="quick")
            self.assertTrue(report.ok)
            self.assertEqual(len(report.warnings), 1)

            registered.write_text("changed\n", encoding="utf-8")
            self._git(source, "add", "registered.txt")
            self._git(source, "commit", "-m", "registered drift")
            report = validate_sources(registry, root, mode="quick")
            self.assertFalse(report.ok)
            self.assertIn("registered.txt", report.errors[0])

    def test_registry_map_and_optional_brain_note_are_pointer_only(self) -> None:
        paths = [
            ROOT / "00_governance/config/reusable_assets.yaml",
            ROOT / MAP_RELATIVE_PATH,
        ]
        brain_note = (
            ROOT.parent
            / "02_Brain/work/active/myIS Research/Reusable Assets for Track C-S.md"
        )
        if brain_note.is_file():
            paths.append(brain_note)
        identifier_row = re.compile(r"\b\d{3}(?:-\d{3}){4}\b")
        qrels_row = re.compile(r"(?m)^\S+\t(?:Q0|0)\t\S+\t")
        for path in paths:
            text = path.read_text(encoding="utf-8")
            self.assertIsNone(identifier_row.search(text), path)
            self.assertIsNone(qrels_row.search(text), path)

    def test_preported_modules_have_no_network_model_or_app_runtime_imports(self) -> None:
        modules = [
            ROOT / "05_code/src/myis_research/harness/dapfam_text.py",
            ROOT / "05_code/src/myis_research/harness/sparse.py",
            ROOT / "05_code/src/myis_research/harness/reranking.py",
            ROOT / "05_code/src/myis_research/harness/usage.py",
        ]
        forbidden = {
            "httpx", "requests", "openai", "torch", "transformers",
            "sentence_transformers", "huggingface_hub",
        }
        for path in modules:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.update(alias.name.split(".", 1)[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.add(node.module.split(".", 1)[0])
            self.assertFalse(imports & forbidden, path)
            self.assertFalse(
                any(name.startswith(("paper_", "is1_projects", "thaiphalex")) for name in imports),
                path,
            )

    def test_plan_bytes_remain_unchanged(self) -> None:
        observed = hashlib.sha256((ROOT / "PLAN.md").read_bytes()).hexdigest()
        self.assertEqual(observed, PLAN_SHA256)

    @staticmethod
    def _git(root: Path, *args: str) -> str:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()

    @staticmethod
    def _minimal_registry(commit: str, registered: Path) -> dict:
        return {
            "source_repositories": {
                "app": {"root_hint": "source", "commit": commit}
            },
            "assets": [
                {
                    "asset_id": "TEST-ASSET",
                    "protected_data_level": "none",
                    "source": {
                        "repository": "app",
                        "paths": [
                            {
                                "path": "registered.txt",
                                "bytes": registered.stat().st_size,
                                "sha256": hashlib.sha256(registered.read_bytes()).hexdigest(),
                            }
                        ],
                    },
                }
            ],
        }


if __name__ == "__main__":
    unittest.main()
