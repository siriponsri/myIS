---
paper_id: U096
title: "PubMed Knowledge Graph 2.0: Connecting Papers, Patents, and Clinical Trials"
pdf_sha256: "3b2a4ee86f919e00e5a37bcdc5a41a854fcf6fee7ba2e20c19533c0e335d8aa0"
object_path: "01_evidence/B-tier/U096_pubmed_knowledge_graph_2_0_connecting_papers_patents_and_clinical_trials.pdf"
legacy_primary_alias: "research/ref-paper/shared/pdfs/17_pubmed_knowledge_graph_2_0_connecting_2025.pdf"
doi: "10.1038/s41597-025-05343-8"
doi_source: "pdf_metadata"
doi_confidence: "high"
arxiv_id: ""
arxiv_source: ""
arxiv_confidence: "not_detected"
page_count: 20
record_type: "paper"
tier: "B"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U096: PubMed Knowledge Graph 2.0: Connecting Papers, Patents, and Clinical Trials

## Bibliographic Identity

- Verified title source: `acquisition_metadata_verified_in_pdf`
- DOI: 10.1038/s41597-025-05343-8 (source: pdf_metadata; confidence: high)
- arXiv ID: not detected (source: not detected; confidence: not_detected)
- Pages: 20
- Source collection: `shared`
- Legacy primary alias: `research/ref-paper/shared/pdfs/17_pubmed_knowledge_graph_2_0_connecting_2025.pdf`
- Identity result: `verified` (filename/title token overlap 1.00)

## Classification

**Tier B.** Transferable retrieval, RAG, evaluation, uncertainty, or knowledge-graph method. Relevant surface: C, R, IS2-adjacent.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, ranking, patent, embedding, knowledge graph, agent, legal, biomedical, named entity recognition, classification.

Abstract/summary section scan:

> EndPosition Integer End position of mention in an abstract. Mention String Entity mentioned in an abstract. Entityid String Normalized entity identifiers, include mesh, mim, CL, cellosaurus, NCBITaxon, NCBIGene, CHEBI. Enumerated type of entity; values include species, disease, gene, drug, mutation, cell_line, cell_type, Type Integer DNA, RNA. For diseases and chemicals, BERN2 use hybrid NEN models, which are a combination of both rule- is_neural_normalized Integer based and neural network-based models. An entity that is not normalized by the rule-based model is then normalized by a neural network-based model. Table 10. Data type for records of Link_Papers_BioEntities. Index Format Short description PMID Integer Unique ID assigned by PubMed to identify articles. PubYear Integer The year in which the journal issue was published. Journal_ISSN String Unique ID of Journal. Journal_Title String Title of Journal. Journal_SJR Float The SJR of the journal when the issue was published. Journal_Hindex Integer The h-index of the journal when the issue was published. Table 11. Data type for records of Link_Papers_Journals. Index Format Short description nct_id String Unique ID assigned by ClinicalTrials.gov to identify clinical trial studies. brief_title String Title of the trial. The date the study started in a date-type format so that it can be used to find studies before/after/inclusive of a date start_date date or dates. For studies that only provide month/year, the last day of the month is used. Table 12. Data type for records of ClinicalTrials. Index Format Short description PMID Integer Unique ID assigned by PubMed to identify articles. NctId String Unique clinical trial study identifier in ClinicalTrials.gov. Table 13. Data type for records of Link_Papers_ClinicalTrials. In

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
