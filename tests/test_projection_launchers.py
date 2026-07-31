from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_only_unified_dashboard_launcher_remains_after_acceptance():
    launchers = {
        "open-dashboard.cmd": "myis-dashboard",
        "open-mlflow.cmd": "readonly_app.py serve",
        "open-obsidian-report.cmd": "myis-report sync",
    }
    for name, marker in launchers.items():
        assert not (ROOT / "projections" / name).exists()
        archived = ROOT / "archive" / "p1-recovery-20260730" / "legacy-launchers" / f"{name}.txt"
        text = archived.read_text(encoding="utf-8")
        assert text.lower().startswith("@echo off")
        assert marker in text
    unified = ROOT / "dashboard" / "open-dashboard.cmd"
    assert unified.is_file()
    assert "myis_research.dashboard.launcher" in unified.read_text(encoding="utf-8")
