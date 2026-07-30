---
paper_id: U097
title: "KGEIR: Knowledge Graph-Enhanced Iterative Reasoning for Multi-Hop QA"
pdf_sha256: "6804b1862a5a0616ad46fee040d8a03f6eaef9d0733d69682b5d0a355a2199ff"
object_path: "01_evidence/B-tier/U097_kgeir_knowledge_graph_enhanced_iterative_reasoning_for_multi_hop_qa.pdf"
legacy_primary_alias: "research/ref-paper/shared/pdfs/18_kgeir_knowledge_graph_enhanced_iterative_reasoning_2025.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: ""
arxiv_source: ""
arxiv_confidence: "not_detected"
page_count: 11
record_type: "paper"
tier: "B"
identity_status: "verified_with_title_variation"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U097: KGEIR: Knowledge Graph-Enhanced Iterative Reasoning for Multi-Hop QA

## Bibliographic Identity

- Verified title source: `acquisition_metadata_verified_in_pdf`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: not detected (source: not detected; confidence: not_detected)
- Pages: 11
- Source collection: `shared`
- Legacy primary alias: `research/ref-paper/shared/pdfs/18_kgeir_knowledge_graph_enhanced_iterative_reasoning_2025.pdf`
- Identity result: `verified_with_title_variation` (filename/title token overlap 0.89)

## Classification

**Tier B.** Transferable retrieval, RAG, evaluation, uncertainty, or knowledge-graph method. Relevant surface: C, R, H/S, IS2-adjacent.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, benchmark, embedding, knowledge graph, graph rag, retrieval-augmented, thai.

Abstract/summary section scan:

> et al., 2020; Touvron et al., 2023), their ability to Multi-hop question answering (MHQA) re- perform structured reasoning over multiple sources quires systems to retrieve and connect informa- remains a challenging area, particularly when ev- tion across multiple documents, a task where idence must be gathered from diverse documents large language models often struggle. We in- without explicit connections (Qi et al., 2019). troduce Knowledge Graph-Enhanced Iterative Existing approaches to MHQA typically follow Reasoning (KGEIR), a framework that dynam- a retrieve-then-read paradigm (Lewis et al., 2020; ically constructs and refines knowledge graphs Karpukhin et al., 2020), where relevant documents during question answering to enhance multi- hop reasoning. KGEIR identifies key entities are first retrieved based on the question, followed from questions, builds an initial graph from re- by a reading comprehension step to extract the an- trieved paragraphs, reasons over this structure, swer. However, this sequential process often strug- identifies information gaps, and iteratively re- gles with complex questions requiring multi-step trieves additional context to refine the graph reasoning, as the initial retrieval may fail to cap- until sufficient information is gathered. Evalu- ture all necessary documents when relationships ations on HotpotQA, 2WikiMultiHopQA, and between different pieces of evidence are not explic- MuSiQue benchmarks show competitive or su- perior performance to state-of-the-art methods. itly considered [11]. Furthermore, most systems Ablation studies confirm that structured knowl- lack an effective mechanism to identify and ad- edge representations significantly outperform dress information gaps through iterative refinement traditional prompting approac

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
