---
paper_id: U152
title: "Marginal Advantage Accumulation for Memory-Driven Agent Self-Evolution"
pdf_sha256: "a77d17230e6e1b29be82a61667dad4ed57fe3224f514aeb48141d71d1e0d14c0"
object_path: "01_evidence/A-tier/U152_marginal_advantage_accumulation_for_memory_driven_agent_self_evolution.pdf"
legacy_primary_alias: "research/ref-paper/is1/pdfs/86_marginal_advantage_accumulation_for_memory_driven_agent.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: "2606.20475"
arxiv_source: "pdf_front_matter"
arxiv_confidence: "medium"
page_count: 26
record_type: "paper"
tier: "A"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U152: Marginal Advantage Accumulation for Memory-Driven Agent Self-Evolution

## Bibliographic Identity

- Verified title source: `pdfinfo`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: 2606.20475 (source: pdf_front_matter; confidence: medium)
- Pages: 26
- Source collection: `is1`
- Legacy primary alias: `research/ref-paper/is1/pdfs/86_marginal_advantage_accumulation_for_memory_driven_agent.pdf`
- Identity result: `verified` (filename/title token overlap 1.00)

## Classification

**Tier A.** Direct agent self-evolution optimization evidence for HarnessOpt. Relevant surface: H/S.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, ranking, benchmark, embedding, prompt optimization, skill optimization, agent, calibration.

Abstract/summary section scan:

> In batch-style trace distillation, the same memory operation may receive contradictory feedback across different batches. Existing methods lack a cross-batch, operation-level evidence accumulation mechanism, making it impossible to distinguish stably effective operations from accidental hits. This pa- per formalizes the requirement as two structural conditions, alignability and comparability, and proposes Marginal Advantage Accumulation (MAA). MAA constructs differential signals to make them com- parable across batches, accumulates signed evidence per operation via EMA, and ensures cross-batch traceability through semantic identity merging. As a post-processing architecture, MAA achieves the best results in 14 out of 16 settings across 4 benchmarks and 4 target models, consistently outperforming existing batch-level distillation baselines and matching or surpassing online alternatives in most settings, while reducing optimization-phase token consumption by approximately 75%. Keywords: Marginal advantage accumulation, operation-level evidence accumulation, trace distilla- tion, agent self-evolution, offline memory optimization

Conclusion/discussion section scan:

> In batch-style trace distillation, feedback received by the same memory operation across different batches is often inconsistent, making it difficult to judge from single-step signals whether it is broadly effective or merely an accidental hit in specific batches. The more complex the task and the longer the trajectory, the more prominent this problem becomes. MAA maintains a cross-batch accumulated signed evidence quantity for each operation. Differential con- struction transforms absolute scores into marginal advantages relative to the current baseline, making signals across different batches comparable; EMA temporally aggregates these marginal advantages with exponen- tial weighting, amplifying directionally consistent signals and canceling directionally alternating ones. This mechanism does not rely on environment rollouts, using only LLM proxy scores as directional signals, com- pleting operation-level screening and ranking under offline settings. From ablation to mechanism diagnosis to training dynamics, experiments consistently show that differencing and accumulation layers jointly form 16 the performance source of MAA. Experimental results show that MAA achieves the best result in 14 out of 16 settings across 4 datasets and 4 target models, with token consumption reduced by approximately 75% and optimization time shortened from 12–14 hours to about 2.5 hours. In scenari

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
