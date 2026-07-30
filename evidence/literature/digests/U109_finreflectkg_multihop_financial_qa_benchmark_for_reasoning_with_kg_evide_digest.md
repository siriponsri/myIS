---
paper_id: U109
title: "FinReflectKG-MultiHop: Financial QA Benchmark for Reasoning with KG Evidence"
pdf_sha256: "c8465346b6321cf54646d28e017ad929c5d85850dfd1c89340ae5ad9680f744f"
object_path: "01_evidence/B-tier/U109_finreflectkg_multihop_financial_qa_benchmark_for_reasoning_with_kg_evide.pdf"
legacy_primary_alias: "research/ref-paper/shared/pdfs/35_finreflectkg_multihop_financial_qa_benchmark_for_2025.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: "2510.02906"
arxiv_source: "acquisition_url"
arxiv_confidence: "high"
page_count: 11
record_type: "paper"
tier: "B"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U109: FinReflectKG-MultiHop: Financial QA Benchmark for Reasoning with KG Evidence

## Bibliographic Identity

- Verified title source: `acquisition_metadata_verified_in_pdf`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: 2510.02906 (source: acquisition_url; confidence: high)
- Pages: 11
- Source collection: `shared`
- Legacy primary alias: `research/ref-paper/shared/pdfs/35_finreflectkg_multihop_financial_qa_benchmark_for_2025.pdf`
- Identity result: `verified` (filename/title token overlap 1.00)

## Classification

**Tier B.** Transferable retrieval, RAG, evaluation, uncertainty, or knowledge-graph method. Relevant surface: C, R, H/S, IS2-adjacent.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, ranking, benchmark, knowledge graph, retrieval-augmented, agent, biomedical.

Abstract/summary section scan:

> Multi-hop reasoning over financial disclosures is often a retrieval problem before it becomes a reasoning or generation problem: relevant facts are dispersed across sections, filings, companies, and years, and LLMs often expend excessive tokens navigating noisy context. Without precise Knowledge Graph (KG)-guided selec- tion of relevant context, even strong reasoning models either fail to answer or consume excessive tokens, whereas KG-linked evidence enables models to focus their reasoning on composing already retrieved facts. We present FinReflectKG - MultiHop, a benchmark built on FinReflectKG, a temporally indexed financial KG that links audited triples to source chunks from S&P 100 filings (2022-2024). Mining frequent 2-3 hop subgraph patterns across sectors (via GICS taxonomy), we generate financial analyst style questions with exact supporting evidence from the KG. A two-phase pipeline first creates QA pairs via pattern-specific prompts, followed by a multi-criteria quality control evaluation to ensure QA validity. We then evaluate three controlled retrieval scenarios: (S1) precise KG-linked paths; (S2) text-only page windows centered on relevant text spans; and (S3) relevant page windows with randomizations & distractors. Across both reasoning and non-reasoning models, KG-guided precise retrieval yields substantial gains on the FinReflectKG - MultiHop QA benchmark dataset, boosting correctness scores by ∼ 24% while reducing token utilization by ∼ 84.5% compared to the page- window setting, which reflects the traditional vector retrieval paradigm. Spanning intra-document, inter-year, and cross-company scopes, our work underscores the pivotal role of knowledge graphs in efficiently connecting evidence for multi-hop financial QA. We also release a curated subset of

Conclusion/discussion section scan:

> No reliable conclusion section was extracted.

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
