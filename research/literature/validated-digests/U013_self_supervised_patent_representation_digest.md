---
unique_id: U013
priority_tier: A
sha256: 39aacd435c9acc78a744b6e818b142e5ff76cd2ab40fedf8ac371da6891d3214
canonical_path: research/ref-paper/is1/pdfs/13_patent_representation_learning_via_self_supervision_2025.pdf
size_bytes: 65240
title: "Patent Representation Learning via Self-supervision"
authors: "You Zuo; Kim Gerdes; Éric de la Clergerie; Benoît Sagot"
year: 2025
venue: "Preprint; arXiv:2511.10657v1 [cs.CL] 3 Nov 2025; Inria / Qatent / Université Paris-Saclay"
doi: null
arxiv: "2511.10657"
extraction_cache: source-packet/03-priority-papers/extraction-cache/U013.md
experience_brain_match: no
recommended_ingestion_action: ingest_new
digest_status: completed
digest_prepared: 2026-07-24
pass_type: "Unique-PDF digestion Batch 1 (token-efficient two-stage protocol)"
authority: "External Knowledge (not Grounded Experience, not Paper D evidence)"
---

# U013: Patent Representation Learning via Self-supervision

**Unique ID:** U013 · **Priority tier:** A · **SHA-256:** `39aacd43…6891d3214`
**Canonical path:** `research/ref-paper/is1/pdfs/13_patent_representation_learning_via_self_supervision_2025.pdf`

## Bibliographic Identity

- **Title:** Patent Representation Learning via Self-supervision
- **Authors:** You Zuo, Kim Gerdes, Éric de la Clergerie, Benoît Sagot — Inria (Paris), Qatent, Université Paris-Saclay (LISN, CNRS)
- **arXiv:** 2511.10657v1, 3 Nov 2025 · code: github.com/ZoeYou/patentmapv1

## Research Problem

Can patent embeddings be learned **fully self-supervised** — without citation or IPC labels (which are brittle/incomplete) — and still match supervised baselines for prior-art retrieval and classification? The paper first identifies a patent-specific failure of SimCSE-style dropout augmentation: it yields **overly uniform embeddings that lose semantic cohesion** (over-dispersion).

## Method (verified against cache)

- **Section-based augmentation:** different sections of the *same* patent (abstract, claims, background, description) serve as complementary contrastive views — injecting natural semantic/structural diversity instead of dropout noise (lines 20–28).
- Shared dropout-based contrastive framework; variants differ only in augmentation policy (dropout-only, classical crop/shuffle/paraphrase, section-based, +IPC-match). Pooled features mapped via tanh projection head (line 280).
- Diagnostics: Alignment↓, Uniformity↓, Singular Spectrum Divergence, intra-document alignment ratio (Figs 5–6).

## Dataset and Evaluation Setting (verified against cache)

- **Prior-art retrieval:** Recall@K (K=20/50/100) averaged over **200 queries**; ranked list de-duplicated at patent level (mirrors examiner claims→full-disclosure workflow); settings include the hard **Claims→All** cross-section task (lines 566–567).
- **IPC subclass classification:** KNN (k=10) on **30k USPTO patents 2005–2009** (6k/yr), 85/15 split from **HUPD** (Suzgun et al. 2022); TA embedding, majority vote (lines 573–578).
- Baselines: dropout-only, classical augs, PaECTER (citation-trained), gte-Qwen2-7B-instruct, PatentBERT.

## Main Findings (verified against cache)

1. **Section augmentation >> dropout:** R@100 rises **56.21 → 71.22** with claims as the second view, **matching or surpassing citation-trained PaECTER (U009)** at several cutoffs (lines 606–610).
2. Dropout-only **collapses in Claims→All**, confirming near-identical positives fail to capture cross-sectional semantics.
3. Classification: section-based augmentation performs **on par with or better than gte-Qwen2-7B-instruct despite far fewer parameters / smaller dim**; +IPC-match variant best overall (expected — its signal is IPC-tied) (lines 627–635).
4. Different sections specialize for different tasks; section-augmented models retrieve a **more balanced section mix** (more summary/background beyond claims), i.e., improved cross-structure generalization (Fig 4).

## Limitations

- English-only USPTO focus; retrieval evaluated on 200 queries (modest query set); relevance/eval derived from HUPD + citation-style setups (label-proxy caveats apply); single-checkpoint reporting without early stopping. Fully self-supervised gains shown on this benchmark, not on DAPFAM's cross-domain OUT split.

## Track C Relevance (candidate-exposure — proposed, NOT AUTHORIZED)

**High.** A candidate-encoder method with a directly actionable insight for the Track-C retrieval stage: **sections-as-views** and the balanced-section retrieval effect map onto multi-view / query-representation design (KNO-20DDBF1D30A0 H1/H2). It shows a *label-free* route to embeddings competitive with citation-supervised PaECTER — attractive where citation labels are sparse (e.g., Thai pharma patents). Would need evaluation on DAPFAM OUT to substantiate cross-domain exposure claims.

## Track R Relevance (fixed-pool reranking — proposed, NOT AUTHORIZED)

**Low.** Representation-learning / bi-encoder work; no reranking contribution.

## Track S Relevance (SkillOpt — EXECUTION CLOSED)

**None.** No prompt-optimization content.

## Relationship to Papers A–D

- **Direct competitor/complement to PAECTER (U009), PatentSBERTa (U005), CoPATE (U007), SearchFormer (U008)** — all patent embedding methods; U013's distinctive claim is that *self-supervised section views* rival *citation-supervised* PaECTER, a counterpoint to the citation-informed lineage of U008/U009.
- Feeds the Track-C candidate-generation question underlying Papers A–D; the section-view idea is a concrete query/corpus-representation lever.
- Retrieval numbers are HUPD/self-defined-query numbers, **not** DAPFAM numbers — do not cross-compare absolute R@100 against U011/U012.
- Relevance labels are citation/IPC proxies, not legal novelty/infringement/FTO judgments.

## Verification Warnings

1. R@100 56.21→71.22, the 200-query retrieval protocol, and the 30k-patent HUPD KNN setup verified against cache (lines 566–635). Full Table 2 cells not transcribed — verify per-cutoff numbers against PDF before citing.
2. arXiv ID 2511.10657 read from cache line 98.
3. Figures 4–6 graphical; captions only in extraction.

## Experience Brain Cross-Check (READ-ONLY)

- **experience_brain_match:** **no** — no record carries source hash `39aacd43…`. Query returned only DAPFAM (KNO-384DFF3E3AC0), PatenTEB (KNO-528A290EA2E4), PAECTER (KNO-92F3E83D2CBF), literature matrix, and the candidate-exposure synthesis — related-topic, not this paper. Note: the IS1 literature matrix does not list this Zuo et al. 2025 paper among A1–A3, so it appears to be a **newer addition** not yet in EB.
- **memory_conflict:** none.
- **query mode:** read-only; no record created or modified.
- **recommended_ingestion_action:** **ingest_new** — not in EB; ingest as external Knowledge (planning input only, not tested evidence) and link to the U005/U007/U008/U009 embedding cluster.

## Status

✅ **completed** — Token-efficient two-stage protocol: reused pre-extracted `extraction-cache/U013.md` (20 pages, 65,240 B); head + targeted greps + one focused line-range read (560–640) for datasets and results. Full markdown not loaded wholesale.

---
*Digest prepared 2026-07-24. Source repository unmodified. Experience Brain queried read-only.*
