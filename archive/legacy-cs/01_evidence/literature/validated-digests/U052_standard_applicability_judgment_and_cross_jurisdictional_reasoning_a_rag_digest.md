---
paper_id: U052
title: "Standard Applicability Judgment and Cross-jurisdictional Reasoning: A RAG-based Framework for Medical Device Compliance"
pdf_sha256: "ddac13574791a286a2685fe68b41c207638c376201a54e9598e73068fd3978ee"
object_path: "01_evidence/B-tier/U052_standard_applicability_judgment_and_cross_jurisdictional_reasoning_a_rag.pdf"
legacy_primary_alias: "research/ref-paper/is1/pdfs/53_standard_applicability_judgment_and_cross_jurisdictional_2025.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: "2506.18511"
arxiv_source: "acquisition_url"
arxiv_confidence: "high"
page_count: 25
record_type: "paper"
tier: "B"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U052: Standard Applicability Judgment and Cross-jurisdictional Reasoning: A RAG-based Framework for Medical Device Compliance

## Bibliographic Identity

- Verified title source: `acquisition_metadata_verified_in_pdf`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: 2506.18511 (source: acquisition_url; confidence: high)
- Pages: 25
- Source collection: `is1`
- Legacy primary alias: `research/ref-paper/is1/pdfs/53_standard_applicability_judgment_and_cross_jurisdictional_2025.pdf`
- Identity result: `verified` (filename/title token overlap 1.00)

## Classification

**Tier B.** Transferable retrieval, RAG, evaluation, uncertainty, or knowledge-graph method. Relevant surface: C, R, H/S.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, reranking, ranking, benchmark, embedding, retrieval-augmented, agent, cross-lingual, legal, biomedical, classification, summarization, hallucination.

Abstract/summary section scan:

> Identifying the appropriate regulatory standard applicability remains a critical yet under- studied challenge in medical device compliance, frequently necessitating expert interpretation of fragmented and heterogeneous documentation across different jurisdictions. To address this challenge, we introduce a modular AI system that leverages a retrieval-augmented gen- eration (RAG) pipeline to automate standard applicability determination. Given a free-text device description, our system retrieves candidate standards from a curated corpus and uses large language models to infer jurisdiction-specific applicability—classified as Mandatory, Recommended, or Not Applicable—with traceable justifications. We construct an inter- national benchmark dataset of medical device descriptions with expert-annotated standard mappings, and evaluate our system against retrieval-only, zero-shot, and rule-based baselines. The proposed approach attains a classification accuracy of 73% and a Top-5 retrieval recall of 87%, demonstrating its effectiveness in identifying relevant regulatory standards. We intro- duce the first end-to-end system for standard applicability reasoning, enabling scalable and interpretable AI-supported regulatory science. Notably, our region-aware RAG agent per- forms cross-jurisdictional reasoning between Chinese and U.S. standards, supporting conflict resolution and applicability justification across regulatory frameworks. Index terms: Regulatory Science; Compliance; Standard Applicability; Retrieval-Augmented Generation (RAG); Intelligent Agents; Semantic Retrieval; AI for Law / Healthcare Regula- tion;simulate expert reasoning; chain-of-thought; fallback rules; domain-specific judgment

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
