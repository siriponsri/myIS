---
paper_id: U149
title: "Benchmarking Patent Embeddings: A Multi-Task Evaluation of 22 Models Across Retrieval, Classification, and Clustering"
pdf_sha256: "07aefa5f1673e1825b696df49ff2d5c0b79c02fe579f131a850f6baf8d0458d9"
object_path: "01_evidence/A-tier/U149_benchmarking_patent_embeddings_a_multi_task_evaluation_of_22_models_acro.pdf"
legacy_primary_alias: "research/ref-paper/is1/dapfam-pdfs/04_benchmarking_patent_embeddings_a_multi_task_evaluation_of_22_models.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: "2605.24297"
arxiv_source: "pdf_front_matter"
arxiv_confidence: "medium"
page_count: 31
record_type: "paper"
tier: "A"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U149: Benchmarking Patent Embeddings: A Multi-Task Evaluation of 22 Models Across Retrieval, Classification, and Clustering

## Bibliographic Identity

- Verified title source: `rendered_first_page_text`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: 2605.24297 (source: pdf_front_matter; confidence: medium)
- Pages: 31
- Source collection: `is1-dapfam`
- Legacy primary alias: `research/ref-paper/is1/dapfam-pdfs/04_benchmarking_patent_embeddings_a_multi_task_evaluation_of_22_models.pdf`
- Identity result: `verified` (filename/title token overlap 1.00)

## Classification

**Tier A.** Direct patent retrieval/search/embedding benchmark evidence. Relevant surface: C, R.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, reranking, ranking, benchmark, patent, prior art, embedding, contrastive, agent, cross-lingual, legal, classification.

Abstract/summary section scan:

> 0.1831 Claim1 0.1813 DWPI-TA 0.1814 Mean 0.1865 sion (Equation 2, k ∈ {10, 60, 100}); Figure 3 Qwen3-8B Qwen3-4B 0.1788 0.1786 0.1871 0.1867 0.1847 0.1816 0.1789 0.1786 0.1772 0.1758 0.1781 0.1792 0.1808 0.1801 plots the linear-interpolation curve, with stars mark- Octen-8B 0.1744 0.1805 0.1804 0.1745 0.1720 0.1723 0.1757 Nemotron-1B 0.1686 0.1808 0.1767 0.1686 0.1648 0.1667 0.1711 ing each model’s dense-only baseline. KaLM-Gemma3-12B 0.1779 0.1564 0.1733 0.1779 0.1693 0.1715 0.1710 patembed-base 0.1634 0.1665 0.1703 0.1634 0.1580 0.1588 0.1634 Qwen3-0.6B GTE-multi-base 0.1620 0.1590 0.1667 0.1540 0.1638 0.1605 0.1620 0.1589 0.1588 0.1527 0.1589 0.1564 0.1620 0.1569 Sparse-Dense Fusion Provides Consistent but Nomic-v2-MoE 0.1546 0.1568 0.1554 0.1546 0.1500 0.1492 0.1534 mE5-large 0.1518 0.1588 0.1572 0.1518 0.1500 0.1488 0.1531 Modest Gains. All five dense models benefit Jina-v3 0.1472 0.1523 0.1546 0.1473 0.1433 0.1480 0.1488 BM25 MiniLM-L6 0.1403 0.1450 0.1529 0.1467 0.1521 0.1453 0.1403 0.1450 0.1346 0.1368 0.1407 0.1418 0.1435 0.1434 from BM25 interpolation, with the optimal interpo- BGE-M3 PatentSBERTa 0.1465 0.1432 0.1323 0.1404 0.1408 0.1425 0.1465 0.1432 0.1404 0.1353 0.1395 0.1336 0.1410 0.1397 lation weight at α = 0.7 (dense-dominant) for four Stella-1.5B 0.1255 0.1528 0.1420 0.1255 0.1178 0.1109 0.1291 Conan-v1 0.1035 0.1042 0.1001 0.1035 0.0953 0.0910 0.0996 of five models. The largest absolute improvement EmbGemma-300m 0.0983 0.0881 0.0990 0.0983 0.0680 0.0781 0.0883 ColBERT models (MaxSim) is for Octen-8B (+0.0152, from 0.1805 to 0.1956), AnswerAI-ColBERT 0.1306 0.1363 0.1363 0.1306 0.1249 0.1264 0.1309 ColBERTv2 Jina-ColBERT-v2 0.1278 0.1307 0.1307 0.1230 0.1312 0.1274 0.1278 0.1304 0.1234 0.1269 0.1232 0.1237 0.1273 0.1270 while the already-strong Llama-

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
