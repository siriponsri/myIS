"""Immutable HarnessOpt kernel and its public adapter methods."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Protocol

from .logging import RunLogger, redact
from .manifest import finalize_manifest, write_json, write_mlflow_receipt
from .models import GoalState, RunResult, RunSpec, RunState
from .policy import HarnessPolicy
from .validation import validate_run_bundle
from ..mlflow_mirror import MLflowMirror, MirrorArtifact, MirrorKind, MirrorSpec, MirrorStage


KERNEL_VERSION = "myis-harness-kernel.v1"


class HarnessAdapter(Protocol):
    """External engines expose these methods through a governed adapter."""

    def preflight(self, spec: RunSpec, policy: HarnessPolicy) -> dict[str, Any]: ...
    def dry_run(self, spec: RunSpec, policy: HarnessPolicy) -> dict[str, Any]: ...
    def execute(self, spec: RunSpec, policy: HarnessPolicy, **kwargs: Any) -> RunResult: ...
    def cancel(self, run_id: str, reason: str) -> dict[str, Any]: ...
    def collect(self, run_id: str) -> RunResult: ...


Executor = Callable[[RunSpec, HarnessPolicy, RunLogger], dict[str, Any]]


class LocalHarness:
    """Fail-closed local kernel; only ``HarnessPolicy`` may evolve."""

    def __init__(self, run_root: Path, *, module_allowlist: set[str] | None = None, mlflow_root: Path | None = None):
        self.run_root = run_root
        self.module_allowlist = module_allowlist or {"lexical", "dense"}
        self.mlflow_root = mlflow_root
        self._cancelled: dict[str, str] = {}

    def preflight(self, spec: RunSpec, policy: HarnessPolicy) -> dict[str, Any]:
        policy.validate(self.module_allowlist)
        errors = []
        try:
            spec.validate_active_contract()
        except ValueError as error:
            errors.append(str(error))
        if spec.kernel_version != KERNEL_VERSION:
            errors.append("kernel_version mismatch")
        if spec.policy_hash != policy.sha256:
            errors.append("policy_hash mismatch")
        if spec.goal.state not in {GoalState.APPROVED, GoalState.ACTIVE}:
            errors.append("goal is not approved or active")
        if spec.approval.scope_hash != spec.scope_hash():
            errors.append("approval scope hash mismatch")
        if spec.split.lower() in {"confirmation", "held-out", "test"} and not spec.approval.held_out_allowed:
            errors.append("confirmation/held-out split requires a separate approval")
        if not spec.evaluator_hash or len(spec.evaluator_hash) != 64:
            errors.append("evaluator_hash must be SHA-256")
        if not spec.split_query_ids_hash or len(spec.split_query_ids_hash) != 64:
            errors.append("split_query_ids_hash must be SHA-256")
        if any(float(value) < 0 for value in spec.budget.values()):
            errors.append("budget values must be non-negative")
        measured = not spec.phase.startswith(("offline", "bootstrap", "fixture"))
        if measured and spec.isolation is None:
            errors.append("measured optimization requires offline execution isolation")
        if spec.isolation is not None:
            try:
                spec.isolation.validate()
            except ValueError as error:
                errors.append(str(error))
        if spec.run_id in self._cancelled:
            errors.append("run is cancelled")
        if errors:
            raise PermissionError("; ".join(errors))
        return {
            "status": "PREFLIGHTED",
            "run_id": spec.run_id,
            "kernel_immutable": True,
            "evaluator_immutable": True,
            "policy_hash": policy.sha256,
            "split_query_ids_hash": spec.split_query_ids_hash,
        }

    def dry_run(self, spec: RunSpec, policy: HarnessPolicy) -> dict[str, Any]:
        preflight = self.preflight(spec, policy)
        return {
            **preflight,
            "status": "DRY_RUN",
            "planned_artifacts": [
                "prompt.json",
                "flow.json",
                "progress.jsonl",
                "result.json",
                "metrics.json",
                "runtime.jsonl",
                "per_query_metrics.jsonl",
                "validation_report.json",
                "manifest.json",
            ],
            "mlflow_mode": "local-mirror-with-receipt",
        }

    def execute(
        self,
        spec: RunSpec,
        policy: HarnessPolicy,
        *,
        executor: Executor,
        prompt_record: dict[str, Any],
        flow_record: dict[str, Any],
    ) -> RunResult:
        self.preflight(spec, policy)
        self.run_root.mkdir(parents=True, exist_ok=True)
        run_dir = self.run_root / spec.run_id
        run_dir.mkdir(exist_ok=False)
        started = datetime.now(timezone.utc).isoformat()
        state = RunState.PREFLIGHTED
        metrics: dict[str, float] = {}
        budget_actual: dict[str, float | int] = {name: 0 for name in spec.budget}
        stop_reason: str | None = None
        caught: BaseException | None = None

        with RunLogger(run_dir, run_id=spec.run_id, goal_id=spec.goal.goal_id, phase=spec.phase) as logger:
            logger.emit("run.preflighted", status=state.value, milestone=True, split=spec.split)
            state = RunState.RUNNING
            logger.emit(
                "run.started",
                status=state.value,
                milestone=True,
                arm=spec.arm,
                git_commit=spec.git_commit,
                config_hash=spec.config_hash,
                prompt_hash=spec.prompt_hash,
                skill_set_hash=spec.skill_set_hash,
                dataset_manifest_hash=spec.dataset_manifest_hash,
                split=spec.split,
            )
            write_json(run_dir / "prompt.json", redact(prompt_record))
            write_json(run_dir / "flow.json", redact(flow_record))
            try:
                payload = executor(spec, policy, logger)
                result_payload = payload.get("result", {})
                metrics = {str(key): float(value) for key, value in payload.get("metrics", {}).items()}
                budget_actual = {
                    str(key): value for key, value in payload.get("budget_actual", budget_actual).items()
                }
                for name, limit in spec.budget.items():
                    actual = float(budget_actual.get(name, 0))
                    logger.emit(
                        "budget.updated",
                        status=state.value,
                        budget_name=name,
                        budget_limit=limit,
                        budget_actual=actual,
                    )
                    if actual > float(limit):
                        logger.emit(
                            "budget.exceeded",
                            status=state.value,
                            level="error",
                            milestone=True,
                            budget_name=name,
                            budget_limit=limit,
                            budget_actual=actual,
                        )
                        raise RuntimeError(f"budget exceeded: {name}")
                per_query = payload.get("per_query", [])
                write_json(run_dir / "result.json", result_payload)
                write_json(run_dir / "metrics.json", metrics)
                with (run_dir / "per_query_metrics.jsonl").open("x", encoding="utf-8") as stream:
                    for row in per_query:
                        stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
                for metric_name, value in metrics.items():
                    logger.emit("metric.recorded", status=state.value, metric_name=metric_name, metric_value=value)
                state = RunState.SUCCEEDED
                logger.emit("run.succeeded", status=state.value, milestone=True)
            except BaseException as error:  # preserve failed/interrupted evidence before re-raising
                caught = error
                state = RunState.CANCELLED if isinstance(error, KeyboardInterrupt) else RunState.FAILED
                stop_reason = "keyboard_interrupt" if isinstance(error, KeyboardInterrupt) else "executor_error"
                if not (run_dir / "result.json").exists():
                    write_json(
                        run_dir / "result.json",
                        {"status": state.value, "error": redact({"type": type(error).__name__, "message": str(error)})},
                    )
                if not (run_dir / "metrics.json").exists():
                    write_json(run_dir / "metrics.json", metrics)
                if not (run_dir / "per_query_metrics.jsonl").exists():
                    (run_dir / "per_query_metrics.jsonl").touch()
                logger.emit(
                    "run.interrupted" if isinstance(error, KeyboardInterrupt) else "run.failed",
                    status=state.value,
                    level="error",
                    milestone=True,
                    error=redact(
                        {
                            "code": "EXECUTOR_ERROR",
                            "type": type(error).__name__,
                            "message": str(error),
                            "retryable": False,
                        }
                    ),
                )

        finished = datetime.now(timezone.utc).isoformat()
        write_json(
            run_dir / "validation_report.json",
            {
                "schema_version": "myis.validation-report.v1",
                "pre_manifest_checks": "PASS",
                "split_hash": spec.split_query_ids_hash,
                "policy_hash": policy.sha256,
                "status": state.value,
            },
        )
        manifest_sha = finalize_manifest(
            run_dir,
            spec,
            status=state.value,
            started_at_utc=started,
            finished_at_utc=finished,
            metrics=metrics,
            budget_actual=budget_actual,
            stop_reason=stop_reason,
        )
        validation = validate_run_bundle(run_dir, expected_split_hash=spec.split_query_ids_hash)
        self._mirror_mlflow(run_dir, spec, metrics, manifest_sha, validation)
        result = RunResult(spec.run_id, state, run_dir, metrics, manifest_sha, stop_reason)
        if caught is not None:
            caught.add_note(f"myIS failed run bundle: {run_dir}")
            raise caught
        return result

    def _mirror_mlflow(
        self,
        run_dir: Path,
        spec: RunSpec,
        metrics: dict[str, float],
        manifest_sha: str,
        validation: dict[str, Any],
    ) -> None:
        receipt: dict[str, Any] = {
            "receipt_id": "initial",
            "run_id": spec.run_id,
            "manifest_sha256": manifest_sha,
            "validation": validation["status"],
        }
        if self.mlflow_root is None:
            receipt.update({"status": "sync_deferred", "reason": "mlflow_root_not_configured"})
            write_mlflow_receipt(run_dir, receipt)
            return
        try:
            selected = (
                MirrorArtifact.from_path(run_dir / "manifest.json", kind=MirrorKind.RESULT, canonical_root=run_dir),
                MirrorArtifact.from_path(
                    run_dir / "validation_report.json", kind=MirrorKind.RESULT, canonical_root=run_dir
                ),
                MirrorArtifact.from_path(run_dir / "result.json", kind=MirrorKind.RESULT, canonical_root=run_dir),
                MirrorArtifact.from_path(run_dir / "metrics.json", kind=MirrorKind.METRIC, canonical_root=run_dir),
            )
            MLflowMirror(self.mlflow_root).sync(
                MirrorSpec(
                    stage=MirrorStage.TRACK_C,
                    run_name=spec.run_id,
                    git_commit=spec.git_commit,
                    canonical_source_sha256=manifest_sha,
                    tags={
                        "goal_id": spec.goal.goal_id,
                        "arm": spec.arm,
                        "phase": spec.phase,
                        "owner_approval_id": spec.approval.approval_id,
                    },
                    parameters={
                        "dataset_id": spec.dataset_id,
                        "split": spec.split,
                        "seed": spec.seed,
                        "model_id": spec.model_id,
                        "evaluator_id": spec.evaluator_id,
                    },
                    metrics=metrics,
                ),
                selected,
                receipt_dir=run_dir / "receipts",
            )
        except Exception as error:
            receipt.update(
                {
                    "status": "sync_deferred",
                    "reason": "mlflow_projection_error",
                    "error_type": type(error).__name__,
                    "error_hash": hashlib.sha256(str(error).encode("utf-8")).hexdigest(),
                }
            )
            write_mlflow_receipt(run_dir, receipt)

    def cancel(self, run_id: str, reason: str) -> dict[str, Any]:
        if not reason.strip():
            raise ValueError("cancellation reason is required")
        self._cancelled[run_id] = reason
        return {"run_id": run_id, "status": RunState.CANCELLED.value, "reason": reason}

    def collect(self, run_id: str) -> RunResult:
        run_dir = self.run_root / run_id
        validation = validate_run_bundle(run_dir)
        manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
        metrics = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))
        return RunResult(
            run_id=run_id,
            state=RunState(manifest["lifecycle"]["status"]),
            run_dir=run_dir,
            metrics=metrics,
            manifest_sha256=validation["manifest_sha256"],
            stop_reason=manifest["lifecycle"].get("stop_reason"),
        )
