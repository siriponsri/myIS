from __future__ import annotations

import json
from pathlib import Path

from myis_research.projections.read_model import build_read_model, write_read_model


def test_empty_campaign_read_model_is_safe(tmp_path: Path) -> None:
    (tmp_path / "control" / "campaigns").mkdir(parents=True)
    (tmp_path / "control" / "decisions").mkdir(parents=True)
    (tmp_path / "control" / "campaigns" / "scope-autoindex-v1.yaml").write_text("campaign:\n  status: preparation\n", encoding="utf-8")
    (tmp_path / "control" / "decisions" / "ledger.jsonl").write_text("", encoding="utf-8")
    model = build_read_model(tmp_path)
    assert model["schema_version"] == "myis.read-model.v1"
    assert model["publication_readiness"]["status"] == "blocked"
    output = write_read_model(tmp_path)
    assert json.loads(output.read_text(encoding="utf-8"))["projection_revision"] == model["projection_revision"]
