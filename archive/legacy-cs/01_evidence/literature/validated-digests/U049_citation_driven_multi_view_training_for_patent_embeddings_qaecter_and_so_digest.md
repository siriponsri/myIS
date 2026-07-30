---
paper_id: U049
title: "Citation-Driven Multi-View Training for Patent Embeddings: QaECTER and Sophia-Bench"
pdf_sha256: "b9a6db6b10c10439cc5f5119f3e6c0e8a44f41c250d6e9125ccd3f6c00c472c3"
object_path: "01_evidence/A-tier/U049_citation_driven_multi_view_training_for_patent_embeddings_qaecter_and_so.pdf"
legacy_primary_alias: "research/ref-paper/is1/pdfs/50_citation_driven_multi_view_training_for_2026.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: "2604.22897"
arxiv_source: "acquisition_url"
arxiv_confidence: "high"
page_count: 17
record_type: "paper"
tier: "A"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U049: Citation-Driven Multi-View Training for Patent Embeddings: QaECTER and Sophia-Bench

## Bibliographic Identity

- Verified title source: `acquisition_metadata_verified_in_pdf`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: 2604.22897 (source: acquisition_url; confidence: high)
- Pages: 17
- Source collection: `is1`
- Legacy primary alias: `research/ref-paper/is1/pdfs/50_citation_driven_multi_view_training_for_2026.pdf`
- Identity result: `verified` (filename/title token overlap 1.00)

## Classification

**Tier A.** Direct patent retrieval/search/embedding benchmark evidence. Relevant surface: C, R, H/S.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, ranking, benchmark, patent, prior art, embedding, contrastive, cross-lingual, legal, classification.

Abstract/summary section scan:

> Patent retrieval underpins critical decisions in innovation, examination, and IP strategy, yet progress has been hampered by the absence of benchmarks that reflect the diversity of real- world search scenarios. We address this gap with two contributions. First, we introduce Sophia- bench, a large-scale patent retrieval benchmark comprising 10,000 queries and 75,000 corpus documents stratified across ten years, eight IPC technology sections, and twelve filing jurisdictions. Unlike prior benchmarks, Sophia-bench tests retrieval using 12 different query types-from structured patent fields to AI-generated summaries-and evaluates results against citation-based ground truth enhanced with a novel domain-relevance metric (InScope). Together, these enable systematic measurement of how well models perform across query types, technology domains, and jurisdictions. Second, we introduce QaECTER, a 344M-parameter embedding model trained on patent citation graphs and multi-view self-alignment. Despite its compact size, QaECTER establishes a new state of the art for patent retrieval. It outperforms the #1 model on the English retrieval text embedding benchmark (RTEB) [1], a model 23× larger, as well as all existing patent- specific models across every query type, IPC section, and jurisdiction on Sophia-bench, with gains of up to 7.2% average NDCG@10 over the next-best model. These results are confirmed on an independent external benchmark, where QaECTER surpasses all prior models without requiring task-specific instruction prompts. Both the benchmark and the model are designed for practical deployment in large-scale patent search systems. 1 AI Lab, Questel, Paris, France 2 Qatent, Paris, France 3 Inria, Paris, France 4 Université Paris-Saclay, Orsay, France Email addresses: ydjemmal@q

Conclusion/discussion section scan:

> We presented two complementary contributions to patent retrieval. Sophia-bench provides the first large-scale benchmark that systematically evaluates embedding models across 12 query rep- resentations, eight technology domains, multiple jurisdictions, and a decade of patent filings. By combining citation-based ground truth with the InScope domain-relevance metric, it enables fine- grained diagnosis of model strengths and failure modes that prior benchmarks could not capture. QaECTER, our 344M-parameter embedding model, establishes a new state of the art on both Sophia-bench and the independent DAPFAM benchmark. Its consistent superiority over models up to 23× larger demonstrates that domain-specific training on patent citation graphs with multi- view self-alignment can be far more effective than scaling general-purpose architectures. Critically, QaECTER achieves this without instruction prompts or task-specific prefixes, making it directly 15 deployable in production search pipelines. Our evaluation also yields several broader findings. AI-generated summaries match or exceed tradi- tional patent fields as queries, validating their use in modern search workflows. The InScope analysis reveals that even the best models struggle with fine-grained IPC subgroup matching, pointing to an important direction for future work. 16

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
