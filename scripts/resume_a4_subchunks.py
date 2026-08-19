from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess


def main() -> int:
    root = Path(r"..\04_Owner_Stores\armindex\a4\a4-goal001-20260818T231900Z")
    parts = sorted((root / "bundle" / "a4x1" / "subchunks").glob("part-*"))
    remote = "/opt/myis/a4-goal001-20260818T235614Z-a4x1/incoming/subchunks"
    key = r"C:\Users\Siripon Sri\.ssh\vast_ed25519"
    known = r"C:\myis-ssh\a3-47790578-known-hosts"

    def resume(path: Path) -> str:
        batch = f'reput "{path.resolve().as_posix()}" {remote}/{path.name}\nquit\n'
        command = [
            "sftp", "-B", "1048576", "-R", "64", "-oBatchMode=yes", "-oStrictHostKeyChecking=yes",
            f"-oUserKnownHostsFile={known}", "-i", key, "-P", "51007",
            "root@38.49.42.120",
        ]
        subprocess.run(command, input=batch, text=True, capture_output=True, check=True, timeout=900)
        return path.name

    with ThreadPoolExecutor(max_workers=4) as pool:
        print(list(pool.map(resume, parts)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
