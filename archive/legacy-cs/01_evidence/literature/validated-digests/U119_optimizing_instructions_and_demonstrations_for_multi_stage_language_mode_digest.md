---
paper_id: U119
title: "Optimizing Instructions and Demonstrations for Multi-Stage Language Model Programs"
pdf_sha256: "f00093af256c7b3e5168c2e98fbb8c4847232a8838c91baad4540cb4f19c91f7"
object_path: "01_evidence/A-tier/U119_optimizing_instructions_and_demonstrations_for_multi_stage_language_mode.pdf"
legacy_primary_alias: "research/ref-paper/shared/pdfs/55_miprov2_optimizing_instructions_and_demonstrations_2024.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: "2406.11695"
arxiv_source: "acquisition_url"
arxiv_confidence: "high"
page_count: 28
record_type: "paper"
tier: "A"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U119: Optimizing Instructions and Demonstrations for Multi-Stage Language Model Programs

## Bibliographic Identity

- Verified title source: `acquisition_metadata_verified_in_pdf`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: 2406.11695 (source: acquisition_url; confidence: high)
- Pages: 28
- Source collection: `shared`
- Legacy primary alias: `research/ref-paper/shared/pdfs/55_miprov2_optimizing_instructions_and_demonstrations_2024.pdf`
- Identity result: `verified` (filename/title token overlap 1.00)

## Classification

**Tier A.** Direct HarnessOpt/skill/prompt optimization method evidence. Relevant surface: C, R, H/S.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, reranking, ranking, benchmark, embedding, prompt optimization, agent, classification, summarization.

Abstract/summary section scan:

> LM Program: for i in range(2): Quality: 21% Language Model Programs, i.e. sophisticated “context, question-> pipelines of modular language model (LM) query = search_query” arXiv:2406.11695v2 [cs.CL] 6 Oct 2024 calls, are increasingly advancing NLP tasks. context.append( retrieve “search_query” ) However, building these pipelines requires “context, question-> answer = crafting prompts that are jointly effective for answer” all modules. We study prompt optimization Train Set: Question/Answer Pairs for LM programs, i.e. how to update these Metric: Exact Match Answer prompts to maximize a downstream metric Optimized LM Program: without access to module-level labels or gra- Quality: 40% for i in range(2): dients. To make this tractable, we factorize “Given the context and question produce a our problem into optimizing the free-form in- query = succinct search query. Here’s an example …” structions and few-shot demonstrations of ev- context.append( retrieve “search_query” ) ery module and introduce several strategies to “Consider the whole context to correctly answer = craft task-grounded instructions and navigate answer to the question. Here’s an example …” credit assignment across modules. Our strate- gies include (i) program-and-data-aware tech- Figure 1: An example of the optimization problem we niques for proposing effective instructions, (ii) explore, shown for a multi-hop retrieval LM program. a stochastic mini-batch evaluation function for Given some question–answer pairs and a metric, the learning a surrogate model of our objective, and optimizer proposes new instructions and bootstraps new (iii) a meta-optimization procedure in which demonstrations (not pictured) for each stage. we refine how LMs construct proposals over time. Using these insights we develop MIPRO,

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
