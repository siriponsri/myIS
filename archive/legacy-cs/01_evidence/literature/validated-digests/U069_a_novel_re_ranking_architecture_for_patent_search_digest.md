---
paper_id: U069
title: "A novel re-ranking architecture for patent search"
pdf_sha256: "5f627c6cf8423df37ad306c1c0de4ec4790a1a9fbf073f019c1adbaa3205ef97"
object_path: "01_evidence/A-tier/U069_a_novel_re_ranking_architecture_for_patent_search.pdf"
legacy_primary_alias: "research/ref-paper/is1/pdfs/70_a_novel_re_ranking_architecture_for_patent_search.pdf"
doi: "10.1016/j.wpi.2024.102282"
doi_source: "acquisition_url"
doi_confidence: "high"
arxiv_id: ""
arxiv_source: ""
arxiv_confidence: "not_detected"
page_count: 9
record_type: "paper"
tier: "A"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U069: A novel re-ranking architecture for patent search

## Bibliographic Identity

- Verified title source: `acquisition_metadata_verified_in_pdf`
- DOI: 10.1016/j.wpi.2024.102282 (source: acquisition_url; confidence: high)
- arXiv ID: not detected (source: not detected; confidence: not_detected)
- Pages: 9
- Source collection: `is1`
- Legacy primary alias: `research/ref-paper/is1/pdfs/70_a_novel_re_ranking_architecture_for_patent_search.pdf`
- Identity result: `verified` (filename/title token overlap 1.00)

## Classification

**Tier A.** Direct patent retrieval, ranking, or representation method. Relevant surface: C, R.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, reranking, ranking, benchmark, patent, prior art, embedding, legal, classification.

Abstract/summary section scan:

> , Description, and Claims) to simplify the higher scores to documents that contain more occurrences of the query modeling of interactions between the query document (QAbstr, QDesc, terms, particularly those that are less common in the overall collection. QClm) and each candidate document (CAbstr, CDesc, CClm). This approach effectively identifies documents that are both relevant to To keep the input length manageable for AI-based methods, we the query and contain unique information. Similarly, semantic scores restrict each section to a maximum of 500 words. If a section exceeds are calculated for each pair using the SBERT model architecture, spe­ this limit, it is further split into 500-word passages. The passage with the cifically the Bi-encoder implementation, to capture both contextual and highest average inverse document frequency (IDF) is chosen as the sequential information in the text. SBERT extends BERT’s capabilities by representative for that section. This results in a maximum representation specifically tailoring it for sentence-level similarity tasks. It utilizes a length of 1500 words for each query and candidate document (500 Siamese architecture, where two identical BERT encoders process each words each for the abstract, description, and claims). Given that AI- sentence pair, independently generating representations. The resulting based methods like BERT-based re-rankers typically have an input representations are then compared using a similarity measure, such as limit of 512 tokens per inference, this 1500-word representation should cosine similarity, to determine the semantic similarity between the adequately capture the essential information for relevance assessment. sentences. We utilize the BERT-for-patents model,1 trained by Google on Even though ou

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
