---
unique_id: U008
priority_tier: A
sha256: af7db61252ecccff373e728c84e406178183d80d3a3c1837e754cf7a9927ca16
canonical_path: research/ref-paper/is1/pdfs/08_searchformer_semantic_patent_embeddings_by_siamese_2023.pdf
size_bytes: null
title: "SEARCHFORMER: Semantic patent embeddings by siamese transformers for prior art search"
authors: "Konrad Vowinckel; Volker D. Hähnke"
year: 2023
venue: "World Patent Information 73 (2023) 102192 (Elsevier)"
doi: "10.1016/j.wpi.2023.102192"
arxiv: null
extraction_cache: source-packet/03-priority-papers/extraction-cache/U008.md
experience_brain_match: no
recommended_ingestion_action: ingest_new
digest_status: completed
digest_prepared: 2026-07-24
pass_type: "Unique-PDF digestion Batch 1 (token-efficient two-stage protocol)"
authority: "External Knowledge (not Grounded Experience, not Paper D evidence)"
---

# U008: SEARCHFORMER — Semantic Patent Embeddings by Siamese Transformers

**Unique ID:** U008 · **Priority tier:** A · **SHA-256:** `af7db612…9927ca16`
**Canonical path:** `research/ref-paper/is1/pdfs/08_searchformer_semantic_patent_embeddings_by_siamese_2023.pdf`

## Bibliographic Identity

- **Title:** SEARCHFORMER: Semantic patent embeddings by siamese transformers for prior art search
- **Authors:** Konrad Vowinckel, Volker D. Hähnke (corresponding) — European Patent Office, Rijswijk, NL
- **Year:** 2023 · **Venue:** World Patent Information 73 (2023) 102192, Elsevier · **DOI:** 10.1016/j.wpi.2023.102192

## Research Problem

Patent examiners must find prior art that prejudices novelty/inventive step of an application. The paper asks whether a **patent-domain fine-tuned siamese/SentenceTransformer** can produce dense embeddings whose vector similarity ranks relevant prior art earlier than the EPO's incumbent BM25-based key-term system and than off-the-shelf semantic-retrieval models.

## Method

- **Base model:** GP-BERT (BERT pre-trained on complete English patents), max sequence 512, **1024-dim** embeddings. Fine-tuned into SEARCHFORMER via SentenceTransformer **triplet loss**.
- **Triplets:** anchor sₐ = **first claim** of the application; positive sₚ = **X-cited** text (novelty/inventive-step-prejudicing); negative sₙ = **A-cited** or non-cited text. Anchors/positives/negatives may be paragraphs.
- **Negative sampling — four difficulty levels:** random (30.8%), same CPC subclass (30.8%), same document (30.2%), A-cited hard negatives (8.2%).
- **Data:** parsed EP search reports, applications published **2007–2016 (train), 2017 (eval)**. **11,276,651 unique triplets** from **177,061 applications** → 9,883,936 train / 1,392,715 eval. Citation targets: 77.1% description paragraphs, 15.3% claims, 7.6% abstracts.
- **Training:** 8× A100 40 GB, batch 48, lr **1e-5** (default 2e-5 dropped accuracy), 2 epochs, 148 h.
- **Ranking:** application (first claim) vs PPA documents by vector distance; six distance measures tried; description paragraphs give multiple vectors aggregated (sliding-window / mean-min). **Reciprocal Rank Fusion (RRF)** combines multiple rankings.

## Dataset and Evaluation Setting

- **Evaluation collection:** 2,014 pairs of patent application + related potential prior art (PPA) documents.
- **Primary metric:** **RFR — Rank of the First Relevant** result (relevant = X-type citation), a cut-off-free proxy for examiner "stepping-stone" behavior; plus **success@k** curves. Statistical testing by **one-sided paired t-tests with Bonferroni correction (n = 74 comparisons, α = 0.01)**.
- Baselines: (i) optimized automatically-built queries + **BM25**; (ii) SOTA language models incl. BERT-cased, GP-BERT (un-fine-tuned), and general-domain SentenceTransformers.

## Baselines & Main Findings (lower RFR = better)

- Random ranking RFR ≈ **167.84**; **BM25 baseline RFR ≈ 72.91** (first claim) / 72.95 (description).
- **Un-fine-tuned** models worse than BM25: BERT-cased best RFR **112.73**, GP-BERT best RFR **80.98** (both standardized-Euclidean).
- **SEARCHFORMER, first claim as PPA text:** best RFR **58.66** (standardized Euclidean; cosine 59.20) — beats BM25.
- **SEARCHFORMER, description paragraphs:** best RFR **52.83** (cosine, sliding-window size 5) — best overall; paragraph-level > first-claim.
- Improvements over BM25, the base model, and general ST models are **statistically significant at α = 0.01**.
- **X-vs-A discrimination:** 53.85% accuracy, comparable to PatentMatch (52%) → A-citations alone are too-hard negatives.
- **RRF data fusion** across methods is effective, efficient, and nearly independent of k; distance-function choice is "of almost no consequence."

## Limitations

1. **1024-dim vectors** → large memory footprint, a production deployment challenge (authors are investigating dimensionality reduction + knowledge distillation).
2. Paragraph-level retrieval beats single-vector but multiplies vector count **>100×**.
3. **Single jurisdiction (EPO), English only, document-level** (not patent-family-level).
4. Application represented only by its **first claim** — "not ideal"; best PPA text selection remains an open question.
5. RFR is a first-relevant proxy (no recall@k / MAP reported); comparability to cut-off metrics is indirect.

## Track C Relevance (candidate-exposure headroom — proposed, NOT AUTHORIZED)

**High.** SEARCHFORMER is a concrete **dense semantic candidate-generation channel** — exactly the "dense semantic channel" in KNO-20DDBF1D30A0's **H1** (multi-view union) — and its paragraph-level retrieval + RRF fusion directly instances **H3** (passage retrieval + prespecified fusion). Its four-level hard-negative curriculum and "random-too-easy / A-cited-alone-too-hard" finding are actionable design guidance for a Track-C dense retriever. Citation-based (X-citation) relevance is closer to DAPFAM's ground truth than CoPatE/PatentSBERTa's CPC-proxy relevance.

## Track R Relevance (fixed-pool ranking headroom — proposed, NOT AUTHORIZED)

**Low–moderate.** SEARCHFORMER produces first-stage rankings and RRF fusion, not an instruction-optimized reranker over a frozen top-K. It defines/expands candidate pools upstream of Paper D's reranking surface; RRF fusion is a fusion-stage, not the reranking channel Paper D tested.

## Track S Relevance (SkillOpt / prompt evolution — revision-stage, EXECUTION CLOSED)

**None.** No prompts or instruction optimization; all learning is embedding fine-tuning.

## Relationship to Papers A–D

- **Closest prior art on the dense-retrieval / passage-fusion axis**, alongside PatentSBERTa (U005) and CoPatE (U007). Cite as embedding-based first-stage prior art and as the source of the RRF-fusion and hard-negative-curriculum precedents relevant to Track C.
- **Relevance definition:** citation-based (X-citations) like DAPFAM (U011), but **document-level, single-jurisdiction, RFR metric** — no direct numeric comparison to DAPFAM family-level Recall@100 or to Paper D reranking metrics.
- **Not prompt-optimization / not reranking** — orthogonal to Papers A/B/C's GEPA/query-rewriting theses; never cite as Paper A–D outcome evidence.

## Verification Warnings

1. **RFR is "lower is better"** and is *not* Recall@k/MAP/MRR — do NOT compare RFR numbers against DAPFAM/PatenTEB recall figures.
2. Best RFR values (52.83 description / 58.66 first claim vs BM25 72.91) are from **Tables 7–8**; the PDF→text cache stacks Table 7's columns vertically — prose-quoted values are reliable, but consult the PDF for the full distance×aggregation grid. ⚠️ visual-check flag.
3. Significance holds under **Bonferroni (n=74)** — strict; authors chose it deliberately over Benjamini–Hochberg.
4. X-vs-A accuracy 53.85% is a *citation-type discrimination* figure, not a retrieval score.
5. Manifest `size_bytes` left `null` (not captured this pass); SHA verified `af7db612…`.

## Experience Brain Cross-Check (READ-ONLY)

- **experience_brain_match:** no (no SEARCHFORMER-specific record)
- **matched_knowledge_ids:** KNO-20DDBF1D30A0 (candidate-exposure synthesis — H1/H3), KNO-528A290EA2E4 (PatenTEB), KNO-384DFF3E3AC0 (DAPFAM).
- **memory_conflict:** none
- **query mode:** read-only; no record created or modified.
- **recommended_ingestion_action:** ingest_new (medium-high priority; dense siamese retriever + RRF fusion precedent for Track-C candidate generation).

## Status

✅ **completed** — Token-efficient two-stage protocol: extracted once to `extraction-cache/U008.md` (16 pages, 15,196 words); targeted reads of abstract, §3.1–3.3 (base model, data, training), §4.2 metrics, §4.3 baselines, §5.2 results, §6 conclusion. Full markdown not loaded wholesale.

---
*Digest prepared 2026-07-24. Source repository unmodified. Experience Brain queried read-only.*
