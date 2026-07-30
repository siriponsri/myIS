---
paper_id: U148
title: "LLaDR: LLM-Assisted Biomedical Concept Mapping for Drug Repurposing"
pdf_sha256: "c8eb99d7926c9febf8e4e416202ad9d13479a2d462167aad7ace539531f58b45"
object_path: "01_evidence/B-tier/U148_lladr_llm_assisted_biomedical_concept_mapping_for_drug_repurposing.pdf"
legacy_primary_alias: "research/ref-paper/is2/pdfs/59_lladr_llm_assisted_biomedical_concept_mapping_2025.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: "2510.12181"
arxiv_source: "acquisition_url"
arxiv_confidence: "high"
page_count: 16
record_type: "paper"
tier: "B"
identity_status: "verified_with_title_variation"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U148: LLaDR: LLM-Assisted Biomedical Concept Mapping for Drug Repurposing

## Bibliographic Identity

- Verified title source: `acquisition_metadata_verified_in_pdf`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: 2510.12181 (source: acquisition_url; confidence: high)
- Pages: 16
- Source collection: `is2`
- Legacy primary alias: `research/ref-paper/is2/pdfs/59_lladr_llm_assisted_biomedical_concept_mapping_2025.pdf`
- Identity result: `verified_with_title_variation` (filename/title token overlap 0.88)

## Classification

**Tier B.** Transferable retrieval, RAG, evaluation, uncertainty, or knowledge-graph method. Relevant surface: IS2-adjacent.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, ranking, benchmark, embedding, contrastive, knowledge graph, agent, thai, biomedical, classification.

Abstract/summary section scan:

> Gene Knowledge Graph Disease Drug repurposing plays a critical role in ac- Embedding Methods Compound arXiv:2510.12181v1 [cs.CL] 14 Oct 2025 Cell line celerating treatment discovery, especially for complex and rare diseases. Biomedical knowl- edge graphs (KGs), which encode rich clin- KG Representation ical associations, have been widely adopted Ours: Common-sense knowledge enhanced KG embedding to support this task. However, existing meth- Semantic ods largely overlook common-sense biomedi- LLM Concept Knowledge KGE cal concept knowledge in real-world labs, such (Pikachu, Pikachu is a fictional species of the as mechanistic priors indicating that certain media…) drugs are fundamentally incompatible with KG Representation specific treatments. To address this gap, we propose LLaDR, a Large Language Model- Figure 1: Comparison of standard KG embedding (top) assisted framework for Drug Repurposing, and LLaDR (bottom). LLaDR incorporating semantic which improves the representation of biomedi- concept knowledge generates more meaningful repre- cal concepts within KGs. Specifically, we ex- sentations, leading to better separation of entities. tract semantically enriched treatment-related textual representations of biomedical entities from large language models (LLMs) and use them to fine-tune knowledge graph embed- drug repurposing relies heavily on expert-driven ding (KGE) models. By injecting treatment- analysis of medical literature and clinical data, re- relevant knowledge into KGE, LLaDR largely quiring interdisciplinary collaboration across phar- improves the representation of biomedical con- macology, chemistry, and medicine (Samborskyi cepts, enhancing semantic understanding of et al., 2017). This process is time-consuming and under-studied or complex indications. Exp

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
