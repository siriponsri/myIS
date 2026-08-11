from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "scripts/a1_2_vast/vastai-raw-compat-v16.cmd"


def test_vastai_compat_wrapper_is_read_only_and_fail_closed() -> None:
    text = WRAPPER.read_text(encoding="ascii")
    assert 'if /I not "%~1"=="show"' in text
    assert 'if /I not "%~2"=="instance"' in text
    assert 'if /I not "%~4"=="--raw"' in text
    assert "--raw show instance" in text
    assert "destroy" not in text.lower()
    assert "MYIS_VASTAI_PYTHON" in text
