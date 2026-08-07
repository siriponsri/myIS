from __future__ import annotations

import json
import tarfile
from pathlib import Path

import numpy as np
import pytest

from myis_research.armindex.a1_2_live_preflight_runtime_v9 import (
    IMAGE_DIGEST,
    LiveRuntimeV9Error,
    attempt_status,
    build_safe_export,
    complete_attempt,
    initialize_attempt,
    measure_qwen_max_length,
    run_checkpoint_worker,
    summarize_attempt,
    teardown_attempt,
    validate_safe_export_archive,
    validate_verification_marker,
    write_verification_marker,
)
from myis_research.kernel.canonical import canonical_sha256


def _identity(path: Path) -> Path:
    body = {
        "schema_version": "myis.armindex-a1.2-live-runtime-identity.v6",
        "status": "PASS",
        "expected_manifest_digest": IMAGE_DIGEST,
        "bundle_sha256": "b" * 64,
    }
    path.write_text(
        json.dumps({**body, "receipt_sha256": canonical_sha256(body)}, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _marker(path: Path) -> Path:
    write_verification_marker(
        path,
        expected_commit="a" * 40,
        expected_tree="c" * 40,
        expected_manifest_digest=IMAGE_DIGEST,
        expected_bundle_sha256="b" * 64,
        runtime_identity_path=_identity(path.parent / "runtime.json"),
    )
    return path


def _attempt(tmp_path: Path) -> tuple[Path, str, Path]:
    output = tmp_path / "output"
    marker = _marker(tmp_path / "marker.json")
    attempt_id = "synthetic-v9-attempt"
    initialize_attempt(output, attempt_id, marker)
    return output, attempt_id, marker


def _write_receipt(path: Path, body: dict[str, object], field: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({**body, field: canonical_sha256(body)}, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _stage_summary_evidence(output: Path, attempt_id: str) -> Path:
    directory = output / "attempts" / attempt_id
    for arm in ("ARM-02", "ARM-03", "ARM-04", "ARM-05"):
        adapter = {
            "schema_version": "synthetic-adapter-test",
            "attempt_id": attempt_id,
            "arm_id": arm,
            "status": "PASS",
        }
        if arm == "ARM-05":
            adapter["qwen_adapter_maximum"] = {
                "measured_adapter_max_input_tokens": 8192
            }
        _write_receipt(
            directory / "preflight" / "adapters" / f"{arm}.json",
            adapter,
            "receipt_sha256",
        )
        _write_receipt(
            directory / "runtime-receipts" / f"{arm}.json",
            {
                "schema_version": "synthetic-worker-test",
                "attempt_id": attempt_id,
                "arm_id": arm,
                "status": "PASS",
                "resumed_after_injected_failure": arm == "ARM-02",
            },
            "receipt_sha256",
        )
    _write_receipt(
        directory / "failure-receipts" / "ARM-02.injected.json",
        {
            "schema_version": "myis.armindex-a1.2-live-injected-failure.v9",
            "attempt_id": attempt_id,
            "arm_id": "ARM-02",
            "failed_before_step": 1,
            "checkpoint_written_for_failed_step": False,
            "status": "EXPECTED_FAILURE",
        },
        "receipt_sha256",
    )
    _write_receipt(
        directory / "steps" / "arm-02-step-1.json",
        {
            "schema_version": "myis.armindex-a1.2-live-step-checkpoint.v9",
            "attempt_id": attempt_id,
            "step_id": "arm-02-step-1",
            "status": "COMPLETE",
            "artifacts": [{"uri": "synthetic", "sha256": "d" * 64}],
        },
        "checkpoint_sha256",
    )
    summarize_attempt(output, attempt_id)
    return directory


def test_v9_marker_is_runtime_bound_and_launch_locked(tmp_path: Path) -> None:
    marker = _marker(tmp_path / "marker.json")
    value = validate_verification_marker(
        marker,
        expected_commit="a" * 40,
        expected_tree="c" * 40,
        expected_manifest_digest=IMAGE_DIGEST,
        expected_bundle_sha256="b" * 64,
    )
    assert value["status"] == "PASS"
    assert value["launch_allowed"] is False
    assert value["adopted_for_execution"] is False
    with pytest.raises(LiveRuntimeV9Error, match="identity mismatch"):
        validate_verification_marker(marker, expected_bundle_sha256="e" * 64)


def test_v9_failed_step_has_no_checkpoint_then_resume_completes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    output, attempt_id, _marker_path = _attempt(tmp_path)
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "0")
    with pytest.raises(LiveRuntimeV9Error, match="injected failure"):
        run_checkpoint_worker(
            output_root=output,
            attempt_id=attempt_id,
            arm_id="ARM-02",
            fail_before_step=1,
        )
    directory = output / "attempts" / attempt_id
    assert not (directory / "steps" / "arm-02-step-1.json").exists()
    receipt = run_checkpoint_worker(output_root=output, attempt_id=attempt_id, arm_id="ARM-02")
    assert receipt["resumed_after_injected_failure"] is True
    assert (directory / "steps" / "arm-02-step-1.json").is_file()


class _FakeOom(RuntimeError):
    pass


class _FakeCuda:
    OutOfMemoryError = _FakeOom

    def empty_cache(self) -> None:
        pass

    def reset_peak_memory_stats(self) -> None:
        pass

    def synchronize(self) -> None:
        pass

    def max_memory_allocated(self) -> int:
        return 1234

    def max_memory_reserved(self) -> int:
        return 2345


class _FakeTorch:
    cuda = _FakeCuda()


class _Mask:
    def __init__(self, count: int) -> None:
        self.count = count

    def sum(self) -> int:
        return self.count


class _FrozenAdapter:
    def __init__(self) -> None:
        self.max_seq_length = 32768
        self.calls: list[dict[str, object]] = []

    def tokenize(self, values: list[str]) -> dict[str, _Mask]:
        count = min(len(values[0].split()), self.max_seq_length)
        return {"attention_mask": _Mask(count)}

    def encode(self, values: list[str], **kwargs: object) -> np.ndarray:
        self.calls.append({"values": values, **kwargs})
        if self.max_seq_length > 8192:
            raise _FakeOom("synthetic oom")
        return np.full((1, 1024), 1 / np.sqrt(1024), dtype=np.float32)


def test_v9_qwen_uses_exact_adapter_tokens_and_encode_only() -> None:
    adapter = _FrozenAdapter()
    value = measure_qwen_max_length(
        adapter,
        pooling_sha256="d" * 64,
        torch_module=_FakeTorch(),
        candidate_token_counts=(8192, 16384),
    )
    assert value["adapter_path"] == "sentence_transformer_encode"
    assert value["measured_adapter_max_input_tokens"] == 8192
    assert value["first_oom_adapter_input_tokens"] == 16384
    assert value["attempts"][0]["actual_tokens"] == 8192
    assert all(call["batch_size"] == 1 and call["normalize_embeddings"] is True for call in adapter.calls)


def test_v9_safe_export_is_attempt_bound_and_teardown_preserves_complete(tmp_path: Path) -> None:
    output, attempt_id, marker_path = _attempt(tmp_path)
    directory = _stage_summary_evidence(output, attempt_id)
    complete_attempt(output, attempt_id, directory / "summary.json")
    archive = output / "exports" / f"{attempt_id}.safe-export.tar.gz"
    with pytest.raises(LiveRuntimeV9Error, match="reaped teardown receipt"):
        build_safe_export(output, attempt_id, archive)
    teardown = teardown_attempt(output, attempt_id, children_reaped=True)
    assert teardown["children_reaped"] is True
    receipt = build_safe_export(output, attempt_id, archive)
    assert receipt["status"] == "PASS"
    assert validate_safe_export_archive(archive)["status"] == "PASS"
    assert build_safe_export(output, attempt_id, archive) == receipt
    with tarfile.open(archive, "r:gz") as value:
        assert "teardown.json" in value.getnames()
    assert attempt_status(output, attempt_id, require_pass=True)["status"] == "COMPLETE"


def test_v9_completion_rejects_tampered_injected_failure_receipt(tmp_path: Path) -> None:
    output, attempt_id, _marker_path = _attempt(tmp_path)
    directory = _stage_summary_evidence(output, attempt_id)
    failure_path = directory / "failure-receipts" / "ARM-02.injected.json"
    failure = json.loads(failure_path.read_text(encoding="utf-8"))
    failure["attempt_id"] = "different-attempt"
    failure_path.write_text(json.dumps(failure, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(LiveRuntimeV9Error, match="evidence-bound PASS"):
        complete_attempt(output, attempt_id, directory / "summary.json")


def test_v9_completion_rejects_minimal_forged_summary(tmp_path: Path) -> None:
    output, attempt_id, marker_path = _attempt(tmp_path)
    directory = output / "attempts" / attempt_id
    marker = validate_verification_marker(marker_path)
    summary_body = {
        "schema_version": "myis.armindex-a1.2-live-preflight-summary.v9",
        "attempt_id": attempt_id,
        "verification_marker_sha256": marker["marker_sha256"],
        "status": "PASS",
    }
    _write_receipt(directory / "summary.json", summary_body, "summary_sha256")
    with pytest.raises(LiveRuntimeV9Error, match="evidence-bound PASS"):
        complete_attempt(output, attempt_id, directory / "summary.json")


def test_v9_launcher_has_immediate_failure_cleanup_and_no_measured_path() -> None:
    root = Path(__file__).resolve().parents[1]
    script = (root / "scripts/a1_2_vast/remote-live-preflight-v9.sh").read_text(encoding="utf-8")
    assert "wait -n -p finished" not in script
    assert "ps -o stat=" in script
    assert "completed[\"${pid}\"]" in script
    assert "trap cleanup EXIT INT TERM" in script
    assert "kill -TERM" in script and "record-process-exit" in script
    assert "CUDA_VISIBLE_DEVICES" in script
    assert "measured" not in script.casefold()
