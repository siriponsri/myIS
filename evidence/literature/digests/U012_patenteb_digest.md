---
unique_id: U012
priority_tier: A
sha256: 528a290ea2e479ed72d377c0fb4d5e762feaf4c5a233dc62464dfc5c11358f85
canonical_path: research/ref-paper/is1/pdfs/12_patenteb_a_comprehensive_benchmark_and_model_2025.pdf
size_bytes: 107607
title: "PatenTEB: A Comprehensive Benchmark and Model Family for Patent Text Embedding"
authors: "Iliass Ayaou; Denis Cavallucci"
year: 2025
venue: "Preprint; arXiv:2510.22264 (per IS1 literature matrix); INSA Strasbourg"
doi: null
arxiv: "2510.22264"
extraction_cache: source-packet/03-priority-papers/extraction-cache/U012.md
experience_brain_match: yes
recommended_ingestion_action: link_existing
digest_status: completed
digest_prepared: 2026-07-24
pass_type: "Unique-PDF digestion Batch 1 (token-efficient two-stage protocol)"
authority: "External Knowledge (not Grounded Experience, not Paper D evidence)"
---

# U012: PatenTEB — A Comprehensive Benchmark and Model Family for Patent Text Embedding

**Unique ID:** U012 · **Priority tier:** A · **SHA-256:** `528a290e…c5c11358f85`
**Canonical path:** `research/ref-paper/is1/pdfs/12_patenteb_a_comprehensive_benchmark_and_model_2025.pdf`

## Bibliographic Identity

- **Title:** PatenTEB: A Comprehensive Benchmark and Model Family for Patent Text Embedding
- **Authors:** Iliass Ayaou, Denis Cavallucci — INSA Strasbourg (same lab as **DAPFAM / U011**)
- **arXiv:** 2510.22264 (per IS1 literature matrix, EB KNO-5449A7642CF9); resources at github.com/iliass-y/patenteb

## Research Problem

General embedding benchmarks (MTEB) include no patent-specific evaluation, and existing patent resources are narrow or lack systematic protocols. How to build a benchmark + model family that captures patent-specific challenges — extreme document length, **asymmetric fragment-to-document matching**, and cross-domain semantics — and jointly optimizes for benchmark performance and real-world generalization.

## Method (verified against cache)

- **Benchmark:** **15 tasks** across retrieval, classification, paraphrase, clustering; **2.06M examples**; domain-stratified splits; **domain-specific hard-negative mining**; asymmetric fragment→document scenarios (lines 8–10).
- **Model family (`patembed`):** multi-task training on **13 training tasks** (clustering is eval-only, line 2328); **67M–344M params**; context up to **4096 tokens**; knowledge distillation for multiple sizes; **prompt-based task conditioning** (line 129).
- **Ablations:** multi-task vs single-task; domain-pretrained initialization vs generic; supervision-signal composition.

## Dataset and Evaluation Setting

Internal: 15-task PatenTEB suite (2.06M examples, domain-stratified). External validation: **MTEB BigPatentClustering.v2** and **DAPFAM (U011)**. Primary metrics vary by task family (NDCG@k for retrieval, V-measure for clustering, etc.).

## Main Findings (verified against cache)

1. **External SOTA:** patembed-base = **0.494 V-measure** on MTEB BigPatentClustering.v2 (vs 0.445 previous best); **patembed-large = 0.377 NDCG@100 on DAPFAM** (line 14) — notably above DAPFAM's own best single-system (~0.3475, U011 audit).
2. **Multi-task trade-off:** diverse supervision marginally reduces in-benchmark scores but **improves external generalization** (lines 52–53).
3. **Domain-pretrained initialization** gives consistent gains across task families, largest in semantic matching.
4. **Persistent cross-domain gap reproduced internally:** patembed-large 0.512 NDCG@10 on retrieval_IN vs **0.172 on retrieval_OUT (2.98× gap)** (line 2031) — independent corroboration of the DAPFAM OUT-gap thesis on a different benchmark.

## Limitations (verified, §8.3, lines 2047–2079)

- English-family / European-filing bias; jurisdictions without an English family member underrepresented.
- Known IPC classification consistency issues affect domain labels.
- **Single-run deterministic evaluation** (fixed seeds, no multi-seed averaging) due to compute cost; robustness argued via external validation only.

## Track C Relevance (candidate-exposure — proposed, NOT AUTHORIZED)

**High.** PatenTEB/patembed are candidate-embedding methods directly evaluable on DAPFAM's OUT split; patembed-large's 0.377 DAPFAM NDCG@100 is the strongest external dense number in the corpus. The internal 2.98× IN/OUT retrieval gap independently supports KNO-20DDBF1D30A0's H1 (candidate exposure is the dominant cross-domain limit). Prompt-based task conditioning and asymmetric fragment→document matching map onto claim-fragment query design.

## Track R Relevance (fixed-pool reranking — proposed, NOT AUTHORIZED)

**Low–medium.** An embedding benchmark/model, not a reranker. patembed could serve as a bi-encoder first stage feeding a reranker, but PatenTEB contributes no fixed-pool reranking evidence.

## Track S Relevance (SkillOpt — EXECUTION CLOSED)

**Low.** "Prompt-based task conditioning" is task-instruction prompting, not prompt-optimization/GEPA; not evidence for Track S.

## Relationship to Papers A–D

- **Sibling to DAPFAM (U011)** from the same lab: DAPFAM = family-level retrieval benchmark, PatenTEB = embedding-task benchmark + trained models; PatenTEB uses DAPFAM as external validation, so the two interlock.
- **patembed is a candidate encoder for the Track-C retrieval stage** underlying Papers A–D; its 2.98× IN/OUT gap corroborates the DAPFAM-motivated reranking hypothesis behind Paper D.
- **Initialization lineage:** the paper notes domain pretraining "serving as the initialization for several patent NLP systems including PAECTER" (line 125) → direct link to **U009 (PAECTER)**. Also positions vs **PatentSBERTa (U005)** (lines 114–117).
- Absolute numbers here are PatenTEB/DAPFAM-reported; do not cross-compare against other papers' differently-measured scores.

## Verification Warnings

1. Abstract-level headline numbers (0.494 V-measure; 0.377 DAPFAM NDCG@100; 2.98× gap 0.512→0.172) verified against cache lines 13–14, 2031. Full per-task result tables (Table 12 spec at line 2327) **not** transcribed cell-by-cell — verify against PDF before citing individual task scores.
2. arXiv ID (2510.22264) taken from the IS1 literature matrix (EB), not re-verified from the PDF body; confirm before external citation.
3. Table cells subject to PDF→text artifacts (same class as U011).

## Experience Brain Cross-Check (READ-ONLY)

- **experience_brain_match:** **yes** — exact PDF is Knowledge **KNO-528A290EA2E4** (source hash `528a290e…` = U012 SHA). Also in the IS1 literature matrix (KNO-5449A7642CF9, listed A2 "PatenTEB … Tier 1") and the candidate-exposure synthesis KNO-20DDBF1D30A0 (external set member).
- **memory_conflict:** none. EB treats PatenTEB as external Knowledge / planning input only, "not evidence that the Agent has tested the claim" — this digest keeps that authority framing.
- **query mode:** read-only; no record created or modified.
- **recommended_ingestion_action:** **link_existing** — already ingested (KNO-528A290EA2E4); attach this digest as the analytical layer.

## Status

✅ **completed** — Token-efficient two-stage protocol: reused pre-extracted `extraction-cache/U012.md` (35 pages, 107,607 B); head + targeted greps for task taxonomy, model config, headline results, and limitations. Full markdown not loaded wholesale.

---
*Digest prepared 2026-07-24. Source repository unmodified. Experience Brain queried read-only.*
