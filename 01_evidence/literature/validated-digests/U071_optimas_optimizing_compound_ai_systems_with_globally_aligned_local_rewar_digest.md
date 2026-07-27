---
paper_id: U071
title: "OPTIMAS: Optimizing Compound AI Systems with Globally Aligned Local Rewards"
pdf_sha256: "2cb380e7918e990a19a32f9b6adcba46d8b2ba98987c2844edfba6e11e9fc744"
object_path: "01_evidence/B-tier/U071_optimas_optimizing_compound_ai_systems_with_globally_aligned_local_rewar.pdf"
legacy_primary_alias: "research/ref-paper/is1/pdfs/73_optimizing_compound_ai_systems.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: "2507.03041"
arxiv_source: "pdf_front_matter"
arxiv_confidence: "medium"
page_count: 22
record_type: "paper"
tier: "B"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U071: OPTIMAS: Optimizing Compound AI Systems with Globally Aligned Local Rewards

## Bibliographic Identity

- Verified title source: `acquisition_metadata_verified_in_pdf`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: 2507.03041 (source: pdf_front_matter; confidence: medium)
- Pages: 22
- Source collection: `is1`
- Legacy primary alias: `research/ref-paper/is1/pdfs/73_optimizing_compound_ai_systems.pdf`
- Identity result: `verified` (filename/title token overlap 1.00)

## Classification

**Tier B.** Transferable retrieval, RAG, evaluation, uncertainty, or knowledge-graph method. Relevant surface: C, R, H/S, IS2-adjacent.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, ranking, benchmark, embedding, contrastive, knowledge graph, retrieval-augmented, prompt optimization, agent, biomedical, classification.

Abstract/summary section scan:

> pairs. Our compound system frames the task as three-way classification; exact-match accuracy is reported. STA RK-P RIME (Semi-Structured Knowledge Base Retrieval). STA RK-P RIME -Prime origi- nates from STARK benchmark introduced by (Wu et al., 2024b). It blends free-text passages with relational triples from biomedical knowledge graphs. Queries are natural-language questions; rele- vance labels are automatically propagated from the original STARK annotations. We uses the original dataset split: 495 / 51 / 96 queries. Performance is measured by Hit@1, which is the rate of ranking the ground truth items in the predicted ranking list. H OTPOT QA (Retrieval-Augmented Multi-Hop QA). We adopt the H OTPOT QA (Yang et al., 2018) and keep the official train/dev/test splits: 1000, 250, and 100 questions respectively. Each example in the set contains a question and its (human-annotated) answer. We report answer-level F1 score. B IG C ODE B ENCH (Self-Verified Code Generation). We use a subset of the full-instruction subset of BigCodeBench (Zhuo et al., 2024) due to efficiency issue. After proportionally drop the data, we obtain 500 / 25 / 70 coding tasks. Each sample includes a natural-language specification and reference unit tests. Our metric is pass@1: the proportion of generated programs that pass all tests in one try. D C OMPOUND AI S YSTEM D ETAILS Table 5 summarizes each pipeline’s modules (columns: System, Module, Model, Config, and Opti- mization). In the table below, we clarify the various configuration spaces and optimization methods used across the five systems. A MAZON (Behavior-Driven Next-item Recommendation). Session Analyzer and Candidate Pro- filer both use the Qwen 2.5 1.5B model; we optimize their model parameters with PPO reinforcement learning (Schulman et a

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
