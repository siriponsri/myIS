---
paper_id: U098
title: "Named Entity Recognition of Pharmacokinetic Parameters in Pharmaceutical Literature"
pdf_sha256: "06a33f3104e1514429cab38e9a410abea56f20728b3d5dd76c6b311864ba4910"
object_path: "01_evidence/C-tier/U098_named_entity_recognition_of_pharmacokinetic_parameters_in_pharmaceutical.pdf"
legacy_primary_alias: "research/ref-paper/shared/pdfs/20_named_entity_recognition_of_pharmacokinetic_parameters_2024.pdf"
doi: "10.1038/s41598-024-73338-3"
doi_source: "pdf_front_matter"
doi_confidence: "medium"
arxiv_id: ""
arxiv_source: ""
arxiv_confidence: "not_detected"
page_count: 8
record_type: "paper"
tier: "C"
identity_status: "verified_with_title_variation"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U098: Named Entity Recognition of Pharmacokinetic Parameters in Pharmaceutical Literature

## Bibliographic Identity

- Verified title source: `acquisition_metadata_verified_in_pdf`
- DOI: 10.1038/s41598-024-73338-3 (source: pdf_front_matter; confidence: medium)
- arXiv ID: not detected (source: not detected; confidence: not_detected)
- Pages: 8
- Source collection: `shared`
- Legacy primary alias: `research/ref-paper/shared/pdfs/20_named_entity_recognition_of_pharmacokinetic_parameters_2024.pdf`
- Identity result: `verified_with_title_variation` (filename/title token overlap 0.86)

## Classification

**Tier C.** Contextual domain, classification, extraction, model, survey, or systems background. Relevant surface: background.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, benchmark, embedding, knowledge graph, thai, biomedical, named entity recognition, classification.

Abstract/summary section scan:

> pool with over a million sentences and the full-text pool with 721,522 sentences. To create a balanced candidate pool for ML model training and evaluation, 721,522 instances were randomly sampled from the abstract pool and combined with full-text sentences, resulting in a balanced pool of 1,443,044 sentences, referred to as the candidate pool. All labelled sentences in the corpus construction were sampled from the candidate pool. Annotation The team responsible for the annotation involved twelve annotators with extensive PK expertise and familiarity with the different parameters and study types in the PK literature. To ensure consistency in the annotation process, each annotator initially labelled a small set of 200 examples to identify sources of disagreement. The Figure 1. Flow diagram showing the main processes involved to generate a pool of candidate sentences for NER labelling. (1) Search for “pharmacokinetics” in PubMed and (2) run binary classification pipeline to filter abstracts containing PK parameters. (3) Parse XML abstract and full-text documents, and (4) filter out introduction sections. Finally, (5) segment each paragraph into sentences to generate the final corpus of PK sentences. Scientific Reports | (2024) 14:23485 | https://doi.org/10.1038/s41598-024-73338-3 2 www.nature.com/scientificreports/ team then discussed which parameters to include and how to define span boundaries using the PK ontology from Wu et al.11 as a reference. Annotation guidelines were provided to annotators before they began the labelling task, and were updated as new challenging examples were resolved during the annotation process. Details about the annotation interface and guidelines can be found in Supplementary Information: Appendix A. Training, development and test sets were d

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
