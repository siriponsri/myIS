---
paper_id: U088
title: "Reciprocal Rank Fusion Based Hybrid Dense\u2013Sparse Information Retrieval (RRF Hybrid)"
pdf_sha256: "f6f481e31beca9961600dbd96381d574bcc9716d133b78fe41b665748f4733bc"
object_path: "01_evidence/B-tier/U088_reciprocal_rank_fusion_based_hybrid_dense_sparse_information_retrieval_r.pdf"
legacy_primary_alias: "research/ref-paper/shared/pdfs/06_reciprocal_rank_fusion_based_hybrid_densesparse_2023.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: ""
arxiv_source: ""
arxiv_confidence: "not_detected"
page_count: 9
record_type: "paper"
tier: "B"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U088: Reciprocal Rank Fusion Based Hybrid Dense–Sparse Information Retrieval (RRF Hybrid)

## Bibliographic Identity

- Verified title source: `acquisition_metadata_verified_in_pdf`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: not detected (source: not detected; confidence: not_detected)
- Pages: 9
- Source collection: `shared`
- Legacy primary alias: `research/ref-paper/shared/pdfs/06_reciprocal_rank_fusion_based_hybrid_densesparse_2023.pdf`
- Identity result: `verified` (filename/title token overlap 1.00)

## Classification

**Tier B.** Transferable retrieval, RAG, evaluation, uncertainty, or knowledge-graph method. Relevant surface: C, R.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, ranking, benchmark, embedding, cross-lingual, biomedical, calibration.

Abstract/summary section scan:

> Social media platforms generate vast amounts of code-mixed text, such as Banglish (Bengali-English), which poses unique challenges for information retrieval due to spelling variations, transliterations, and informal usage. Traditional sparse retrieval methods like BM25 fail to fully capture semantic meaning, while dense embedding models such as Sentence Transformers may overlook lexical matches. In this work, we propose a hybrid retrieval framework that integrates BM25 and a triplet-tuned Sentence Transformer model using Reciprocal Rank Fusion (RRF). Our approach leverages the complementary strengths of sparse and dense retrieval, ensuring robust performance on noisy Banglish social media data. We evaluate our system on the FIRE 2025 code-mixed information retrieval shared task, achieving 6th place with a MAP score of 0.123, NDCG score of 0.376, P@5 of 0.293, and P@10 of 0.21. The results demonstrate that RRF fusion significantly improves retrieval effectiveness compared to standalone methods, making it a promising strategy for code-mixed information retrieval.

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
