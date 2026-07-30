---
paper_id: U046
title: "Large Language Model Informed Patent Image Retrieval (Multimodal Distribution-Aware)"
pdf_sha256: "b405a9444717795e2791767f438f56d938a3bd98ddaf3e593ea37a5f01e11cab"
object_path: "01_evidence/A-tier/U046_large_language_model_informed_patent_image_retrieval_multimodal_distribu.pdf"
legacy_primary_alias: "research/ref-paper/is1/pdfs/47_large_language_model_informed_patent_image_2024.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: "2405.01775"
arxiv_source: "acquisition_url"
arxiv_confidence: "high"
page_count: 10
record_type: "paper"
tier: "A"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U046: Large Language Model Informed Patent Image Retrieval (Multimodal Distribution-Aware)

## Bibliographic Identity

- Verified title source: `acquisition_metadata_verified_in_pdf`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: 2405.01775 (source: acquisition_url; confidence: high)
- Pages: 10
- Source collection: `is1`
- Legacy primary alias: `research/ref-paper/is1/pdfs/47_large_language_model_informed_patent_image_2024.pdf`
- Identity result: `verified` (filename/title token overlap 1.00)

## Classification

**Tier A.** Direct patent retrieval/search/embedding benchmark evidence. Relevant surface: C, R.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, ranking, benchmark, patent, prior art, embedding, contrastive, agent, legal, classification.

Abstract/summary section scan:

> In patent prosecution, image-based retrieval systems for identifying similarities between current patent images and prior art are pivotal to ensure the novelty and non-obviousness of patent applications. Despite their growing popularity in recent years, existing attempts, while effective at recognizing images within the same patent, fail to deliver practical value due to their limited generalizability in retrieving relevant prior art. Moreover, this task inherently involves the challenges posed by the abstract visual features of patent images, the skewed distribution of image classifications, and the semantic information of image descriptions. Therefore, we propose a language-informed, distribution-aware multimodal approach to patent image feature learning, which enriches the semantic understanding of patent image by integrating Large Language Models and improves the performance of underrepresented classes with our proposed distribution-aware contrastive losses. Extensive experiments on DeepPatent2 dataset show that our proposed method achieves state-of-the-art or comparable performance in image-based patent retrieval with mAP +53.3%, Recall@10 +41.8%, and MRR@10 +51.9%. Furthermore, through an in-depth user analysis, we explore our model in aiding patent professionals in their image retrieval efforts, highlighting the model’s real-world applicability and effectiveness. 1. Introduction ited, can be broadly categorized into two: (i) Low-level vision-based methods, which employee basic visual fea- Prior art search aims to identify similarities between new tures such as visual words [9], shape and contour [10, 11], inventions and existing technologies, thus ensuring the relational skeletons [12], and adaptive hierarchical den- inventions satisfy novelty and non-obviousness

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
