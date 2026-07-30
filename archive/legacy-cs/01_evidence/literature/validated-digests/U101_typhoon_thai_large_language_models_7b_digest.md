---
paper_id: U101
title: "Typhoon: Thai Large Language Models (7B)"
pdf_sha256: "b9161f4b088b19efaf7cb573b85c163e8361d26c78a71c7b706acbf0e47b0e0d"
object_path: "01_evidence/B-tier/U101_typhoon_thai_large_language_models_7b.pdf"
legacy_primary_alias: "research/ref-paper/shared/pdfs/23_typhoon_thai_large_language_models_7b_2023.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: "2312.13951"
arxiv_source: "acquisition_url"
arxiv_confidence: "high"
page_count: 12
record_type: "paper"
tier: "B"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U101: Typhoon: Thai Large Language Models (7B)

## Bibliographic Identity

- Verified title source: `acquisition_metadata_verified_in_pdf`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: 2312.13951 (source: acquisition_url; confidence: high)
- Pages: 12
- Source collection: `shared`
- Legacy primary alias: `research/ref-paper/shared/pdfs/23_typhoon_thai_large_language_models_7b_2023.pdf`
- Identity result: `verified` (filename/title token overlap 1.00)

## Classification

**Tier B.** Transferable Thai/cross-lingual/legal evidence for the adjacent IS2 track. Relevant surface: IS2-adjacent.

## Content Triage

Controlled content signals found in the full-text extraction: benchmark, embedding, cross-lingual, thai, classification, summarization, hallucination.

Abstract/summary section scan:

> Typhoon is a series of Thai large language models (LLMs) developed specifically for the Thai language. This technical report presents challenges and insights in developing Thai LLMs, including data preparation, pretraining, instruction- tuning, and evaluation. As one of the challenges of low-resource languages is the amount of pretraining data, we apply continual training to transfer existing world knowledge from a strong LLM. To evaluate the Thai knowledge encapsulated in each model from the pretraining stage, we develop ThaiExam, a benchmark based on examinations for high-school students and investment professionals in Thailand. In addition, we fine-tune Typhoon to follow Thai instructions, and we evaluate instruction-tuned models on Thai instruction datasets as well as translation, summarization, and question-answering tasks. Experimental results on a suite of Thai benchmarks show that Typhoon outperforms all open-source Thai language models, and its performance is on par with GPT-3.5 in Thai while having only 7 billion parameters and being 2.62 times more efficient in tokenizing Thai text. Model Weights: https://huggingface.co/scb10x/typhoon-7b

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
