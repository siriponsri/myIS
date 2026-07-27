# DAPFAM — PDF Extraction & Structured Review (Read-Only Audit)

**Test type:** Read-only PDF extraction + structured review
**Extraction tool:** `markdownify` MCP server (`pdf-to-markdown`)
**Source PDF:** `dapfam.pdf` (working-directory local file — NOT modified)
**Date:** 2026-07-23
**Coverage read:** 1,697 / 1,697 lines (100%) of the extracted markdown.
Lines 0–1375 = main body (title → Conclusion + References); lines 1376–1697 = Appendix run matrix (Tables 23–26). No new narrative content in the appendix.

> **Extraction caveat:** All numeric values below are transcribed from an automated PDF→markdown
> conversion that introduced table-formatting artifacts (stray pipe characters, split cells).
> See the Reviewer Correction section — values must be cross-checked against the original PDF
> before any downstream publication or citation.

---

## 1. Title

**DAPFAM: A Domain-Aware Family-level Dataset to benchmark cross-domain patent retrieval**
Iliass Ayaou, Denis Cavallucci, Hicham Chibane — INSA Strasbourg, ICUBE Laboratory, Strasbourg, France.
Preprint submitted to Elsevier, 12 September 2025. arXiv:2506.22141 (v2).

## 2. Research question

How well do retrieval systems optimized for in-domain matching cope with **cross-domain**
(out-of-domain) patent prior-art search, and which design choices — retrieval granularity,
query/corpus field representation, passage length, aggregation strategy, and hybrid fusion —
most reduce the out-of-domain performance gap at the patent-family level?

Underlying motivation: existing benchmarks lack explicit domain partitions, preventing
systematic measurement of cross-domain retrieval difficulty.

## 3. Dataset

| Item | Value |
|------|-------|
| Source | Lens.org (JSONL bulk download) |
| Query families | 1,247 (balanced ~10 per IPC3 domain) |
| Target families | 45,336 |
| Evaluation records | 49,869 (~20 positives + ~20 negatives per query) |
| Language | English only |
| Temporal | Query earliest-claim date ≥ 2000; targets span 1964–2023 |
| Query inclusion threshold | ≥ 100 combined forward + backward citations |
| Text fields | title, abstract, claims, description (merged at family level) |
| Domain label | IPC3 overlap: IN-domain = ≥1 shared IPC3 code; OUT-domain = none shared |
| OUT proportion | ~26.08% of relevant pairs (avg 5.7381 per query); IN ~73.92% (avg 16.2169) |
| Jurisdictions | US 77.71%, JP 8.90%, KR 2.41%, DE 1.92%, EP 1.84%, GB 1.68%, CN 1.20%, others |
| Text length | Query mean ~20,448 tokens; target mean ~11,090 tokens |
| Availability | HuggingFace (URL rendered as "this repository" — link not resolved in extraction) |
| Construction | Three-step medallion architecture (bronze → silver → gold) |

## 4. Method

- **Design:** 249 unique controlled experimental configurations (Cartesian product of design factors, deduplicated).
- **Backends:**
  - Lexical: BM25 (`bm25s`; k₁=1.2, b=0.75, library defaults).
  - Dense: single multilingual encoder `Snowflake/snowflake-arctic-embed-m-v2.0`, int8-quantized.
- **Granularity:** document-level vs. passage-level (token windows p ∈ {64, 128, 256, 512, 1024, 2048, 4096, 8192}).
- **Query representation:** Title (T), T+A, T+A+C, Keywords (K).
- **Corpus representation:** Full Text, T+A, T+A+C, Description.
- **Passage aggregation:** maxP, avg_top3 (N=3), avgP, sumP.
- **Hybrid fusion:** Reciprocal Rank Fusion (RRF); K grid-searched over {10, 30, 60, 100} on the ALL subset → K=30 (passage-capable), K=60 (document-only).
- **Evaluation subsets:** ALL / IN / OUT (disjoint), rank cutoff k=100.
- **Hardware:** 24-core CPU, RTX 4090, 60 GB RAM.

## 5. Primary metrics

- **NDCG@100** (primary) — normalized discounted cumulative gain at rank 100.
- **Recall@100** (secondary) — fraction of relevant families retrieved within the top 100.
- Both macro-averaged over queries within each subset (ALL / IN / OUT).

## 6. Main results

Best configuration per method (Table 15 + RRF Tables 18–21). **Numbers transcribed from PDF — see verification warnings.**

| Method | NDCG ALL | NDCG IN | NDCG OUT | R@100 ALL | R@100 IN | R@100 OUT |
|--------|:--------:|:-------:|:--------:|:---------:|:--------:|:---------:|
| BM25-document | 0.2728 | 0.3032 | 0.0525 | 0.3278 | 0.3949 | 0.1368 |
| BM25-passage | 0.2929 | 0.3275 | 0.0589 | 0.3468 | 0.4175 | 0.1521 |
| Dense-document | 0.3055 | 0.3477 | 0.0509 | 0.3627 | 0.4437 | 0.1332 |
| Dense-passage | 0.3381 | 0.3839 | 0.0592 | 0.4072 | 0.4973 | 0.1538 |
| Hybrid RRF (K=30, passage) | 0.3475 | 0.3913 | 0.0625 | 0.4171 | 0.5062 | 0.1653 |
| Hybrid RRF (K=60, doc-only) | 0.3324 | 0.3737 | 0.0586 | 0.4020 | 0.4887 | 0.1600 |

**OUT/ALL relative retention (Table 22):** BM25-passage 0.201 · Dense-passage 0.174 · Hybrid K=30 0.180 · BM25-doc 0.192 · Dense-doc 0.158 · Hybrid-doc K=60 0.176.

Key findings:
1. **Severe domain gap (~5×):** OUT NDCG@100 drops to roughly 15–20% of IN across all methods.
2. **Dense loses its edge at OUT:** dense vs BM25 differ by only ~0.0003 NDCG on OUT (vs ~0.0564 on IN).
3. **BM25 is relatively more robust** to domain shift than dense (retention 20.1% vs 17.5%).
4. **Passage-level > document-level** consistently (+0.020–0.036 NDCG@100).
5. **Best query representation:** Title+Abstract+Claims (T+A+C) across all subsets.
6. **Optimal passage length:** 1024–2048 tokens (dense); 4096+ tokens (BM25).
7. **Best aggregation:** avg_top3 for dense IN; maxP for dense OUT and for BM25 everywhere.
8. **Document-only RRF (K=60)** gives the best effectiveness–efficiency trade-off: +0.0269 NDCG@100 on ALL vs best single doc method, with no passage-indexing overhead (~3× the passage-level RRF gain of +0.0094).

## 7. Limitations (as stated by the authors)

- English-language families from Lens.org → jurisdictional/linguistic bias (US-dominant).
- IPC3-based domain partitioning is one scheme among several; CPC or text-derived clusters could shift domain boundaries.
- Citation-based relevance labels are examiner proxies; they do not capture all technical relatedness or legal invalidity sufficiency.
- A single fixed encoder was used to isolate design choices → no model-specific insights.
- Consumer-hardware setting (24-core CPU + RTX 4090) may not reflect enterprise-scale deployments.

## 8. Relevance to Track C, R, S

> The DAPFAM paper does **not** itself name "Track C", "Track R", or "Track S". The mapping
> below is inferred from IS1 project context retrieved from the Experience Brain store and is
> interpretive, not asserted by the source.

- **Track C — Candidate generation / exposure:** DAPFAM is the core benchmark; Recall@100 measures candidate exposure and the OUT gap appears at the retrieval (candidate) stage. Best candidate strategy observed: dense-passage + RRF hybrid.
- **Track R — Reranking:** DAPFAM supplies the candidate sets a reranker would operate on. RRF's OUT gain is small (+0.0036 NDCG). Paper D used DAPFAM to test instruction-aware reranking (GEPA) → recorded OUTCOME-BOUNDARY. Fixed-pool reranking cannot recover families absent from the pool.
- **Track S:** No mapping found in either the DAPFAM paper or the Experience Brain records; cannot be substantiated.

## 9. Pages / sections requiring later verification

| Item | Reason |
|------|--------|
| Figures 2–10 (pp. 13–26) | Graphical; extraction captured captions only, not plotted values. |
| Table 15 footnote | "For the IN subset, the dense–passage best uses avg_top3 at p=1024; the ALL row shows the method's ALL-best setting" — confirm consistency with Appendix Table 26 (line 1640: T+A+C p1024 avg_topN NDCG ALL=0.3381, IN=0.3839 appears consistent). |
| HuggingFace dataset URL | Section 1.6 renders as "this repository"; hyperlink not resolved in extraction — open original PDF. |
| Dense encoder model card | `Snowflake/snowflake-arctic-embed-m-v2.0` — verify context length and training corpus. |
| Appendix Tables 23–26 (pp. 32–35, lines 1376–1697) | Read structurally, but PDF→markdown introduced formatting artifacts (stray pipes, merged cells). Cross-check any cited value against the source. |
| BM25 avg_topN anomaly | BM25-passage avg_topN NDCG at p64 ≈ 0.0222 (vs maxP 0.2746) is unexplained in text — confirm whether implementation artifact or genuine. |

---

## 10. Reviewer Correction — REQUIRED CAVEATS

> **This section is a reviewer-added correction layer. It qualifies the interpretations above
> and takes precedence over any stronger causal reading elsewhere in this document.**

1. **Gap ≠ pre-reranking causation.** DAPFAM demonstrates a severe OUT-domain retrieval gap and low OUT Recall@100, but it does **not** by itself causally prove that the *entire* gap occurs *before* reranking. The evidence establishes that candidate-stage performance is weak on OUT; it does not decompose how much of the total gap is attributable to candidate exposure versus ordering.

2. **Recall@K is the candidate-exposure metric for Track C.** For a candidate-exposure interpretation (Track C), **Recall@K is the primary metric.** NDCG@100 also encodes ordering effects and therefore conflates exposure with rank quality — it should not be read as a pure exposure measure.

3. **RRF is not a pure fixed-pool Track R experiment.** Reciprocal Rank Fusion combines two rankers and can change **both candidate membership and ordering** of the fused top-K. It must **not** be treated as a clean fixed-pool reranking (Track R) experiment, because the fused pool is not identical to either component's pool.

4. **No evidence for Track S / SkillOpt.** DAPFAM provides **no direct evidence** that Track S or any SkillOpt / prompt-optimization approach will improve performance. Any such expectation is a hypothesis, not a result supported by this paper.

5. **Numbers are provisional.** All numerical values extracted from the PDF tables (Sections 6, 9, and elsewhere) were transcribed from an automated conversion with known formatting artifacts and **must be cross-checked against the original PDF before publication or citation.**

---

*Read-only audit. The original `dapfam.pdf`, the Experience Brain store, and the thaipha-lex repository were not modified.*
