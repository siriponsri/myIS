---
paper_id: U136
title: "LegalBench-RAG: Benchmark for RAG in Legal Domain"
pdf_sha256: "49f456c744cac4048018588550bf5ccb68ad29b49442d7bd227f21c9398824cd"
object_path: "01_evidence/B-tier/U136_legalbench_rag_benchmark_for_rag_in_legal_domain.pdf"
legacy_primary_alias: "research/ref-paper/is2/pdfs/26_legalbench_rag_benchmark_for_rag_in_2024.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: "2408.10343"
arxiv_source: "acquisition_url"
arxiv_confidence: "high"
page_count: 12
record_type: "paper"
tier: "B"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U136: LegalBench-RAG: Benchmark for RAG in Legal Domain

## Bibliographic Identity

- Verified title source: `acquisition_metadata_verified_in_pdf`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: 2408.10343 (source: acquisition_url; confidence: high)
- Pages: 12
- Source collection: `is2`
- Legacy primary alias: `research/ref-paper/is2/pdfs/26_legalbench_rag_benchmark_for_rag_in_2024.pdf`
- Identity result: `verified` (filename/title token overlap 1.00)

## Classification

**Tier B.** Transferable retrieval, RAG, evaluation, uncertainty, or knowledge-graph method. Relevant surface: C, R, IS2-adjacent.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, reranking, ranking, benchmark, embedding, retrieval-augmented, legal, summarization, hallucination.

Abstract/summary section scan:

> arXiv:2408.10343v1 [cs.AI] 19 Aug 2024 Retrieval-Augmented Generation (RAG) systems are showing promising potential, and are becom- ing increasingly relevant in AI-powered legal ap- plications. Existing benchmarks, such as Legal- Bench, assess the generative capabilities of Large Language Models (LLMs) in the legal domain, but there is a critical gap in evaluating the retrieval component of RAG systems. To address this, we introduce LegalBench-RAG, the first benchmark specifically designed to evaluate the retrieval step of RAG pipelines within the legal space. LegalBench-RAG emphasizes precise retrieval by focusing on extracting minimal, highly rele- Figure 1. Benchmarking The Retrieval Step Of RAG Systems vant text segments from legal documents. These highly relevant snippets are preferred over retriev- ing document IDs, or large sequences of imprecise 1. Introduction chunks, both of which can exceed context window In the rapidly evolving landscape of AI in the legal sec- limitations. Long context windows cost more to tor, Retrieval-Augmented Generation (RAG) (Lewis et al., process, induce higher latency, and lead LLMs to 2020) systems have emerged as a crucial technology. These forget or hallucinate information. Additionally, systems, which combine retrieval mechanisms with gen- precise results allow LLMs to generate citations erative large language models (LLMs), show promising for the end user. The LegalBench-RAG bench- potential for contextualized generation. However, as com- mark is constructed by retracing the context used panies race to develop RAG-based solutions, a critical gap in LegalBench queries back to their original loca- in the ecosystem remains unaddressed: the lack of a ded- tions within the legal corpus, resulting in a dataset icated benchmark for ev

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
