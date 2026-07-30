---
paper_id: U084
title: "ColBERTv2: Effective and Efficient Retrieval via Lightweight Late Interaction"
pdf_sha256: "46e0a2712eabf9e0b9486120356a2110f65516fa7e0d75c35e9ee3eef9ea78c0"
object_path: "01_evidence/B-tier/U084_colbertv2_effective_and_efficient_retrieval_via_lightweight_late_interac.pdf"
legacy_primary_alias: "research/ref-paper/shared/pdfs/02_colbertv2_effective_and_efficient_retrieval_via_2022.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: "2112.01488"
arxiv_source: "acquisition_url"
arxiv_confidence: "high"
page_count: 20
record_type: "paper"
tier: "B"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U084: ColBERTv2: Effective and Efficient Retrieval via Lightweight Late Interaction

## Bibliographic Identity

- Verified title source: `acquisition_metadata_verified_in_pdf`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: 2112.01488 (source: acquisition_url; confidence: high)
- Pages: 20
- Source collection: `shared`
- Legacy primary alias: `research/ref-paper/shared/pdfs/02_colbertv2_effective_and_efficient_retrieval_via_2022.pdf`
- Identity result: `verified` (filename/title token overlap 1.00)

## Classification

**Tier B.** Transferable retrieval, RAG, evaluation, uncertainty, or knowledge-graph method. Relevant surface: C, R.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, ranking, benchmark, embedding, contrastive.

Abstract/summary section scan:

> relevance is estimated using rich yet scalable in- teractions between these two sets of vectors. Col- Neural information retrieval (IR) has greatly advanced search and other knowledge- BERT produces an embedding for every token in intensive language tasks. While many neural the query (and document) and models relevance IR methods encode queries and documents as the sum of maximum similarities between each arXiv:2112.01488v3 [cs.IR] 10 Jul 2022 into single-vector representations, late query vector and all vectors in the document. interaction models produce multi-vector repre- By decomposing relevance modeling into token- sentations at the granularity of each token and level computations, late interaction aims to reduce decompose relevance modeling into scalable the burden on the encoder: whereas single-vector token-level computations. This decomposition has been shown to make late interaction more models must capture complex query–document re- effective, but it inflates the space footprint of lationships within one dot product, late interaction these models by an order of magnitude. In this encodes meaning at the level of tokens and del- work, we introduce ColBERTv2, a retriever egates query–document matching to the interac- that couples an aggressive residual compres- tion mechanism. This added expressivity comes sion mechanism with a denoised supervision at a cost: existing late interaction systems impose strategy to simultaneously improve the quality an order-of-magnitude larger space footprint than and space footprint of late interaction. We single-vector models, as they must store billions evaluate ColBERTv2 across a wide range of benchmarks, establishing state-of-the-art of small vectors for Web-scale collections. Con- quality within and outside the training domain

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
