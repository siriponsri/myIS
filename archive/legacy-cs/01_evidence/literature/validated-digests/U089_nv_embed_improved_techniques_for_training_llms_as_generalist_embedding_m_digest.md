---
paper_id: U089
title: "NV-Embed: Improved Techniques for Training LLMs as Generalist Embedding Models"
pdf_sha256: "54b7f1f28a36dfeed20d7524fca57903c7af4f438c63ae5615aa0b1881c4384a"
object_path: "01_evidence/B-tier/U089_nv_embed_improved_techniques_for_training_llms_as_generalist_embedding_m.pdf"
legacy_primary_alias: "research/ref-paper/shared/pdfs/07_nv_embed_improved_techniques_for_training_2024.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: ""
arxiv_source: ""
arxiv_confidence: "not_detected"
page_count: 24
record_type: "paper"
tier: "B"
identity_status: "verified_with_title_variation"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U089: NV-Embed: Improved Techniques for Training LLMs as Generalist Embedding Models

## Bibliographic Identity

- Verified title source: `acquisition_metadata_verified_in_pdf`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: not detected (source: not detected; confidence: not_detected)
- Pages: 24
- Source collection: `shared`
- Legacy primary alias: `research/ref-paper/shared/pdfs/07_nv_embed_improved_techniques_for_training_2024.pdf`
- Identity result: `verified_with_title_variation` (filename/title token overlap 0.89)

## Classification

**Tier B.** Transferable retrieval, RAG, evaluation, uncertainty, or knowledge-graph method. Relevant surface: C, R, H/S.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, reranking, ranking, benchmark, embedding, contrastive, retrieval-augmented, agent, thai, legal, biomedical, classification.

Abstract/summary section scan:

> field are used for the query 6 Published as a conference paper at ICLR 2025 q + . For binary classification tasks the label texts are used as documents d+ , d− . For multi-class classification and clustering tasks, a randomly sampled example from the ground-truth class/cluster is used for the positive document d+ and randomly sampled examples from other classes/clusters are used for negative documents d− k . We will present ablation experiments supporting this approach in section 5.2.4. For semantic textual similarity datasets, we use the training splits of three semantic similarity datasets STS12 (Agirre et al., 2012), STS22 (Chen et al., 2022), STS-Benchmark (Cer et al., 2017) from MTEB Huggingface datasets. For any pair of texts with associated relevance scores (ta , tb , score), we create two examples (q + = ta , d+ = tb ) and (q + = tb , d+ = ta ) if score ≥ 4. We mine the hard negatives d− k from the pool of other texts using the same technique as section 4.1.1. Task instructions are appended to d+ , d− since they are symmmetric with the query. 4.3 S YNTHETIC TASKS DATASET Due to the limited variety of subjects and tasks in public training datasets, the available instruction templates for training are also restricted. To enhance task-wise generalization, we employ the Mixtral-8x22B-Instruct-v0.1 model (MistralAI) to create a dataset consisting of 120,000 synthetic examples across 60,000 synthetic tasks. Following a two-step prompting approach proposed by E5-mistral-7b-instruct (Wang et al., 2023b), we adjust the prompts for Mixtral-8x22B-Instruct-v0.1 and English text. We generate only the short-long, long-short, and short-short examples (40,000 of each), as we use public STS datasets and do not assess bitext retrieval tasks. Example prompts for synthetic data gen

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
