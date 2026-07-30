#!/usr/bin/env python3
"""Validate the tracked catalog and ignored tier-organized PDF corpus."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


RESEARCH_ROOT = Path(__file__).resolve().parents[2]
MYIS_ROOT = RESEARCH_ROOT.parent
APP_ROOT = MYIS_ROOT / "00_App"
LITERATURE_ROOT = RESEARCH_ROOT / "01_evidence/literature"
CATALOG_ROOT = LITERATURE_ROOT / "catalog"
MANIFEST_PATH = CATALOG_ROOT / "corpus_manifest.csv"
ALIASES_PATH = CATALOG_ROOT / "legacy_aliases.csv"
TIERS_PATH = CATALOG_ROOT / "tier_assignments.csv"
IMPORT_MANIFEST_PATH = LITERATURE_ROOT / "IMPORT_MANIFEST.csv"
REPORT_PATH = LITERATURE_ROOT / "qa-provenance/CORPUS_MIGRATION_VALIDATION.json"
EXTRACTION_ROOT = RESEARCH_ROOT / "tmp/literature-corpus-extract"
TIER_ROOT = RESEARCH_ROOT / "01_evidence"
LEGACY_OBJECT_ROOT = RESEARCH_ROOT / "01_evidence/private/literature/objects/sha256"
DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE)
ARXIV_RE = re.compile(r"\d{4}\.\d{4,5}")
DOI_CONTEXT_RE = re.compile(
    r"(?:https?://(?:dx\.)?doi\.org/|\bdoi\s*:\s*)(10\.\d{4,9}/[-._;()/:A-Z0-9]+)",
    re.IGNORECASE,
)
ARXIV_CONTEXT_RE = re.compile(
    r"(?:arXiv\s*:\s*|arxiv\.org/(?:abs|pdf)/)(\d{4}\.\d{4,5})",
    re.IGNORECASE,
)
IDENTIFIER_CONFIDENCE = {
    "acquisition_url": "high",
    "pdf_metadata": "high",
    "pdf_front_matter": "medium",
}
IDENTIFIER_SOURCES = set(IDENTIFIER_CONFIDENCE)


def find_pdf_tool(name: str) -> str:
    """Prefer the standalone Poppler binary over MiKTeX compatibility tools."""
    executable = f"{name}.exe" if os.name == "nt" else name
    candidates: list[Path] = []
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        directory = directory.strip().strip('"')
        if not directory:
            continue
        candidate = Path(directory) / executable
        if candidate.is_file():
            candidates.append(candidate)
    if not candidates:
        return name
    candidates.sort(key=lambda path: ("poppler" not in str(path).lower(), str(path).lower()))
    return str(candidates[0])


PDFINFO = find_pdf_tool("pdfinfo")
PDFTOTEXT = find_pdf_tool("pdftotext")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def normalize_doi(value: str) -> str:
    doi = value.strip().rstrip(".,;:)\]}>").lower()
    if (
        not doi
        or re.search(r"(?:x{4,}|n{4,})", doi)
        or doi in {"10.48550/arxiv", "10.18653/v1/"}
        or doi.startswith("10.48550/arxiv.")
    ):
        return ""
    return doi


def doi_candidates(pattern: re.Pattern[str], text: str) -> set[str]:
    values = {
        normalize_doi(match.group(0) if match.lastindex is None else match.group(1))
        for match in pattern.finditer(text)
    }
    values.discard("")
    return values


def arxiv_candidates(text: str) -> set[str]:
    return {match.group(1) for match in ARXIV_CONTEXT_RE.finditer(text)}


def decode_output(stdout: bytes) -> str:
    for encoding in ("utf-8", "cp1252", "latin-1"):
        try:
            return stdout.decode(encoding)
        except UnicodeDecodeError:
            continue
    return stdout.decode("utf-8", errors="replace")


def run_text(command: list[str], *, env: dict[str, str] | None = None) -> str:
    # Some Windows Poppler builds crash while emitting Unicode PDF metadata to
    # an anonymous pipe. File-backed handles preserve the bytes without that
    # code path and keep the validator deterministic.
    with tempfile.TemporaryFile() as stdout_handle, tempfile.TemporaryFile() as stderr_handle:
        result = subprocess.run(
            command,
            check=False,
            cwd=RESEARCH_ROOT,
            env=env,
            stdout=stdout_handle,
            stderr=stderr_handle,
        )
        stdout_handle.seek(0)
        stderr_handle.seek(0)
        stdout = stdout_handle.read()
        stderr = stderr_handle.read()
    if result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, command, output=stdout, stderr=stderr)
    return decode_output(stdout)


def pdf_tool_path(path: Path) -> str:
    """Prefer a short Research-relative path for Windows PDF command-line tools."""
    try:
        return str(path.relative_to(RESEARCH_ROOT))
    except ValueError:
        return str(path)


def run_pdf_tool(prefix: list[str], path: Path, suffix: list[str] | None = None) -> str:
    """Run Poppler, retrying through a short temp name for Windows path bugs."""
    suffix = suffix or []
    try:
        return run_text([*prefix, pdf_tool_path(path), *suffix])
    except subprocess.CalledProcessError:
        with tempfile.TemporaryDirectory(prefix="myis-pdf-") as temp_dir:
            short_path = Path(temp_dir) / "source.pdf"
            try:
                short_path.hardlink_to(path)
            except OSError:
                shutil.copyfile(path, short_path)
            return run_text([*prefix, str(short_path), *suffix])


def available_pdf_paths(row: dict[str, str]) -> list[Path]:
    candidates = [
        RESEARCH_ROOT / row["object_path"],
        LEGACY_OBJECT_ROOT / row["sha256"][:2] / f"{row['sha256']}.pdf",
        APP_ROOT / row["legacy_primary_alias"],
    ]
    return [path for path in candidates if path.is_file()]


def identifier_evidence(row: dict[str, str], source: str) -> tuple[set[str], set[str]]:
    if source == "acquisition_url":
        text = f"{row.get('source_url', '')} {row.get('acquired_from', '')}"
        return doi_candidates(DOI_RE, text), arxiv_candidates(text)

    sources = available_pdf_paths(row)
    if not sources:
        raise FileNotFoundError(f"No PDF source available for {row['u_id']}")
    object_path = sources[0]
    suffix = ".info.txt" if source == "pdf_metadata" else ".txt"
    cache_path = EXTRACTION_ROOT / f"{row['sha256']}{suffix}"
    if cache_path.exists():
        text = cache_path.read_text(encoding="utf-8-sig", errors="replace")
    elif source == "pdf_metadata":
        text = run_pdf_tool([PDFINFO], object_path)
    else:
        text = run_pdf_tool(
            [PDFTOTEXT, "-f", "1", "-l", "1", "-layout"],
            object_path,
            ["-"],
        )
    if source == "pdf_front_matter":
        text = text.split("\f", 1)[0]
    return doi_candidates(DOI_CONTEXT_RE, text), arxiv_candidates(text)


def record(checks: dict[str, bool], issues: list[str], name: str, passed: bool, detail: str) -> None:
    checks[name] = passed
    if not passed:
        issues.append(f"{name}: {detail}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--phase",
        choices=("pre-migration", "final"),
        default="final",
        help="Validate either movable sources or the completed tier-root corpus.",
    )
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()

    checks: dict[str, bool] = {}
    issues: list[str] = []
    for required in (MANIFEST_PATH, ALIASES_PATH, TIERS_PATH, CATALOG_ROOT / "tier_policy.md"):
        record(checks, issues, f"exists_{required.name}", required.exists(), str(required))
    if issues:
        print(json.dumps({"checks": checks, "issues": issues, "overall_pass": False}, indent=2))
        return 1

    manifest = read_csv(MANIFEST_PATH)
    aliases = read_csv(ALIASES_PATH)
    tiers = read_csv(TIERS_PATH)
    record(checks, issues, "manifest_153_rows", len(manifest) == 153, str(len(manifest)))
    record(checks, issues, "aliases_169_rows", len(aliases) == 169, str(len(aliases)))
    record(checks, issues, "tiers_153_rows", len(tiers) == 153, str(len(tiers)))

    uids = [row["u_id"] for row in manifest]
    expected_uids = [f"U{value:03d}" for value in range(1, 154)]
    record(checks, issues, "uids_contiguous_u001_u153", uids == expected_uids, f"first={uids[:3]} last={uids[-3:]}")
    hashes = [row["sha256"] for row in manifest]
    record(checks, issues, "manifest_hashes_unique", len(hashes) == len(set(hashes)), "duplicate manifest SHA")
    record(checks, issues, "verified_titles_nonempty", all(row["verified_title"].strip() for row in manifest), "blank verified title")
    record(checks, issues, "page_counts_positive", all(int(row["page_count"]) > 0 for row in manifest), "zero page count")
    identifier_failures: list[str] = []
    evidence_cache: dict[tuple[str, str], tuple[set[str], set[str]]] = {}
    for row in manifest:
        uid = row["u_id"]
        doi = row.get("doi", "").strip()
        doi_source = row.get("doi_source", "").strip()
        doi_confidence = row.get("doi_confidence", "").strip()
        arxiv_id = row.get("arxiv_id", "").strip()
        arxiv_source = row.get("arxiv_source", "").strip()
        arxiv_confidence = row.get("arxiv_confidence", "").strip()
        if bool(doi) != bool(doi_source):
            identifier_failures.append(f"doi_source_pair:{uid}")
        if doi and (not DOI_RE.fullmatch(doi) or doi_source not in IDENTIFIER_SOURCES):
            identifier_failures.append(f"doi_format_or_source:{uid}:{doi}:{doi_source}")
        if doi and normalize_doi(doi) != doi:
            identifier_failures.append(f"doi_placeholder_or_arxiv_alias:{uid}:{doi}")
        expected_doi_confidence = IDENTIFIER_CONFIDENCE.get(doi_source, "not_detected")
        if doi_confidence != expected_doi_confidence:
            identifier_failures.append(
                f"doi_confidence:{uid}:{doi_confidence}:{expected_doi_confidence}"
            )
        if bool(arxiv_id) != bool(arxiv_source):
            identifier_failures.append(f"arxiv_source_pair:{uid}")
        if arxiv_id and (not ARXIV_RE.fullmatch(arxiv_id) or arxiv_source not in IDENTIFIER_SOURCES):
            identifier_failures.append(f"arxiv_format_or_source:{uid}:{arxiv_id}:{arxiv_source}")
        expected_arxiv_confidence = IDENTIFIER_CONFIDENCE.get(arxiv_source, "not_detected")
        if arxiv_confidence != expected_arxiv_confidence:
            identifier_failures.append(
                f"arxiv_confidence:{uid}:{arxiv_confidence}:{expected_arxiv_confidence}"
            )

        for source in {doi_source, arxiv_source} - {""}:
            cache_key = (row["sha256"], source)
            if cache_key not in evidence_cache:
                evidence_cache[cache_key] = identifier_evidence(row, source)
            source_dois, source_arxiv_ids = evidence_cache[cache_key]
            if doi_source == source and doi not in source_dois:
                identifier_failures.append(f"doi_not_in_claimed_source:{uid}:{doi}:{source}")
            if arxiv_source == source and arxiv_id not in source_arxiv_ids:
                identifier_failures.append(
                    f"arxiv_not_in_claimed_source:{uid}:{arxiv_id}:{source}"
                )
    record(
        checks,
        issues,
        "identifiers_have_conservative_provenance",
        not identifier_failures,
        str(identifier_failures[:10]),
    )
    mismatch_uids = {row["u_id"] for row in manifest if row["identity_status"] == "alias_title_mismatch"}
    record(
        checks,
        issues,
        "known_wrong_acquisitions_isolated",
        mismatch_uids == {"U110", "U111", "U114", "U115", "U138"},
        str(sorted(mismatch_uids)),
    )
    alias_hash_counts = Counter(row["sha256"] for row in aliases)
    record(checks, issues, "alias_unique_hash_count_153", len(alias_hash_counts) == 153, str(len(alias_hash_counts)))
    duplicate_groups = sum(1 for count in alias_hash_counts.values() if count > 1)
    record(checks, issues, "duplicate_groups_16", duplicate_groups == 16, str(duplicate_groups))

    manifest_by_uid = {row["u_id"]: row for row in manifest}
    record(
        checks,
        issues,
        "known_false_dois_cleared",
        not manifest_by_uid.get("U001", {}).get("doi") and not manifest_by_uid.get("U151", {}).get("doi"),
        f"U001={manifest_by_uid.get('U001', {}).get('doi')} U151={manifest_by_uid.get('U151', {}).get('doi')}",
    )
    record(
        checks,
        issues,
        "known_arxiv_ids_preserved",
        manifest_by_uid.get("U001", {}).get("arxiv_id") == "2012.13919"
        and manifest_by_uid.get("U151", {}).get("arxiv_id") == "2607.03451",
        f"U001={manifest_by_uid.get('U001', {}).get('arxiv_id')} U151={manifest_by_uid.get('U151', {}).get('arxiv_id')}",
    )
    record(
        checks,
        issues,
        "u082_is_pdf84",
        manifest_by_uid.get("U082", {}).get("legacy_primary_alias", "").endswith("84_skillopt_executive_strategy_for_self_evolving_agent_skills.pdf"),
        manifest_by_uid.get("U082", {}).get("legacy_primary_alias", "missing"),
    )
    for uid, suffix in {
        "U151": "85_skillopt_lite_better_and_faster_agent.pdf",
        "U152": "86_marginal_advantage_accumulation_for_memory_driven_agent.pdf",
        "U153": "87_skillgrad_optimizing_agent_skills_like_gradient_descent.pdf",
    }.items():
        record(
            checks,
            issues,
            f"{uid.lower()}_mapping",
            manifest_by_uid.get(uid, {}).get("legacy_primary_alias", "").endswith(suffix),
            manifest_by_uid.get(uid, {}).get("legacy_primary_alias", "missing"),
        )
    record(checks, issues, "u150_template", manifest_by_uid.get("U150", {}).get("record_type") == "template", str(manifest_by_uid.get("U150")))
    record(checks, issues, "u150_tier_n", manifest_by_uid.get("U150", {}).get("tier") == "N", str(manifest_by_uid.get("U150")))
    record(checks, issues, "u152_tier_a", manifest_by_uid.get("U152", {}).get("tier") == "A", str(manifest_by_uid.get("U152")))
    expected_titles = {
        "U017": "Needle in a haystack: Harnessing AI in drug patent searches and prediction",
        "U059": "Is ChatGPT Good at Search? Investigating Large Language Models as Re-Ranking Agents",
        "U060": "RankZephyr: Effective and Robust Zero-Shot Listwise Reranking is a Breeze!",
        "U063": "Rank-without-GPT: Building GPT-Independent Listwise Rerankers on Open-Source Large Language Models",
        "U077": "Is It Novel and Why? Fine-Grained Patent Novelty Prediction Based on Passage Retrieval",
        "U078": "Benchmarking Patent Embeddings: A Multi-Task Evaluation of 22 Models Across Retrieval, Classification, and Clustering",
        "U079": "PEEM: Prompt Engineering Evaluation Metrics for Interpretable Joint Evaluation of Prompts and Responses",
        "U091": "RAPTOR: Recursive Abstractive Processing for Tree-Organized Retrieval",
        "U108": "Qwen3 Technical Report",
        "U118": "Graph RAG for Legal Norms: A Hierarchical and Temporal Approach",
        "U143": "Beyond Keywords: Optimizing Legal Information Retrieval through Embeddings, Cross-Encoders, and Large Language Models",
        "U149": "Benchmarking Patent Embeddings: A Multi-Task Evaluation of 22 Models Across Retrieval, Classification, and Clustering",
        "U152": "Marginal Advantage Accumulation for Memory-Driven Agent Self-Evolution",
    }
    title_failures = {
        uid: manifest_by_uid.get(uid, {}).get("verified_title")
        for uid, expected in expected_titles.items()
        if manifest_by_uid.get(uid, {}).get("verified_title") != expected
    }
    record(checks, issues, "title_anomalies_zero", not title_failures, str(title_failures))

    tier_by_uid = {row["u_id"]: row["tier"] for row in tiers}
    record(checks, issues, "tier_uids_match_manifest", set(tier_by_uid) == set(uids), "tier UID set differs")
    record(checks, issues, "tier_values_valid", set(tier_by_uid.values()) <= set("ABCN"), str(set(tier_by_uid.values())))
    tier_counts = Counter(tier_by_uid.values())
    record(
        checks,
        issues,
        "tier_counts_match_owner_decision",
        tier_counts == Counter({"A": 55, "B": 64, "C": 28, "N": 6}),
        str(dict(sorted(tier_counts.items()))),
    )
    for tier in "ABCN":
        view = read_csv(CATALOG_ROOT / f"tier_{tier}.csv")
        expected = {uid for uid, value in tier_by_uid.items() if value == tier}
        record(checks, issues, f"tier_{tier.lower()}_view_matches", {row["u_id"] for row in view} == expected, f"expected {len(expected)} got {len(view)}")

    digest_files = list((LITERATURE_ROOT / "validated-digests").glob("U*.md"))
    digest_uids = Counter(path.name[:4] for path in digest_files)
    record(checks, issues, "digests_153_files", len(digest_files) == 153, str(len(digest_files)))
    record(checks, issues, "one_digest_per_uid", set(digest_uids) == set(uids) and all(count == 1 for count in digest_uids.values()), str(digest_uids.most_common(3)))
    missing_digest_paths = [row["digest_path"] for row in manifest if not (RESEARCH_ROOT / row["digest_path"]).is_file()]
    record(checks, issues, "manifest_digest_paths_resolve", not missing_digest_paths, str(missing_digest_paths[:5]))

    frozen_failures: list[str] = []
    for row in read_csv(IMPORT_MANIFEST_PATH):
        target = RESEARCH_ROOT / row["current_repo_relative_path"]
        if not target.is_file():
            frozen_failures.append(f"missing:{row['current_repo_relative_path']}")
            continue
        if sha256_file(target).upper() != row["target_sha256"].upper():
            frozen_failures.append(f"sha:{row['current_repo_relative_path']}")
    record(checks, issues, "frozen_import_manifest_hashes_match", not frozen_failures, str(frozen_failures[:5]))

    object_failures: list[str] = []
    object_paths: list[str] = []
    for row in manifest:
        object_paths.append(row["object_path"])
        expected_prefix = f"01_evidence/{row['tier']}-tier/"
        filename = Path(row["object_path"]).name
        if not row["object_path"].startswith(expected_prefix):
            object_failures.append(f"tier_path:{row['u_id']}:{row['object_path']}")
            continue
        if not re.fullmatch(rf"{row['u_id']}_[a-z0-9_]+\.pdf", filename):
            object_failures.append(f"filename:{row['u_id']}:{filename}")
            continue
        sources = available_pdf_paths(row)
        if args.phase == "final":
            expected_path = RESEARCH_ROOT / row["object_path"]
            sources = [expected_path] if expected_path.is_file() else []
        if len(sources) != 1:
            object_failures.append(f"source_count:{row['u_id']}:{len(sources)}")
            continue
        object_path = sources[0]
        if object_path.stat().st_size != int(row["size_bytes"]):
            object_failures.append(f"size:{row['u_id']}")
            continue
        if sha256_file(object_path) != row["sha256"]:
            object_failures.append(f"sha:{row['u_id']}")
    record(checks, issues, "object_paths_unique", len(object_paths) == len(set(object_paths)), "duplicate object paths")
    record(
        checks,
        issues,
        "migration_sources_153_hash_verified" if args.phase == "pre-migration" else "tier_pdfs_153_hash_verified",
        not object_failures,
        str(object_failures[:5]),
    )

    tier_pdfs = sorted(
        path
        for tier in "ABCN"
        for path in (TIER_ROOT / f"{tier}-tier").glob("*.pdf")
    )
    manifest_pdf_paths = {RESEARCH_ROOT / row["object_path"] for row in manifest}
    if args.phase == "final":
        record(
            checks,
            issues,
            "tier_folder_contains_only_manifest_pdfs",
            set(tier_pdfs) == manifest_pdf_paths,
            f"disk={len(tier_pdfs)} manifest={len(manifest_pdf_paths)}",
        )
    legacy_object_pdfs = sorted(LEGACY_OBJECT_ROOT.rglob("*.pdf")) if LEGACY_OBJECT_ROOT.exists() else []
    if args.phase == "final":
        record(
            checks,
            issues,
            "legacy_sha_store_empty",
            not legacy_object_pdfs,
            str([str(path) for path in legacy_object_pdfs[:5]]),
        )

    app_pdfs = sorted((APP_ROOT / "research/ref-paper").rglob("*.pdf"))
    if args.phase == "final":
        record(checks, issues, "app_literature_pdfs_removed", not app_pdfs, str([str(path) for path in app_pdfs[:5]]))

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "phase": args.phase,
        "checks": checks,
        "counts": {
            "manifest_rows": len(manifest),
            "alias_rows": len(aliases),
            "tier_rows": len(tiers),
            "digest_files": len(digest_files),
            "duplicate_groups": duplicate_groups,
            "app_literature_pdfs": len(app_pdfs),
            "tier_pdfs": len(tier_pdfs),
            "legacy_object_pdfs": len(legacy_object_pdfs),
            "tier_counts": dict(sorted(tier_counts.items())),
        },
        "issues": issues,
        "overall_pass": all(checks.values()),
    }
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    print(text, end="")
    if args.write_report:
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(text, encoding="utf-8")
    return 0 if report["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
