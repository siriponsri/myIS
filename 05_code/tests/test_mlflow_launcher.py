import os
import subprocess
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
LAUNCHER = REPO_ROOT / "06_forntend" / "mlflow" / "mlflow.sh"
GIT_BASH_CANDIDATES = (
    Path("C:/Program Files/Git/bin/bash.exe"),
    Path("C:/Program Files/Git/usr/bin/bash.exe"),
)


def git_bash():
    return next((str(path) for path in GIT_BASH_CANDIDATES if path.is_file()), None)


class MLflowLauncherTests(unittest.TestCase):
    def test_launcher_has_valid_bash_syntax_and_no_install_path(self) -> None:
        bash = git_bash()
        if bash is None:
            self.skipTest("Git Bash is unavailable")
        result = subprocess.run([bash, "-n", str(LAUNCHER)], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        source = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn("uv run --no-sync", source)
        self.assertNotIn("uv sync", source)
        self.assertNotIn("pip install", source)
        self.assertNotIn("0.0.0.0", source)
        self.assertNotIn("C:/Users/", source)

    def test_url_command_uses_loopback_and_integer_port_override(self) -> None:
        bash = git_bash()
        if bash is None:
            self.skipTest("Git Bash is unavailable")
        env = os.environ.copy()
        env["MYIS_MLFLOW_PORT"] = "5123"
        result = subprocess.run(
            [bash, str(LAUNCHER), "url"],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "http://127.0.0.1:5123")

    def test_invalid_port_fails_before_startup(self) -> None:
        bash = git_bash()
        if bash is None:
            self.skipTest("Git Bash is unavailable")
        env = os.environ.copy()
        env["MYIS_MLFLOW_PORT"] = "remote"
        result = subprocess.run(
            [bash, str(LAUNCHER), "start"],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("must be an integer", result.stderr)


if __name__ == "__main__":
    unittest.main()
