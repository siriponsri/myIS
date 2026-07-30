---
paper_id: U122
title: "DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models"
pdf_sha256: "6cc20b3c5b8d25b8b53868fc4ec1792c144f07d67bdf7395138efd4422197e7b"
object_path: "01_evidence/C-tier/U122_deepseekmath_pushing_the_limits_of_mathematical_reasoning_in_open_langua.pdf"
legacy_primary_alias: "research/ref-paper/shared/pdfs/58_deepseekmath_pushing_limits_mathematical_reasoning_2024.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: "2402.03300"
arxiv_source: "acquisition_url"
arxiv_confidence: "high"
page_count: 30
record_type: "paper"
tier: "C"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U122: DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models

## Bibliographic Identity

- Verified title source: `acquisition_metadata_verified_in_pdf`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: 2402.03300 (source: acquisition_url; confidence: high)
- Pages: 30
- Source collection: `shared`
- Legacy primary alias: `research/ref-paper/shared/pdfs/58_deepseekmath_pushing_limits_mathematical_reasoning_2024.pdf`
- Identity result: `verified` (filename/title token overlap 1.00)

## Classification

**Tier C.** Contextual domain, classification, extraction, model, survey, or systems background. Relevant surface: H/S.

## Content Triage

Controlled content signals found in the full-text extraction: ranking, benchmark, agent, classification.

Abstract/summary section scan:

> Mathematical reasoning poses a significant challenge for language models due to its complex and structured nature. In this paper, we introduce DeepSeekMath 7B, which continues pre- training DeepSeek-Coder-Base-v1.5 7B with 120B math-related tokens sourced from Common Crawl, together with natural language and code data. DeepSeekMath 7B has achieved an impressive score of 51.7% on the competition-level MATH benchmark without relying on external toolkits and voting techniques, approaching the performance level of Gemini-Ultra and GPT-4. Self-consistency over 64 samples from DeepSeekMath 7B achieves 60.9% on MATH. The mathematical reasoning capability of DeepSeekMath is attributed to two key factors: First, we harness the significant potential of publicly available web data through a meticulously engineered data selection pipeline. Second, we introduce Group Relative Policy Optimization (GRPO), a variant of Proximal Policy Optimization (PPO), that enhances mathematical reasoning abilities while concurrently optimizing the memory usage of PPO. Figure 1 | Top1 accuracy of open-source models on the competition-level MATH benchmark (Hendrycks et al., 2021) without the use of external toolkits and voting techniques. ∗ Core contributors. † Work done during internship at DeepSeek-AI. 1. Introduction Large language models (LLM) have revolutionized the approach to mathematical reasoning in artificial intelligence, spurring significant advancements in both the quantitative reasoning benchmark (Hendrycks et al., 2021) and the geometry reasoning benchmark (Trinh et al., 2024). Moreover, these models have proven instrumental in assisting humans in solving complex mathematical problems (Tao, 2023). However, cutting-edge models such as GPT-4 (OpenAI, 2023) and Gemini-Ultra (Anil et al., 2

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
