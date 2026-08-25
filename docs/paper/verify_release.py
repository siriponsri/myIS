from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys


EXPECTED_INPUT_SHA256 = "ad869ef99254df10c2e155911a1aa1a975dc9e41f1203bffa1fac2ab66043c1e"
FIGURE_OUTPUTS = (
    "figures/isainlp2026/evidence_chain.pdf",
    "figures/isainlp2026/evidence_chain.png",
    "figures/isainlp2026/out_domain_diagnosis.pdf",
    "figures/isainlp2026/out_domain_diagnosis.png",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify and rebuild the aggregate-safe paper package.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--build", action="store_true", help="Also build the review PDF with latexmk.")
    args = parser.parse_args()

    root = args.root.resolve()
    input_csv = root / "tables" / "a7-layer-aggregate-metrics.csv"
    actual_hash = sha256(input_csv)
    if actual_hash != EXPECTED_INPUT_SHA256:
        raise SystemExit(
            f"Figure input hash mismatch: {actual_hash} != {EXPECTED_INPUT_SHA256}"
        )

    subprocess.run([sys.executable, str(root / "figures" / "generate_figures.py")],
                   cwd=root, check=True)
    for relative_path in FIGURE_OUTPUTS:
        output = root / relative_path
        if not output.is_file() or output.stat().st_size == 0:
            raise SystemExit(f"Missing or empty generated figure: {relative_path}")

    if args.build:
        latexmk = shutil.which("latexmk")
        if not latexmk:
            raise SystemExit("latexmk is required for --build")
        build = root / "build"
        build.mkdir(exist_ok=True)
        build_env = os.environ.copy()
        build_env["SOURCE_DATE_EPOCH"] = "1787616000"
        build_env["FORCE_SOURCE_DATE"] = "1"
        subprocess.run(
            [latexmk, "-gg", "-pdf", "-interaction=nonstopmode", "-halt-on-error",
             f"-outdir={build}", "paper_isainlp2026.tex"],
            cwd=root / "manuscript", check=True, env=build_env,
        )
        pdf = build / "paper_isainlp2026.pdf"
        if not pdf.is_file() or pdf.stat().st_size == 0:
            raise SystemExit("Review PDF was not produced")

    print(f"PASS input_sha256={actual_hash} figures={len(FIGURE_OUTPUTS)} build={args.build}")


if __name__ == "__main__":
    main()
