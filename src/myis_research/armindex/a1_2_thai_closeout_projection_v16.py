"""Render one beginner-readable Thai A1.2 closeout projection from safe evidence."""

from __future__ import annotations

import argparse
import os
import re
import tempfile
from collections.abc import Mapping
from pathlib import Path

from .a1_2_measured_result_summary_v16 import (
    MeasuredResultSummaryV16Error,
    validate_measured_result_summary_file,
)
from .a1_2_terminal_attempt_v16 import (
    TerminalAttemptV16Error,
    validate_current_attempt_pointer,
)

_ATTEMPT = re.compile(r"^a12-v16-(?P<date>[0-9]{8})-(?P<retry>r[0-9]+)$")


class ThaiCloseoutProjectionV16Error(ValueError):
    """Raised when terminal evidence cannot support the Thai closeout report."""


def report_path(attempt_id: str) -> Path:
    match = _ATTEMPT.fullmatch(attempt_id)
    if match is None:
        raise ThaiCloseoutProjectionV16Error("attempt ID cannot form a report path")
    retry = match.group("retry").upper()
    return Path(
        f"docs/operations/A1_2_{retry}_MEASURED_CLOSEOUT_{match.group('date')}_TH.md"
    )


def _number(value: object, digits: int = 6) -> str:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ThaiCloseoutProjectionV16Error(
            "measured summary contains an invalid number"
        )
    return f"{float(value):.{digits}f}"


def build_thai_closeout_report(repository_root: Path) -> tuple[Path, str]:
    """Build deterministic Thai Markdown from the current validated PASS attempt."""

    root = repository_root.resolve(strict=True)
    try:
        current = validate_current_attempt_pointer(root)
        receipt = current["receipt"]
        if receipt.get("status") != "PASS":
            raise ThaiCloseoutProjectionV16Error("current A1.2 attempt is not PASS")
        summary = validate_measured_result_summary_file(root, receipt["attempt_id"])
    except (TerminalAttemptV16Error, MeasuredResultSummaryV16Error) as error:
        raise ThaiCloseoutProjectionV16Error(str(error)) from error
    lineage = summary.get("lineage")
    if not isinstance(lineage, Mapping) or any(
        lineage.get(summary_field) != receipt.get(receipt_field)
        for summary_field, receipt_field in (
            ("safe_return_archive_sha256", "safe_return_sha256"),
            ("promotion_receipt_sha256", "promotion_receipt_sha256"),
            ("evaluator_closeout_receipt_sha256", "evaluator_receipt_sha256"),
        )
    ):
        raise ThaiCloseoutProjectionV16Error(
            "measured summary does not bind the terminal receipt"
        )
    promoted = ", ".join(summary["promoted_arm_ids"])
    metric_rows = []
    for arm in summary["arm_results"]:
        metric_rows.append(
            "| {arm} | {recall} | {ndcg100} | {ndcg10} | {latency} | {wall} |".format(
                arm=arm["arm_id"],
                recall=_number(arm["out_recall_at_100_mean"]),
                ndcg100=_number(arm["out_ndcg_at_100_mean"]),
                ndcg10=_number(arm["out_ndcg_at_10_mean"]),
                latency=_number(arm["search_latency_p95_ms_mean"], 3),
                wall=_number(arm["wall_seconds_sum"], 3),
            )
        )
    target = report_path(receipt["attempt_id"])
    text = "\n".join(
        [
            "---",
            "managed_by: myis-a1.2-thai-closeout-v16",
            "edit_policy: generated_do_not_edit",
            "status: completed",
            "evidence_class: measured_development_aggregate",
            "scientific_authority: true",
            f"attempt_id: {receipt['attempt_id']}",
            f"source_summary_sha256: {summary['summary_sha256']}",
            f"source_terminal_sha256: {receipt['receipt_sha256']}",
            "---",
            "",
            "# รายงานปิด A1.2 ภาษาไทย",
            "",
            "เอกสารนี้สร้างอัตโนมัติจาก receipt ที่ผ่านการตรวจสอบแล้ว ห้ามแก้ตัวเลขด้วยมือ",
            "เพราะ canonical JSON เป็นแหล่งตัวเลขเพียงแห่งเดียว",
            "",
            "## สรุปสำหรับ Owner",
            "",
            "- สถานะ A1 / A1.2: `COMPLETE` / `PASS 25/25`",
            f"- ค่าใช้จ่ายของ A1 attempt นี้: `${receipt['final_charge_usd']}`",
            f"- สถานะ instance หลังปิด A1: `{receipt['provider_disposition_status']}`",
            f"- Arms ที่ผ่าน frozen promotion rule: `{promoted}`",
            "- A2, HARNESS-DEV, Selection และ Final: ยังไม่เริ่ม",
            "",
            "## Metric ที่วัดได้",
            "",
            "Primary metric คือ `OUT Recall@100` หมายถึงสัดส่วน family ที่เกี่ยวข้องซึ่งพบภายใน 100 อันดับแรก",
            "Secondary metrics คือ `OUT nDCG@100` และ `OUT nDCG@10` ซึ่งสะท้อนคุณภาพการจัดลำดับผลลัพธ์",
            "ค่าด้านล่างเป็นค่าเฉลี่ยจาก common programs 5 แบบต่อ arm ส่วน wall time เป็นผลรวมของทั้ง 5 programs",
            "",
            "| Arm | OUT Recall@100 | OUT nDCG@100 | OUT nDCG@10 | Search p95 ms | Wall seconds |",
            "|---|---:|---:|---:|---:|---:|",
            *metric_rows,
            "",
            "## การตีความที่อนุญาต",
            "",
            "ผลนี้ใช้เปรียบเทียบ retriever arms บน REP-DEV ภายใต้ frozen A1 contract ได้",
            "และใช้กำหนด promoted-arm set สำหรับเตรียม A2 เท่านั้น ยังไม่ใช่ผลยืนยันบน Final split",
            "ผลนี้ไม่ใช่ข้อสรุปด้าน novelty, validity, infringement หรือ freedom to operate ทางกฎหมาย",
            "",
            "## หลักฐาน",
            "",
            f"- Measured summary: `{summary['summary_uri']}`",
            f"- Terminal receipt: `{current['pointer']['target_uri']}`",
            "- Current pointer: `campaigns/armindex-multiretriever-v2/evidence/a1.2-current-attempt.v16.json`",
            "",
            "## ขั้นตอนถัดไป",
            "",
            "หยุดก่อน A2 งาน A2 ต้องผ่าน entry preflight, fresh provider admission และ fresh execution adoption",
            "รวมทั้งใช้ remote root ใหม่ที่แยกจาก A1 โดยยังเก็บ A1 artifacts เดิมไว้แบบ read-only",
            "",
        ]
    )
    return target, text


def write_thai_closeout_report(repository_root: Path) -> Path:
    root = repository_root.resolve(strict=True)
    relative, text = build_thai_closeout_report(root)
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = text.encode("utf-8")
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    return path


def main() -> int:
    parser = argparse.ArgumentParser(prog="myis-a1.2-thai-closeout-v16")
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    args = parser.parse_args()
    try:
        path = write_thai_closeout_report(args.repository_root)
    except (OSError, ThaiCloseoutProjectionV16Error) as error:
        parser.error(str(error))
    print(path.relative_to(args.repository_root.resolve()).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "ThaiCloseoutProjectionV16Error",
    "build_thai_closeout_report",
    "main",
    "report_path",
    "write_thai_closeout_report",
]
