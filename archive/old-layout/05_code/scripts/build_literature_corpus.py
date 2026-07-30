#!/usr/bin/env python3
"""Build the tracked literature catalog and U041-U153 triage digests.

This is a migration helper, not a downloader. It preserves the historical
U001-U150 mapping, appends U151-U153, and emits tracked metadata/digests for
the ignored Research-local tiered PDF corpus.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Iterable


RESEARCH_ROOT = Path(__file__).resolve().parents[2]
MYIS_ROOT = RESEARCH_ROOT.parent
APP_ROOT = MYIS_ROOT / "00_App"
WORKSPACE_ROOT = RESEARCH_ROOT.parents[2]
ARCHIVE_MANIFEST = (
    WORKSPACE_ROOT
    / "99_Archive/00_myIS/workspaces/thaiphalex-hyperresearch-review-20260726"
    / "source-packet/00-governance/LOCAL_CORPUS_MANIFEST.csv"
)
LITERATURE_ROOT = RESEARCH_ROOT / "01_evidence/literature"
CATALOG_ROOT = LITERATURE_ROOT / "catalog"
DIGEST_ROOT = LITERATURE_ROOT / "validated-digests"
QA_ROOT = LITERATURE_ROOT / "qa-provenance"
EXTRACTION_ROOT = RESEARCH_ROOT / "tmp/literature-corpus-extract"
TIER_ROOT = RESEARCH_ROOT / "01_evidence"
LEGACY_OBJECT_ROOT = RESEARCH_ROOT / "01_evidence/private/literature/objects/sha256"


def find_pdf_tool(name: str) -> str:
    """Prefer standalone Poppler over MiKTeX's stateful compatibility tools."""
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

NEW_UID_OBJECTS = {
    "U151": {
        "path": "research/ref-paper/is1/pdfs/85_skillopt_lite_better_and_faster_agent.pdf",
        "sha256": "4e7d36b233673a3793b95e7834e588acf19bcea3b292c7168781a95df792797d",
        "size_bytes": 1051972,
    },
    "U152": {
        "path": "research/ref-paper/is1/pdfs/86_marginal_advantage_accumulation_for_memory_driven_agent.pdf",
        "sha256": "a77d17230e6e1b29be82a61667dad4ed57fe3224f514aeb48141d71d1e0d14c0",
        "size_bytes": 5257658,
    },
    "U153": {
        "path": "research/ref-paper/is1/pdfs/87_skillgrad_optimizing_agent_skills_like_gradient_descent.pdf",
        "sha256": "ac08480ae67c537dcfdc7ddb9dd1938adde2330943c09b3682a8f8e7383b1cfe",
        "size_bytes": 767174,
    },
}

CURATED_OVERRIDES: dict[str, dict[str, str]] = {
    "U017": {
        "title": "Needle in a haystack: Harnessing AI in drug patent searches and prediction",
        "title_source": "rendered_first_page_text",
        "identity_status": "verified",
        "tier": "A",
        "tier_reason": "Direct patent search and drug-patent identification evidence",
    },
    "U027": {
        "tier": "B",
        "tier_reason": "Transferable graph-transformer patent-search method without primary benchmark status",
    },
    "U028": {
        "tier": "C",
        "tier_reason": "Patent classification context rather than direct prior-art retrieval evidence",
    },
    "U029": {
        "tier": "B",
        "tier_reason": "Historical CLEF-IP retrieval context and evaluation protocol",
    },
    "U030": {
        "tier": "B",
        "tier_reason": "Historical CLEF-IP retrieval experiment context",
    },
    "U031": {
        "tier": "B",
        "tier_reason": "Historical CLEF-IP summarization and retrieval experiment context",
    },
    "U032": {
        "tier": "B",
        "tier_reason": "Transferable patent-similarity embedding comparison",
    },
    "U035": {
        "tier": "A",
        "tier_reason": "Primary heterogeneous retrieval benchmark used by active methods",
    },
    "U036": {
        "tier": "C",
        "tier_reason": "Patent workflow and multi-agent systems context without direct retrieval evaluation",
    },
    "U037": {
        "tier": "A",
        "tier_reason": "Primary late-interaction retrieval method and benchmark baseline",
    },
    "U039": {
        "tier": "B",
        "tier_reason": "Patent retrieval method with limited evaluation breadth",
    },
    "U059": {
        "title": "Is ChatGPT Good at Search? Investigating Large Language Models as Re-Ranking Agents",
        "title_source": "rendered_first_page_text",
        "identity_status": "verified",
    },
    "U060": {
        "title": "RankZephyr: Effective and Robust Zero-Shot Listwise Reranking is a Breeze!",
        "title_source": "rendered_first_page_text",
        "identity_status": "verified",
    },
    "U063": {
        "title": "Rank-without-GPT: Building GPT-Independent Listwise Rerankers on Open-Source Large Language Models",
        "title_source": "rendered_first_page_text",
        "identity_status": "verified",
        "tier": "B",
        "tier_reason": "Transferable open-source listwise reranking method",
    },
    "U075": {
        "title": "Algorithmic Learning in a Random World",
        "title_source": "rendered_title_page_visual_review",
        "identity_status": "verified_by_visual_review",
        "record_type": "book",
        "tier": "B",
        "tier_reason": "Foundational conformal prediction and online learning background",
    },
    "U077": {
        "title": "Is It Novel and Why? Fine-Grained Patent Novelty Prediction Based on Passage Retrieval",
        "title_source": "rendered_first_page_text",
        "identity_status": "verified",
    },
    "U078": {
        "title": "Benchmarking Patent Embeddings: A Multi-Task Evaluation of 22 Models Across Retrieval, Classification, and Clustering",
        "title_source": "rendered_first_page_text",
        "identity_status": "verified",
    },
    "U079": {
        "title": "PEEM: Prompt Engineering Evaluation Metrics for Interpretable Joint Evaluation of Prompts and Responses",
        "title_source": "rendered_first_page_text",
        "identity_status": "verified",
    },
    "U080": {
        "title": "AIPO: Automatic Instruction Prompt Optimization by Model Itself with Gradient Ascent",
        "title_source": "pdfinfo",
    },
    "U091": {
        "title": "RAPTOR: Recursive Abstractive Processing for Tree-Organized Retrieval",
        "title_source": "rendered_first_page_text",
        "identity_status": "verified_with_title_variation",
        "tier": "C",
        "tier_reason": "Contextual hierarchical retrieval background; retained at the existing tier",
    },
    "U108": {
        "title": "Qwen3 Technical Report",
        "title_source": "rendered_first_page_text",
        "identity_status": "verified",
    },
    "U081": {
        "title": "ResearchRubrics: A Benchmark of Prompts and Rubrics for Evaluating Deep Research Agents",
        "title_source": "pdfinfo",
    },
    "U082": {
        "title": "SkillOpt: Executive Strategy for Self-Evolving Agent Skills",
        "title_source": "pdfinfo",
    },
    "U110": {
        "title": "ICD-10-PCS Official Guidelines for Coding and Reporting 2023",
        "title_source": "pdfinfo",
        "identity_status": "alias_title_mismatch",
        "record_type": "guideline",
        "tier": "N",
        "tier_reason": "Wrong acquisition: coding guidelines under a biomedical knowledge-graph survey alias",
    },
    "U111": {
        "title": "Large Language Models Are Better Reasoners with Self-Verification",
        "title_source": "rendered_first_page_text",
        "identity_status": "alias_title_mismatch",
        "tier": "N",
        "tier_reason": "Wrong acquisition: reasoning paper under an E5-Mistral embedding alias",
    },
    "U114": {
        "title": "New Artificial Intelligence Functionality in PE2E Search",
        "title_source": "pdfinfo",
        "identity_status": "alias_title_mismatch",
        "record_type": "agency_memo",
        "tier": "N",
        "tier_reason": "Wrong acquisition: USPTO PE2E Similarity Search memo under a commercial FTO article alias",
    },
    "U115": {
        "title": "Trademark Guide in Thailand",
        "title_source": "rendered_first_page_text",
        "identity_status": "alias_title_mismatch",
        "record_type": "guide",
        "tier": "N",
        "tier_reason": "Wrong acquisition: trademark guide under a medical-device patent-trends alias",
    },
    "U118": {
        "title": "Graph RAG for Legal Norms: A Hierarchical and Temporal Approach",
        "title_source": "rendered_first_page_text",
        "identity_status": "verified",
    },
    "U138": {
        "title": "Using the Triangle Inequality to Accelerate k-Means",
        "title_source": "pdfinfo",
        "identity_status": "alias_title_mismatch",
        "tier": "N",
        "tier_reason": "Wrong acquisition: k-means paper under a pgvector alias",
    },
    "U143": {
        "title": "Beyond Keywords: Optimizing Legal Information Retrieval through Embeddings, Cross-Encoders, and Large Language Models",
        "title_source": "rendered_title_page_visual_review",
        "identity_status": "verified",
    },
    "U146": {
        "title": "Medical Graph RAG: Towards Safe Medical Large Language Models via Graph Retrieval-Augmented Generation",
        "title_source": "rendered_first_page_text",
        "identity_status": "verified_with_title_variation",
        "tier": "B",
        "tier_reason": "Transferable medical graph-RAG method; alias uses the MedGraphRAG shorthand",
    },
    "U149": {
        "title": "Benchmarking Patent Embeddings: A Multi-Task Evaluation of 22 Models Across Retrieval, Classification, and Clustering",
        "title_source": "rendered_first_page_text",
        "identity_status": "verified",
        "tier": "A",
        "tier_reason": "Direct patent retrieval/search/embedding benchmark evidence",
    },
    "U150": {
        "title": "The Structure of an Academic Paper",
        "title_source": "rendered_first_page_text",
        "identity_status": "verified",
        "record_type": "template",
        "tier": "N",
        "tier_reason": "Non-literature paper-structure template",
    },
    "U151": {
        "title": "SkillOpt-Lite: Better and Faster Agent Self-Evolution via One Line of Vibe",
        "title_source": "pdfinfo",
    },
    "U152": {
        "title": "Marginal Advantage Accumulation for Memory-Driven Agent Self-Evolution",
        "title_source": "pdfinfo",
        "tier": "A",
        "tier_reason": "Direct agent self-evolution optimization evidence for HarnessOpt",
    },
    "U153": {
        "title": "SkillGrad: Optimizing Agent Skills Like Gradient Descent",
        "title_source": "pdfinfo",
    },
}

GENERIC_TITLES = {
    "",
    "untitled",
    "microsoft word",
    "latex2e",
    "full text",
    "main document",
    "paper",
}

STOP_WORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "by",
    "for",
    "from",
    "in",
    "into",
    "of",
    "on",
    "or",
    "the",
    "to",
    "using",
    "via",
    "with",
    "2020",
    "2021",
    "2022",
    "2023",
    "2024",
    "2025",
    "2026",
}

DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE)
DOI_CONTEXT_RE = re.compile(
    r"(?:https?://(?:dx\.)?doi\.org/|\bdoi\s*:\s*)(10\.\d{4,9}/[-._;()/:A-Z0-9]+)",
    re.IGNORECASE,
)
ARXIV_RE = re.compile(
    r"(?:arXiv\s*:\s*|arxiv\.org/(?:abs|pdf)/)(\d{4}\.\d{4,5})",
    re.IGNORECASE,
)

CONTENT_SIGNALS = (
    "retrieval",
    "reranking",
    "ranking",
    "benchmark",
    "patent",
    "prior art",
    "embedding",
    "contrastive",
    "knowledge graph",
    "graph rag",
    "retrieval-augmented",
    "query rewriting",
    "prompt optimization",
    "skill optimization",
    "agent",
    "cross-lingual",
    "thai",
    "legal",
    "biomedical",
    "named entity recognition",
    "classification",
    "summarization",
    "calibration",
    "faithfulness",
    "hallucination",
    "conformal",
)


@dataclass(frozen=True)
class AliasRow:
    uid: str
    dedup_role: str
    sha256: str
    size_bytes: int
    collection: str
    repo_relative_path: str
    canonical_path: str


@dataclass
class PdfMetadata:
    uid: str
    sha256: str
    size_bytes: int
    collection: str
    primary_alias: str
    title: str
    title_source: str
    expected_title: str
    title_token_overlap: float
    identity_status: str
    doi: str
    doi_source: str
    doi_confidence: str
    arxiv_id: str
    arxiv_source: str
    arxiv_confidence: str
    page_count: int
    record_type: str
    tier: str
    tier_reason: str
    abstract_text: str
    conclusion_text: str
    content_signals: list[str]
    source_url: str
    acquired_from: str
    digest_path: str
    object_path: str


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_text(command: list[str]) -> str:
    result = subprocess.run(
        command,
        check=True,
        cwd=RESEARCH_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    for encoding in ("utf-8", "cp1252", "latin-1"):
        try:
            return result.stdout.decode(encoding)
        except UnicodeDecodeError:
            continue
    return result.stdout.decode("utf-8", errors="replace")


def pdf_info(path: Path, sha256: str) -> dict[str, str]:
    cache_path = EXTRACTION_ROOT / f"{sha256}.info.txt"
    text = (
        cache_path.read_text(encoding="utf-8-sig", errors="replace")
        if cache_path.exists()
        else run_text([PDFINFO, str(path)])
    )
    result: dict[str, str] = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        result[key.strip().lower()] = value.strip()
    return result


def pdf_text(path: Path, sha256: str) -> str:
    cache_path = EXTRACTION_ROOT / f"{sha256}.txt"
    return (
        cache_path.read_text(encoding="utf-8-sig", errors="replace")
        if cache_path.exists()
        else run_text([PDFTOTEXT, "-layout", str(path), "-"])
    )


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\x00", " ")).strip()


def expected_title_from_path(path: str) -> str:
    stem = Path(path).stem
    stem = re.sub(r"^_?\d+_+", "", stem)
    stem = re.sub(r"_20(?:1\d|2\d)$", "", stem)
    stem = stem.replace("_", " ")
    return clean_text(stem)


def title_tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if len(token) > 1 and token not in STOP_WORDS
    }


def token_overlap(expected: str, actual: str) -> float:
    expected_tokens = title_tokens(expected)
    actual_tokens = title_tokens(actual)
    if not expected_tokens or not actual_tokens:
        return 0.0
    return len(expected_tokens & actual_tokens) / len(expected_tokens)


def title_supported_by_text(expected: str, text: str) -> float:
    expected_tokens = title_tokens(expected)
    if not expected_tokens:
        return 0.0
    front_matter = " ".join(text.split("\f")[:2])
    document_tokens = title_tokens(front_matter)
    return len(expected_tokens & document_tokens) / len(expected_tokens)


def usable_pdfinfo_title(value: str) -> bool:
    normalized = clean_text(value).lower()
    if normalized in GENERIC_TITLES or len(normalized) < 10:
        return False
    if any(marker in normalized for marker in ("microsoft word", "acrobat distiller", ".docx")):
        return False
    return len(title_tokens(normalized)) >= 3


def title_from_first_page(text: str, expected: str) -> str:
    first_page = text.split("\f", 1)[0]
    raw_lines = [clean_text(line) for line in first_page.splitlines()]
    lines = [line for line in raw_lines if line]
    candidates: list[tuple[float, str]] = []
    exclusions = (
        "abstract",
        "keywords",
        "copyright",
        "arxiv",
        "proceedings",
        "journal",
        "university",
        "department",
        "institute",
        "http://",
        "https://",
        "doi:",
    )
    for start in range(min(35, len(lines))):
        for width in (1, 2, 3):
            candidate = clean_text(" ".join(lines[start : start + width]))
            words = re.findall(r"[A-Za-z][A-Za-z0-9'-]*", candidate)
            if not 4 <= len(words) <= 30 or not 20 <= len(candidate) <= 260:
                continue
            lowered = candidate.lower()
            if lowered.startswith(exclusions) or "@" in candidate:
                continue
            alpha_ratio = sum(char.isalpha() for char in candidate) / max(len(candidate), 1)
            if alpha_ratio < 0.55:
                continue
            overlap = token_overlap(expected, candidate)
            position_bonus = max(0.0, 1.5 - start / 20)
            length_bonus = min(len(words), 18) / 18
            score = overlap * 4 + position_bonus + length_bonus
            candidates.append((score, candidate))
    if not candidates:
        return expected
    return max(candidates, key=lambda item: item[0])[1]


def verified_title(info: dict[str, str], text: str, expected: str) -> tuple[str, str, float, str]:
    info_title = clean_text(info.get("title", ""))
    page_title = title_from_first_page(text, expected)
    candidates = [(token_overlap(expected, page_title), page_title, "first_page_text")]
    if usable_pdfinfo_title(info_title):
        candidates.append((token_overlap(expected, info_title), info_title, "pdfinfo"))
    _, chosen, source = max(candidates, key=lambda item: item[0])
    overlap = token_overlap(expected, chosen)
    if overlap >= 0.60:
        status = "verified"
    elif overlap >= 0.35:
        status = "verified_with_title_variation"
    else:
        status = "alias_title_mismatch"
    return chosen, source, overlap, status


def first_match(pattern: re.Pattern[str], text: str) -> str:
    match = pattern.search(text)
    if not match:
        return ""
    value = match.group(0) if match.lastindex is None else match.group(1)
    return value.rstrip(".,;:)\]}>")


def normalize_doi(value: str) -> str:
    doi = value.strip().rstrip(".,;:)\]}>").lower()
    lowered = doi.lower()
    if (
        not doi
        or re.search(r"(?:x{4,}|n{4,})", lowered)
        or lowered in {"10.48550/arxiv", "10.18653/v1/"}
    ):
        return ""
    if lowered.startswith("10.48550/arxiv."):
        return ""
    return doi


def best_doi_match(pattern: re.Pattern[str], text: str) -> str:
    candidates = {
        normalize_doi(match.group(0) if match.lastindex is None else match.group(1))
        for match in pattern.finditer(text)
    }
    candidates.discard("")
    return max(candidates, key=lambda value: (len(value), value), default="")


def identifier_confidence(source: str) -> str:
    if source in {"acquisition_url", "pdf_metadata"}:
        return "high"
    if source == "pdf_front_matter":
        return "medium"
    return "not_detected"


def verified_identifiers(
    acquisition: dict[str, str], info: dict[str, str], text: str
) -> tuple[str, str, str, str, str, str]:
    """Return conservative identifiers and their evidence source.

    Bibliographies are intentionally excluded. Acquisition URLs are strongest;
    otherwise only explicit DOI/arXiv labels in the PDF front matter are used.
    """

    acquisition_text = " ".join(
        value
        for value in (acquisition.get("source_url", ""), acquisition.get("final_pdf_url", ""))
        if value
    )
    doi = best_doi_match(DOI_RE, acquisition_text)
    arxiv_id = first_match(ARXIV_RE, acquisition_text)
    doi_source = "acquisition_url" if doi else ""
    arxiv_source = "acquisition_url" if arxiv_id else ""

    metadata_text = " ".join(info.values())
    if not doi:
        doi = best_doi_match(DOI_CONTEXT_RE, metadata_text)
        doi_source = "pdf_metadata" if doi else ""
    if not arxiv_id:
        arxiv_id = first_match(ARXIV_RE, metadata_text)
        arxiv_source = "pdf_metadata" if arxiv_id else ""

    first_page = text.split("\f", 1)[0]
    if not doi:
        doi = best_doi_match(DOI_CONTEXT_RE, first_page)
        doi_source = "pdf_front_matter" if doi else ""
    if not arxiv_id:
        arxiv_id = first_match(ARXIV_RE, first_page)
        arxiv_source = "pdf_front_matter" if arxiv_id else ""
    return (
        doi,
        doi_source,
        identifier_confidence(doi_source),
        arxiv_id,
        arxiv_source,
        identifier_confidence(arxiv_source),
    )


def section_excerpt(text: str, heading: str, stop_headings: Iterable[str], limit: int) -> str:
    normalized = text.replace("\r", "")
    heading_match = re.search(rf"(?im)^\s*(?:\d+(?:\.\d+)*\s+)?{heading}\s*$", normalized)
    if not heading_match:
        inline = re.search(rf"(?i)\b{heading}\b\s*[:.-]?\s*", normalized)
        if not inline:
            return ""
        start = inline.end()
    else:
        start = heading_match.end()
    tail = normalized[start : start + limit * 4]
    stop_pattern = "|".join(re.escape(item) for item in stop_headings)
    stop = re.search(rf"(?im)^\s*(?:\d+(?:\.\d+)*\s+)?(?:{stop_pattern})\s*$", tail)
    if stop:
        tail = tail[: stop.start()]
    return clean_text(tail)[:limit]


def find_abstract(text: str) -> str:
    excerpt = section_excerpt(
        text,
        "abstract",
        ("keywords", "index terms", "introduction", "1 introduction", "background"),
        1800,
    )
    if excerpt:
        return excerpt
    first_pages = clean_text(" ".join(text.split("\f")[:2]))
    return first_pages[:1200]


def find_conclusion(text: str) -> str:
    matches = list(re.finditer(r"(?im)^\s*(?:\d+(?:\.\d+)*\s+)?(?:conclusion|conclusions|discussion and conclusion)\s*$", text))
    if not matches:
        return ""
    tail = text[matches[-1].end() :]
    stop = re.search(r"(?im)^\s*(?:references|acknowledg(?:e)?ments|appendix)\s*$", tail)
    if stop:
        tail = tail[: stop.start()]
    return clean_text(tail)[:1400]


def content_signals(text: str) -> list[str]:
    lowered = text.lower()
    return [signal for signal in CONTENT_SIGNALS if signal in lowered]


def read_alias_seed() -> list[AliasRow]:
    if not ARCHIVE_MANIFEST.exists():
        raise FileNotFoundError(f"Missing archived manifest: {ARCHIVE_MANIFEST}")
    rows: list[AliasRow] = []
    with ARCHIVE_MANIFEST.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            rows.append(
                AliasRow(
                    uid=row["unique_id"],
                    dedup_role=row["dedup_role"],
                    sha256=row["sha256"].lower(),
                    size_bytes=int(row["size_bytes"]),
                    collection=row["collection"],
                    repo_relative_path=row["repo_relative_path"].replace("\\", "/"),
                    canonical_path=row["canonical_path"].replace("\\", "/"),
                )
            )
    for uid, pinned in NEW_UID_OBJECTS.items():
        relative_path = str(pinned["path"])
        digest = str(pinned["sha256"])
        rows.append(
            AliasRow(
                uid=uid,
                dedup_role="canonical",
                sha256=digest,
                size_bytes=int(pinned["size_bytes"]),
                collection="is1",
                repo_relative_path=relative_path,
                canonical_path=relative_path,
            )
        )
    return rows


def read_acquisition_metadata() -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for relative in (
        "research/ref-paper/is1/pdf-acquisition-status.csv",
        "research/ref-paper/is2/pdf-acquisition-status.csv",
        "research/ref-paper/shared/pdf-acquisition-status.csv",
    ):
        path = APP_ROOT / relative
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                filename = row.get("pdf_filename", "")
                if filename:
                    result[filename] = row
    return result


def frozen_digest_metadata() -> dict[str, tuple[str, str]]:
    metadata: dict[str, tuple[str, str]] = {}
    for path in sorted(DIGEST_ROOT.glob("U0[0-4][0-9]_*.md")):
        uid = path.name[:4]
        if int(uid[1:]) > 40:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        tier_match = re.search(r'(?m)^(?:priority_)?tier:\s*["\']?([ABCN])', text)
        title_match = re.search(r'(?m)^title:\s*(.+?)\s*$', text)
        if not tier_match or not title_match:
            raise ValueError(f"Frozen digest metadata incomplete: {path}")
        raw_title = title_match.group(1).strip()
        title = json.loads(raw_title) if raw_title.startswith('"') else raw_title.strip("'\"")
        metadata[uid] = (title, tier_match.group(1))
    if set(metadata) != {f"U{value:03d}" for value in range(1, 41)}:
        raise ValueError("Expected frozen metadata for U001-U040")
    return metadata


def assign_tier(uid: str, title: str, abstract: str, identity_status: str, record_type: str) -> tuple[str, str]:
    if record_type == "template":
        return "N", "Non-literature paper-structure template"
    if identity_status == "alias_title_mismatch":
        return "N", "Source alias does not match the PDF's verified title; retained for provenance review"
    text = f"{title} {abstract}".lower()
    patent = "patent" in text or "prior art" in text
    retrieval = any(term in text for term in ("retrieval", "search", "rerank", "ranking", "embedding"))
    benchmark = any(term in text for term in ("benchmark", "dataset", "evaluation"))
    if patent and retrieval and benchmark:
        return "A", "Direct patent retrieval/search/embedding benchmark evidence"
    if patent and retrieval:
        return "A", "Direct patent retrieval, ranking, or representation method"
    if any(term in text for term in ("prompt optimization", "skill optimization", "skillgrad", "skillopt", "textgrad", "gepa")):
        return "A", "Direct HarnessOpt/skill/prompt optimization method evidence"
    if any(
        term in text
        for term in (
            "information retrieval",
            "retrieval-augmented",
            "retrieval augmented",
            "rerank",
            "ranking",
            "query rewriting",
            "dense retrieval",
            "late interaction",
            "embedding model",
            "knowledge graph",
            "graph rag",
            "faithfulness",
            "hallucination",
            "conformal prediction",
        )
    ):
        return "B", "Transferable retrieval, RAG, evaluation, uncertainty, or knowledge-graph method"
    if any(term in text for term in ("thai legal", "legal qa", "cross-lingual", "thai language")):
        return "B", "Transferable Thai/cross-lingual/legal evidence for the adjacent IS2 track"
    return "C", "Contextual domain, classification, extraction, model, survey, or systems background"


def slugify(title: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
    return value[:72].rstrip("_") or "untitled"


def tier_pdf_relative_path(uid: str, tier: str, title: str) -> str:
    return f"01_evidence/{tier}-tier/{uid}_{slugify(title)}.pdf"


def find_source_pdf(alias: AliasRow) -> Path:
    app_path = APP_ROOT / alias.repo_relative_path
    if app_path.is_file():
        return app_path

    legacy_object = LEGACY_OBJECT_ROOT / alias.sha256[:2] / f"{alias.sha256}.pdf"
    if legacy_object.is_file():
        return legacy_object

    tier_matches = sorted(TIER_ROOT.glob(f"[ABCN]-tier/{alias.uid}_*.pdf"))
    if len(tier_matches) == 1:
        return tier_matches[0]
    if len(tier_matches) > 1:
        raise ValueError(
            f"Multiple tier PDFs found for {alias.uid}: "
            + ", ".join(str(path) for path in tier_matches)
        )
    raise FileNotFoundError(
        f"Missing App, legacy object, and tier PDF for {alias.repo_relative_path}"
    )


def write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def yaml_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=True)


def digest_markdown(metadata: PdfMetadata) -> str:
    signals = ", ".join(metadata.content_signals) or "No controlled keyword signal detected"
    abstract = (metadata.abstract_text or "No reliable abstract section was extracted.").rstrip()
    conclusion = (metadata.conclusion_text or "No reliable conclusion section was extracted.").rstrip()
    relevant_tracks = []
    title_text = f"{metadata.title} {metadata.abstract_text}".lower()
    if "patent" in title_text or "retrieval" in title_text or "ranking" in title_text:
        relevant_tracks.extend(["C", "R"])
    if any(term in title_text for term in ("prompt", "skill", "agent", "optimization")):
        relevant_tracks.append("H/S")
    if any(term in title_text for term in ("thai", "legal", "knowledge graph", "cross-lingual")):
        relevant_tracks.append("IS2-adjacent")
    if not relevant_tracks:
        relevant_tracks.append("background")
    tracks = ", ".join(dict.fromkeys(relevant_tracks))
    doi_value = metadata.doi or "not detected"
    arxiv_value = metadata.arxiv_id or "not detected"
    return f'''---
paper_id: {metadata.uid}
title: {yaml_quote(metadata.title)}
pdf_sha256: {yaml_quote(metadata.sha256)}
object_path: {yaml_quote(metadata.object_path)}
legacy_primary_alias: {yaml_quote(metadata.primary_alias)}
doi: {yaml_quote(metadata.doi)}
doi_source: {yaml_quote(metadata.doi_source)}
doi_confidence: {yaml_quote(metadata.doi_confidence)}
arxiv_id: {yaml_quote(metadata.arxiv_id)}
arxiv_source: {yaml_quote(metadata.arxiv_source)}
arxiv_confidence: {yaml_quote(metadata.arxiv_confidence)}
page_count: {metadata.page_count}
record_type: {yaml_quote(metadata.record_type)}
tier: {yaml_quote(metadata.tier)}
identity_status: {yaml_quote(metadata.identity_status)}
review_depth: "metadata_plus_full_text_section_scan"
digest_created: {yaml_quote(date.today().isoformat())}
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# {metadata.uid}: {metadata.title}

## Bibliographic Identity

- Verified title source: `{metadata.title_source}`
- DOI: {doi_value} (source: {metadata.doi_source or 'not detected'}; confidence: {metadata.doi_confidence})
- arXiv ID: {arxiv_value} (source: {metadata.arxiv_source or 'not detected'}; confidence: {metadata.arxiv_confidence})
- Pages: {metadata.page_count}
- Source collection: `{metadata.collection}`
- Legacy primary alias: `{metadata.primary_alias}`
- Identity result: `{metadata.identity_status}` (filename/title token overlap {metadata.title_token_overlap:.2f})

## Classification

**Tier {metadata.tier}.** {metadata.tier_reason}. Relevant surface: {tracks}.

## Content Triage

Controlled content signals found in the full-text extraction: {signals}.

Abstract/summary section scan:

> {abstract}

Conclusion/discussion section scan:

> {conclusion}

## Evidence Use

This record is indexed for source discovery and method/background triage. Any
numeric or comparative claim used in a paper, thesis, slide, or experiment
protocol must be checked against the canonical PDF object and cited to the
relevant page; this digest is not a substitute for claim-level verification.

## Limitations And Verification

- Review depth is metadata verification plus a full-text scan for abstract,
  conclusion, and controlled topic signals. Identifiers are recorded only from
  acquisition URLs, PDF metadata, or explicitly labeled first-page front
  matter; bibliographies are excluded from identifier discovery.
- Tables, figures, equations, appendices, and numeric results were not
  independently transcribed in this corpus migration pass.
- Legacy aliases remain in `catalog/legacy_aliases.csv`; misleading aliases do
  not create a second paper identity.
'''


def build_metadata(alias_rows: list[AliasRow]) -> tuple[list[PdfMetadata], list[dict[str, object]]]:
    acquisition = read_acquisition_metadata()
    frozen_metadata = frozen_digest_metadata()
    aliases_by_uid: dict[str, list[AliasRow]] = defaultdict(list)
    for row in alias_rows:
        aliases_by_uid[row.uid].append(row)

    canonical_rows = [row for row in alias_rows if row.dedup_role == "canonical"]
    if len(canonical_rows) != 153:
        raise ValueError(f"Expected 153 canonical rows, found {len(canonical_rows)}")

    metadata_rows: list[PdfMetadata] = []
    identity_rows: list[dict[str, object]] = []
    for index, alias in enumerate(canonical_rows, start=1):
        source_path = find_source_pdf(alias)
        actual_sha = sha256_file(source_path)
        if actual_sha != alias.sha256:
            raise ValueError(f"SHA mismatch for {alias.repo_relative_path}: {actual_sha} != {alias.sha256}")
        if source_path.stat().st_size != alias.size_bytes:
            raise ValueError(f"Size mismatch for {alias.repo_relative_path}")

        info = pdf_info(source_path, alias.sha256)
        full_text = pdf_text(source_path, alias.sha256)
        acq = acquisition.get(Path(alias.repo_relative_path).name, {})
        filename_expected = expected_title_from_path(alias.repo_relative_path)
        expected = clean_text(acq.get("paper", "")) or filename_expected
        title, title_source, overlap, identity_status = verified_title(info, full_text, expected)
        text_support = title_supported_by_text(expected, full_text)
        if acq and text_support >= 0.80:
            title = expected
            title_source = "acquisition_metadata_verified_in_pdf"
            identity_status = "verified" if text_support >= 0.95 else "verified_with_title_variation"
            overlap = text_support
        (
            doi,
            doi_source,
            doi_confidence,
            arxiv_id,
            arxiv_source,
            arxiv_confidence,
        ) = verified_identifiers(acq, info, full_text)
        pages_raw = info.get("pages", "0")
        page_count = int(pages_raw) if pages_raw.isdigit() else 0
        record_type = "template" if alias.uid == "U150" else "paper"
        abstract = find_abstract(full_text)
        conclusion = find_conclusion(full_text)
        signals = content_signals(full_text)
        if alias.uid in frozen_metadata:
            title, _historical_tier = frozen_metadata[alias.uid]
            title_source = "frozen_digest_verified_against_pdf"
            identity_status = "verified"
            overlap = token_overlap(expected, title)
            tier, tier_reason = assign_tier(
                alias.uid, title, abstract, identity_status, record_type
            )
        else:
            tier, tier_reason = assign_tier(alias.uid, title, abstract, identity_status, record_type)

        override = CURATED_OVERRIDES.get(alias.uid, {})
        title = override.get("title", title)
        title_source = override.get("title_source", title_source)
        identity_status = override.get("identity_status", identity_status)
        record_type = override.get("record_type", record_type)
        tier = override.get("tier", tier)
        tier_reason = override.get("tier_reason", tier_reason)

        source_url = acq.get("source_url", "")
        acquired_from = acq.get("final_pdf_url", "")
        object_path = tier_pdf_relative_path(alias.uid, tier, title)
        if int(alias.uid[1:]) <= 40:
            matches = sorted(DIGEST_ROOT.glob(f"{alias.uid}_*.md"))
            if len(matches) != 1:
                raise ValueError(f"Expected one frozen digest for {alias.uid}, found {len(matches)}")
            digest_path = matches[0].relative_to(RESEARCH_ROOT).as_posix()
        else:
            digest_path = f"01_evidence/literature/validated-digests/{alias.uid}_{slugify(title)}_digest.md"

        metadata = PdfMetadata(
            uid=alias.uid,
            sha256=alias.sha256,
            size_bytes=alias.size_bytes,
            collection=alias.collection,
            primary_alias=alias.repo_relative_path,
            title=title,
            title_source=title_source,
            expected_title=expected,
            title_token_overlap=overlap,
            identity_status=identity_status,
            doi=doi,
            doi_source=doi_source,
            doi_confidence=doi_confidence,
            arxiv_id=arxiv_id,
            arxiv_source=arxiv_source,
            arxiv_confidence=arxiv_confidence,
            page_count=page_count,
            record_type=record_type,
            tier=tier,
            tier_reason=tier_reason,
            abstract_text=abstract,
            conclusion_text=conclusion,
            content_signals=signals,
            source_url=source_url,
            acquired_from=acquired_from,
            digest_path=digest_path,
            object_path=object_path,
        )
        metadata_rows.append(metadata)
        for legacy in aliases_by_uid[alias.uid]:
            alias_expected = expected_title_from_path(legacy.repo_relative_path)
            alias_overlap = token_overlap(alias_expected, title)
            alias_identity = (
                "verified" if alias_overlap >= 0.60 else
                "verified_with_title_variation" if alias_overlap >= 0.35 else
                "alias_title_mismatch"
            )
            identity_rows.append(
                {
                    "u_id": alias.uid,
                    "legacy_path": legacy.repo_relative_path,
                    "expected_title_from_alias": alias_expected,
                    "verified_title": title,
                    "title_source": title_source,
                    "title_token_overlap": f"{alias_overlap:.4f}",
                    "identity_status": alias_identity,
                    "doi": doi,
                    "doi_source": doi_source,
                    "doi_confidence": doi_confidence,
                    "arxiv_id": arxiv_id,
                    "arxiv_source": arxiv_source,
                    "arxiv_confidence": arxiv_confidence,
                }
            )
        print(f"[{index:03d}/153] {alias.uid} {identity_status} {title[:80]}")
    return metadata_rows, identity_rows


def emit_outputs(alias_rows: list[AliasRow], metadata_rows: list[PdfMetadata], identity_rows: list[dict[str, object]]) -> None:
    metadata_by_uid = {row.uid: row for row in metadata_rows}
    CATALOG_ROOT.mkdir(parents=True, exist_ok=True)
    DIGEST_ROOT.mkdir(parents=True, exist_ok=True)
    QA_ROOT.mkdir(parents=True, exist_ok=True)

    manifest_fields = [
        "u_id", "sha256", "size_bytes", "collection", "record_type", "verified_title",
        "title_source", "identity_status", "title_token_overlap", "doi", "doi_source",
        "doi_confidence", "arxiv_id", "arxiv_source", "arxiv_confidence",
        "page_count", "tier", "source_url", "acquired_from", "legacy_primary_alias",
        "object_path", "digest_path",
    ]
    write_csv(
        CATALOG_ROOT / "corpus_manifest.csv",
        manifest_fields,
        (
            {
                "u_id": row.uid,
                "sha256": row.sha256,
                "size_bytes": row.size_bytes,
                "collection": row.collection,
                "record_type": row.record_type,
                "verified_title": row.title,
                "title_source": row.title_source,
                "identity_status": row.identity_status,
                "title_token_overlap": f"{row.title_token_overlap:.4f}",
                "doi": row.doi,
                "doi_source": row.doi_source,
                "doi_confidence": row.doi_confidence,
                "arxiv_id": row.arxiv_id,
                "arxiv_source": row.arxiv_source,
                "arxiv_confidence": row.arxiv_confidence,
                "page_count": row.page_count,
                "tier": row.tier,
                "source_url": row.source_url,
                "acquired_from": row.acquired_from,
                "legacy_primary_alias": row.primary_alias,
                "object_path": row.object_path,
                "digest_path": row.digest_path,
            }
            for row in metadata_rows
        ),
    )

    alias_fields = [
        "u_id", "legacy_path", "sha256", "size_bytes", "collection", "dedup_role",
        "historical_canonical_path", "object_path", "alias_identity_status",
    ]
    identity_by_path = {str(row["legacy_path"]): str(row["identity_status"]) for row in identity_rows}
    write_csv(
        CATALOG_ROOT / "legacy_aliases.csv",
        alias_fields,
        (
            {
                "u_id": row.uid,
                "legacy_path": row.repo_relative_path,
                "sha256": row.sha256,
                "size_bytes": row.size_bytes,
                "collection": row.collection,
                "dedup_role": row.dedup_role,
                "historical_canonical_path": row.canonical_path,
                "object_path": metadata_by_uid[row.uid].object_path,
                "alias_identity_status": identity_by_path[row.repo_relative_path],
            }
            for row in alias_rows
        ),
    )

    tier_fields = ["u_id", "tier", "reason", "verified_title", "sha256", "digest_path"]
    tier_rows = [
        {
            "u_id": row.uid,
            "tier": row.tier,
            "reason": row.tier_reason,
            "verified_title": row.title,
            "sha256": row.sha256,
            "digest_path": row.digest_path,
        }
        for row in metadata_rows
    ]
    write_csv(CATALOG_ROOT / "tier_assignments.csv", tier_fields, tier_rows)
    for tier in "ABCN":
        write_csv(
            CATALOG_ROOT / f"tier_{tier}.csv",
            ["u_id", "verified_title", "sha256", "object_path", "digest_path"],
            (
                {
                    "u_id": row.uid,
                    "verified_title": row.title,
                    "sha256": row.sha256,
                    "object_path": row.object_path,
                    "digest_path": row.digest_path,
                }
                for row in metadata_rows
                if row.tier == tier
            ),
        )

    write_csv(
        QA_ROOT / "CORPUS_IDENTITY_REVIEW.csv",
        [
            "u_id", "legacy_path", "expected_title_from_alias", "verified_title",
            "title_source", "title_token_overlap", "identity_status", "doi", "doi_source",
            "doi_confidence", "arxiv_id", "arxiv_source", "arxiv_confidence",
        ],
        identity_rows,
    )

    for row in metadata_rows:
        if int(row.uid[1:]) <= 40:
            continue
        digest_path = RESEARCH_ROOT / row.digest_path
        digest_path.write_text(digest_markdown(row), encoding="utf-8", newline="\n")

    duplicate_groups = sum(1 for count in Counter(row.sha256 for row in alias_rows).values() if count > 1)
    tier_counts = Counter(row.tier for row in metadata_rows)
    identity_counts = Counter(str(row["identity_status"]) for row in identity_rows)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_pdf_paths": len(alias_rows),
        "unique_sha256": len(metadata_rows),
        "duplicate_groups": duplicate_groups,
        "digests_frozen_untouched": 40,
        "digests_generated": sum(1 for row in metadata_rows if int(row.uid[1:]) >= 41),
        "tier_counts": dict(sorted(tier_counts.items())),
        "alias_identity_counts": dict(sorted(identity_counts.items())),
        "identifier_counts": {
            "doi": sum(1 for row in metadata_rows if row.doi),
            "arxiv_id": sum(1 for row in metadata_rows if row.arxiv_id),
        },
        "identifier_source_counts": {
            "doi": dict(sorted(Counter(row.doi_source or "not_detected" for row in metadata_rows).items())),
            "arxiv_id": dict(sorted(Counter(row.arxiv_source or "not_detected" for row in metadata_rows).items())),
        },
        "u082_primary_alias": metadata_by_uid["U082"].primary_alias,
        "new_uid_paths": {uid: str(pinned["path"]) for uid, pinned in NEW_UID_OBJECTS.items()},
        "u150_record_type": metadata_by_uid["U150"].record_type,
        "u150_tier": metadata_by_uid["U150"].tier,
    }
    (QA_ROOT / "CORPUS_BUILD_REPORT.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Extract and print metadata without writing catalog or digest files.",
    )
    args = parser.parse_args()
    alias_rows = read_alias_seed()
    if len(alias_rows) != 169:
        raise ValueError(f"Expected 169 source paths, found {len(alias_rows)}")
    metadata_rows, identity_rows = build_metadata(alias_rows)
    if not args.report_only:
        emit_outputs(alias_rows, metadata_rows, identity_rows)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, subprocess.CalledProcessError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
