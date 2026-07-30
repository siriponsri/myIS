---
paper_id: U123
title: "OpenThaiGPT 1.5: A Thai-Centric Open Source LLM"
pdf_sha256: "12024560d3be8dcd486e96e402dd114565a5b4d73d263148b196168c5f7f84fd"
object_path: "01_evidence/B-tier/U123_openthaigpt_1_5_a_thai_centric_open_source_llm.pdf"
legacy_primary_alias: "research/ref-paper/is2/pdfs/02_openthaigpt_1_5_a_thai_centric_2024.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: "2411.07238"
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

# U123: OpenThaiGPT 1.5: A Thai-Centric Open Source LLM

## Bibliographic Identity

- Verified title source: `acquisition_metadata_verified_in_pdf`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: 2411.07238 (source: acquisition_url; confidence: high)
- Pages: 8
- Source collection: `is2`
- Legacy primary alias: `research/ref-paper/is2/pdfs/02_openthaigpt_1_5_a_thai_centric_2024.pdf`
- Identity result: `verified` (filename/title token overlap 1.00)

## Classification

**Tier B.** Transferable retrieval, RAG, evaluation, uncertainty, or knowledge-graph method. Relevant surface: C, R, IS2-adjacent.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, benchmark, cross-lingual, thai, classification, summarization.

Abstract/summary section scan:

> OpenThaiGPT 1.5 is an advanced Thai language chat model based on Qwen v2.5, finetuned on over 2,000,000 Thai instruction pairs. This report provides an engineering perspective on the model’s development, capabilities, and performance. We discuss the model’s architecture, training process, and key features, including multi-turn conversation support, Retrieval Augmented Generation (RAG) compatibility, and tool-calling functionality. Benchmark results demonstrate OpenThaiGPT 1.5’s state-of-the-art performance on various Thai language tasks, outperforming other open-source Thai language models. We also address practical considerations such as GPU memory requirements and deployment strategies. 1 Model Architecture and Training 1.1 Base Model OpenThaiGPT 1.5 is built upon the Qwen v2.5 architecture [5], leveraging its advanced capabilities as a foundation for Thai language modeling. The model is available in two sizes: 7 billion and 72 billion parameters, catering to different computational resource constraints and performance requirements. The 7B model was finetuned from Qwen/Qwen2.5-7B-Instruct on Huggingface, and the 72B model was fine- tuned from Qwen/Qwen2.5-72B-Instruct. Both base models have a vocabulary size of 152,064 and a maximum input length of 32,768. Inspection of the tokenizers and initial experimentation revealed that the Qwen 2.5 models already support the Thai language. For this reason, as well as due to the limitation of our computing, we opted not to perform any continued pretraining of the model with Thai data and start with instruction finetuning. 1.2 Finetuning Process The model underwent extensive finetuning on a diverse dataset of over 2,000,000 Thai instruction pairs. This process was crucial in adapting the base model to the nuances of the Thai lang

Conclusion/discussion section scan:

> We have developed and released OpenThaiGPT version 1.5 on Huggingface at openthaigpt/openthaigpt1.5- {size}b-instruct where {size} are 7, 14 or 72. There are based on Qwen2.5 family of models. Extensive experiments on Thai exams data showed that OpenThaiGPT1.5 is currently the most capable open model for the Thai language. 4 Table 2: Performance Comparison of Different Language Models in the 14B sizes on OpenThaiGPT Evaluation Dataset. Note that there are no 14B sized models for Llama-3.1 and Typhoon-v1.5x. Qwen2.5-14B OpenThaiGPT1.5-14b Exam Name Score Total % Score Total % A Level 74 120 61.67 78 120 65.00 TGAT 22 50 44.00 25 50 50.00 TPAT1 24 40 60.00 21 40 52.50 Investment Consult 19 25 76.00 18 25 72.00 Facebook Beleble TH 169 200 84.50 174 200 87.00 XCOPA TH 170 200 85.00 173 200 86.50 XNLI 2.0 TH 139 200 69.50 129 200 64.50 O-NET M3 Thai 19 25 76.00 21 25 84.00 O-NET M3 Social 18 20 90.00 18 20 90.00 O-NET M3 Math 7 16 43.75 2 16 12.50 O-NET M3 Science 13 26 50.00 14 26 53.85 O-NET M3 English 28 30 93.33 28 30 93.33 O-NET M6 Thai 34 65 52.31 37 65 56.92 O-NET M6 Math 4 17 23.53 7 17 41.18 O-NET M6 Social 33 55 60.00 34 55 61.82 O-NET M6 Science 14 28 50.00 16 28 57.14 O-NET M6 English 43 52 82.69 41 52 78.85 Total/Average 830 1169 71.09 836 1169 71.51 Table 3: Performance Comparison of Different Language Models in the 70B - 72B sizes on OpenThaiGPT Evaluation Dataset Lla

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
