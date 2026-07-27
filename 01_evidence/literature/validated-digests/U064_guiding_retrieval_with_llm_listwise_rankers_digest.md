---
paper_id: U064
title: "Guiding Retrieval with LLM Listwise Rankers"
pdf_sha256: "8defa5deb51e7f0adaa7d7fee920c47671e5f88163ff6513616f91b2deaf59a9"
object_path: "01_evidence/B-tier/U064_guiding_retrieval_with_llm_listwise_rankers.pdf"
legacy_primary_alias: "research/ref-paper/is1/pdfs/65__guiding_retrieval_llm_listwise_rankers_2025.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: "2501.09186"
arxiv_source: "acquisition_url"
arxiv_confidence: "high"
page_count: 16
record_type: "paper"
tier: "B"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U064: Guiding Retrieval with LLM Listwise Rankers

## Bibliographic Identity

- Verified title source: `acquisition_metadata_verified_in_pdf`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: 2501.09186 (source: acquisition_url; confidence: high)
- Pages: 16
- Source collection: `is1`
- Legacy primary alias: `research/ref-paper/is1/pdfs/65__guiding_retrieval_llm_listwise_rankers_2025.pdf`
- Identity result: `verified` (filename/title token overlap 1.00)

## Classification

**Tier B.** Transferable retrieval, RAG, evaluation, uncertainty, or knowledge-graph method. Relevant surface: C, R, H/S.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, reranking, ranking, benchmark, query rewriting, agent.

Abstract/summary section scan:

> Large Language Models (LLMs) have shown strong promise as rerankers, especially in “listwise” settings where an LLM is prompted to rerank several search results at once. However, this “cascading” retrieve- and-rerank approach is limited by the bounded recall problem: relevant documents not retrieved initially are permanently excluded from the final ranking. Adaptive retrieval techniques address this problem, but do not work with listwise rerankers because they assume a document’s score is computed independently from other documents. In this paper, we propose an adaptation of an existing adaptive retrieval method that supports the listwise setting and helps guide the retrieval process itself (thereby overcoming the bounded recall problem for LLM rerankers). Specifically, our proposed algorithm merges results both from the initial ranking and feedback documents provided by the most relevant doc- uments seen up to that point. Through extensive experiments across diverse LLM rerankers, first stage retrievers, and feedback sources, we demonstrate that our method can improve nDCG@10 by up to 13.23% and recall by 28.02%–all while keeping the total number of LLM infer- ences constant and overheads due to the adaptive process minimal. The work opens the door to leveraging LLM-based search in settings where the initial pool of results is limited, e.g., by legacy systems, or by the cost of deploying a semantic first-stage. Keywords: Reranking · Adaptive Retrieval · LLM

Conclusion/discussion section scan:

> We augment existing adaptive ranking algorithms to work with listwise LLM reranking models. We find that our proposed method, SlideGar, is able to successfully overcome the bounded recall problem from first-stage retrievers by successfully leveraging feedback signals from an LLM. Also, the computational overhead of applying SlideGar is minimal compared to a typical LLM rerank- ing pipeline. In our opinion this work enables the broader adoption of LLM reranking, such as in cases where the first stage is unsuccessful or systems are limited by legacy first-stage (lexical) keyword-based retrieval systems. 14 Mandeep Rathee, Sean MacAvaney, and Avishek Anand

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
