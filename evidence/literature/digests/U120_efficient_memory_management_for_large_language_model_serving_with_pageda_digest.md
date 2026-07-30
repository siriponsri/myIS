---
paper_id: U120
title: "Efficient Memory Management for Large Language Model Serving with PagedAttention"
pdf_sha256: "55b3b324d779a67c59dac2519445e3b07c14e6ff5c656fadb47a3d7b5997469e"
object_path: "01_evidence/C-tier/U120_efficient_memory_management_for_large_language_model_serving_with_pageda.pdf"
legacy_primary_alias: "research/ref-paper/shared/pdfs/56_vllm_efficient_memory_management_pagedattention_2023.pdf"
doi: "10.1145/3600006.3613165"
doi_source: "pdf_front_matter"
doi_confidence: "medium"
arxiv_id: "2309.06180"
arxiv_source: "acquisition_url"
arxiv_confidence: "high"
page_count: 16
record_type: "paper"
tier: "C"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U120: Efficient Memory Management for Large Language Model Serving with PagedAttention

## Bibliographic Identity

- Verified title source: `acquisition_metadata_verified_in_pdf`
- DOI: 10.1145/3600006.3613165 (source: pdf_front_matter; confidence: medium)
- arXiv ID: 2309.06180 (source: acquisition_url; confidence: high)
- Pages: 16
- Source collection: `shared`
- Legacy primary alias: `research/ref-paper/shared/pdfs/56_vllm_efficient_memory_management_pagedattention_2023.pdf`
- Identity result: `verified` (filename/title token overlap 1.00)

## Classification

**Tier C.** Contextual domain, classification, extraction, model, survey, or systems background. Relevant surface: background.

## Content Triage

Controlled content signals found in the full-text extraction: benchmark, embedding, thai.

Abstract/summary section scan:

> Existing systems vLLM 40 Memory usage (GB) High throughput serving of large language models (LLMs) requires batching sufficiently many requests at a time. How- arXiv:2309.06180v1 [cs.LG] 12 Sep 2023 30 ever, existing systems struggle because the key-value cache KV Parameters Cache Parameter size (KV cache) memory for each request is huge and grows (>30%) 20 (26GB, 65%) Throughput (token/s) and shrinks dynamically. When managed inefficiently, this 1.2k memory can be significantly wasted by fragmentation and 0.8k Others redundant duplication, limiting the batch size. To address 0.4k this problem, we propose PagedAttention, an attention al- NVIDIA A100 40GB 0 gorithm inspired by the classical virtual memory and pag- 0 10 20 30 40 Batch size (# requests) ing techniques in operating systems. On top of it, we build vLLM, an LLM serving system that achieves (1) near-zero Figure 1. Left: Memory layout when serving an LLM with waste in KV cache memory and (2) flexible sharing of KV 13B parameters on NVIDIA A100. The parameters (gray) cache within and across requests to further reduce mem- persist in GPU memory throughout serving. The memory ory usage. Our evaluations show that vLLM improves the for the KV cache (red) is (de)allocated per serving request. throughput of popular LLMs by 2-4× with the same level A small amount of memory (yellow) is used ephemerally of latency compared to the state-of-the-art systems, such for activation. Right: vLLM smooths out the rapid growth as FasterTransformer and Orca. The improvement is more curve of KV cache memory seen in existing systems [31, 60], pronounced with longer sequences, larger models, and more leading to a notable boost in serving throughput. complex decoding algorithms. vLLM’s source code is publicly available at https://github

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
