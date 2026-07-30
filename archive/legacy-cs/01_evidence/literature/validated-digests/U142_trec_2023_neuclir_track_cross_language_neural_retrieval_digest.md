---
paper_id: U142
title: "TREC 2023 NeuCLIR Track: Cross-Language Neural Retrieval"
pdf_sha256: "49aa9c8c578b09560e8bc59cf84b1575cbb531e6d4a9cb6e405d1092e6a354c7"
object_path: "01_evidence/B-tier/U142_trec_2023_neuclir_track_cross_language_neural_retrieval.pdf"
legacy_primary_alias: "research/ref-paper/is2/pdfs/50_trec_2023_neuclir_track_cross_language_2023.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: ""
arxiv_source: ""
arxiv_confidence: "not_detected"
page_count: 27
record_type: "paper"
tier: "B"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U142: TREC 2023 NeuCLIR Track: Cross-Language Neural Retrieval

## Bibliographic Identity

- Verified title source: `acquisition_metadata_verified_in_pdf`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: not detected (source: not detected; confidence: not_detected)
- Pages: 27
- Source collection: `is2`
- Legacy primary alias: `research/ref-paper/is2/pdfs/50_trec_2023_neuclir_track_cross_language_2023.pdf`
- Identity result: `verified` (filename/title token overlap 1.00)

## Classification

**Tier B.** Transferable retrieval, RAG, evaluation, uncertainty, or knowledge-graph method. Relevant surface: C, R.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, reranking, ranking, benchmark, embedding, cross-lingual, biomedical.

Abstract/summary section scan:

> distinguish CLIR from monolingual retrieval: (1) less robust training The principal goal of the TREC Neural Cross-Language Informa- data than is presently available for monolingual ranked retrieval tion Retrieval (NeuCLIR) track is to study the impact of neural tasks; and (2) imbalances and misalignments in present multilingual approaches to cross-language information retrieval. The track has embeddings that must be addressed to optimize the use of that created four collections, large collections of Chinese, Persian, and computational infrastructure for CLIR tasks. Monolingual ranked Russian newswire and a smaller collection of Chinese scientific retrieval results, created using topics in the collection language, abstracts. The principal tasks are ranked retrieval of news in one of are also reported as a baselines. Five of the six participating teams the three languages, using English topics. Results for a multilingual submitted CLIR runs. task, also with English topics but with documents from all three New in this second year of the track is ranked MLIR for news, newswire collections, are also reported. New in this second year with topics in English. This task requires generating a single ranked of the track is a pilot technical documents CLIR task for ranked list for a given topic that includes Chinese, Persian and Russian retrieval of Chinese technical documents using English topics. A documents. The principal additional challenge in this task is that total of 220 runs across all tasks were submitted by six participating scores computed for documents in different languages are usually teams and, as baselines, by track coordinators. Task descriptions incomparable, making generation of a unified ranked list difficult. and results are presented. While data from NeuCLIR

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
