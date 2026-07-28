"""Read-only validation for the myIS Research 1.0 restructure."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path
import re
from typing import Iterable


ROOT = Path(__file__).resolve().parents[2]
LITERATURE = ROOT / "01_evidence" / "literature"
MANIFEST = LITERATURE / "IMPORT_MANIFEST.csv"
DIGESTS = LITERATURE / "validated-digests"
CORPUS_MANIFEST = LITERATURE / "catalog" / "corpus_manifest.csv"

ACTIVE_CONTEXT_PATHS = (
    Path("AGENTS.md"),
    Path("CLAUDE.md"),
    Path("README.md"),
    Path("PLAN.md"),
    Path("FULL_RESEARCH_TRACK_PLAN.md"),
    Path("LOCAL_RESEARCH_HARNESS_BUILD_PLAN.md"),
    Path("HANDOFF.md"),
    Path(".gitattributes"),
    Path(".agents/skills"),
    Path("00_governance"),
    Path("02_tracks/00_C_crossroute"),
    Path("02_tracks/01_S_skillopt"),
    Path("03_experiments/config"),
    Path("03_experiments/templates"),
    Path("05_code"),
    Path("06_frontend"),
)

EXCLUDED_ACTIVE_PREFIXES = (
    Path("01_evidence"),
    Path("02_tracks/99_legacy"),
    Path("03_experiments/V01_brain_drive_agent_demo"),
    Path("04_outputs"),
    Path("00_governance/approvals"),
    Path("05_code/tests"),
)
EXCLUDED_ACTIVE_FILES = {
    Path("00_governance/ARCHIVE_CUTOVER_20260727.md"),
    Path("00_governance/CLEANUP_APPROVALS.md"),
    Path("00_governance/PATH_MIGRATION_MAP.csv"),
    Path("00_governance/PDF_DUPLICATE_MANIFEST.csv"),
    Path("05_code/scripts/validate_restructure.py"),
}
IGNORED_DIRECTORY_NAMES = {".git", ".pytest_cache", ".venv", "__pycache__"}
TEXT_SUFFIXES = {".cmd", ".css", ".html", ".js", ".json", ".md", ".ps1", ".py", ".sh", ".toml", ".txt", ".yaml", ".yml"}
LEGACY_PATTERNS = (
    ("IS1 Research V0.1", re.compile(r"\bIS1 Research V0\.1\b")),
    ("is1-research", re.compile(r"\bis1-research\b", re.IGNORECASE)),
    ("Paper E", re.compile(r"\bPaper E\b")),
    ("Track R", re.compile(r"\bTrack R\b", re.IGNORECASE)),
    ("Gate R", re.compile(r"\bGate R\b", re.IGNORECASE)),
    ("Phase R", re.compile(r"\bPhase R\d*\b", re.IGNORECASE)),
)

REQUIRED_PATHS = (
    Path("HANDOFF.md"),
    Path("00_governance/config/project.yaml"),
    Path("00_governance/IS_RESEARCH_TRACK_C_V0.1_CROSSROUTE_PLAN.md"),
    Path("00_governance/IS_RESEARCH_TRACK_S_V0.1_SKILLOPT_HARNESSOPT_PLAN.md"),
    Path("02_tracks/00_C_crossroute/C_artifacts/configs"),
    Path("02_tracks/00_C_crossroute/C_artifacts/manifests"),
    Path("02_tracks/00_C_crossroute/C_artifacts/diagnostics"),
    Path("02_tracks/00_C_crossroute/C_artifacts/results"),
    Path("02_tracks/00_C_crossroute/C_artifacts/receipts"),
    Path("02_tracks/00_C_crossroute/C_documents"),
    Path("02_tracks/01_S_skillopt/S_artifacts/configs"),
    Path("02_tracks/01_S_skillopt/S_artifacts/manifests"),
    Path("02_tracks/01_S_skillopt/S_artifacts/optimization"),
    Path("02_tracks/01_S_skillopt/S_artifacts/results"),
    Path("02_tracks/01_S_skillopt/S_artifacts/receipts"),
    Path("02_tracks/01_S_skillopt/S_documents"),
    Path("02_tracks/99_legacy/01_R_ranking_evidence"),
    Path("06_frontend"),
)
OBSOLETE_ACTIVE_PATHS = (
    Path("02_tracks/00_C_candidate_exposure"),
    Path("02_tracks/01_R_ranking_evidence"),
    Path("02_tracks/02_S_skill_evolution"),
    Path("06_forntend"),
)

MARKDOWN_INLINE_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
MARKDOWN_REFERENCE_LINK = re.compile(r"^\s*\[[^\]]+\]:\s*(\S+)", re.MULTILINE)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def is_excluded_from_active_context(relative: Path) -> bool:
    """Return whether a repository-relative path is immutable or legacy context."""
    if relative in EXCLUDED_ACTIVE_FILES:
        return True
    return any(relative == prefix or prefix in relative.parents for prefix in EXCLUDED_ACTIVE_PREFIXES)


def iter_active_context_files(root: Path) -> Iterable[Path]:
    """Yield text files that define the mutable active program context only."""
    for relative_root in ACTIVE_CONTEXT_PATHS:
        candidate = root / relative_root
        if candidate.is_file():
            candidates = (candidate,)
        elif candidate.is_dir():
            candidates = (path for path in candidate.rglob("*") if path.is_file())
        else:
            continue

        for path in candidates:
            relative = path.relative_to(root)
            if is_excluded_from_active_context(relative):
                continue
            if any(part in IGNORED_DIRECTORY_NAMES for part in relative.parts):
                continue
            if path.suffix.lower() in TEXT_SUFFIXES:
                yield path


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def active_context_failures(root: Path) -> list[str]:
    failures: list[str] = []
    for path in iter_active_context_files(root):
        relative = path.relative_to(root).as_posix()
        content = read_text(path)
        for label, pattern in LEGACY_PATTERNS:
            if pattern.search(content):
                failures.append(f"legacy active-context reference ({label}): {relative}")
    return failures


def local_markdown_target(target: str) -> str | None:
    """Return a local Markdown target, or ``None`` for external/anchor links."""
    target = target.strip()
    if target.startswith("<") and ">" in target:
        target = target[1 : target.index(">")]
    else:
        target = target.split(maxsplit=1)[0]
    target = target.split("#", maxsplit=1)[0].replace("\\", "/")
    if not target or target.startswith(("http://", "https://", "mailto:", "tel:", "data:")):
        return None
    return target


def markdown_link_failures(root: Path) -> list[str]:
    failures: list[str] = []
    for path in iter_active_context_files(root):
        if path.suffix.lower() != ".md":
            continue
        content = read_text(path)
        targets = [*MARKDOWN_INLINE_LINK.findall(content), *MARKDOWN_REFERENCE_LINK.findall(content)]
        for raw_target in targets:
            target = local_markdown_target(raw_target)
            if target is None:
                continue
            resolved = (path.parent / target).resolve()
            try:
                resolved.relative_to(root.resolve())
            except ValueError:
                failures.append(
                    f"Markdown link escapes repository: {path.relative_to(root).as_posix()} -> {raw_target}"
                )
                continue
            if not resolved.exists():
                failures.append(
                    f"broken Markdown link: {path.relative_to(root).as_posix()} -> {raw_target}"
                )
    return failures


def migration_contract_failures(root: Path) -> list[str]:
    failures: list[str] = []
    for relative in REQUIRED_PATHS:
        if not (root / relative).exists():
            failures.append(f"missing migration path: {relative.as_posix()}")
    for relative in OBSOLETE_ACTIVE_PATHS:
        if (root / relative).exists():
            failures.append(f"obsolete active migration path remains: {relative.as_posix()}")

    project_config = root / "00_governance/config/project.yaml"
    if project_config.is_file():
        config_text = read_text(project_config)
        for required in (
            "program_id: myis-research",
            "display_name: myIS Research",
            'protocol_version: "1.0"',
            'research_version: "0.1"',
            "track_order: [C, S]",
            "seed: 42",
            "partitions: {train: 250, selection: 125, joint_test: 872}",
        ):
            if required not in config_text:
                failures.append(f"project config missing migration commitment: {required}")

    plan = root / "PLAN.md"
    if plan.is_file():
        plan_text = read_text(plan)
        for phase in ("F0", "F1", "D0", "C0", "C1", "CF", "S0", "S1", "SF", "CT", "Q", "PC", "PS"):
            if not re.search(rf"\b{phase}\b", plan_text):
                failures.append(f"PLAN.md missing active phase: {phase}")
    active_graph_documents = (
        root / "PLAN.md",
        root / "FULL_RESEARCH_TRACK_PLAN.md",
        root / "README.md",
        root / "HANDOFF.md",
    )
    if not any(
        document.is_file()
        and "Track C -> frozen C1 harness -> Track S" in read_text(document)
        for document in active_graph_documents
    ):
        failures.append("active documentation missing the C -> frozen C1 harness -> S path")

    gates = root / "00_governance/OWNER_GATES.md"
    if gates.is_file():
        gate_text = read_text(gates)
        for gate in range(9):
            if not re.search(rf"\bG{gate}\b", gate_text):
                failures.append(f"OWNER_GATES.md missing gate G{gate}")

    return failures


def validate(root: Path = ROOT) -> list[str]:
    """Return all read-only restructure validation failures for ``root``."""
    failures: list[str] = []
    digest_files = sorted((root / "01_evidence/literature/validated-digests").glob("U*_digest.md"))
    digest_ids = {path.name[:4] for path in digest_files}
    expected_ids = {f"U{number:03d}" for number in range(1, 154)}

    if len(digest_files) != 153:
        failures.append(f"expected 153 digests, found {len(digest_files)}")
    if digest_ids != expected_ids:
        failures.append("digest IDs are not exactly U001-U153")

    corpus_manifest = root / "01_evidence/literature/catalog/corpus_manifest.csv"
    if not corpus_manifest.is_file():
        failures.append("missing canonical corpus manifest")
    else:
        with corpus_manifest.open("r", encoding="utf-8-sig", newline="") as handle:
            corpus_rows = list(csv.DictReader(handle))
        if len(corpus_rows) != 153:
            failures.append(f"expected 153 corpus rows, found {len(corpus_rows)}")
        if {row.get("u_id", "") for row in corpus_rows} != expected_ids:
            failures.append("corpus manifest IDs are not exactly U001-U153")

    manifest = root / "01_evidence/literature/IMPORT_MANIFEST.csv"
    if not manifest.is_file():
        failures.append("missing import manifest")
    else:
        with manifest.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        if len(rows) != 64:
            failures.append(f"expected 64 import rows, found {len(rows)}")

        for row in rows:
            relative = row.get("current_repo_relative_path", "")
            if not relative:
                failures.append("manifest row missing current_repo_relative_path")
                continue
            target = root / Path(relative)
            try:
                target.resolve().relative_to(root.resolve())
            except ValueError:
                failures.append(f"manifest path escapes repository: {relative}")
                continue
            if not target.is_file():
                failures.append(f"missing imported artifact: {relative}")
                continue
            actual = sha256(target)
            expected = row["target_sha256"].upper()
            if actual != expected:
                failures.append(f"hash mismatch: {relative}")

    failures.extend(migration_contract_failures(root))
    failures.extend(active_context_failures(root))
    failures.extend(markdown_link_failures(root))
    return failures


def main() -> int:
    failures = validate()

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print("RESEARCH_RESTRUCTURE_VALID=true")
    print("VALIDATED_DIGEST_COUNT=153")
    print("U041_U153_TRIAGE_AUTHORIZED=true")
    print("CORPUS_MANIFEST_ROWS=153")
    print("IMPORT_MANIFEST_ROWS=64")
    print("IMPORT_HASHES_MATCH=true")
    print("IMPORT_PATHS_PORTABLE=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
