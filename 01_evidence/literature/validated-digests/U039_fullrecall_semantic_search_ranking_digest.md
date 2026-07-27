---
paper_id: U039
title: "FullRecall: A Semantic Search-Based Ranking Approach for Maximizing Recall in Patent Retrieval"
authors: "Amna Ali, Liyanage C. De Silva, Pg Emeroylariffion Abas"
year: 2025
venue: "Information Processing and Management (Elsevier)"
affiliation: "Faculty of Integrated Technologies / School of Digital Science, Universiti Brunei Darussalam"
pdf_sha256: "1a7441812abe43487ecc4b5995dc998c4d97aa3ed39ea9726e2dc263ef60b8c7"
eb_status: "ingest_new"
tier: "B"
extraction_cache: "extraction-cache/U039.md"
digest_created: "2026-07-25"
schema_version: "PDF_DIGEST_SCHEMA_V1"
---

# U039: FullRecall — Semantic Search-Based Ranking for Maximizing Recall in Patent Retrieval

## Bibliographic Identity
Ali, De Silva & Abas 2025, Information Processing and Management, Universiti Brunei Darussalam. SHA-256 verified against manifest (exact match).

## Classification
**Tier B.** A genuine prior-art retrieval task with a real recall metric (100% recall claimed across 5 test patents) compared against two named baselines (HRR2, ReQ-ReC) using examiner-citation ground truth from MineSoft PatBase — a real retrieval evaluation, not classification. However, the evaluation is narrow: only **5 query patents total** (no standard benchmark like CLEF-IP/DAPFAM), no Precision/MAP/NDCG reported (only binary recall — did all examiner citations appear anywhere in a large retrieved set), and the baseline comparison methodology is unusual (ReQ-ReC's top-n cutoff was manually expanded per-query to match FullRecall's retrieved-set size, e.g. n=1660, rather than using each method's own natural stopping point) — a methodological choice that could favor the proposed method. This combination (real retrieval task/metric, narrow n=5 evaluation, no ranking-quality metric beyond recall, comparison protocol favoring the proposed system) places it at Tier B, consistent with other narrow-scope retrieval papers in this batch.

## Research Problem / Method
Motivated by patent retrieval's asymmetric cost structure: missing a single relevant prior-art document (a false negative) can invalidate a granted patent or cause litigation, so recall must be prioritized over precision — unlike general-purpose IR. Proposes **FullRecall**, a 3-phase pipeline: **Phase 1 (feature extraction)** — aggregate IPC/CPC classification-code descriptions for the query patent's assigned IPC codes into a knowledge base D; extract bi/tri-gram key phrases via YAKE (unsupervised, no reference corpus needed); score sentences in the query patent by cosine similarity to these key phrases (384-dim embeddings) to select the most technically salient sentences; extract noun phrases from those sentences (noun phrases carry >90% of patent technical terminology per cited prior work); cluster noun phrases via HDBSCAN; rank phrases using a composite score combining a **connectivity score** (weighted Euclidean distance to cluster centroid + global centroid, Eq. 18-20) and a **uniqueness score** (min cosine similarity to same-cluster and cross-cluster phrases, Eq. 21-23), further supplemented by graph centrality measures (PageRank, Degree, Betweenness) on a phrase-similarity graph. **Phase 2 (intermediary)**: human-in-the-loop refinement of the ranked-phrase-derived search query. **Phase 3 (full recall)**: execute the refined query against an IPC-filtered document subset (simulating a realistic corpus scope), apply a weighted semantic-similarity scoring between retrieved documents and the Phase-1 ranked phrases, and rank the final result set — targeting 100% recall while keeping the returned set small enough to review.

## Main Findings
Evaluated on 5 real granted US patents (P1_UO through P5_UO, with 10, 4, 6, 5, and 7 examiner-cited prior-art documents respectively per Table 2, drawn from diverse IPC domains: telecom/H04L, EV battery/B60L, wind-turbine/mixed mechanical, biochemistry/C12Q, and RF communications). FullRecall achieved **100% recall in all 5 test cases** — every examiner-cited document was present in its retrieved set (though retrieved-set sizes were large, e.g. 1,660 documents for P1_UO). Baselines: **HRR2** recall was 10%, 25%, 33.3%, 0%, 14.29% across the 5 cases (retrieved far fewer documents, e.g. 140 for P1_UO, but captured only 1/10 target citations); **ReQ-ReC** recall was 50%, 25%, 0%, 0%, 0% (despite its retrieval cutoff n being deliberately expanded to match FullRecall's retrieved-set size for a "fair" comparison, it still failed to retrieve most target citations in 3 of 5 cases).

## Limitations
Not extensively self-acknowledged in a dedicated limitations section (none found in Sections 4-5); acknowledged implicitly: human-in-the-loop intermediary phase requires domain expertise, limiting full automation. Additional concerns (from digest analysis): (1) **extremely small evaluation set** — n=5 query patents is not a statistically meaningful sample and no significance testing is reported; (2) **no precision/MAP/NDCG reported** — 100% recall achieved via retrieving very large document sets (up to 1,660+ documents per query) says nothing about ranking quality or reviewer burden, which the paper's own motivation section frames as a "balancing precision and recall" goal not actually demonstrated quantitatively; (3) **baseline comparison protocol is asymmetric** — ReQ-ReC's cutoff n was manually extended per-query specifically to match FullRecall's retrieved-set size rather than run under each baseline's own natural operating point, which could disadvantage or advantage either method depending on how each degrades past its intended cutoff; (4) ground truth relies solely on examiner citations (a known incomplete proxy for true prior art, not exhaustively verified); (5) no publicly available corpus or reproducible benchmark — the "IPC-filtered subset simulating the actual database" is not described with enough specificity (corpus size, source) to assess whether 100% recall was achieved against a genuinely large-scale collection or a curated smaller pool.

## Track C/R/S Relevance (proposed, NOT AUTHORIZED / execution-closed)
Track C: MODERATE — the IPC-description-driven key-phrase extraction (YAKE + HDBSCAN clustering + connectivity/uniqueness graph-centrality ranking) is a distinctive query-formulation technique for candidate generation, directly relevant as an alternative to embedding-only or citation-based query construction methods surveyed elsewhere in this literature set (e.g., U022's summarization-based query formulation). Track R: LOW — the final "weighted semantic similarity" reranking of retrieved documents is a simple scoring step, not a dedicated cross-encoder or learned reranker. Track S: NOT RELEVANT.

## Relationship to Papers A–D
No direct connection. FullRecall's binary recall-only evaluation on 5 individual patents is not comparable to DAPFAM/Papers A-D's family-level Recall@100/NDCG@100 framework (different scale, different relevance definition, no cross-comparison made per schema §15).

## Verification Warnings
Non-blocking for extraction fidelity (Tables 2-4 and the HRR2/ReQ-ReC comparison narrative extracted cleanly, no OCR/grid-damage), but **the baseline-comparison methodology itself warrants caution** when citing this paper's headline "100% vs. 10-50%" recall superiority claim — the asymmetric protocol (expanding ReQ-ReC's cutoff specifically to match FullRecall's retrieved-set size) and the very small n=5 evaluation mean this result should not be treated as a rigorously controlled comparison without independent verification.

## EB Cross-Check
Query: "FullRecall semantic search-based ranking approach maximizing recall patent retrieval Ali De Silva Abas Universiti Brunei Darussalam" (narrow SHA/title-scoped check; no DOI cited in extracted text). Result: NO_MATCH (returned only unrelated IS1 literature-matrix/DAPFAM/PatenTEB/plan records; no record for this SHA or title). → **ingest_new**.

---
**Digest Author:** Batch 2A Processing Agent · **Batch ID:** BATCH_2A · **Processing Status:** ✅ COMPLETED · **Content Coverage:** Introduction, full Methodology (§2), Results (§3, Tables 2-4), Performance Comparison (§4), Conclusion (§5) read directly (~900 of 1612 extraction lines); detailed mathematical formulation of scoring equations (§2, Eq. 1-26) confirmed present but not all individually re-derived, as they do not affect headline findings.

**END OF DIGEST**
