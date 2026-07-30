---
paper_id: U070
title: "POSIX: A Prompt Sensitivity Index For Large Language Models"
pdf_sha256: "5d0729622cd43ff6044f672aff054f231d35b87aed3ca3d6caa6a88af00e0170"
object_path: "01_evidence/C-tier/U070_posix_a_prompt_sensitivity_index_for_large_language_models.pdf"
legacy_primary_alias: "research/ref-paper/is1/pdfs/72_a_prompt_sensitivity_index_for_large_language_models.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: "2410.02185"
arxiv_source: "pdf_front_matter"
arxiv_confidence: "medium"
page_count: 16
record_type: "paper"
tier: "C"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U070: POSIX: A Prompt Sensitivity Index For Large Language Models

## Bibliographic Identity

- Verified title source: `acquisition_metadata_verified_in_pdf`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: 2410.02185 (source: pdf_front_matter; confidence: medium)
- Pages: 16
- Source collection: `is1`
- Legacy primary alias: `research/ref-paper/is1/pdfs/72_a_prompt_sensitivity_index_for_large_language_models.pdf`
- Identity result: `verified` (filename/title token overlap 1.00)

## Classification

**Tier C.** Contextual domain, classification, extraction, model, survey, or systems background. Relevant surface: H/S.

## Content Triage

Controlled content signals found in the full-text extraction: benchmark, embedding.

Abstract/summary section scan:

> token-prediction objective and they can perform a Despite their remarkable capabilities, Large variety of NLP tasks via “prompting” (Brown et al., Language Models (LLMs) are found to be 2020; Kojima et al., 2022; Almazrouei et al., 2023; surprisingly sensitive to minor variations in Liu et al., 2023; Touvron et al., 2023). However, arXiv:2410.02185v2 [cs.CL] 4 Oct 2024 prompts, often generating significantly diver- LLMs have been found to be surprisingly sensi- gent outputs in response to minor variations tive even to the smallest of variations in prompts in the prompts, such as spelling errors, alter- that do not significantly alter its meaning – such as ation of wording or the prompt template. How- wording, prompt template or even minor spelling ever, while assessing the quality of an LLM, errors – so much so that prompt engineering, which the focus often tends to be solely on its per- formance on downstream tasks, while very is a process of iteratively tuning prompts to elicit little to no attention is paid to prompt sen- desired responses, has become a widespread prac- sitivity. To fill this gap, we propose POSIX tice (Reynolds and McDonell, 2021). – a novel PrOmpt Sensitivity IndeX as a re- Despite prompt sensitivity being a crucial aspect liable measure of prompt sensitivity, thereby for assessing the usability of an LLM, standard offering a more comprehensive evaluation of evaluation benchmarks such as MMLU (Hendrycks LLM performance. The key idea behind et al., 2021) or BBH (Suzgun et al., 2022) focus POSIX is to capture the relative change in log- likelihood of a given response upon replac- predominantly on performance metrics like exact ing the corresponding prompt with a different match, leaving prompt sensitivity sidelined. Simi- intent-preserving prompt. We

Conclusion/discussion section scan:

> Ethical Considerations We introduced POSIX - a novel prompt sensitivity Since we use open-source large language models index, as a reliable measure of sensitivity of LLMs and open-source datasets like MMLU and Alpaca, towards intent-preserving variations in prompts our work encompasses all the corresponding con- such as spelling errors, prompt templates, and alter- siderations of those works. Although, our method ations in the wording. We presented thorough em- would be expected to largely benefit the commu- pirical analysis for the efficacy of POSIX in captur- nity by providing a reliable way to evaluate sensi- ing prompt sensitivity and subsequently used it to tivity of large language models towards variations measure and compare multiple open-source LLMs, in prompts. While attempting to paraphrase the revealing some interesting observations such as prompts in MMLU using GPT-3.5-Turbo, quite prompt template is the most sensitive variant type a few prompts have been flagged as either vio- for MCQ tasks and paraphrasing is the most sensi- lent or biased, etc. Most of them were from the tive variant type for open-ended generation tasks, moral_scenarios split of MMLU. We made sure to and also that parameter count or instruction tuning remove these from our analyses. do not necessarily decrease prompt sensitivity of the models. These findings highlight the nuanced Acknowledgments

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
