---
paper_id: U138
title: "Using the Triangle Inequality to Accelerate k-Means"
pdf_sha256: "2ed9197ce01aa3bc55611ec163939fe00444a7f6473334365c3f7c1f2f6212b3"
object_path: "01_evidence/N-tier/U138_using_the_triangle_inequality_to_accelerate_k_means.pdf"
legacy_primary_alias: "research/ref-paper/is2/pdfs/34_pgvector_open_source_vector_similarity_search_2021.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: ""
arxiv_source: ""
arxiv_confidence: "not_detected"
page_count: 7
record_type: "paper"
tier: "N"
identity_status: "alias_title_mismatch"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U138: Using the Triangle Inequality to Accelerate k-Means

## Bibliographic Identity

- Verified title source: `pdfinfo`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: not detected (source: not detected; confidence: not_detected)
- Pages: 7
- Source collection: `is2`
- Legacy primary alias: `research/ref-paper/is2/pdfs/34_pgvector_open_source_vector_similarity_search_2021.pdf`
- Identity result: `alias_title_mismatch` (filename/title token overlap 0.00)

## Classification

**Tier N.** Wrong acquisition: k-means paper under a pgvector alias. Relevant surface: background.

## Content Triage

Controlled content signals found in the full-text extraction: No controlled keyword signal detected.

Abstract/summary section scan:

> this center. Conversely, if a point is much closer to one  The -means algorithm is by far the most widely center than to any other, calculating exact distances is not necessary to know that the point should be assigned to the used method for discovering clusters in data. We show how to accelerate it dramatically, while first center. We show below how to make these intuitions still always computing exactly the same result concrete. as the standard algorithm. The accelerated al-  We want the accelerated -means algorithm to be usable gorithm avoids unnecessary distance calculations wherever the standard algorithm is used. Therefore, we by applying the triangle inequality in two differ- need the accelerated algorithm to satisfy three properties. ent ways, and by keeping track of lower and up- First, it should be able to start with any initial centers, so per bounds for distances between points and cen- that all existing initialization methods can continue to be ters. Experiments show that the new algorithm used. Second, given the same initial centers, it should al- is effective for datasets with up to 1000 dimen- ways produce exactly the same final centers as the standard sions, and becomes more and more effective as   algorithm. Third, it should be able to use any black-box the number of clusters increases. For distance metric, so it should not rely for example on opti- it is many times faster than the best previously  mizations specific to Euclidean distance. known accelerated -means method. Our algorithm in fact satisfies a condition stronger than the second one above: after each iteration, it produces the same 1. Introduction  set of center locations as the standard -means method. This stronger property means that heuristics for merging or The most common me

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
