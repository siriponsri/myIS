---
paper_id: U146
title: "Medical Graph RAG: Towards Safe Medical Large Language Models via Graph Retrieval-Augmented Generation"
pdf_sha256: "c1f7caa804e849a941fa106272f0fbc3ee0c1ba49fb5b4c45e9ca1d3f1c8a113"
object_path: "01_evidence/B-tier/U146_medical_graph_rag_towards_safe_medical_large_language_models_via_graph_r.pdf"
legacy_primary_alias: "research/ref-paper/is2/pdfs/57_medgraphrag_medical_kg_rag_with_evidence_2025.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: "2408.04187"
arxiv_source: "acquisition_url"
arxiv_confidence: "high"
page_count: 10
record_type: "paper"
tier: "B"
identity_status: "verified_with_title_variation"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U146: Medical Graph RAG: Towards Safe Medical Large Language Models via Graph Retrieval-Augmented Generation

## Bibliographic Identity

- Verified title source: `rendered_first_page_text`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: 2408.04187 (source: acquisition_url; confidence: high)
- Pages: 10
- Source collection: `is2`
- Legacy primary alias: `research/ref-paper/is2/pdfs/57_medgraphrag_medical_kg_rag_with_evidence_2025.pdf`
- Identity result: `verified_with_title_variation` (filename/title token overlap 0.29)

## Classification

**Tier B.** Transferable medical graph-RAG method; alias uses the MedGraphRAG shorthand. Relevant surface: C, R.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, benchmark, embedding, knowledge graph, graph rag, retrieval-augmented, agent, thai, biomedical, summarization.

Abstract/summary section scan:

> 2023a), has accelerated research in natural lan- guage processing and driven numerous AI applica- We introduce a novel graph-based Retrieval- tions. However, these models still face significant Augmented Generation (RAG) framework arXiv:2408.04187v2 [cs.CV] 15 Oct 2024 challenges in specialized fields like medicine (Hadi specifically designed for the medical domain, et al., 2024; Williams et al., 2024; Xie et al., 2024). called MedGraphRAG, aimed at enhancing Large Language Model (LLM) capabilities for The first challenge is that these domains rely on vast generating evidence-based medical responses, knowledge bases -principles and notions discov- thereby improving safety and reliability when ered and accumulated over thousands years; fitting handling private medical data. Graph-based such knowledge into the finite context window of RAG (GraphRAG) leverages LLMs to orga- current LLMs is a hopeless task. Supervised Fine- nize RAG data into graphs, showing strong po- Tuning (SFT) provides an alternative to using the tential for gaining holistic insights from long- context window, but it is often prohibitively expen- form documents. However, its standard im- sive or unfeasible due to the closed-source nature plementation is overly complex for general use and lacks the ability to generate evidence- of most commercial models. Second, medicine is based responses, limiting its effectiveness in a specialized field that relies on a precise terminol- the medical field. To extend the capabilities ogy system and numerous established truths, such of GraphRAG to the medical domain, we pro- as specific disease symptoms or drug side effects. pose unique Triple Graph Construction and U- In this domain, it is essential that LLMs do not dis- Retrieval techniques over it. In our graph con-

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
