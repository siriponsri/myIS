import copy
import hashlib
import io
import json
import os
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

import yaml

from myis_research.harness.cli import main
from myis_research.harness.drafts import (
    DRAFT_MEASURED_MANIFEST_SCHEMA,
    DRAFT_RUNSPEC_SCHEMA,
    DraftValidationError,
    validate_draft_document,
)
from myis_research.harness.reproduction import reproduce_dapfam
from myis_research.harness.validation import ValidationError, validate_manifest_payload


ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_ROOT = ROOT / "03_experiments" / "templates"
RUNSPEC_TEMPLATE = TEMPLATE_ROOT / "f1-dapfam-runspec-draft.yaml"
MEASURED_TEMPLATE = TEMPLATE_ROOT / "f1-dapfam-measured-manifest-draft.yaml"


class ReproductionScaffoldTests(TestCase):
    def _template(self, path: Path) -> dict[str, object]:
        return yaml.safe_load(path.read_text(encoding="utf-8"))

    def _run_cli(self, *args: str) -> tuple[int, dict[str, object]]:
        previous = Path.cwd()
        stdout = io.StringIO()
        try:
            os.chdir(ROOT)
            with redirect_stdout(stdout):
                exit_code = main(list(args))
        finally:
            os.chdir(previous)
        return exit_code, json.loads(stdout.getvalue())

    def test_checked_in_drafts_validate_only_as_draft_contracts(self) -> None:
        runspec = self._template(RUNSPEC_TEMPLATE)
        measured = self._template(MEASURED_TEMPLATE)

        self.assertEqual(
            validate_draft_document(runspec)["schema_version"], DRAFT_RUNSPEC_SCHEMA
        )
        self.assertEqual(
            validate_draft_document(measured)["schema_version"], DRAFT_MEASURED_MANIFEST_SCHEMA
        )
        for document in (runspec, measured):
            self.assertEqual(document["status"], "draft")
            self.assertFalse(document["executable"])
            self.assertEqual(document["gate"], "G1")
            self.assertEqual(document["gate_status"], "pending")
            with self.assertRaises(ValidationError):
                validate_manifest_payload(document)

    def test_draft_contract_rejects_executable_or_approved_values(self) -> None:
        template = self._template(RUNSPEC_TEMPLATE)
        for key, invalid in (
            ("status", "approved"),
            ("executable", True),
            ("gate", "G2"),
            ("document_kind", "other"),
        ):
            invalid_template = copy.deepcopy(template)
            invalid_template[key] = invalid
            with self.subTest(key=key), self.assertRaises(DraftValidationError):
                validate_draft_document(invalid_template)
        invalid_template = copy.deepcopy(template)
        invalid_template["owner_commitments"]["qrels"] = "APPROVED"
        with self.assertRaises(DraftValidationError):
            validate_draft_document(invalid_template)

    def test_default_command_refuses_without_opening_supplied_manifest(self) -> None:
        with patch("myis_research.harness.reproduction.load_draft_document") as load_draft:
            exit_code, payload = self._run_cli(
                "reproduce", "dapfam", "--manifest", "01_evidence/qrels/not-permitted.yaml"
            )
        load_draft.assert_not_called()
        self.assertEqual(exit_code, 2)
        self.assertEqual(payload["status"], "WAITING_GATE")
        self.assertEqual(payload["dataset_access"], "none")
        self.assertFalse(payload["scientific_run"])
        self.assertEqual(payload["artifact_count"], 0)
        self.assertEqual(payload["scientific_metric_count"], 0)

    def test_dry_run_validates_checked_in_draft_then_refuses(self) -> None:
        exit_code, payload = self._run_cli(
            "reproduce", "dapfam", "--manifest", str(RUNSPEC_TEMPLATE), "--dry-run"
        )
        self.assertEqual(exit_code, 2)
        self.assertEqual(payload["status"], "WAITING_GATE")
        self.assertEqual(payload["draft_validation"]["status"], "PASS")
        self.assertFalse(payload["executor_available"])
        self.assertEqual(payload["network_access"], "none")
        self.assertEqual(payload["provider_access"], "none")
        self.assertEqual(payload["gpu_access"], "none")
        self.assertEqual(payload["mlflow_access"], "none")
        self.assertEqual(payload["artifact_count"], 0)
        self.assertEqual(payload["scientific_metric_count"], 0)

    def test_dry_run_rejects_paths_outside_checked_in_templates(self) -> None:
        exit_code, payload = self._run_cli(
            "reproduce", "dapfam", "--manifest", "01_evidence/qrels/not-permitted.yaml", "--dry-run"
        )
        self.assertEqual(exit_code, 2)
        self.assertEqual(payload["reason"], "DRAFT_VALIDATION_FAILED")
        self.assertEqual(payload["dataset_access"], "none")

    def test_invalid_handoff_input_returns_generic_blocked_payload(self) -> None:
        with patch(
            "myis_research.harness.cli.reproduce_dapfam",
            side_effect=ValueError("protected owner-local payload detail"),
        ):
            exit_code, payload = self._run_cli(
                "reproduce",
                "dapfam",
                "--owner-batch",
                "owner-batch.json",
                "--g1-decision",
                "g1.json",
                "--frozen-runspec",
                "runspec.yaml",
            )
        self.assertEqual(exit_code, 2)
        self.assertEqual(payload["status"], "BLOCKED")
        self.assertEqual(payload["reason"], "G1_HANDOFF_VALIDATION_FAILED")
        self.assertNotIn("message", payload)
        self.assertNotIn("protected owner-local payload detail", json.dumps(payload))

    def test_valid_handoff_remains_non_executable_without_measured_executor(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            batch_path = Path(temp) / "batch.json"
            batch_path.write_text("{}", encoding="utf-8")
            batch_sha = hashlib.sha256(batch_path.read_bytes()).hexdigest()
            proposal_sha = "a" * 64
            split = {role: hashlib.sha256(role.encode()).hexdigest() for role in ("train", "selection", "joint_test")}
            sources = {role: hashlib.sha256(role.encode()).hexdigest() for role in ("corpus", "queries", "qrels")}
            expected_sources = {
                **sources,
                "family": "b" * 64,
                "evaluator": "e" * 64,
                "field_protocol": "f" * 64,
            }
            batch = SimpleNamespace(
                proposal_sha256=proposal_sha,
                split=SimpleNamespace(membership_sha256=split),
                sources=tuple(SimpleNamespace(role=role, sha256=value) for role, value in sources.items()),
                family_commitment_sha256="b" * 64,
                evaluator=SimpleNamespace(model_dump=lambda **_: {"evaluator": "fixture"}),
                field_protocol={"view": "fixture"},
                generator=SimpleNamespace(git_commit="d" * 40),
            )
            runspec_sha = "c" * 64
            runspec = SimpleNamespace(
                owner_value_batch_sha256=batch_sha,
                proposal_sha256=proposal_sha,
                split_membership_sha256=split,
                source_sha256=expected_sources,
                git_commit="d" * 40,
            )
            decision = {
                "decision_id": "G1-fixture",
                "evidence_manifest_hashes": [batch_sha, runspec_sha],
                "git_commit": "d" * 40,
            }
            with (
                patch("myis_research.harness.reproduction._validate_g1_decision", return_value=decision),
                patch("myis_research.harness.reproduction._validate_frozen_runspec", return_value=(runspec, runspec_sha)),
                patch("myis_research.harness.reproduction.validate_owner_value_batch", return_value=batch),
                patch("myis_research.harness.reproduction.sha256_payload", side_effect=["e" * 64, "f" * 64]),
            ):
                payload = reproduce_dapfam(
                    repository_root=ROOT,
                    manifest=None,
                    validate_draft=False,
                    owner_batch=batch_path,
                    g1_decision=Path(temp) / "decision.json",
                    frozen_runspec=Path(temp) / "runspec.yaml",
                )
                batch.generator.git_commit = "e" * 40
                with self.assertRaisesRegex(DraftValidationError, "generator commit"):
                    reproduce_dapfam(
                        repository_root=ROOT,
                        manifest=None,
                        validate_draft=False,
                        owner_batch=batch_path,
                        g1_decision=Path(temp) / "decision.json",
                        frozen_runspec=Path(temp) / "runspec.yaml",
                    )
                batch.generator.git_commit = "d" * 40
                decision["evidence_manifest_hashes"] = [batch_sha]
                with self.assertRaisesRegex(DraftValidationError, "must bind"):
                    reproduce_dapfam(
                        repository_root=ROOT,
                        manifest=None,
                        validate_draft=False,
                        owner_batch=batch_path,
                        g1_decision=Path(temp) / "decision.json",
                        frozen_runspec=Path(temp) / "runspec.yaml",
                    )
        self.assertEqual(payload["status"], "HANDOFF_READY_EXECUTOR_UNAVAILABLE")
        self.assertEqual(payload["reason"], "REPRODUCTION_EXECUTOR_NOT_IMPLEMENTED")
        self.assertFalse(payload["executor_available"])
        self.assertFalse(payload["scientific_run"])
        for boundary in ("dataset_access", "network_access", "provider_access", "gpu_access", "mlflow_access"):
            self.assertEqual(payload[boundary], "none")
        self.assertEqual(payload["artifact_count"], 0)
        self.assertEqual(payload["scientific_metric_count"], 0)
