from __future__ import annotations

from pathlib import Path

from test_armindex_a1_2_terminal_attempt_v16 import (
    _receipt,
    _root,
    _write_current,
    _write_measured_summary,
)

from myis_research.armindex.a1_2_thai_closeout_projection_v16 import (
    build_thai_closeout_report,
    write_thai_closeout_report,
)


def test_builds_beginner_thai_report_from_canonical_summary(tmp_path: Path) -> None:
    root = _root(tmp_path)
    receipt = _receipt(root, status="PASS", completed=25)
    _write_current(root, receipt)
    _write_measured_summary(root, str(receipt["attempt_id"]))

    relative, text = build_thai_closeout_report(root)

    assert relative.as_posix().endswith("A1_2_R14_MEASURED_CLOSEOUT_20260811_TH.md")
    assert "PASS 25/25" in text
    assert "OUT Recall@100" in text
    assert "ARM-01, ARM-02, ARM-03" in text
    assert "# รายงานปิด A1.2 ภาษาไทย" in text
    assert "## สรุปสำหรับ Owner" in text
    assert "ยังไม่ใช่ผลยืนยันบน Final split" in text
    assert "เธฃ" not in text and "เน€" not in text
    assert "Q-" not in text and "F-" not in text
    path = write_thai_closeout_report(root)
    assert path.read_text(encoding="utf-8") == text
