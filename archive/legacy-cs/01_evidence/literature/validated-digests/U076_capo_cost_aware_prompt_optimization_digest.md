---
paper_id: U076
title: "CAPO: Cost-Aware Prompt Optimization"
pdf_sha256: "b124700f3361363d403810179a3723cc1c5c821eb588dbfc2cadcc04bad3ee43"
object_path: "01_evidence/A-tier/U076_capo_cost_aware_prompt_optimization.pdf"
legacy_primary_alias: "research/ref-paper/is1/pdfs/78_cost_aware_prompt_optimization.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: "2504.16005"
arxiv_source: "pdf_front_matter"
arxiv_confidence: "medium"
page_count: 45
record_type: "paper"
tier: "A"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U076: CAPO: Cost-Aware Prompt Optimization

## Bibliographic Identity

- Verified title source: `acquisition_metadata_verified_in_pdf`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: 2504.16005 (source: pdf_front_matter; confidence: medium)
- Pages: 45
- Source collection: `is1`
- Legacy primary alias: `research/ref-paper/is1/pdfs/78_cost_aware_prompt_optimization.pdf`
- Identity result: `verified` (filename/title token overlap 1.00)

## Classification

**Tier A.** Direct HarnessOpt/skill/prompt optimization method evidence. Relevant surface: H/S.

## Content Triage

Controlled content signals found in the full-text extraction: ranking, benchmark, prompt optimization, agent, named entity recognition, classification, summarization, hallucination.

Abstract/summary section scan:

> Large language models (LLMs) have revolutionized natural language processing by solving a wide range of tasks simply guided by a prompt. Yet their performance is highly sensitive to arXiv:2504.16005v4 [cs.CL] 17 Jun 2025 prompt formulation. While automatic prompt optimization addresses this challenge by find- ing optimal prompts, current methods require a substantial number of LLM calls and input tokens, making prompt optimization expensive. We introduce CAPO (Cost-Aware Prompt Optimization), an algorithm that enhances prompt optimization efficiency by integrating AutoML techniques. CAPO is an evolutionary approach with LLMs as operators, incorporat- ing racing to save evaluations and multi-objective optimization to balance performance with prompt length. It jointly optimizes instructions and few-shot examples while leveraging task descriptions for improved robustness. Our extensive experiments across diverse datasets and LLMs demonstrate that CAPO outperforms state-of-the-art discrete prompt optimization methods in 11/15 cases with improvements up to 21%p in accuracy. Our algorithm achieves better performances already with smaller budgets, saves evaluations through racing, and decreases average prompt length via a length penalty, making it both cost-efficient and cost-aware. Even without few-shot examples, CAPO outperforms its competitors and gener- ally remains robust to initial prompts. CAPO represents an important step toward making prompt optimization more powerful and accessible by improving cost-efficiency.

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
