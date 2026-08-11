from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/a1_2_vast/remote-bootstrap-measured-v16.sh"


def test_measured_bootstrap_is_offline_hash_bound_and_four_gpu() -> None:
    text = SCRIPT.read_text(encoding="ascii")
    assert "HF_HUB_OFFLINE=1" in text
    assert "TRANSFORMERS_OFFLINE=1" in text
    assert "PIP_NO_INDEX=1" in text
    assert "--no-index" in text
    assert "sha256sum --check SHA256SUMS" in text
    assert "requirements SHA-256 mismatch" in text
    assert 'torch.cuda.device_count() != 4' in text
    assert '["NVIDIA GeForce RTX 3090"] * 4' in text
    assert "PASS_RUNTIME_STAGE" in text


def test_measured_bootstrap_uses_existing_frozen_bundle_without_extracting_it() -> None:
    text = SCRIPT.read_text(encoding="ascii")
    assert "a1.2-engineering-execution-bundle-v16-frozen-69a056f7.tar.gz" in text
    assert "tar -" not in text
    assert "git clone" not in text
    assert "huggingface" not in text.lower()
