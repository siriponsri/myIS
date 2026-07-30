---
unique_id: U009
priority_tier: A
sha256: 92f3e83d2cbf257acdd4efc6e46aad8c93610dbe4b89d303fe4c964c49d4436a
canonical_path: research/ref-paper/is1/pdfs/09_paecter_patent_level_representation_learning_using_2024.pdf
size_bytes: null
title: "PaECTER: Patent-level Representation Learning using Citation-informed Transformers"
authors: "Mainak Ghosh; Michael E. Rose; Sebastian Erhardt; Erik Buunk; Dietmar Harhoff"
year: 2024
venue: "arXiv:2402.19411 (v2, 1 Oct 2025); Max Planck Institute for Innovation and Competition"
doi: null
arxiv: "2402.19411"
extraction_cache: source-packet/03-priority-papers/extraction-cache/U009.md
experience_brain_match: yes
recommended_ingestion_action: link_existing
digest_status: completed
digest_prepared: 2026-07-24
pass_type: "Unique-PDF digestion Batch 1 (token-efficient two-stage protocol)"
authority: "External Knowledge (not Grounded Experience, not Paper D evidence)"
---

# U009: PaECTER — Patent-level Representation Learning using Citation-informed Transformers

**Unique ID:** U009 · **Priority tier:** A · **SHA-256:** `92f3e83d…c49d4436a`
**Canonical path:** `research/ref-paper/is1/pdfs/09_paecter_patent_level_representation_learning_using_2024.pdf`

## Bibliographic Identity

- **Title:** PaECTER: Patent-level Representation Learning using Citation-informed Transformers
- **Authors:** Mainak Ghosh, Michael E. Rose, Sebastian Erhardt, Erik Buunk, Dietmar Harhoff — Max Planck Institute for Innovation and Competition, Munich
- **Year:** 2024 · **arXiv:** 2402.19411 (v2 1 Oct 2025) · **Artifacts:** open-source on HuggingFace (`mpi-inno-comp/paecter` model + `paecter_dataset`)

## Research Problem

Prior-art / similarity search for patents needs a **document-level patent encoder** whose vector similarity tracks examiner-judged relatedness. General-purpose and even patent-pretrained models (BERT for Patents) are not optimized for the *similarity* objective. PaECTER fine-tunes BERT for Patents with **examiner-added citation** signal to produce dense representations that rank truly related patents first.

## Method

- **Base:** BERT for Patents (Google), 1024-dim, 512-token limit, wrapped in a SentenceTransformer siamese architecture.
- **Input:** concatenated **title + abstract**; final embedding = **mean pooling** of output tokens (beat [CLS] empirically).
- **Objective:** **triplet margin loss** (L2, margin m=1); focal / positive / negative patents.
- **Relevance signal:** EPO examiner citation categories — **X, Y, I, A treated as similar (positive)**; negatives split into **easy** (same-CPC, ≤5 yr prior, not cited) and **hard** (cited by focal's backward citations but not by focal itself).
- **Training config:** lr 1e-5, 10% warmup, AdamW/decoupled weight decay, 4 epochs (plateaus after 2), batch 4 × grad-accum 8 → effective 128, 4× A100-40GB, ~20 h/epoch.

## Dataset and Evaluation Setting

- **Training:** 300,000 EPO patent families (filed 1985–2022) sampled from 1,358,264 eligible focal patents (PATSTAT 2023 Spring); English abstract required, else best DOCDB family sibling by priority WO>US>GB>…>JP; 85:15 train/val; 1.5M triplet rows.
- **Test:** 1,000 samples, each = 1 focal + 5 positive + 25 negatives (10 hard, 15 easy); no train overlap; 976/1000 in multi-authority families (921 with US sibling).
- **Metrics:** **Avg RFR** (rank of first relevant, lower=better), **MAP** (5 pos / 25 neg), **MRR@10**; CLS vs mean pooling both reported.

## Baselines & Main Findings

- Baselines: BM25, BERT-large, SciBERT, SPECTER, SPECTER 2.0, BERT for Patents, **PatentSBERTa (U005)**, GTE-large, BGE-large-en-v1.5, E5-large-v2.
- **PaECTER wins every metric/pooling (Table 2, mean pooling):** **Avg RFR 1.31, MAP 68.17, MRR@10 88.25** — vs next-best BGE (RFR 1.53 / MAP 60.51 / MRR 81.18) and BERT-for-Patents (1.55 / 60.32 / 80.49).
- Gains over BERT for Patents: **+7.85 MAP, +7.76 MRR@10 (p < .001)**. Headline: predicts a most-similar patent at **average rank 1.32** against 25 irrelevants.
- **Head-to-head vs SEARCHFORMER (U008) on SEARCHFORMER's own test set (Table 3):** PaECTER RFR **49.66** vs SEARCHFORMER 58.73; MAP 11.13 vs 9.38; MRR@10 17.93 vs 15.33 — PaECTER wins all three (≈9 fewer documents to inspect), despite SEARCHFORMER training on claims and PaECTER on title+abstract.
- **Ablation (Table 4):** abstract-trained model > CPC-code-trained / ablated model. External eval (Ganguli et al. 2024) tests PaECTER on US independent-claim interference / annotation / tech-classification tasks.

## Limitations

1. **512-token limit → title+abstract only**, not full claims/description "central to defining legal scope"; weaker on fine-grained technical detail.
2. **English-only**; non-English needs MT pre-inference.
3. **Temporal drift** — training reflects past technologies.
4. CPC-dependence in some settings (~103k training patents lack CPC codes).
5. Document-level; relevance defined by examiner citations (EPO-centric).

## Track C Relevance (candidate-exposure headroom — proposed, NOT AUTHORIZED)

**High.** PaECTER is an **open-source, ready-to-use dense candidate-generation encoder** with examiner-citation relevance — a strong off-the-shelf "dense semantic channel" for KNO-20DDBF1D30A0's **H1** multi-view union, and a legitimate Track-C baseline to benchmark against (it already outperforms PatentSBERTa/SPECTER2/BGE/E5 on citation-prediction ranking). Its **easy-vs-hard negative** construction is directly reusable design guidance. Caveat: title+abstract input and document-level scope — not claim-element chunking; would be a *baseline*, not the claim-level intervention.

## Track R Relevance (fixed-pool ranking headroom — proposed, NOT AUTHORIZED)

**Low.** PaECTER is a bi-encoder for first-stage similarity/candidate generation, not an instruction-optimized reranker over a frozen top-K. No prompt/instruction channel. Upstream of Paper D's reranking surface.

## Track S Relevance (SkillOpt / prompt evolution — revision-stage, EXECUTION CLOSED)

**None.** No prompts or instruction optimization; embedding fine-tuning only.

## Relationship to Papers A–D

- **Closest-prior-art dense encoder and the natural benchmark opponent** for any DAPFAM (U011) candidate-generation baseline, in the PatentSBERTa (U005) → SEARCHFORMER (U008) → PaECTER lineage. PaECTER **directly beats both U005 and U008** on citation-prediction ranking → the current open-source SOTA bi-encoder among the digested set. Cite as the dense first-stage baseline.
- **Relevance = examiner X/Y/I/A citations**, family-aware (DOCDB) but scored document-level on a curated 1-focal/30-candidate test — *not* DAPFAM family-level Recall@100 cross-domain, and RFR/MAP/MRR here use tiny candidate pools (25–30). Do not cross-compare absolute numbers with DAPFAM.
- **Not prompt-optimization / not reranking** — orthogonal to Papers A/B/C GEPA/query-rewriting theses; never cite as Paper A–D outcome evidence.

## Verification Warnings

1. **Two different RFR scales** — Table 2 uses a 30-candidate pool (PaECTER RFR ≈1.31); Table 3 uses SEARCHFORMER's large pool (RFR ≈49.66). Never mix the two; both are "lower is better."
2. Table 2/3 columns are de-gridded in the PDF→text cache (numbers on separate lines) — values here are mapped by row order and cross-checked against prose; ⚠️ visual-check flag, confirm the grid in the PDF if citing precise cells.
3. "Rank 1.32" (abstract) vs "Avg RFR 1.31/1.32" (Table 2) — same quantity, rounding differs.
4. Year: filename/manifest = 2024; arXiv v2 stamped 1 Oct 2025 — cite as Ghosh et al. 2024 (arXiv:2402.19411).
5. MAP/MRR are on very small candidate sets (5 pos/25 neg) — high absolute values are expected and not comparable to large-corpus retrieval MAP.

## Experience Brain Cross-Check (READ-ONLY)

- **experience_brain_match:** **yes** — this exact PDF is already ingested as Knowledge **KNO-92F3E83D2CBF** (source hash `92f3e83d2cbf…` = U009 SHA). Duplicate-detection hit; no separate Grounded Experience (measured) record exists.
- **matched_knowledge_ids:** KNO-92F3E83D2CBF (PaECTER PDF itself), KNO-20DDBF1D30A0 (candidate-exposure synthesis — H1), KNO-528A290EA2E4 (PatenTEB), KNO-384DFF3E3AC0 (DAPFAM).
- **memory_conflict:** none.
- **query mode:** read-only; no record created or modified.
- **recommended_ingestion_action:** **link_existing** — do NOT re-ingest the PDF (already KNO-92F3E83D2CBF); attach this digest as the analytical layer over the existing knowledge record.

## Status

✅ **completed** — Token-efficient two-stage protocol: extracted once to `extraction-cache/U009.md` (9 pages, 4,928 words); targeted reads of abstract, §2 training data (objective, focal/positive/negative, test set), §3 training, §4.1–4.3 evaluation + Tables 2–4, §5 conclusion, §6 limitations. Full markdown not loaded wholesale.

---
*Digest prepared 2026-07-24. Source repository unmodified. Experience Brain queried read-only.*
