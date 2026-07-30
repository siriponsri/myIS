---
paper_id: U100
title: "HalluGraph: Auditable Hallucination Detection for Legal RAG via Knowledge Graph Alignment"
pdf_sha256: "c14450394f85b53f3e3cdf2746f9e4f48efba7c895ab1af591607938ec066a4b"
object_path: "01_evidence/B-tier/U100_hallugraph_auditable_hallucination_detection_for_legal_rag_via_knowledge.pdf"
legacy_primary_alias: "research/ref-paper/shared/pdfs/22_hallugraph_auditable_hallucination_detection_for_legal_2025.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: "2512.01659"
arxiv_source: "acquisition_url"
arxiv_confidence: "high"
page_count: 8
record_type: "paper"
tier: "B"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U100: HalluGraph: Auditable Hallucination Detection for Legal RAG via Knowledge Graph Alignment

## Bibliographic Identity

- Verified title source: `acquisition_metadata_verified_in_pdf`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: 2512.01659 (source: acquisition_url; confidence: high)
- Pages: 8
- Source collection: `shared`
- Legacy primary alias: `research/ref-paper/shared/pdfs/22_hallugraph_auditable_hallucination_detection_for_legal_2025.pdf`
- Identity result: `verified` (filename/title token overlap 1.00)

## Classification

**Tier B.** Transferable retrieval, RAG, evaluation, uncertainty, or knowledge-graph method. Relevant surface: C, R, IS2-adjacent.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, benchmark, embedding, knowledge graph, retrieval-augmented, legal, classification, summarization, faithfulness, hallucination.

Abstract/summary section scan:

> Legal AI systems powered by retrieval-augmented generation (RAG) face a critical accountability challenge: when an AI assistant cites case law, statutes, or contractual clauses, practitioners need verifiable guarantees that generated text faithfully represents source documents. Existing hallucination detectors rely on semantic similarity metrics that tolerate entity substitutions, a dangerous failure mode when confusing parties, dates, or legal provisions can have material consequences. We introduce HalluGraph, a graph-theoretic framework that quantifies hallucinations through structural alignment between knowledge graphs extracted from context, query, and response. Our approach produces bounded, interpretable metrics decomposed into Entity Grounding (EG), measuring whether entities in the response appear in source documents, and Relation Preservation (RP), verifying that asserted relationships are supported by context. On structured control documents, HalluGraph achieves near-perfect discrimination (>400 words, >20 entities), HalluGraph achieves AU C = 0.979, while maintaining robust performance (AU C ≈ 0.89) on challenging generative legal task, consistently outperforming semantic similarity baselines. The framework provides the transparency and traceability required for high-stakes legal applications, enabling full audit trails from generated assertions back to source passages. Code and dataset will be made available upon admission.

Conclusion/discussion section scan:

> HalluGraph provides auditable hallucination detection for legal RAG systems through knowledge graph alignment. By decomposing fidelity into Entity Grounding and Relation Preservation, the framework offers bounded, interpretable metrics that can be directly inspected and debugged, aligning with the transparency and accountability requirements of legal practice. On structured documents typical of legal workflows, HalluGraph achieves near-perfect discrimination on control tasks (AUC ≈ 0.98) and strong performance on generative legal tasks (AUC ≈ 0.89), significantly outperforming semantic similarity baselines that hover around chance (≈ 0.50). These results support the view that structural, graph-based verification is not just a cosmetic add-on but a critical component for trustworthy legal AI, enabling practitioners to deploy LLM assistants with verifiable accountability guarantees, thereby aligning generative capabilities with the regulatory frameworks necessary for safe public-sector adoption.

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
