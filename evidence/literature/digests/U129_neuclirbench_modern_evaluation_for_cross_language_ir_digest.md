---
paper_id: U129
title: "NeuCLIRBench: Modern Evaluation for Cross-Language IR"
pdf_sha256: "a376e80138afe1c3b55cc8e9c8834c37bd157ebbac3a301755ce30a16bf70543"
object_path: "01_evidence/C-tier/U129_neuclirbench_modern_evaluation_for_cross_language_ir.pdf"
legacy_primary_alias: "research/ref-paper/is2/pdfs/10_neuclirbench_modern_evaluation_for_cross_language_2025.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: "2511.14758"
arxiv_source: "acquisition_url"
arxiv_confidence: "high"
page_count: 14
record_type: "paper"
tier: "C"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U129: NeuCLIRBench: Modern Evaluation for Cross-Language IR

## Bibliographic Identity

- Verified title source: `acquisition_metadata_verified_in_pdf`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: 2511.14758 (source: acquisition_url; confidence: high)
- Pages: 14
- Source collection: `is2`
- Legacy primary alias: `research/ref-paper/is2/pdfs/10_neuclirbench_modern_evaluation_for_cross_language_2025.pdf`
- Identity result: `verified` (filename/title token overlap 1.00)

## Classification

**Tier C.** Contextual domain, classification, extraction, model, survey, or systems background. Relevant surface: C, R.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, reranking, ranking, benchmark, embedding, agent, cross-lingual, thai.

Abstract/summary section scan:

> to index given its size. To support the evalua- tion of English monolingual retrieval, all docu- To measure advances in retrieval, test collec- tions with relevance judgments that can faith- ments have been translated into English using ma- fully distinguish systems are required. This chine translation. Cross-Language Information Re- arXiv:2511.14758v1 [cs.IR] 18 Nov 2025 paper presents NeuCLIRBench, an evaluation trieval (CLIR) evaluation in this paper uses English collection for cross-language and multilingual queries and documents in the other three languages. retrieval. The collection consists of documents The collection includes manual translations of the written natively in Chinese, Persian, and Rus- queries into Chinese, Persian and Russian; these sian, as well as those same documents machine queries support multi-monolingual experiments, translated into English. The collection supports several retrieval scenarios including: monolin- as well as cross-language retrieval experiments gual retrieval in English, Chinese, Persian, or over other language pairs (e.g., Chinese queries Russian; cross-language retrieval with English with Russian documents). Finally, the collection as the query language and one of the other three supports evaluation of Multilingual Retrieval ap- languages as the document language; and mul- proaches by combining the documents from all tilingual retrieval, again with English as the three languages and using queries expressed in En- query language and relevant documents in all glish. three languages. NeuCLIRBench combines the NeuCLIRBench is derived from the work of TREC NeuCLIR track topics of 2022, 2023, and 2024. The 250,128 judgments across ap- the TREC Neural Cross-Language Information Re- proximately 150 queries for the monolingual trieva

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
