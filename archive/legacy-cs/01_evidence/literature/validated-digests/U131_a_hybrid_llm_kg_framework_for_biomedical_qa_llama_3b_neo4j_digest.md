---
paper_id: U131
title: "A Hybrid LLM\u2013KG Framework for Biomedical QA (LLaMA-3B + Neo4j)"
pdf_sha256: "46838903990945d2b2880da5427f7ba22cbc5473eaadbba2c668aa4ad8256006"
object_path: "01_evidence/B-tier/U131_a_hybrid_llm_kg_framework_for_biomedical_qa_llama_3b_neo4j.pdf"
legacy_primary_alias: "research/ref-paper/is2/pdfs/14_a_hybrid_llmkg_framework_for_biomedical_2025.pdf"
doi: "10.38094/jastt62404"
doi_source: "pdf_front_matter"
doi_confidence: "medium"
arxiv_id: ""
arxiv_source: ""
arxiv_confidence: "not_detected"
page_count: 16
record_type: "paper"
tier: "B"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U131: A Hybrid LLM–KG Framework for Biomedical QA (LLaMA-3B + Neo4j)

## Bibliographic Identity

- Verified title source: `acquisition_metadata_verified_in_pdf`
- DOI: 10.38094/jastt62404 (source: pdf_front_matter; confidence: medium)
- arXiv ID: not detected (source: not detected; confidence: not_detected)
- Pages: 16
- Source collection: `is2`
- Legacy primary alias: `research/ref-paper/is2/pdfs/14_a_hybrid_llmkg_framework_for_biomedical_2025.pdf`
- Identity result: `verified` (filename/title token overlap 1.00)

## Classification

**Tier B.** Transferable retrieval, RAG, evaluation, uncertainty, or knowledge-graph method. Relevant surface: IS2-adjacent.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, ranking, benchmark, embedding, knowledge graph, retrieval-augmented, prompt optimization, agent, biomedical, summarization, hallucination.

Abstract/summary section scan:

> Biomedical question answering requires accurate and interpretable systems; however, existing approaches often face challenges such as language model hallucinations and limited reasoning when relying solely on standalone knowledge graphs. To address these limitations, this study proposes a hybrid framework that integrates the LLaMA-3B language model with a Neo4j-based drug–disease–symptom knowledge graph. The system translates natural language questions into executable Cypher queries, operates on an iBKH-derived graph comprising over 65,000 entities and 3 million relationships, and returns answers with supporting evidence through a transparent interface. Experiments conducted on 60 biomedical questions across three levels of difficulty demonstrate the robustness of the approach: 96% exact match for simple queries, 95% for medium queries, and 86.7% for complex queries. Overall, the system achieves Precision@5 of 96.1%, Recall@5 of 89.0%, F1@5 of 91.0%, Hits@k of 96.1%, and an MRR of 94.4%, while maintaining an average response time of only 6.07 seconds. These results indicate that the system retrieves nearly all relevant answers, ranks them correctly, and delivers them with latency low enough for interactive use. Moreover, unlike cloud-based APIs such as ChatGPT, which require internet connectivity and external data transmission, the proposed framework operates fully offline, ensuring privacy, reproducibility, and compliance with biomedical data governance. Overall, this pipeline provides an accurate, efficient, and privacy-preserving solution for biomedical question answering, making it a practical alternative to cloud-dependent approaches in sensitive healthcare contexts. Keywords: Knowledge Graph, LLM, Question Answering, Neo4j, Biomedical Informatics, Healthcare AI, L

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
