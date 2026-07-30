---
paper_id: U083
title: "BEIR: A Heterogeneous Benchmark for Zero-shot Evaluation of Information Retrieval Models"
pdf_sha256: "1925755aeb627123d1a63c66f02e5aa2432f7e92751a02bea7c8c3b6bbb6ec33"
object_path: "01_evidence/B-tier/U083_beir_a_heterogeneous_benchmark_for_zero_shot_evaluation_of_information_r.pdf"
legacy_primary_alias: "research/ref-paper/shared/pdfs/01_beir_a_heterogeneous_benchmark_for_zero_2021.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: "2104.08663"
arxiv_source: "acquisition_url"
arxiv_confidence: "high"
page_count: 24
record_type: "paper"
tier: "B"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U083: BEIR: A Heterogeneous Benchmark for Zero-shot Evaluation of Information Retrieval Models

## Bibliographic Identity

- Verified title source: `acquisition_metadata_verified_in_pdf`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: 2104.08663 (source: acquisition_url; confidence: high)
- Pages: 24
- Source collection: `shared`
- Legacy primary alias: `research/ref-paper/shared/pdfs/01_beir_a_heterogeneous_benchmark_for_zero_2021.pdf`
- Identity result: `verified` (filename/title token overlap 1.00)

## Classification

**Tier B.** Transferable retrieval, RAG, evaluation, uncertainty, or knowledge-graph method. Relevant surface: C, R.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, ranking, benchmark, embedding, contrastive, cross-lingual, legal, biomedical, classification.

Abstract/summary section scan:

> Existing neural information retrieval (IR) models have often been studied in ho- mogeneous and narrow settings, which has considerably limited insights into their out-of-distribution (OOD) generalization capabilities. To address this, and to facili- tate researchers to broadly evaluate the effectiveness of their models, we introduce Benchmarking-IR (BEIR), a robust and heterogeneous evaluation benchmark for information retrieval. We leverage a careful selection of 18 publicly available datasets from diverse text retrieval tasks and domains and evaluate 10 state-of-the- art retrieval systems including lexical, sparse, dense, late-interaction and re-ranking architectures on the BEIR benchmark. Our results show BM25 is a robust baseline and re-ranking and late-interaction based models on average achieve the best zero- shot performances, however, at high computational costs. In contrast, dense and sparse-retrieval models are computationally more efficient but often underperform other approaches, highlighting the considerable room for improvement in their generalization capabilities. We hope this framework allows us to better evaluate and understand existing retrieval systems, and contributes to accelerating progress towards better robust and generalizable systems in the future. BEIR is publicly available at https://github.com/UKPLab/beir.

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
