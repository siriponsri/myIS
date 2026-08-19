from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess


def main() -> int:
    root = Path(r"..\04_Owner_Stores\armindex\a4\a4-goal001-20260818T231900Z")
    parts = sorted((root / "bundle" / "a4x1" / "subchunks").glob("part-*"))
    destination = "/opt/myis/a4-goal001-20260818T235614Z-a4x1/incoming/subchunks"
    base = [
        "scp", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
        "-o", r"UserKnownHostsFile=C:\myis-ssh\a3-47790578-known-hosts",
        "-i", r"C:\Users\Siripon Sri\.ssh\vast_ed25519", "-P", "51007",
    ]

    def upload(path: Path) -> str:
        subprocess.run(base + [str(path), f"root@38.49.42.120:{destination}/{path.name}"], check=True, timeout=900)
        return path.name

    with ThreadPoolExecutor(max_workers=8) as pool:
        print(list(pool.map(upload, parts)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
