from __future__ import annotations

import io
import json
import tarfile
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from myis_research.armindex.a1_2_safe_return_v16 import (
    ARM_IDS,
    PROGRAM_IDS,
    SafeReturnV16Error,
    validate_safe_return_archive,
)
from myis_research.kernel.canonical import canonical_sha256


def _tokens(prefix: str, count: int) -> list[str]:
    return [f"{prefix}-{index:032x}" for index in range(count)]


def _archive(tmp_path: Path, *, mutate: str | None = None) -> Path:
    attempt = "a12-v16-safe-test"
    work = _tokens("Q", 150)
    families = _tokens("F", 100)
    payloads: dict[str, bytes] = {}
    specs: list[dict[str, object]] = []
    for arm in ARM_IDS:
        for program in PROGRAM_IDS:
            ranking_name = f"rankings/{arm}--{program.replace('-', '_')}.jsonl"
            rows = []
            for token in work:
                row: dict[str, object] = {"work_token": token, "family_tokens": families}
                if mutate == "score" and not rows and arm == "ARM-01" and program == PROGRAM_IDS[0]:
                    row["score"] = 0.1
                if mutate == "duplicate" and not rows and arm == "ARM-01" and program == PROGRAM_IDS[0]:
                    row["family_tokens"] = families[:-1] + [families[0]]
                rows.append(json.dumps(row, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
            payloads[ranking_name] = ("\n".join(rows) + "\n").encode("ascii")
            specs.append({"kind": "ranking", "arm_id": arm, "program_id": program, "relative_path": ranking_name, "sha256": __import__("hashlib").sha256(payloads[ranking_name]).hexdigest(), "size_bytes": len(payloads[ranking_name])})
            receipt_name = f"receipts/{arm}--{program.replace('-', '_')}.json"
            body = {"schema_version": "myis.armindex-a1.2-safe-return-resource-receipt.v16", "attempt_id": attempt, "arm_id": arm, "program_id": program, "status": "PASS", "checkpoint_sha256": "a" * 64, "ranking_sha256": specs[-1]["sha256"]}
            receipt = {**body, "receipt_sha256": canonical_sha256(body)}
            payloads[receipt_name] = (json.dumps(receipt, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")
            specs.append({"kind": "receipt", "arm_id": arm, "program_id": program, "relative_path": receipt_name, "sha256": __import__("hashlib").sha256(payloads[receipt_name]).hexdigest(), "size_bytes": len(payloads[receipt_name])})
    if mutate == "missing":
        payloads.pop("rankings/ARM-05--P04_SECTION_MULTIVIEW.jsonl")
        specs = [item for item in specs if item["relative_path"] != "rankings/ARM-05--P04_SECTION_MULTIVIEW.jsonl"]
    if mutate == "tamper":
        name = "rankings/ARM-02--P00_TAC_DOC.jsonl"
        payloads[name] = payloads[name].replace(b"Q-", b"X-", 1)
    manifest_body = {"schema_version": "myis.armindex-a1.2-safe-return-manifest.v16", "attempt_id": attempt, "status": "PASS", "transfer_manifest_sha256": "b" * 64, "split_commitment_sha256": "c" * 64, "ephemeral_token_map_sha256": "d" * 64, "work_token_set_sha256": canonical_sha256({"work_tokens": work}), "members": specs}
    manifest = {**manifest_body, "manifest_sha256": canonical_sha256(manifest_body)}
    payloads["safe-return-manifest.v16.json"] = (json.dumps(manifest, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")
    if mutate == "extra":
        payloads["logs/leak.txt"] = b"query_id=original"
    archive = tmp_path / "safe-return.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        for name, data in payloads.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return archive


def test_v16_safe_return_validates_exact_25_cells_and_aggregate_shape(tmp_path: Path) -> None:
    result = validate_safe_return_archive(_archive(tmp_path))
    assert result["status"] == "PASS"
    assert result["cells"] == 25 and result["rows"] == 150 and result["top_k"] == 100


@pytest.mark.parametrize("mutate", ["score", "duplicate", "missing", "tamper", "extra"])
def test_v16_safe_return_rejects_malicious_or_incomplete_content(tmp_path: Path, mutate: str) -> None:
    with pytest.raises(SafeReturnV16Error):
        validate_safe_return_archive(_archive(tmp_path, mutate=mutate))


def test_v16_watchdog_pins_attempt_known_hosts_and_requires_strict_checking() -> None:
    source = Path("scripts/a1_2_vast/Invoke-A12GovernedWatchdogV16.ps1").read_text(encoding="utf-8")
    assert "attempt-known_hosts" in source
    assert "StrictHostKeyChecking=yes" in source
    assert "UserKnownHostsFile=$knownHostsPath" in source
    assert "StrictHostKeyChecking=no" not in source
    assert "UserKnownHostsFile=NUL" not in source
    assert "ssh_keyscan_failed" in source and "ssh_fingerprint_mismatch" in source
    assert "$raw | & $sshKeygen -lf - -E sha256" in source
    assert "python - <<'PY'" in source
    assert "platform.machine() == 'x86_64'" in source
    assert "ssh_runtime_probe_failed" in source and "provider_query_failed" in source
    assert "probeStage" in source and "watchdog_${probeStage}_failed" in source
    assert "OwnerDashboardSsh" in source
    assert "OwnerDashboardEvidenceSha256" in source
    assert "OwnerManualDestroyReady" in source
    assert "provider_authenticated = ($ProviderObservationMode -eq 'AuthenticatedCli')" in source
    assert "gpu_uuid_set_sha256" in source and "runtime_identity_mismatch" in source
    assert "& $VastCliPath show instance $InstanceId --raw" in source
    assert "& $VastCliPath vastai show instance" not in source


@pytest.mark.parametrize("member_name,member_type", [("../escape", tarfile.REGTYPE), ("rankings/link.jsonl", tarfile.SYMTYPE)])
def test_v16_safe_return_rejects_traversal_and_nonregular_members(tmp_path: Path, member_name: str, member_type: bytes) -> None:
    archive = tmp_path / "unsafe.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        info = tarfile.TarInfo(member_name)
        info.type = member_type
        info.linkname = "target"
        info.size = 0
        tar.addfile(info)
    with pytest.raises(SafeReturnV16Error):
        validate_safe_return_archive(archive)


def test_v16_safe_return_rejects_oversized_member(tmp_path: Path) -> None:
    archive = tmp_path / "oversized.tar.gz"
    data = b"x" * (1024 * 1024 + 1)
    with tarfile.open(archive, "w:gz") as tar:
        info = tarfile.TarInfo("rankings/ARM-01--P00_TAC_DOC.jsonl")
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
    with pytest.raises(SafeReturnV16Error, match="size limit"):
        validate_safe_return_archive(archive)


def test_v16_safe_return_contract_is_self_hashed_and_schema_valid() -> None:
    root = Path("control/armindex/a1.2/scientific-safe-return-contract.v16.json")
    schema_path = Path("schemas/armindex/a1.2-scientific-safe-return-contract.v16.json")
    value = json.loads(root.read_text(encoding="utf-8"))
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    assert not list(Draft202012Validator(schema).iter_errors(value))
    assert value["contract_sha256"] == canonical_sha256({key: item for key, item in value.items() if key != "contract_sha256"})
