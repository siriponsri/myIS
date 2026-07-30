---
paper_id: U086
title: "M3-Embedding: Multi-Linguality, Multi-Functionality, Multi-Granularity Text Embeddings (BGE-M3)"
pdf_sha256: "eb38e53565da260dc1f3d49708f45441936447a7f3c7d7ef025ff62ea3e1e575"
object_path: "01_evidence/B-tier/U086_m3_embedding_multi_linguality_multi_functionality_multi_granularity_text.pdf"
legacy_primary_alias: "research/ref-paper/shared/pdfs/04_m3_embedding_multi_linguality_multi_functionality_2024.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: "2402.03216"
arxiv_source: "acquisition_url"
arxiv_confidence: "high"
page_count: 18
record_type: "paper"
tier: "B"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U086: M3-Embedding: Multi-Linguality, Multi-Functionality, Multi-Granularity Text Embeddings (BGE-M3)

## Bibliographic Identity

- Verified title source: `acquisition_metadata_verified_in_pdf`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: 2402.03216 (source: acquisition_url; confidence: high)
- Pages: 18
- Source collection: `shared`
- Legacy primary alias: `research/ref-paper/shared/pdfs/04_m3_embedding_multi_linguality_multi_functionality_2024.pdf`
- Identity result: `verified` (filename/title token overlap 1.00)

## Classification

**Tier B.** Transferable retrieval, RAG, evaluation, uncertainty, or knowledge-graph method. Relevant surface: C, R, IS2-adjacent.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, ranking, benchmark, embedding, contrastive, cross-lingual, legal, biomedical.

Abstract/summary section scan:

> Multi-Granularity Multi-Linguality Multi-Functionality Multi-Granularity In this paper,Dense 100+ Languages weRetrieval Sentence-Level introduce a new embedding 100+ Languages Dense Retrieval Sentence-Level arXiv:2402.03216v5 [cs.CL] 12 Dec 2025 model called M3-Embedding, which is distin- Multi-Lingual Sparse Retrieval Passage-Level Multi-Lingual Sparse Retrieval Passage-Level guished for its versatility in Multi-Linguality, Multi-Functionality, Cross-Lingual and Multi-Granularity. Multi-Vec Retrieval Doc-Level (≤8192) It Cross-Lingual Multi-Vec Retrieval Doc-Level (≤8192) provides a uniform support for the semantic re- trieval of more than 100 working languages. It can simultaneously accomplish the three com- BGE M3-Embedding M3-Embedding mon retrieval functionalities: dense retrieval, multi-vector retrieval, and sparse retrieval. Be- sides, it is also capable of processing inputs Figure 1: Characters of M3-Embedding. of different granularities, spanning from short sentences to long documents of up to 8,192 to- dense retrieval, where relevant answers to the query kens. The effective training of M3-Embedding can be retrieved based on the embedding similarity presents a series of technical contributions. No- (Karpukhin et al., 2020; Xiong et al., 2020; Nee- tably, we propose a novel self-knowledge dis- lakantan et al., 2022; Wang et al., 2022; Xiao et al., tillation approach, where the relevance scores 2023). Besides, the embedding model can also be from different retrieval functionalities can be applied to other IR tasks, such as multi-vector re- integrated as the teacher signal to enhance the training quality. We also optimize the trieval where the fine-grained relevance between batching strategy, which enables a large batch query and document is computed based on the

Conclusion/discussion section scan:

> the uneven distribution of training data for differ- In this paper, we introduce M3-Embedding, which ent languages, the model’s performance may vary substantially advances the versatility of text em- across languages, which could potentially be seen beddings in terms of supporting multi-lingual re- as discriminatory or unfair. We ensure that our trieval, handling input of diverse granularities, and work is conformant to the ACL Ethics Policy7 . unifying different retrieval functionalities. M3- Embedding presents three technical contributions: Acknowledgements self-knowledge distillation, efficient batching, and We would like to thank anonymous reviewers for high-quality curation of data. The effectiveness their helpful feedback, and ACL 2024 and ACL of M3-Embedding is empirically verified, where Rolling Review organizers for their efforts. This it leads to superior performances on multi-lingual research is supported by National Science and Tech- retrieval, cross-lingual retrieval, and multi-lingual nology Major Project (2023ZD0121504). long-document retrieval tasks. Limitations References First of all, while our proposed M3-Embedding Luiz Bonifacio, Vitor Jeronymo, Hugo Queiroz model achieves state-of-the-art performance on Abonizio, Israel Campiotti, Marzieh Fadaee, Roberto Lotufo, and Rodrigo Nogueira. 2021. mmarco: A popular multi-lingual and cross-lingual bench- marks such

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
