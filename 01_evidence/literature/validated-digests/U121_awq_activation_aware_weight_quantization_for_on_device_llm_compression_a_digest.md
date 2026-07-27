---
paper_id: U121
title: "AWQ: Activation-Aware Weight Quantization for On-Device LLM Compression and Acceleration"
pdf_sha256: "6e35c8fe7af1f18a5c48dd2524629d859a2013a91d4b3666b554705287a17764"
object_path: "01_evidence/C-tier/U121_awq_activation_aware_weight_quantization_for_on_device_llm_compression_a.pdf"
legacy_primary_alias: "research/ref-paper/shared/pdfs/57_awq_activation_aware_weight_quantization_2024.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: "2306.00978"
arxiv_source: "acquisition_url"
arxiv_confidence: "high"
page_count: 15
record_type: "paper"
tier: "C"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U121: AWQ: Activation-Aware Weight Quantization for On-Device LLM Compression and Acceleration

## Bibliographic Identity

- Verified title source: `acquisition_metadata_verified_in_pdf`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: 2306.00978 (source: acquisition_url; confidence: high)
- Pages: 15
- Source collection: `shared`
- Legacy primary alias: `research/ref-paper/shared/pdfs/57_awq_activation_aware_weight_quantization_2024.pdf`
- Identity result: `verified` (filename/title token overlap 1.00)

## Classification

**Tier C.** Contextual domain, classification, extraction, model, survey, or systems background. Relevant surface: background.

## Content Triage

Controlled content signals found in the full-text extraction: benchmark, embedding, classification, calibration, hallucination.

Abstract/summary section scan:

> AWQ: A CTIVATION - AWARE W EIGHT Q UANTIZATION FOR O N -D EVICE LLM C OMPRESSION AND ACCELERATION Ji Lin * 1 Jiaming Tang * 1 2 Haotian Tang † 1 Shang Yang † 1 Wei-Ming Chen 3 Wei-Chen Wang 1 Guangxuan Xiao 1 Xingyu Dang 1 4 Chuang Gan 5 6 Song Han 1 3 https://github.com/mit-han-lab/llm-awq A BSTRACT arXiv:2306.00978v6 [cs.CL] 25 Apr 2026 Large language models (LLMs) have transformed numerous AI applications. On-device LLM is becoming increas- ingly important: running LLMs locally on edge devices can reduce the cloud computing cost and protect users’ privacy. However, the astronomical model size and the limited hardware resource pose significant deployment challenges. We propose Activation-aware Weight Quantization (AWQ), a hardware-friendly approach for LLM low-bit weight-only quantization. AWQ finds that not all weights in an LLM are equally important. Protecting only 1% salient weights can greatly reduce quantization error. To identify salient weight channels, we should refer to the activation distribution, not weights. To avoid the hardware-inefficient mix-precision quantization, we mathematically derive that scaling up the salient channels can reduce the quantization error. AW

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
