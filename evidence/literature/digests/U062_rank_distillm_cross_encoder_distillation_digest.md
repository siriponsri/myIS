---
paper_id: U062
title: "Rank-DistiLLM cross-encoder distillation"
pdf_sha256: "4c8ff39e0748759e036f89ddf2549f1ed160c38964b832133ac56685450bd563"
object_path: "01_evidence/C-tier/U062_rank_distillm_cross_encoder_distillation.pdf"
legacy_primary_alias: "research/ref-paper/is1/pdfs/63__rank_distillm_cross_encoder_distillation_2024.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: "2405.07920"
arxiv_source: "acquisition_url"
arxiv_confidence: "high"
page_count: 12
record_type: "paper"
tier: "C"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U062: Rank-DistiLLM cross-encoder distillation

## Bibliographic Identity

- Verified title source: `acquisition_metadata_verified_in_pdf`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: 2405.07920 (source: acquisition_url; confidence: high)
- Pages: 12
- Source collection: `is1`
- Legacy primary alias: `research/ref-paper/is1/pdfs/63__rank_distillm_cross_encoder_distillation_2024.pdf`
- Identity result: `verified` (filename/title token overlap 1.00)

## Classification

**Tier C.** Contextual domain, classification, extraction, model, survey, or systems background. Relevant surface: background.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, reranking, ranking, benchmark, embedding, contrastive, agent.

Abstract/summary section scan:

> Cross-encoders distilled from large language models (LLMs) are often more effective re-rankers than cross-encoders fine-tuned on manually labeled data. However, distilled models do not match the effectiveness of their teacher LLMs. We hypothesize that this effectiveness gap is due to the fact that previous work has not applied the best-suited methods for fine-tuning cross-encoders on manually labeled data (e.g., hard-negative sampling, deep sampling, and listwise loss functions). To close this gap, we create a new dataset, Rank-DistiLLM. Cross-encoders trained on Rank-DistiLLM achieve the effectiveness of LLMs while being up to 173 times faster and 24 times more memory efficient. Our code and data is available at https://github.com/webis-de/ECIR-25.

Conclusion/discussion section scan:

> Using our new Rank-DistiLLM datset, we have systematically investigated several aspects of distilling cross-encoders from LLM rankings. Our findings indicate that rankings of the top-50 passages for 10,000 queries suffice to achieve competitive effectiveness compared to LLMs, but the passages need to be sampled using a very effective first-stage retrieval model. By first fine-tuning on MS MARCO labels and then further on Rank-DistiLLM, our best model is more effective than previous cross-encoders and matches the effectiveness of LLMs for in- and out-of-domain re-ranking while being orders of magnitude more efficient. Acknowledgements This publication has received funding from the European Union’s Horizon Europe research and innovation programme under grant agreement No 101070014 (OpenWebSearch.EU, https://doi.org/10.3030/101070014). 8 Schlatt et al.

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
