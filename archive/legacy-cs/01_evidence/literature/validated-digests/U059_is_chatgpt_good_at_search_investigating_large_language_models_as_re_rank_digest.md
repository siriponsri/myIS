---
paper_id: U059
title: "Is ChatGPT Good at Search? Investigating Large Language Models as Re-Ranking Agents"
pdf_sha256: "3a2ca388b4a2fb17e58551f1a77b2c7decbbf6767255382cfa2d9e435c7a7e70"
object_path: "01_evidence/B-tier/U059_is_chatgpt_good_at_search_investigating_large_language_models_as_re_rank.pdf"
legacy_primary_alias: "research/ref-paper/is1/pdfs/60__rankgpt_chatgpt_search_reranking_2023.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: "2304.09542"
arxiv_source: "acquisition_url"
arxiv_confidence: "high"
page_count: 20
record_type: "paper"
tier: "B"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U059: Is ChatGPT Good at Search? Investigating Large Language Models as Re-Ranking Agents

## Bibliographic Identity

- Verified title source: `rendered_first_page_text`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: 2304.09542 (source: acquisition_url; confidence: high)
- Pages: 20
- Source collection: `is1`
- Legacy primary alias: `research/ref-paper/is1/pdfs/60__rankgpt_chatgpt_search_reranking_2023.pdf`
- Identity result: `verified` (filename/title token overlap 1.00)

## Classification

**Tier B.** Transferable retrieval, RAG, evaluation, uncertainty, or knowledge-graph method. Relevant surface: C, R, H/S.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, reranking, ranking, benchmark, embedding, contrastive, retrieval-augmented, agent, thai.

Abstract/summary section scan:

> Large Language Models (LLMs) have demon- strated remarkable zero-shot generalization arXiv:2304.09542v3 [cs.CL] 28 Dec 2024 across various language-related tasks, includ- ing search engines. However, existing work utilizes the generative ability of LLMs for In- formation Retrieval (IR) rather than direct pas- sage ranking. The discrepancy between the pre- training objectives of LLMs and the ranking objective poses another challenge. In this pa- per, we first investigate generative LLMs such as ChatGPT and GPT-4 for relevance ranking Figure 1: Average results of ChatGPT and GPT-4 in IR. Surprisingly, our experiments reveal that (zero-shot) on passage re-ranking benchmarks (TREC, properly instructed LLMs can deliver compet- BEIR, and Mr.TyDi), compared with BM25 and itive, even superior results to state-of-the-art previous best-supervised systems (SOTA sup., e.g., supervised methods on popular IR benchmarks. monoT5 (Nogueira et al., 2020)). Furthermore, to address concerns about data contamination of LLMs, we collect a new test set called NovelEval, based on the latest knowl- As one of the most successful AI applications, edge and aiming to verify the model’s ability Information Retrieval (IR) systems satisfy user re- to rank unknown knowledge. Finally, to im- quirements through several pipelined sub-modules, prove efficiency in real-world applications, we delve into the potential for distilling the rank- such as passage retrieval and re-ranking (Lin et al., ing capabilities of ChatGPT into small special- 2020). Most previous methods heavily rely on ized models using a permutation distillation manual supervision signals, which require signifi- scheme. Our evaluation results turn out that cant human effort and demonstrate weak generaliz- a distilled 440M model outperforms

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
