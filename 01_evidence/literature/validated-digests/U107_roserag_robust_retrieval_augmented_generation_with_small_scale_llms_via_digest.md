---
paper_id: U107
title: "ROSERAG: Robust Retrieval-Augmented Generation with Small-Scale LLMs via Diverse Augmentation"
pdf_sha256: "029f0085a205644c224ac7287d1027e5a8f5905ad47fe5e41c5e3e2b852ae1ad"
object_path: "01_evidence/B-tier/U107_roserag_robust_retrieval_augmented_generation_with_small_scale_llms_via.pdf"
legacy_primary_alias: "research/ref-paper/shared/pdfs/31_roserag_robust_retrieval_augmented_generation_with_2025.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: ""
arxiv_source: ""
arxiv_confidence: "not_detected"
page_count: 19
record_type: "paper"
tier: "B"
identity_status: "verified_with_title_variation"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U107: ROSERAG: Robust Retrieval-Augmented Generation with Small-Scale LLMs via Diverse Augmentation

## Bibliographic Identity

- Verified title source: `acquisition_metadata_verified_in_pdf`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: not detected (source: not detected; confidence: not_detected)
- Pages: 19
- Source collection: `shared`
- Legacy primary alias: `research/ref-paper/shared/pdfs/31_roserag_robust_retrieval_augmented_generation_with_2025.pdf`
- Identity result: `verified_with_title_variation` (filename/title token overlap 0.80)

## Classification

**Tier B.** Transferable retrieval, RAG, evaluation, uncertainty, or knowledge-graph method. Relevant surface: C, R, H/S.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, benchmark, contrastive, retrieval-augmented, thai, classification.

Abstract/summary section scan:

> 0.6 Exact Match F1 0.4 Exact Match 0.3 F1 0.5 Large language models (LLMs) have achieved impressive performance but face high compu- 0.4 0 1 2 3 5 0.2 1 2 5 8 10 tational costs and latency, limiting their de- Number of Noisy Documents Number of Retrieved Documents ployment in resource-constrained settings. In (a) (b) contrast, small-scale LLMs (SLMs) are more efficient yet struggle to capture evolving real- Figure 1: Pilot studies. Fig. 1a: Ground Truth Doc- world knowledge. Retrieval-augmented genera- uments with varying amounts of noisy documents. tion (RAG) helps by integrating external knowl- Fig. 1b: Performance w.r.t. varying numbers of re- edge, but imperfect retrieval can introduce dis- trieved documents. Both the two sub-figures are results tracting noise that misleads SLMs. We pro- with Qwen2.5-1.5B-Instruct on HotPotQA. pose ROSE RAG, a robust RAG framework for SLMs via Margin-aware Preference Optimiza- deploy in resource-constrained environments (Lu tion. ROSE RAG employs multi-turn prompt- ing for detailed reasoning, rejection sampling et al., 2024; Vernikos et al., 2024). for high-quality explanations, and contrastive Despite their efficiency, SLMs are fundamen- preference selection to refine responses by max- tally constrained by their limited capacity. During imizing the likelihood gap between preferred pre-training, they cannot fully capture the vast and and non-preferred outputs. By integrating these continuously evolving body of real-world knowl- components into a margin-aware optimization edge (Ovadia et al., 2024). As a result, SLMs of- process, ROSE RAG robustly enhances the ac- ten struggle in real-world scenarios where accurate curacy and reliability of SLMs for RAG appli- cations. Extensive experiments on three open- responses depend on newly em

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
