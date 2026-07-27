---
paper_id: U102
title: "NitiBench: A Comprehensive Study of LLM Framework Capabilities for Thai Legal QA"
pdf_sha256: "bce607dec5791b8dec916ed010c9a2538fa4af63982ea07bab005e7ee73c8bda"
object_path: "01_evidence/B-tier/U102_nitibench_a_comprehensive_study_of_llm_framework_capabilities_for_thai_l.pdf"
legacy_primary_alias: "research/ref-paper/shared/pdfs/24_nitibench_a_comprehensive_study_of_llm_2025.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: "2502.10868"
arxiv_source: "acquisition_url"
arxiv_confidence: "high"
page_count: 53
record_type: "paper"
tier: "B"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U102: NitiBench: A Comprehensive Study of LLM Framework Capabilities for Thai Legal QA

## Bibliographic Identity

- Verified title source: `acquisition_metadata_verified_in_pdf`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: 2502.10868 (source: acquisition_url; confidence: high)
- Pages: 53
- Source collection: `shared`
- Legacy primary alias: `research/ref-paper/shared/pdfs/24_nitibench_a_comprehensive_study_of_llm_2025.pdf`
- Identity result: `verified` (filename/title token overlap 1.00)

## Classification

**Tier B.** Transferable Thai/cross-lingual/legal evidence for the adjacent IS2 track. Relevant surface: C, R, IS2-adjacent.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, reranking, ranking, benchmark, embedding, knowledge graph, retrieval-augmented, agent, thai, legal, classification, summarization, faithfulness, hallucination.

Abstract/summary section scan:

> and general sections constitute foundational knowledge that the LLM requires for all queries within a RAG system, rather than retrieving them selectively. Second, keyword matching retrieval could prove effective for terminology sections, as query terms often directly match defined phrases. Beyond the Generic Section Retrieval Challenge, our analysis of NitiBench-Tax revealed two additional error categories: 6.6.2 Incorrect Legislation Retrieval Table 21 presents the distribution of false positives at the law code level. Law Code False Positive Revenue Code 280 Petroleum Income Tax Act, B.E. 2514 30 Civil and Commercial Code 21 Securities and Exchange Act, B.E. 2535 15 Government Procurement and Supplies Management Act, B.E. 2560 15 Budget Procedure Act, B.E. 2561 14 Energy Industry Act, B.E. 2550 12 Business Registration Act, B.E. 2499 10 Public Limited Companies Act, B.E. 2535 8 Energy Conservation Promotion Act, B.E. 2535 5 Trust for Transactions in Capital Market Act, B.E. 2550 5 Financial Institutions Business Act, B.E. 2551 4 National Economic and Social Development Act, B.E. 2561 3 Accounting Profession Act, B.E. 2547 3 Act on the Management of Shares and Stocks of Ministers, B.E. 2543 2 State Enterprise Development and Governance Act, B.E. 2562 2 Fiscal Discipline Act, B.E. 2561 2 Accounting Act, B.E. 2543 1 Emergency Decree on Special Purpose Juristic Person for Securitization, B.E. 2540 1 Provident Fund Act, B.E. 2530 1 Emergency Decree on Digital Asset Businesses, B.E. 2561 1 Foreign Business Act, B.E. 2542 1 Derivatives Act, B.E. 2546 1 Table 21: False positive distribution on NitiBench-Tax on law code level While the NitiBench-Tax’s ground truth labels span only 4 legislation, retrieved false positives originate from 21 different legislation. This mirrors th

Conclusion/discussion section scan:

> One of the most significant challenges in implementing LLMs for Thai Legal QA systems is the lack of a standardized evaluation process. This issue arises due to the limited availability of Thai legal QA corpora and the absence of robust evaluation metrics. To address this, we introduce a novel benchmark dataset along with a corresponding task and evaluation framework named NitiBench. Specifically, we construct two datasets: (1) NitiBench-CCL (derived from WangchanX-Legal-ThaiCCL), which covers general QA across 21 Thai financial law codes in its test split and 35 codes in its training split, and (2) NitiBench-Tax, which focuses on specialized QA involving real-world tax cases from the Thai Revenue Department, requiring extensive legal reasoning. To complement this benchmark, we propose an evaluation framework that includes: (1) Multi-label retrieval metrics, in addition to traditional single-label metrics; (2) An E2E task, evaluating the system’s ability to generate correct answers consistent with ground truth while providing accurate legal citations; and (3) E2E evaluation metrics, measuring Coverage (how well the generated answer aligns with the ground truth), Contradiction (whether the generated answer contradicts the ground truth), and Citation (the accuracy of legal citations provided in the generated answer). Using the proposed benchmark, we aim to address the research qu

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
