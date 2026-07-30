---
paper_id: U133
title: "TREC 2024 RAG Track: Human vs LLM Support Judges"
pdf_sha256: "d60e93a406b54650b9e28980b70ace00cf9126c23a04f0f2de51fb35a2bf88df"
object_path: "01_evidence/B-tier/U133_trec_2024_rag_track_human_vs_llm_support_judges.pdf"
legacy_primary_alias: "research/ref-paper/is2/pdfs/23_trec_2024_rag_track_human_vs_2025.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: "2504.15205"
arxiv_source: "acquisition_url"
arxiv_confidence: "high"
page_count: 16
record_type: "paper"
tier: "B"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U133: TREC 2024 RAG Track: Human vs LLM Support Judges

## Bibliographic Identity

- Verified title source: `acquisition_metadata_verified_in_pdf`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: 2504.15205 (source: acquisition_url; confidence: high)
- Pages: 16
- Source collection: `is2`
- Legacy primary alias: `research/ref-paper/is2/pdfs/23_trec_2024_rag_track_human_vs_2025.pdf`
- Identity result: `verified` (filename/title token overlap 1.00)

## Classification

**Tier B.** Transferable retrieval, RAG, evaluation, uncertainty, or knowledge-graph method. Relevant surface: C, R.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, reranking, ranking, benchmark, retrieval-augmented, agent, thai, legal, summarization, faithfulness, hallucination.

Abstract/summary section scan:

> Retrieval-augmented generation (RAG) enables large language models (LLMs) to generate answers with citations from source documents containing “ground truth”, thereby reducing system hallucinations. A crucial factor in RAG evaluation is “support”—whether the information in the cited documents supports the answer. To this end, we conducted a large-scale comparative study of 45 participant submis- sions on 36 topics to the TREC 2024 RAG Track, comparing an automatic LLM judge (GPT-4o) against human judges for support assessment. We considered two conditions: (1) fully manual assessments from scratch and (2) manual assessments with post-editing of LLM predictions. Our results indicate that for 56% of the manual from-scratch assessments, human and GPT-4o predictions match perfectly (on a three-level scale), increasing to 72% in the manual with post-editing condi- tion. Furthermore, by carefully analyzing the disagreements in an unbiased study, we found that an independent human judge correlates better with GPT-4o than a human judge, suggesting that LLM judges can be a reliable alternative for support assessment. To conclude, we provide a qualitative analysis of human and GPT-4o errors to help guide future iterations of support assessment.

Conclusion/discussion section scan:

> In this work, we evaluated support in RAG answers by analyzing 45 submissions across 36 topics from the TREC 2024 RAG Track in a large-scale comparative study involving both humans and LLMs as judges. We critiqued and evaluated strong LLM judges, like GPT-4o, against human annotators for support assessment. 9 Our results show a high agreement between GPT-4o and human judgments, with a perfect match between judgments occurring 56% of the time in the manual from-scratch condition, increasing to 72% in the manual with post-editing condition. We observe that disagreements between humans and LLMs mainly occur for sentence–passage pairs indicating partial support, i.e., in the middle of the support evaluation spectrum. To better understand these disagreements, we conducted an unbiased evaluation by carefully re- assessing judgments with an independent human judge and a different LLM. Interestingly, in cases of disagreements, both the independent human judge and the LLAMA-3.1 judge agreed more with the GPT-4o judge than with the human judge, providing evidence for widely divergent opinions and perhaps the veracity of using LLMs for support evaluation. Further research could explore the nuances of disagreements between human and LLM judges and investigate limitations of both humans and LLMs to improve future iterations of support assessment.

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
