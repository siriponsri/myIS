---
paper_id: U056
title: "An automatic patent literature retrieval system based on LLM-RAG"
pdf_sha256: "1343ea48ad7ad8af9f63083701376d1c16aa4c058d261a6e52dc5b9f3455695f"
object_path: "01_evidence/A-tier/U056_an_automatic_patent_literature_retrieval_system_based_on_llm_rag.pdf"
legacy_primary_alias: "research/ref-paper/is1/pdfs/57_an_automatic_patent_literature_retrieval_system_2025.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: "2508.14064"
arxiv_source: "acquisition_url"
arxiv_confidence: "high"
page_count: 7
record_type: "paper"
tier: "A"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U056: An automatic patent literature retrieval system based on LLM-RAG

## Bibliographic Identity

- Verified title source: `acquisition_metadata_verified_in_pdf`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: 2508.14064 (source: acquisition_url; confidence: high)
- Pages: 7
- Source collection: `is1`
- Legacy primary alias: `research/ref-paper/is1/pdfs/57_an_automatic_patent_literature_retrieval_system_2025.pdf`
- Identity result: `verified` (filename/title token overlap 1.00)

## Classification

**Tier A.** Direct patent retrieval/search/embedding benchmark evidence. Relevant surface: C, R.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, patent, prior art, embedding, knowledge graph, retrieval-augmented, agent, legal, biomedical, classification, summarization, faithfulness.

Abstract/summary section scan:

> With the acceleration of technological innovation, efficient retrieval and classification of patent literature have become essential for intellectual property management and enterprise R&D. Traditional keyword- and rule-based retrieval methods often fail to address complex query intents or capture semantic associations across technical domains, resulting in incomplete and low-relevance results. This study presents an automated patent retrieval framework integrating Large Language Models (LLMs) with Retrieval-Augmented Generation (RAG) technology. The system comprises three components: (1) a preprocessing module for patent data standardization, (2) a high-efficiency vector retrieval engine leveraging LLM- generated embeddings, and (3) a RAG-enhanced query module that combines external document retrieval with context-aware response generation. Evaluations were conducted on the Google Patents dataset (2006–2024), containing millions of global patent records with metadata such as filing date, domain, and status. The proposed gpt- 3.5-turbo-0125+RAG configuration achieved 80.5% semantic matching accuracy and 92.1% recall, surpassing baseline LLM methods by 28 percentage points. The framework also demonstrated strong generalization in cross-domain classification and semantic clustering tasks. These results validate the effectiveness of LLM–RAG integration for intelligent patent retrieval, providing a foundation for next-generation AI-driven intellectual property analysis platforms. Keywords: Rag technology, knowledge base retrieval, big language model, patent literature retrieval 1. Introduction In the context of today’s rapid knowledge expansion and technological innovation, patents serve as a critical indicator of technological advancement and intellectual property protecti

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
