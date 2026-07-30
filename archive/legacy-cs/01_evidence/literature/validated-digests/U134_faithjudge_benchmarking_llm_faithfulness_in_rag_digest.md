---
paper_id: U134
title: "FaithJudge: Benchmarking LLM Faithfulness in RAG"
pdf_sha256: "6df788707b91ad54b598e04262f416ed695088f9bcceab34cb624bf299e9d241"
object_path: "01_evidence/B-tier/U134_faithjudge_benchmarking_llm_faithfulness_in_rag.pdf"
legacy_primary_alias: "research/ref-paper/is2/pdfs/24_faithjudge_benchmarking_llm_faithfulness_in_rag_2025.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: "2505.04847"
arxiv_source: "acquisition_url"
arxiv_confidence: "high"
page_count: 13
record_type: "paper"
tier: "B"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U134: FaithJudge: Benchmarking LLM Faithfulness in RAG

## Bibliographic Identity

- Verified title source: `acquisition_metadata_verified_in_pdf`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: 2505.04847 (source: acquisition_url; confidence: high)
- Pages: 13
- Source collection: `is2`
- Legacy primary alias: `research/ref-paper/is2/pdfs/24_faithjudge_benchmarking_llm_faithfulness_in_rag_2025.pdf`
- Identity result: `verified` (filename/title token overlap 1.00)

## Classification

**Tier B.** Transferable retrieval, RAG, evaluation, uncertainty, or knowledge-graph method. Relevant surface: C, R.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, ranking, benchmark, contrastive, retrieval-augmented, thai, legal, classification, summarization, faithfulness, hallucination.

Abstract/summary section scan:

> retrieved contexts, misrepresent information, or generate outright contradictions (Niu et al., 2024). Retrieval-augmented generation (RAG) aims to arXiv:2505.04847v2 [cs.CL] 6 Nov 2025 An ongoing challenge within RAG is evaluat- reduce hallucinations by grounding responses ing and ensuring context-faithfulness (Niu et al., in external context, yet large language models 2024; Jia et al., 2023; Ming et al., 2024). In this pa- (LLMs) still frequently introduce unsupported information or contradictions even when pro- per, we mainly focus on evaluating faithfulness in vided with relevant context. This paper presents summarization tasks, building upon extensive prior two complementary efforts at Vectara to mea- research on summary consistency evaluation. Sum- sure and benchmark LLM faithfulness in RAG. marization tasks provide a practical benchmark First, we describe our original hallucination for faithfulness, thanks to rich available hallucina- leaderboard, which has tracked hallucination tion datasets and established automated evaluation rates for LLMs since 2023 using our HHEM methods. However, despite recent progress, both hallucination detection model. Motivated by fine-tuned detection models and LLM-as-a-judge limitations observed in current hallucination detection methods, we introduce FaithJudge, techniques (Zheng et al., 2023; Luo et al., 2023; an LLM-as-a-judge framework that leverages Jacovi et al., 2025) continue to struggle with accu- a pool of diverse human-annotated hallucina- rately identifying hallucinations in LLM outputs. tion examples to substantially improve the au- We present two complementary efforts at Vectara tomated hallucination evaluation of LLMs. We for measuring and benchmarking LLM faithfulness introduce an enhanced hallucination leader- in RAG

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
