---
paper_id: U085
title: "Precise Zero-Shot Dense Retrieval without Relevance Labels (HyDE)"
pdf_sha256: "dc0ae3c5584ed146beee122e6a9ad9c48547dde048d53e9be8435d8f1d354531"
object_path: "01_evidence/B-tier/U085_precise_zero_shot_dense_retrieval_without_relevance_labels_hyde.pdf"
legacy_primary_alias: "research/ref-paper/shared/pdfs/03_precise_zero_shot_dense_retrieval_without_2023.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: "2212.10496"
arxiv_source: "acquisition_url"
arxiv_confidence: "high"
page_count: 11
record_type: "paper"
tier: "B"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U085: Precise Zero-Shot Dense Retrieval without Relevance Labels (HyDE)

## Bibliographic Identity

- Verified title source: `acquisition_metadata_verified_in_pdf`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: 2212.10496 (source: acquisition_url; confidence: high)
- Pages: 11
- Source collection: `shared`
- Legacy primary alias: `research/ref-paper/shared/pdfs/03_precise_zero_shot_dense_retrieval_without_2023.pdf`
- Identity result: `verified` (filename/title token overlap 1.00)

## Classification

**Tier B.** Transferable retrieval, RAG, evaluation, uncertainty, or knowledge-graph method. Relevant surface: C, R.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, benchmark, embedding, contrastive, cross-lingual.

Abstract/summary section scan:

> pre-training (Izacard et al., 2021; Gao and Callan, 2021; Lu et al., 2021; Gao and Callan, 2022; Liu While dense retrieval has been shown effec- and Shao, 2022) have been proposed to improve the tive and efficient across tasks and languages, effectiveness of supervised dense retrieval models. it remains difficult to create effective fully arXiv:2212.10496v1 [cs.IR] 20 Dec 2022 zero-shot dense retrieval systems when no rel- On the other hand, zero-shot dense retrieval still evance label is available. In this paper, we remains difficult. Many recent works consider the recognize the difficulty of zero-shot learning alternative transfer learning setup, where the dense and encoding relevance. Instead, we pro- retrievers are trained on a high-resource dataset and pose to pivot through Hypothetical Document then evaluated on queries from new tasks. The MS- Embeddings (HyDE). Given a query, HyDE first MARCO collection (Bajaj et al., 2016), a massive zero-shot instructs an instruction-following language model (e.g. InstructGPT) to gen- judged dataset with a large number of judged query- erate a hypothetical document. The docu- document pairs, is arguably the most commonly ment captures relevance patterns but is unreal used. As argued by Izacard et al. (2021), in prac- and may contain false details. Then, an un- tice, however, the existence of such a large dataset supervised contrastively learned encoder (e.g. cannot always be assumed. Even MS-MARCO re- Contriever) encodes the document into an stricts commercial use and cannot be adopted in a embedding vector. This vector identifies a variety of real-world search scenarios. neighborhood in the corpus embedding space, where similar real documents are retrieved In this paper, we aim to build effective fully based on vector similari

Conclusion/discussion section scan:

> In Table 4, we show HyDE using other instruction-following language models. In At the end of the paper, we encourage the readers particular, we consider a 52-billion Cohere to take a moment and reflect on the HyDE model. model (command-xlarge-20221108) and a Compare it to some of the other recently seen re- 11-billion FLAN model (FLAN-T5-xxl; Wei trievers or re-ranker. These other models probably et al. (2022)).2 Generally, we observe that all differ in their architecture, training method, and/or 2 Model sizes are from https://crfm.stanford.edu/ task, but probably all of them involve modeling helm/v1.0/?models. relevance scores between a pair of query and docu- ment. Dense retrievers consider vector similarities Tom B. Brown, Benjamin Mann, Nick Ryder, Melanie while self-attentive re-rankers regression scores. In Subbiah, Jared Kaplan, Prafulla Dhariwal, Arvind Neelakantan, Pranav Shyam, Girish Sastry, Amanda comparison, the concept of relevance in HyDE is Askell, Sandhini Agarwal, Ariel Herbert-Voss, captured by an NLG model and the language gener- Gretchen Krueger, Tom Henighan, Rewon Child, ation process. We demonstrate in many cases, HyDE Aditya Ramesh, Daniel M. Ziegler, Jeffrey Wu, can be as effective as dense retrievers that learn to Clemens Winter, Christopher Hesse, Mark Chen, model numerical relevance scores. So, is numeri- Eric Sigler, Mateusz Litwin, Scott Gray, Ben

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
