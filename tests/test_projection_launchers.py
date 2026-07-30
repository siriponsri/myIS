from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_projection_launchers_are_separate_and_point_to_active_root():
    launchers = {
        "open-dashboard.cmd": "myis-dashboard",
        "open-mlflow.cmd": "readonly_app.py serve",
        "open-obsidian-report.cmd": "myis-report sync",
    }
    for name, marker in launchers.items():
        path = ROOT / "projections" / name
        text = path.read_text(encoding="utf-8")
        assert text.lower().startswith("@echo off")
        assert marker in text
        assert "05_code" not in text
        assert "06_frontend" not in text
