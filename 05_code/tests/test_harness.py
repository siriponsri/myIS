import hashlib
import io
import json
import tempfile
import unittest
import uuid
from contextlib import redirect_stderr
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from myis_research.harness import (
    ApprovalRecord,
    GoalSpec,
    GoalState,
    HarnessPolicy,
    LocalHarness,
    RunSpec,
    ValidationError,
    validate_run_bundle,
)
from myis_research.harness.benchmark import SelectionDecision, deterministic_stratified_split
from myis_research.harness.models import canonical_hash
from myis_research.harness.runner import KERNEL_VERSION


def build_spec(policy: HarnessPolicy, run_id: str, *, split: str = "development") -> RunSpec:
    goal = GoalSpec("goal-fixture", "offline fixture", "F0", GoalState.APPROVED, ("score",))
    approval = ApprovalRecord("approval-fixture", "unit-test", datetime.now(timezone.utc).isoformat(), "pending")
    spec = RunSpec(
        run_id=run_id,
        goal=goal,
        approval=approval,
        arm="human",
        phase="offline-test",
        dataset_id="fixture",
        dataset_manifest_hash=hashlib.sha256(b"dataset").hexdigest(),
        split=split,
        split_query_ids_hash=hashlib.sha256(b"q1").hexdigest(),
        evaluator_id="fixture-evaluator",
        evaluator_hash=hashlib.sha256(b"evaluator").hexdigest(),
        kernel_version=KERNEL_VERSION,
        policy_hash=policy.sha256,
        config_hash=canonical_hash({"seed": 7}),
        prompt_hash=hashlib.sha256(b"prompt").hexdigest(),
        skill_set_hash=hashlib.sha256(b"skill").hexdigest(),
        seed=7,
        budget={"max_seconds": 5, "max_api_cost_usd": 0},
    )
    return replace(spec, approval=replace(approval, scope_hash=spec.scope_hash()))


class HarnessTests(unittest.TestCase):
    def test_complete_bundle_projection_redaction_and_collect(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            policy = HarnessPolicy("fixture")
            spec = build_spec(policy, uuid.uuid4().hex)
            harness = LocalHarness(root)
            stderr = io.StringIO()

            def executor(_, __, logger):
                logger.emit("tool.completed", status="RUNNING", milestone=True, password="never-visible")
                return {"result": {"ok": True}, "metrics": {"score": 1.0}, "per_query": [{"query_id": "q1", "score": 1.0}]}

            with redirect_stderr(stderr):
                result = harness.execute(
                    spec,
                    policy,
                    executor=executor,
                    prompt_record={"template": "fixture", "authorization": "Bearer secret-value"},
                    flow_record={"steps": ["fixture"], "api_key": "flow-secret-value"},
                )
            validation = validate_run_bundle(result.run_dir, expected_split_hash=spec.split_query_ids_hash)
            self.assertEqual(validation["status"], "PASS")
            runtime = [json.loads(line) for line in (result.run_dir / "runtime.jsonl").read_text(encoding="utf-8").splitlines()]
            progress = [json.loads(line) for line in (result.run_dir / "progress.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertTrue({row["event_id"] for row in progress} <= {row["event_id"] for row in runtime})
            combined = (
                stderr.getvalue()
                + (result.run_dir / "runtime.jsonl").read_text(encoding="utf-8")
                + (result.run_dir / "prompt.json").read_text(encoding="utf-8")
                + (result.run_dir / "flow.json").read_text(encoding="utf-8")
            )
            self.assertNotIn("never-visible", combined)
            self.assertNotIn("secret-value", combined)
            self.assertNotIn("flow-secret-value", combined)
            self.assertEqual(harness.collect(spec.run_id).metrics["score"], 1.0)

    def test_tamper_and_held_out_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            policy = HarnessPolicy("fixture")
            held_out = build_spec(policy, "held-out", split="confirmation")
            with self.assertRaises(PermissionError):
                LocalHarness(root).preflight(held_out, policy)
            spec = build_spec(policy, "tamper")
            result = LocalHarness(root).execute(
                spec,
                policy,
                executor=lambda *_: {"result": {}, "metrics": {"score": 0.1}, "per_query": []},
                prompt_record={"template": "fixture"},
                flow_record={"steps": []},
            )
            (result.run_dir / "metrics.json").write_text('{"score": 9}\n', encoding="utf-8")
            with self.assertRaises(ValidationError):
                validate_run_bundle(result.run_dir)

    def test_executor_failure_finalizes_valid_bundle_and_deferred_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            policy = HarnessPolicy("fixture")
            spec = build_spec(policy, "failed-run")

            def fail(*_):
                raise ValueError("password=must-not-leak")

            with self.assertRaises(ValueError):
                LocalHarness(root).execute(
                    spec,
                    policy,
                    executor=fail,
                    prompt_record={"template": "fixture"},
                    flow_record={"steps": ["fail"]},
                )
            run_dir = root / spec.run_id
            validation = validate_run_bundle(run_dir)
            manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
            receipt = json.loads((run_dir / "receipts" / "mlflow-initial.json").read_text(encoding="utf-8"))
            self.assertEqual(validation["status"], "PASS")
            self.assertEqual(manifest["lifecycle"]["status"], "FAILED")
            self.assertEqual(receipt["status"], "sync_deferred")
            self.assertNotIn("must-not-leak", (run_dir / "runtime.jsonl").read_text(encoding="utf-8"))

    def test_dapfam_split_and_strict_selection_rule(self) -> None:
        split_a = deterministic_stratified_split(
            [(f"q{i}", "A" if i % 2 else "B") for i in range(20)],
            seed=7,
            ratios=(0.60, 0.20, 0.20),
        )
        split_b = deterministic_stratified_split(
            [(f"q{i}", "A" if i % 2 else "B") for i in range(20)],
            seed=7,
            ratios=(0.60, 0.20, 0.20),
        )
        self.assertEqual(split_a, split_b)
        accepted = SelectionDecision.decide(
            candidate_id="new", incumbent_id="old", primary_metric="out_recall_at_100",
            candidate_score=0.22, incumbent_score=0.21,
        )
        tied = SelectionDecision.decide(
            candidate_id="tie", incumbent_id="old", primary_metric="out_recall_at_100",
            candidate_score=0.21, incumbent_score=0.21,
        )
        self.assertTrue(accepted.accepted)
        self.assertFalse(tied.accepted)


if __name__ == "__main__":
    unittest.main()
