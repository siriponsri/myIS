---
unique_id: U020
priority_tier: B
sha256: 9bd2b1f5eea98637de9ff49bd810b49be774502bd9732bf2b74a0c27404a6458
canonical_path: research/ref-paper/is1/pdfs/20_zero_shot_hybrid_retrieval_and_reranking_2022.pdf
size_bytes: 618170
title: "Zero-shot Hybrid Retrieval and Reranking Models for Biomedical Literature"
authors: "Jing Lu; Ji Ma; Keith Hall"
year: 2022
venue: "CLEF 2022 Working Notes — 10th BioASQ challenge (Task B Phase A)"
doi: null
arxiv: null
extraction_cache: source-packet/03-priority-papers/extraction-cache/U020.md
experience_brain_match: no
recommended_ingestion_action: ingest_new
digest_status: completed
digest_prepared: 2026-07-24
pass_type: "Unique-PDF digestion Batch 1 (token-efficient two-stage protocol)"
authority: "External Knowledge (not Grounded Experience, not Paper D evidence)"
---

# U020: Zero-shot Hybrid Retrieval and Reranking for Biomedical Literature

**Unique ID:** U020 · **Priority tier:** B · **SHA-256:** `9bd2b1f5…6458`
**Canonical path:** `research/ref-paper/is1/pdfs/20_zero_shot_hybrid_retrieval_and_reranking_2022.pdf`

## Bibliographic Identity
Lu, Ma & Hall (Google Research), 2022. Participating-system paper at the 10th BioASQ challenge document-retrieval sub-task (Task B Phase A), CLEF 2022 working notes.

## Research Problem
Build an effective **zero-shot** document retrieval system for biomedical questions (retrieve relevant PubMed articles) using **only synthetic training data** — no in-domain labeled query-document pairs.

## Method (verified against cache)
Two-stage pipeline:
1. **Hybrid retrieval** = sparse (**BM25**) + **dense dual-encoder**; dense model improved with a **T5-based synthetic question generation** model and an **iterative training strategy** with low-quality synthetic-data filtering (lines 9–13, 539–541).
2. **Hybrid reranking** trained on first-stage candidates; robust across different first-stage retrievers (lines 14–17).
3. Explored **knowledge distillation** from the hybrid reranker back into the dense retriever (lines 15–16).
4. **Reciprocal Rank Fusion (RRF)** to combine multiple systems for additional accuracy gains (line 18).
Backbone: domain-adapted BERT-based encoders (line 65).

## Dataset & Evaluation
BioASQ 10 Task B Phase A, PubMed corpus, expert-authored biomedical questions. Metric = **MAP**.

## Main Findings (verified against cache)
- MAP across six batches: **0.4696, 0.3984, 0.4586, 0.4089, 0.4065, 0.1704** (abstract line 20).
- Hybrid retrieval + T5-based reranking **outperforms the best reporting system on Batches 2, 4, 6** (lines 541–542).
- Hybrid reranker is effective even applied to *different* first-stage retrieval models (line 17).
- **RRF fusion** of systems yields additional gains (line 18).

## Limitations
Biomedical (PubMed), **not patent** — no patent/DAPFAM/claim-level evaluation. Challenge-system paper (leaderboard framing, per-batch variance — note the low Batch-6 MAP 0.1704). Zero-shot via synthetic data is the whole premise, so no supervised in-domain comparison.

## Track C Relevance (candidate-exposure — proposed, NOT AUTHORIZED)
**Medium.** Hybrid **sparse+dense** first-stage is exactly the multi-view candidate-generation direction in the IS1 hypothesis set (lexical + dense union). Zero-shot synthetic-query generation is a candidate mechanism for cross-domain OUT exposure without labeled data.

## Track R Relevance (fixed-pool reranking — proposed, NOT AUTHORIZED)
**Medium-High (mechanism).** Two-stage retrieve-then-rerank with a reranker trained on first-stage candidates, plus **RRF fusion** and **reranker→retriever distillation** — all directly relevant reranking-stage mechanics. Domain differs (biomedical), so it is an analogue, not a patent result.

## Track S Relevance (SkillOpt — EXECUTION CLOSED)
**None.**

## Relationship to Papers A–D
**Methodological analogue**, not closest prior art. Corroborates the project's hybrid + RRF-fusion + rerank architecture from an independent (biomedical) domain. Its MAP figures are **biomedical**, unrelated to Paper D's OUT metrics — do not cross-compare. Pairs with U014/U015 (retrieve-rerank on CLEF-IP) as non-patent/quasi-patent reranking evidence.

## Verification Warnings
- MAP six-batch numbers transcribed verbatim from abstract (line 20) — clean, not from a fragmented table.
- "Outperforms best system on Batches 2/4/6" is the authors' leaderboard claim (Conclusion 541–542), not an independent metric.
- No arXiv/DOI located in extraction; cite as CLEF 2022 BioASQ working notes.

## Experience Brain Cross-Check (READ-ONLY, narrow)
- **SHA query** (`9bd2b1f5…6458`): `no_match`.
- **Title query** ("Zero-shot Hybrid … BioASQ … RRF"): returned only broad IS1 synthesis / literature-review records (KNO-20DDBF1D30A0, KNO-3D43C4514725, KNO-32D2DB87C6AB) — none is this paper by hash or title.
- **experience_brain_match:** **no** · **memory_conflict:** none · **query mode:** read-only, nothing created/modified.
- **recommended_ingestion_action:** **ingest_new** (Tier-B methodological analogue: hybrid + RRF + rerank + distillation).

## Status
✅ **completed** — CACHE_HIT on `extraction-cache/U020.md` (29,143 B); head + targeted greps + one line-range read (537–560). Full markdown not loaded wholesale.

---
*Digest prepared 2026-07-24. Source repository unmodified. Experience Brain queried read-only (SHA→title, ≤3 records).*
