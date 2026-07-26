---
unique_id: U007
priority_tier: A
sha256: 210989901f720903067f41ad4b7d3c15c3467a2067076ccf65b422dab995dfe6
canonical_path: research/ref-paper/is1/pdfs/07_copate_a_novel_contrastive_learning_framework_2022.pdf
size_bytes: 1644437
title: "CoPatE: A Novel Contrastive Learning Framework for Patent Embeddings"
authors: "Huahang Li; Shuangyin Li; Yuncheng Jiang; Gansen Zhao"
year: 2022
venue: "CIKM '22 — 31st ACM International Conference on Information and Knowledge Management, Atlanta, GA"
doi: "10.1145/3511808.3557270"
arxiv: null
extraction_cache: source-packet/03-priority-papers/extraction-cache/U007.md
experience_brain_match: no
recommended_ingestion_action: ingest_new
digest_status: completed
digest_prepared: 2026-07-24
pass_type: "Unique-PDF digestion Batch 1 (token-efficient two-stage protocol)"
authority: "External Knowledge (not Grounded Experience, not Paper D evidence)"
---

# U007: CoPatE — A Contrastive Learning Framework for Patent Embeddings

**Unique ID:** U007 · **Priority tier:** A · **SHA-256:** `21098990…b995dfe6`
**Canonical path:** `research/ref-paper/is1/pdfs/07_copate_a_novel_contrastive_learning_framework_2022.pdf`

## Bibliographic Identity

- **Title:** CoPatE: A Novel Contrastive Learning Framework for Patent Embeddings
- **Authors:** Huahang Li, Shuangyin Li (corresponding), Yuncheng Jiang, Gansen Zhao — School of Computer Science, South China Normal University, Guangzhou, China
- **Year:** 2022 · **Venue:** CIKM '22 (ACM CIKM, Atlanta) · **DOI:** 10.1145/3511808.3557270

## Research Problem

Traditional patent search relies on keyword-based Boolean queries requiring complex expressions, giving poor performance and heavy manual post-filtering. CoPatE aims to learn high-quality **patent embeddings** that capture high-level semantics of large-scale patents for two downstream tasks — **patent retrieval** (prior-art comprehensiveness) and **patent classification** (CPC indexing). Two challenges are targeted: (1) patent claims are very long → applying BERT-style encoders directly incurs O(n²) cost and memory; (2) patent structure (tags/metadata) is under-used by generic NLP embeddings.

## Method

A contrastive-learning framework with two novel modules on top of a BERT-base encoder:
1. **Patent Semantic Compression module** — learns/selects the *informative claims* (exploiting the claim tree hierarchy, where claim 1 is the backbone) to reduce sequence length and computational complexity before encoding.
2. **Tags Auxiliary Learning module** — injects structured patent metadata (applicant, CPC/IPC class, filing date, and official category descriptions used as tags) to enrich semantics via joint text+tag embedding.
3. **Supervised contrastive loss** — a "Rater" model constructs positive/negative sample pairs; the supervised contrastive objective pulls same-class patents together and pushes negatives apart, tuned with temperature τ=0.1 and threshold hyper-params (tup=0.2, tdown=−0.05, K=3).
- Training: BERT-base (110M, 12-layer, 768-hidden), AdamW, lr 1e-4 (warmup 10% then linear decay), 5 epochs, batch 32, on dual Tesla A40 (96GB total). Embedding dimension 200 (fast retrieval).

## Dataset and Evaluation Setting

- **Training:** "New USPTO-2M" — **2,040,320 USPTO patents (2013–2020)** (distinguished from the older USPTO-2M 2006–2015).
- **Test:** "2021-A" — 5,000 patents randomly sampled from 298,559 patents filed in 2021.
- **Retrieval task:** query = title + abstract sentences (avg ~30 tokens); relevant = patents sharing the **CPC subclass**; metrics **Recall@{100,200,500}, MAP@100, MRR@100**, plus query latency.
- **Classification task:** CPC subclass level, **664 categories**; Micro/Macro Precision-Recall-F1; official USPTO category descriptions serve as tags.

## Baselines

BM25 (Boolean/lexical), Word2vec (Skip-gram & CBOW), FastText, Doc2vec (PV-DM & PV-DBOW), BERT, PatentBERT (first-claim CPC fine-tuning), Patent2vec (multi-view graph). Embedding baselines implemented via Gensim.

## Main Findings

1. **Retrieval:** CoPatE outperforms all baselines across Recall@100/200/500; reaches **50.4% Recall@100**, a **+17.7% relative increase over the second-best method** (abstract headline), and **+14.2% on MAP@100** (results text).
2. **Classification:** **64.5% Micro-F1** at CPC subclass level.
3. BM25 remains the strongest *traditional* baseline; among embedding baselines, Skip-gram Word2vec variants beat Doc2vec.
4. **Efficiency:** 200-dim embeddings give low query latency — faster than most traditional/deep approaches while more accurate; semantic compression addresses the O(n²) claim-length problem.
5. Visualization confirms learned embeddings cluster by technological category.

## Limitations

1. **CPC-subclass co-membership as relevance** — retrieval "relevance" = same CPC subclass, a *classification proxy*, not citation-based prior-art ground truth (unlike DAPFAM's citation qrels). Recall@100 here measures category recall, not prior-art recall.
2. Uses title+abstract as query and compressed claims for documents — full description not used.
3. Single-jurisdiction (USPTO), document-level (not family-level), English only.
4. Many hyper-parameters (tup/tdown/K/τ/K1-3) tuned on the same USPTO distribution; transfer unverified.
5. Future work: incorporate other unstructured texts (description) and richer structure.

## Track C Relevance (candidate-exposure headroom — proposed, NOT AUTHORIZED)

**High.** CoPatE is a **dense candidate-generation** model reporting exactly the exposure metrics Track C targets (Recall@100/200/500). Its contrastive claim+tag embedding is a concrete instance of KNO-20DDBF1D30A0's H1 (semantic channel for candidate exposure) and H2 (structure/tag-aware representation). The semantic-compression-of-claims idea aligns with claim-element chunking discussed in the IS1 gap report (KNO-3D43C4514725). Caveat: its Recall@100 is CPC-category recall, not citation-based — not directly comparable to DAPFAM OUT Recall@100 ≈0.1655.

## Track R Relevance (fixed-pool ranking headroom — proposed, NOT AUTHORIZED)

**Low–moderate.** CoPatE produces first-stage embeddings/ranking, not a reranker over a frozen top-K, and does no instruction optimization. It defines candidate pools upstream of Paper D's reranking surface rather than testing that surface.

## Track S Relevance (SkillOpt / prompt evolution — revision-stage, EXECUTION CLOSED)

**None.** No prompts or instruction optimization; the "supervised contrastive" learning is model training, not prompt evolution.

## Relationship to Papers A–D

- **Closest-prior-art candidate in the patent-embedding lineage**, alongside PatentSBERTa (U005). CoPatE is the kind of dense encoder that builds the candidate pools DAPFAM (U011) / PatenTEB (U012) benchmark and that Paper D reranks. Cite as external embedding-method prior art.
- **Different relevance definition and dataset from Paper D:** CoPatE = CPC-subclass retrieval on USPTO 2013–2021, document-level; Paper D = citation-based family-level cross-domain DAPFAM reranking. No metric cross-comparison.
- **Not prompt-optimization** — orthogonal to Papers A/B/C's GEPA/query-rewriting theses; never cite as Paper A–D evidence.

## Verification Warnings

1. **+17.7% Recall@100 is *relative* to the second-best method**, not an absolute point gain; absolute CoPatE Recall@100 = 50.4%.
2. **Relevance = same CPC subclass**, a category proxy — do NOT equate with prior-art/citation Recall or DAPFAM OUT Recall@100.
3. **MAP gain stated two ways:** abstract emphasizes Recall@100 +17.7%; results text says +14.2% MAP@100 vs second-best — cite each to its correct metric.
4. Filename/manifest label year is 2022 (CIKM '22 confirmed on slide, DOI 10.1145/3511808.3557270).
5. Numeric Table 1 columns (latency, Recall@k, MAP, MRR) are interleaved/stacked in the PDF→text cache — only prose-quoted values (50.4%, +17.7%, +14.2%, 64.5%) are reliable; consult PDF Table 1 for the full grid.

## Experience Brain Cross-Check (READ-ONLY)

- **experience_brain_match:** no (no CoPatE-specific record)
- **matched_knowledge_ids:** KNO-20DDBF1D30A0 (candidate-exposure synthesis — H1/H2 alignment), KNO-3D43C4514725 (IS1 gap report — claim-element chunking), KNO-528A290EA2E4 (PatenTEB), KNO-5449A7642CF9 (IS1 literature matrix).
- **memory_conflict:** none
- **query mode:** read-only; no record created or modified.
- **recommended_ingestion_action:** ingest_new (medium priority; a contrastive patent-embedding baseline relevant to Track-C candidate generation).

## Status

✅ **completed** — Token-efficient two-stage protocol: extracted once to `extraction-cache/U007.md` (10 pages, 8,680 words); targeted reads of abstract, intro §1, preliminaries §2, method modules, experiments §4.1–4.2, results (Table 1 prose), conclusion §5. Full markdown not loaded wholesale.

---
*Digest prepared 2026-07-24. Source repository unmodified. Experience Brain queried read-only.*
