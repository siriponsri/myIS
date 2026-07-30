---
paper_id: U144
title: "Case-Aware LLM-as-a-Judge for Enterprise RAG"
pdf_sha256: "079b2c06a2d90c717d86e1c2127122ce9a7ac5e2b574ce26162d1155b02fc02a"
object_path: "01_evidence/B-tier/U144_case_aware_llm_as_a_judge_for_enterprise_rag.pdf"
legacy_primary_alias: "research/ref-paper/is2/pdfs/52_case_aware_llm_as_a_judge_2025.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: "2602.20379"
arxiv_source: "acquisition_url"
arxiv_confidence: "high"
page_count: 15
record_type: "paper"
tier: "B"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U144: Case-Aware LLM-as-a-Judge for Enterprise RAG

## Bibliographic Identity

- Verified title source: `acquisition_metadata_verified_in_pdf`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: 2602.20379 (source: acquisition_url; confidence: high)
- Pages: 15
- Source collection: `is2`
- Legacy primary alias: `research/ref-paper/is2/pdfs/52_case_aware_llm_as_a_judge_2025.pdf`
- Identity result: `verified` (filename/title token overlap 1.00)

## Classification

**Tier B.** Transferable retrieval, RAG, evaluation, uncertainty, or knowledge-graph method. Relevant surface: C, R, H/S.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, ranking, benchmark, retrieval-augmented, thai, calibration, faithfulness, hallucination.

Abstract/summary section scan:

> Enterprise Retrieval-Augmented Generation (RAG) assistants operate in multi-turn, case-based workflows such as technical support and IT operations, where evaluation must reflect operational constraints, structured identifiers (e.g., error codes, versions), and resolution workflows. Existing RAG evaluation frameworks are primarily designed for benchmark-style or single-turn settings and often fail to capture enterprise-specific failure modes such as case misidentification, workflow misalignment, and partial resolution across turns. We present a case-aware LLM-as-a-Judge evaluation framework for enterprise multi-turn RAG systems. The framework evaluates each turn using eight operationally grounded metrics that separate retrieval quality, grounding fidelity, answer utility, precision integrity, and case/workflow alignment. A severity-aware scoring protocol reduces score inflation and improves diagnostic clarity across heterogeneous enterprise cases. The system uses deterministic prompting with strict JSON outputs, enabling scalable batch evaluation, regression testing, and production monitoring. Through a comparative study of two instruction-tuned models across short and long workflows, we show that generic proxy metrics provide ambiguous signals, while the proposed framework exposes enterprise-critical tradeoffs that are actionable for system improvement. 1 Introduction framework based on the LLM-as-a-Judge paradigm (Zheng et al., 2023). Our key contribution is case- Retrieval-Augmented Generation (RAG) is widely aware evaluation: the judge conditions on multi- used to deploy large language models (LLMs) in turn history, case metadata, and retrieved evidence enterprise environments by combining retrieval while enforcing structured scoring across eight over proprietary con

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
