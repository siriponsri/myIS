---
paper_id: U068
title: "RAPO Retrieval-Augmented Prompt Optimization"
pdf_sha256: "2c1012c9aa8414a92ac0bbfff8c8b53dd6f19d89654e0e32cdc344919456b095"
object_path: "01_evidence/A-tier/U068_rapo_retrieval_augmented_prompt_optimization.pdf"
legacy_primary_alias: "research/ref-paper/is1/pdfs/69__rapo_retrieval_augmented_prompt_optimization_2024.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: ""
arxiv_source: ""
arxiv_confidence: "not_detected"
page_count: 10
record_type: "paper"
tier: "A"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U068: RAPO Retrieval-Augmented Prompt Optimization

## Bibliographic Identity

- Verified title source: `acquisition_metadata_verified_in_pdf`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: not detected (source: not detected; confidence: not_detected)
- Pages: 10
- Source collection: `is1`
- Legacy primary alias: `research/ref-paper/is1/pdfs/69__rapo_retrieval_augmented_prompt_optimization_2024.pdf`
- Identity result: `verified` (filename/title token overlap 1.00)

## Classification

**Tier A.** Direct HarnessOpt/skill/prompt optimization method evidence. Relevant surface: C, R, H/S.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, reranking, ranking, benchmark, embedding, retrieval-augmented, prompt optimization, agent, classification, hallucination.

Abstract/summary section scan:

> Published at ICLR 2024 Workshop on Secure and Trustworthy Large Language Models R ETRIEVAL AUGMENTED P ROMPT O PTIMIZATION Yifan Sun, Jean-Baptiste Tien, Karthik Lakshmanan Google {yifansun,jbtien,lakshmanan}@google.com A BSTRACT Prompt optimization for Large Language Models (LLMs) has recently made great strides in complex tasks such as solving arithmetic problems and reasoning. Yet, its efficacy remains limited in tasks demanding extensive domain expertise beyond the internal knowledge of LLMs. As context length increases, prompt optimization tends to plateau in performance, which limits the amount of domain knowledge we can provide in the prompt. We postulate that this difficulty stems from an inherent tradeoff between adding information and easing comprehension. To tackle this challenge, we present a divide-and-conquer approach (RAPO) to prompt optimization by means of retrieval augmentation. RAPO breaks the entire problem space into a number of subspaces, where each subspace can be handled separately by a local prompt specifically designed to cater to it. This approach not only scales more effectively to larger training datasets but also naturally accommodates domain knowledge

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
