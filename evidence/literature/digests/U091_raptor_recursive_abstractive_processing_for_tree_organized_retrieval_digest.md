---
paper_id: U091
title: "RAPTOR: Recursive Abstractive Processing for Tree-Organized Retrieval"
pdf_sha256: "01319e2e6e6ecfd504ee1bbda41d023f9e060bd3505ab3c161baa1d6d696cf75"
object_path: "01_evidence/C-tier/U091_raptor_recursive_abstractive_processing_for_tree_organized_retrieval.pdf"
legacy_primary_alias: "research/ref-paper/shared/pdfs/11_raptor_recursive_abstractive_processing_for_tree_2024.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: "2401.18059"
arxiv_source: "acquisition_url"
arxiv_confidence: "high"
page_count: 23
record_type: "paper"
tier: "C"
identity_status: "verified_with_title_variation"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U091: RAPTOR: Recursive Abstractive Processing for Tree-Organized Retrieval

## Bibliographic Identity

- Verified title source: `rendered_first_page_text`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: 2401.18059 (source: acquisition_url; confidence: high)
- Pages: 23
- Source collection: `shared`
- Legacy primary alias: `research/ref-paper/shared/pdfs/11_raptor_recursive_abstractive_processing_for_tree_2024.pdf`
- Identity result: `verified_with_title_variation` (filename/title token overlap 0.14)

## Classification

**Tier C.** Contextual hierarchical retrieval background; retained at the existing tier. Relevant surface: C, R.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, ranking, benchmark, embedding, contrastive, retrieval-augmented, summarization, faithfulness, hallucination.

Abstract/summary section scan:

> ” reflects performance when only the title and abstract of the papers are used for context. RAPTOR outperforms the established baselines BM25 and DPR across all tested language models. Specifically, RAPTOR’s F-1 scores are at least 1.8% points higher than DPR and at least 5.3% points higher than BM25. Retriever GPT-3 F-1 Match GPT-4 F-1 Match UnifiedQA F-1 Match Title + Abstract 25.2 22.2 17.5 BM25 46.6 50.2 26.4 DPR 51.3 53.0 32.1 RAPTOR 53.1 55.7 36.6 Comparison to State-of-the-art Systems Table 4: Comparison of accuracies on the QuAL- Building upon our controlled comparisons, ITY dev dataset for two different language mod- we examine RAPTOR’s performance relative els (GPT-3, UnifiedQA 3B) using various retrieval to other state-of-the-art models. As shown methods. RAPTOR outperforms the baselines of in Table 5, RAPTOR with GPT-4 sets a new BM25 and DPR by at least 2.0% in accuracy. benchmark on QASPER, with a 55.7% F-1 score, surpassing the CoLT5 XL’s score of Model GPT-3 Acc. UnifiedQA Acc. 53.9%. BM25 57.3 49.9 In the QuALITY dataset, as shown in Table 7, DPR 60.4 53.9 RAPTOR paired with GPT-4 sets a new state- RAPTOR 62.4 56.6 of-the-art with an accuracy of 82.6%, surpass- ing the previous best result of 62.3%. In par- Table 5: Results on F-1 Match scores of various ticular, it outperforms CoLISA by 21.5% on models on the QASPER dataset. QuALITY-HARD, which represents questions that humans took unusually long to correctly Model F-1 Match answer, requiring rereading parts of the text, LongT5 XL (Guo et al., 2022) 53.1 difficult reasoning, or both. CoLT5 XL (Ainslie et al., 2023) 53.9 For the NarrativeQA dataset, as represented in RAPTOR + GPT-4 55.7 Table 6, RAPTOR paired with UnifiedQA sets a new state-of-the-art METEOR score. When compared to the recursively summa

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
