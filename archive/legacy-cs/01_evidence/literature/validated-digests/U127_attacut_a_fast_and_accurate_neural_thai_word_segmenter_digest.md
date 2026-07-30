---
paper_id: U127
title: "AttaCut: A Fast and Accurate Neural Thai Word Segmenter"
pdf_sha256: "847942b6a9aea84ea7a7ce52153b6aeac222f4383d457d41a36a020c7b00876d"
object_path: "01_evidence/C-tier/U127_attacut_a_fast_and_accurate_neural_thai_word_segmenter.pdf"
legacy_primary_alias: "research/ref-paper/is2/pdfs/07_attacut_a_fast_and_accurate_neural_2020.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: "1911.07056"
arxiv_source: "acquisition_url"
arxiv_confidence: "high"
page_count: 13
record_type: "paper"
tier: "C"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U127: AttaCut: A Fast and Accurate Neural Thai Word Segmenter

## Bibliographic Identity

- Verified title source: `acquisition_metadata_verified_in_pdf`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: 1911.07056 (source: acquisition_url; confidence: high)
- Pages: 13
- Source collection: `is2`
- Legacy primary alias: `research/ref-paper/is2/pdfs/07_attacut_a_fast_and_accurate_neural_2020.pdf`
- Identity result: `verified` (filename/title token overlap 1.00)

## Classification

**Tier C.** Contextual domain, classification, extraction, model, survey, or systems background. Relevant surface: IS2-adjacent.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, benchmark, embedding, thai, classification.

Abstract/summary section scan:

> Word segmentation is a fundamental pre-processing step for Thai Natural Lan- guage Processing. The current off-the-shelf solutions are not benchmarked con- sistently, so it is difficult to compare their trade-offs. We conducted a speed and accuracy comparison of the popular systems on three different domains and found that the state-of-the-art deep learning system is slow and moreover does not use sub-word structures to guide the model. Here, we propose a fast and accurate neu- ral Thai Word Segmenter that uses dilated CNN filters to capture the environment of each character and uses syllable embeddings as features. Our system runs at least 5.6× faster and outperforms the previous state-of-the-art system on some do- mains. In addition, we develop the first ML-based Thai orthographical syllable segmenter, which yields syllable embeddings to be used as features by the word segmenter.

Conclusion/discussion section scan:

> Thai word segmentation is a challenging task in which speed is often exchanged for quality. We proposed an efficient CNN-based word segmenter for Thai that utilizes character and syllable em- beddings. The segmenter is at least 5.6× faster than previous state-of-the-art segmenters, and it achieved comparable and, in some domains, better performance. In addition, our analysis shows that learning-based approaches suffer an out-of-domain problem with idiosyncratic datasets such as poetry. Future work could experiment with transfer learning to address this issue.

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
