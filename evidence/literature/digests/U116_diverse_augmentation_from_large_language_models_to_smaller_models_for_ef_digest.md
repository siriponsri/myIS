---
paper_id: U116
title: "Diverse Augmentation from Large Language Models to Smaller Models for Efficient Retrieval (ACL 2025)"
pdf_sha256: "66223cee6c9baa0726af956d295ce9fc4c025d66280b4d367d840c9f89e1bfd2"
object_path: "01_evidence/C-tier/U116_diverse_augmentation_from_large_language_models_to_smaller_models_for_ef.pdf"
legacy_primary_alias: "research/ref-paper/shared/pdfs/47_diverse_augmentation_from_large_language_models_2025.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: ""
arxiv_source: ""
arxiv_confidence: "not_detected"
page_count: 17
record_type: "paper"
tier: "C"
identity_status: "verified_with_title_variation"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U116: Diverse Augmentation from Large Language Models to Smaller Models for Efficient Retrieval (ACL 2025)

## Bibliographic Identity

- Verified title source: `acquisition_metadata_verified_in_pdf`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: not detected (source: not detected; confidence: not_detected)
- Pages: 17
- Source collection: `shared`
- Legacy primary alias: `research/ref-paper/shared/pdfs/47_diverse_augmentation_from_large_language_models_2025.pdf`
- Identity result: `verified_with_title_variation` (filename/title token overlap 0.89)

## Classification

**Tier C.** Contextual domain, classification, extraction, model, survey, or systems background. Relevant surface: C, R.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, reranking, ranking, benchmark, embedding, contrastive, agent, cross-lingual, thai, classification.

Abstract/summary section scan:

> In this work, we holistically explore how to effec- tively leverage LLMs to create smaller retrievers, Large language models (LLMs) have demon- in terms of both data and model backbone, to de- strated strong effectiveness and robustness velop generalizable yet efficient dense retrievers when fine-tuned as dense retrievers. How- ever, their large parameter size presents sig- with fewer than 1B parameters. nificant computational challenges at inference Although several works have discussed using time. While smaller retrievers offer better ef- LLMs for retrieval data augmentation, such as ficiency, they often fail to generalize effec- directly generating training triplet (Wang et al., tively with limited supervised fine-tuning data. 2024b) or using LLM to mine positive and negative In this work, we introduce D RAMA, a train- documents from a real corpus (Lee et al., 2024), ing framework that leverages LLMs to train the effectiveness of these methods has not been smaller generalizable dense retrievers. In par- ticular, we adopt pruned LLMs as the backbone rigorously compared. We comprehensively study and train on diverse LLM-augmented data in a the effectiveness of multiple LLM data augmen- single-stage contrastive learning setup. Exper- tation methods with a controlled setup: using the iments show that D RAMA offers better multi- same models and corpora across different data cre- lingual and long-context capabilities than tra- ation methods and only relying on open-sourced ditional encoder-based retrievers, and achieves models and open-access data. Specifically, we uti- strong performance across multiple tasks and lize an LLM retriever based on Llama3.18B and languages.1 an instruction-tuned LLM based on Llama3.370B - 1 Introduction Instruct to generate augmentation data.

Conclusion/discussion section scan:

> encoder-only model. However, unlike Modern- BERT, our approach retains multilingual support We introduce D RAMA, a training framework that and leverages existing LLM pretraining, dropping leverages large language models to train smaller, the need to train the backbone from scratch. generalizable dense retrievers by cohesively inte- grating LLM pruning and diverse LLM data aug- 6.3 Attention and Pooling Mechanism mentation. D RAMA achieves strong performance In Table 5, we analyze how the attention mecha- across English and multilingual retrieval tasks, en- nism and pooling strategy affect retrieval perfor- abling the training of smaller retrievers to improve mance when training the pruned model as a text en- together with advancements in LLMs. 30178 Limitations Ethics Statement While D RAMA achieves strong retrieval effective- This work complies with the ACL Ethics Policy. ness across English and multilingual tasks, several We declare that there are no ethical issues in this areas remain open for further investigation. paper, to the best of our knowledge. Firstly, the scope of language support. As ob-

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
