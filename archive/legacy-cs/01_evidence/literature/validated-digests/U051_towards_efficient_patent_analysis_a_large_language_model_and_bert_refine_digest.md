---
paper_id: U051
title: "Towards efficient patent analysis: A large language model and BERT-refined methodology for keyphrase extraction"
pdf_sha256: "e669433386ebff350d54575f710889cb090f5077a406c623bff98d0b8e23b56d"
object_path: "01_evidence/A-tier/U051_towards_efficient_patent_analysis_a_large_language_model_and_bert_refine.pdf"
legacy_primary_alias: "research/ref-paper/is1/pdfs/52_towards_efficient_patent_analysis_a_large_2026.pdf"
doi: "10.1016/j.wpi.2026.102435"
doi_source: "acquisition_url"
doi_confidence: "high"
arxiv_id: ""
arxiv_source: ""
arxiv_confidence: "not_detected"
page_count: 16
record_type: "paper"
tier: "A"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U051: Towards efficient patent analysis: A large language model and BERT-refined methodology for keyphrase extraction

## Bibliographic Identity

- Verified title source: `acquisition_metadata_verified_in_pdf`
- DOI: 10.1016/j.wpi.2026.102435 (source: acquisition_url; confidence: high)
- arXiv ID: not detected (source: not detected; confidence: not_detected)
- Pages: 16
- Source collection: `is1`
- Legacy primary alias: `research/ref-paper/is1/pdfs/52_towards_efficient_patent_analysis_a_large_2026.pdf`
- Identity result: `verified` (filename/title token overlap 1.00)

## Classification

**Tier A.** Direct patent retrieval/search/embedding benchmark evidence. Relevant surface: C, R, IS2-adjacent.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, ranking, benchmark, patent, embedding, knowledge graph, legal, biomedical, named entity recognition, classification.

Abstract/summary section scan:

> Keywords: Patents play a pivotal role in engineering design by safeguarding innovation, forecasting technical trends, and Patent analysis promoting knowledge sharing. However, the vast volume of patents and their complex technical descriptions Keyword extraction pose significant challenges for effective analysis and information retrieval. To address these issues, we propose Keyphrase extraction an integrated framework that combines large language models (LLM) and a BERT-refined approach for patent Named entity recognition analysis. Specifically, patent titles and abstracts are first collected, and term frequency-inverse document BERT Large language model frequency (TF-IDF) is introduced to extract candidate keyphrases. An LLM is then employed to refine these keyphrases by filtering irrelevant terms and identifying significant keywords. Subsequently, a fine-tuned BERT model is developed for named entity recognition (NER) to extract domain-specific keywords, which are further refined into keyphrases through our BERT-refined keyphrase extraction (BRKE) method. Experimental results on a large dataset of USPTO patents demonstrate the effectiveness of the proposed BRKE. It achieves the highest F1-score of 52.97% when the top-10 keyphrases are retained, outperforming keyBERT, YAKE, and RAKE by 9.52%, 6.1%, and 2.35%, respectively. By enhancing the accuracy of patent keyphrase extraction, our contributions make patent analysis more efficient and accessible to both analysts and design engineers. 1. Introduction volume of patents, their dense technical language, and the extensive legal descriptions they contain pose significant challenges for effective Patents constitute one of the most comprehensive repositories of analysis and knowledge extraction [3]. global technical knowledg

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
