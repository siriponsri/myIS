from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class VerifyReleaseTest(unittest.TestCase):
    def test_rejects_changed_figure_input(self) -> None:
        source = ROOT / "tables" / "a7-layer-aggregate-metrics.csv"
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            table_dir = temp_root / "tables"
            table_dir.mkdir()
            (table_dir / source.name).write_bytes(source.read_bytes() + b"\n")
            result = subprocess.run(
                [sys.executable, str(ROOT / "verify_release.py"), "--root", str(temp_root)],
                capture_output=True, text=True,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Figure input hash mismatch", result.stderr + result.stdout)


if __name__ == "__main__":
    unittest.main()
