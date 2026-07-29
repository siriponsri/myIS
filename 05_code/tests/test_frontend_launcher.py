import subprocess
from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_ROOT = REPO_ROOT / "06_frontend"


class FrontendLauncherTests(unittest.TestCase):
    def test_one_click_wrappers_target_local_powershell_scripts(self) -> None:
        start = (FRONTEND_ROOT / "START_OWNER_CONSOLE.cmd").read_text(encoding="utf-8")
        stop = (FRONTEND_ROOT / "STOP_OWNER_CONSOLE.cmd").read_text(encoding="utf-8")
        self.assertIn("start_owner_console.ps1", start)
        self.assertIn("stop_owner_console.ps1", stop)
        self.assertIn("ExecutionPolicy Bypass", start)
        self.assertIn("ExecutionPolicy Bypass", stop)

    def test_launcher_is_loopback_only_and_never_installs_dependencies(self) -> None:
        script = (FRONTEND_ROOT / "start_owner_console.ps1").read_text(encoding="utf-8")
        self.assertIn("127.0.0.1", script)
        self.assertIn("8765..8770", script)
        self.assertIn("http://127.0.0.1:5000", script)
        self.assertIn('"--no-sync"', script)
        self.assertIn('program_id -eq "myis-research"', script)
        self.assertIn('"myis-dashboard.exe", "myis-assets.exe", "myis-sessions.exe"', script)
        lowered = script.lower()
        self.assertNotIn('-argumentlist @("sync"', lowered)
        self.assertNotIn("pip install", lowered)
        self.assertNotIn("npm install", lowered)
        self.assertNotIn("0.0.0.0", script)

    def test_powershell_launchers_parse(self) -> None:
        for filename in ("start_owner_console.ps1", "stop_owner_console.ps1"):
            path = FRONTEND_ROOT / filename
            command = (
                "$ErrorActionPreference='Stop';"
                f"[scriptblock]::Create((Get-Content -Raw -LiteralPath '{path}')) | Out-Null"
            )
            completed = subprocess.run(
                ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()
