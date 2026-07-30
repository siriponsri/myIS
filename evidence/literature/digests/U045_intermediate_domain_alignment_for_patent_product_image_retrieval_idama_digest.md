---
paper_id: U045
title: "Intermediate Domain Alignment for Patent-Product Image Retrieval (IDAMA)"
pdf_sha256: "90dc3724e0dac7a5b645eae0a52151ad50897db53343f7a48c1645b6a32a5d1b"
object_path: "01_evidence/A-tier/U045_intermediate_domain_alignment_for_patent_product_image_retrieval_idama.pdf"
legacy_primary_alias: "research/ref-paper/is1/pdfs/46_intermediate_domain_alignment_for_patent_product_2024.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: ""
arxiv_source: ""
arxiv_confidence: "not_detected"
page_count: 23
record_type: "paper"
tier: "A"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U045: Intermediate Domain Alignment for Patent-Product Image Retrieval (IDAMA)

## Bibliographic Identity

- Verified title source: `acquisition_metadata_verified_in_pdf`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: not detected (source: not detected; confidence: not_detected)
- Pages: 23
- Source collection: `is1`
- Legacy primary alias: `research/ref-paper/is1/pdfs/46_intermediate_domain_alignment_for_patent_product_2024.pdf`
- Identity result: `verified` (filename/title token overlap 1.00)

## Classification

**Tier A.** Direct patent retrieval/search/embedding benchmark evidence. Relevant surface: C, R.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, benchmark, patent, prior art, embedding, contrastive, knowledge graph, biomedical, classification.

Abstract/summary section scan:

> Recent advances in artificial intelligence have significantly impacted image retrieval tasks, yet Patent-Product Image Retrieval (PPIR) has received limited attention. PPIR, which retrieves patent images based on product images to identify potential infringements, presents unique challenges: (1) both product and patent images often contain numerous categories of artificial objects, but models pre-trained on standard datasets exhibit limited discriminative power to recognize some of those unseen objects; and (2) the significant domain gap between binary patent line drawings and colorful RGB product images further complicates similarity comparisons for product-patent pairs. To address these challenges, we formulate it as an open-set image retrieval task and introduce a comprehensive Patent-Product Image Retrieval Dataset (PPIRD) including a test set with 439 product-patent pairs, a retrieval pool of 727,921 patents, and an unlabeled pre-training set of 3,799,695 images. We further propose a novel Intermediate Domain Alignment and Morphology Analogy (IDAMA) strategy. IDAMA maps both image types to an intermediate sketch domain using edge detection to minimize the domain discrepancy, and employs a Morphology Analogy Filter to select discriminative patent images based on visual features via analogical reasoning. Extensive experiments on PPIRD demonstrate that IDAMA significantly outperforms baseline methods (+7.58 mAR) and offers valuable insights into domain mapping and representation learning for PPIR. (The PPIRD dataset is available at: https://loslorien.github.io/idama-project/)

Conclusion/discussion section scan:

> In summary, we formulate Patent-Product Image Retrieval (PPIR) as an open-set image retrieval task and propose a large-scale Patent-Product Image Retrieval Dataset (PPIRD) comprising (1) a testing set with 439 product-patent pairs (annotated and validated by experts with detailed descriptions) and a retrieval pool of 727,921 patents, and (2) an unlabeled pre-training set with 3,799,695 product/patent images. We propose a novel Intermediate Domain Alignment and Morphology Analogy (IDAMA) strategy tailored for PPIR. IDAMA contains an Intermediate Domain Mapping method to align binary line drawing patent images and colorful RGB product images by mapping them into an intermediate sketch domain using an edge detector to effectively mitigate the domain discrepancy and a Morphology Analogy Filter to select discriminative patent images containing distinctive visual feature of patents for efficient similarity comparison (inspired the cognitive principle—an unknown object can be described by analogy to a known object (patent image with high classification score regardless of label). Extensive experiments on PPIRD demonstrate that the intermediate domain is more suitable for aligning patent/product images and improving performance.

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
