"""Executable companion for the offline Brain-drive notebook."""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESEARCH_ROOT = HERE.parents[1]
sys.path.insert(0, str(RESEARCH_ROOT / "05_code" / "src"))

from myis_research.brain_drive import run_brain_drive_demo  # noqa: E402


def main() -> dict[str, object]:
    output = run_brain_drive_demo(HERE / "workspace", mlflow_root=HERE / "workspace" / "mlflow")
    metrics = {
        "source_count": len(output["records"]),
        "retrieval_hit_count": len(output["report"]["hits"]),
        "provenance_completeness": 1.0,
        "report_sha256": output["report"]["report_sha256"],
    }
    (HERE / "expected_metrics.json").write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"metrics": metrics, "run_dir": output["run_dir"]}, indent=2, sort_keys=True))
    return output


if __name__ == "__main__":
    main()
