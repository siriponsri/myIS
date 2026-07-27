---
paper_id: U073
title: "DSPy: Compiling Declarative Language Model Calls into Self-Improving Pipelines"
pdf_sha256: "5309836325c3a580b6c176242f49f21ca40e413b0acd514e74b67e16bb1b56bc"
object_path: "01_evidence/C-tier/U073_dspy_compiling_declarative_language_model_calls_into_self_improving_pipe.pdf"
legacy_primary_alias: "research/ref-paper/is1/pdfs/75_compiling_declarative_language_model_calls_into_self_improving_pipelines.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: "2310.03714"
arxiv_source: "pdf_front_matter"
arxiv_confidence: "medium"
page_count: 32
record_type: "paper"
tier: "C"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U073: DSPy: Compiling Declarative Language Model Calls into Self-Improving Pipelines

## Bibliographic Identity

- Verified title source: `acquisition_metadata_verified_in_pdf`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: 2310.03714 (source: pdf_front_matter; confidence: medium)
- Pages: 32
- Source collection: `is1`
- Legacy primary alias: `research/ref-paper/is1/pdfs/75_compiling_declarative_language_model_calls_into_self_improving_pipelines.pdf`
- Identity result: `verified` (filename/title token overlap 1.00)

## Classification

**Tier C.** Contextual domain, classification, extraction, model, survey, or systems background. Relevant surface: H/S.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, benchmark, retrieval-augmented, prompt optimization, agent, legal, classification.

Abstract/summary section scan:

> any particular text transformation, like answering a question or summarizing a paper. We then pa- rameterize each module so that it can learn its desired behavior by iteratively bootstrapping useful demonstrations within the pipeline. Inspired directly by PyTorch abstractions (Paszke et al., 2019), DSPy modules are used via expressive define-by-run computational graphs. Pipelines are expressed by (1) declaring the modules needed and (2) using these modules in any logical control flow (e.g., if statements, for loops, exceptions, etc.) to logically connect the modules. We then develop the DSPy compiler (Sec 4), which optimizes any DSPy program to improve quality or cost. The compiler inputs are the program, a few training inputs with optional labels, and a valida- tion metric. The compiler simulates versions of the program on the inputs and bootstraps example traces of each module for self-improvement, using them to construct effective few-shot prompts or finetuning small LMs for steps of the pipeline. Optimization in DSPy is highly modular: it is conducted by teleprompters,2 which are general-purpose optimization strategies that determine how the modules should learn from data. In this way, the compiler automatically maps the declarative modules to high-quality compositions of prompting, finetuning, reasoning, and augmentation. Programming models like DSPy could be assessed along many dimensions, but we focus on the role of expert-crafted prompts in shaping system performance. We are seeking to reduce or even remove their role through DSPy modules (e.g., versions of popular techniques like Chain of Thought) and teleprompters. We report on two expansive case studies: math word problems (GMS8K; Cobbe et al. 2021) and multi-hop question answering (HotPotQA; Yang et al. 2018

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
