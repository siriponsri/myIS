---
paper_id: U087
title: "Query Rewriting for Retrieval-Augmented Large Language Models"
pdf_sha256: "483472d9ccc633fe649a87f2224a09c717fcfe052c2914c50f8abce5f34dca84"
object_path: "01_evidence/B-tier/U087_query_rewriting_for_retrieval_augmented_large_language_models.pdf"
legacy_primary_alias: "research/ref-paper/shared/pdfs/05_query_rewriting_for_retrieval_augmented_large_2023.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: "2305.14283"
arxiv_source: "acquisition_url"
arxiv_confidence: "high"
page_count: 13
record_type: "paper"
tier: "B"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U087: Query Rewriting for Retrieval-Augmented Large Language Models

## Bibliographic Identity

- Verified title source: `acquisition_metadata_verified_in_pdf`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: 2305.14283 (source: acquisition_url; confidence: high)
- Pages: 13
- Source collection: `shared`
- Legacy primary alias: `research/ref-paper/shared/pdfs/05_query_rewriting_for_retrieval_augmented_large_2023.pdf`
- Identity result: `verified` (filename/title token overlap 1.00)

## Classification

**Tier B.** Transferable retrieval, RAG, evaluation, uncertainty, or knowledge-graph method. Relevant surface: C, R, H/S.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, benchmark, retrieval-augmented, query rewriting, agent, classification, summarization, hallucination.

Abstract/summary section scan:

> of the real world. Thus, LLMs still have to face the issue of hallucination (Yao et al., 2023; Bang Large Language Models (LLMs) play pow- et al., 2023) and temporal misalignment (Röttger erful, black-box readers in the retrieve-then- and Pierrehumbert, 2021; Luu et al., 2022; Jang arXiv:2305.14283v3 [cs.CL] 23 Oct 2023 read pipeline, making remarkable progress et al., 2022). This affects the reliability of LLMs in knowledge-intensive tasks. This work in- troduces a new framework, Rewrite-Retrieve- and hinders wider practical application, because Read instead of the previous retrieve-then-read the consistency between the LLM responses with for the retrieval-augmented LLMs from the per- the real world needs further validation. Exist- spective of the query rewriting. Unlike prior ing work has proved that incorporating external studies focusing on adapting either the retriever knowledge (i.e., non-parametric knowledge) with or the reader, our approach pays attention to internal knowledge (i.e., parametric knowledge) the adaptation of the search query itself, for can effectively alleviate hallucination, especially there is inevitably a gap between the input text and the needed knowledge in retrieval. We for knowledge-intensive tasks. In fact, retrieval- first prompt an LLM to generate the query, augmented LLMs have been shown so effective then use a web search engine to retrieve con- that they have been regarded as a standard solu- texts. Furthermore, to better align the query tion to alleviate the factuality drawbacks in naive to the frozen modules, we propose a trainable LLM generations. Retrieval augmentation is ap- scheme for our pipeline. A small language plied to select relative passages as external contexts model is adopted as a trainable rewriter to cater for the la

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
