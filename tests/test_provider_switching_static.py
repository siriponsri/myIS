from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_provider_launchers_are_secret_free_and_fail_closed() -> None:
    scripts = [
        ROOT / "scripts/dev/check-codex-profile.ps1",
        ROOT / "scripts/dev/start-codex-official.ps1",
        ROOT / "scripts/dev/start-codex-maxplus.ps1",
    ]
    for path in scripts:
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        assert "auth.json" not in lowered
        assert "api_key=" not in lowered
        assert "bearer " not in lowered
        assert "whatif" in lowered
        assert "copy-item" not in lowered
        if path.name.startswith("start-codex"):
            assert "myis_store" in lowered and "myis_mlflow_store" in lowered
            assert "remove-item" in lowered
        if path.name == "check-codex-profile.ps1":
            assert "trimend" in lowered
            assert "ordinalignorecase" in lowered


def test_provider_doc_keeps_machine_state_outside_repository() -> None:
    text = (ROOT / "docs/CODEX_PROVIDER_SWITCHING.md").read_text(encoding="utf-8")
    assert "$HOME\\.codex-official" in text
    assert "$HOME\\.codex-maxplus" in text
    assert "scientific evidence" in text.lower()
    assert "`auth.json`" in text
    assert "protected" in text.lower()
