---
paper_id: U048
title: "Hierarchical Multi-Positive Contrastive Learning for Patent Image Retrieval (DeepPatent2)"
pdf_sha256: "1248bb844e415db2dfb029ec429218606183427460f0acef864313a090c3017c"
object_path: "01_evidence/A-tier/U048_hierarchical_multi_positive_contrastive_learning_for_patent_image_retrie.pdf"
legacy_primary_alias: "research/ref-paper/is1/pdfs/49_hierarchical_multi_positive_contrastive_learning_for_2025.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: "2506.13496"
arxiv_source: "acquisition_url"
arxiv_confidence: "high"
page_count: 5
record_type: "paper"
tier: "A"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U048: Hierarchical Multi-Positive Contrastive Learning for Patent Image Retrieval (DeepPatent2)

## Bibliographic Identity

- Verified title source: `acquisition_metadata_verified_in_pdf`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: 2506.13496 (source: acquisition_url; confidence: high)
- Pages: 5
- Source collection: `is1`
- Legacy primary alias: `research/ref-paper/is1/pdfs/49_hierarchical_multi_positive_contrastive_learning_for_2025.pdf`
- Identity result: `verified` (filename/title token overlap 1.00)

## Classification

**Tier A.** Direct patent retrieval/search/embedding benchmark evidence. Relevant surface: C, R.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, ranking, benchmark, patent, embedding, contrastive, classification.

Abstract/summary section scan:

> Patent images are technical drawings that convey information about a patent’s innovation. Patent image retrieval systems aim to search in vast collections and retrieve the most relevant images. Despite recent advances in information retrieval, patent images still pose significant challenges due to their technical intricacies and complex semantic information, requiring efficient fine-tuning for domain adaptation. Current methods neglect patents’ hierarchical relationships, such as those defined by the Locarno International Classification (LIC) system, which groups broad categories (e.g., “furnishing”) into subclasses (e.g., “seats” and “beds”) and further into specific patent designs. In this work, we introduce a hierarchical multi-positive contrastive loss that leverages the LIC’s taxonomy to induce such relations in the retrieval process. Our approach assigns multiple positive pairs to each patent image within a batch, with varying similarity scores based on the hierarchical taxonomy. Our experimental analysis with various vision and multimodal models on the DeepPatent2 dataset shows that the proposed method enhances the retrieval results. Notably, our method is effective with low-parameter models, which require fewer computational resources and can be deployed on environments with limited hardware.

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
