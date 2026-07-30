---
paper_id: U063
title: "Rank-without-GPT: Building GPT-Independent Listwise Rerankers on Open-Source Large Language Models"
pdf_sha256: "9edc0971af4f8fb32f06604ce95da556d36bdc1074a04801e0a6748ee292d304"
object_path: "01_evidence/B-tier/U063_rank_without_gpt_building_gpt_independent_listwise_rerankers_on_open_sou.pdf"
legacy_primary_alias: "research/ref-paper/is1/pdfs/64__format_robust_reranking_open_llms_2023.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: "2312.02969"
arxiv_source: "acquisition_url"
arxiv_confidence: "high"
page_count: 21
record_type: "paper"
tier: "B"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U063: Rank-without-GPT: Building GPT-Independent Listwise Rerankers on Open-Source Large Language Models

## Bibliographic Identity

- Verified title source: `rendered_first_page_text`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: 2312.02969 (source: acquisition_url; confidence: high)
- Pages: 21
- Source collection: `is1`
- Legacy primary alias: `research/ref-paper/is1/pdfs/64__format_robust_reranking_open_llms_2023.pdf`
- Identity result: `verified` (filename/title token overlap 0.20)

## Classification

**Tier B.** Transferable open-source listwise reranking method. Relevant surface: C, R.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, reranking, ranking, benchmark, contrastive, agent, thai, legal, classification.

Abstract/summary section scan:

> language models (LLM) and their capacity to con- sume long-context inputs, a new paradigm of neural Listwise rerankers based on large language rerankers has been proposed using listwise rank- models (LLM) are the zero-shot state-of-the- ing (Ma et al., 2023b; Sun et al., 2023; Pradeep art. However, current works in this direction arXiv:2312.02969v1 [cs.CL] 5 Dec 2023 et al., 2023; Tang et al., 2023). These models con- all depend on the GPT models, making it a single point of failure in scientific reproducibil- sume a combined list of passages at a time and ity. Moreover, it raises the concern that the directly outputs the reordered ranking list.1 current research findings only hold for GPT Not only does it achieve the state of the art on models but not LLM in general. In this work, two TREC DL datasets (Tang et al., 2023), listwise we lift this pre-condition and build for the first ranking provides a novel perspective to passage time effective listwise rerankers without any reranking: this new paradigm questions the neces- form of dependency on GPT. Our passage re- sity to convert the ranking task into a classification trieval experiments show that our best listwise reranker surpasses the listwise rerankers based task, and instead frames it as a pure text genera- on GPT-3.5 by 13% and achieves 97% effective- tion task that could be solved end-to-end in a gen- ness of the ones based on GPT-4. Our results eralized text-to-text fashion (Raffel et al., 2020). also show that the existing training datasets, For the first time, the model directly generates the which were expressly constructed for pointwise entire ranking list in the form of text, instead of ranking, are insufficient for building such list- requiring multiple disjoint inference passes of the wise rerankers. Ins

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
