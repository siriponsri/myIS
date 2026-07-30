from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_projection_launchers_are_separate_and_point_to_active_root():
    launchers = {
        "start-dashboard.sh": "myis-dashboard",
        "start-mlflow.sh": "dashboard/mlflow/mlflow.sh",
        "start-obsidian-report.sh": "myis-report sync",
    }
    for name, marker in launchers.items():
        path = ROOT / "projections" / name
        text = path.read_text(encoding="utf-8")
        assert text.startswith("#!/usr/bin/env bash")
        assert marker in text
        assert "05_code" not in text
        assert "06_frontend" not in text
