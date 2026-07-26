---
unique_id: U004
priority_tier: B
sha256: bcb2a7726c342934f30893b66901720751e372131510364007cfde89e0b7289c
canonical_path: research/ref-paper/is1/pdfs/04_patent_prior_art_search_using_deep_2020.pdf
size_bytes: 6836250
title: "Patent Prior Art Search using Deep Learning Language Model"
authors: "Dylan Myungchul Kang; Charles Cheolgi Lee; Suan Lee; Wookey Lee"
year: 2020
venue: "IDEAS 2020 — 24th International Database Applications & Engineering Symposium (ACM)"
doi: "10.1145/3410566.3410597"
arxiv: null
extraction_cache: source-packet/03-priority-papers/extraction-cache/U004.md
experience_brain_match: no
recommended_ingestion_action: ingest_new
digest_status: completed
digest_prepared: 2026-07-24
pass_type: "Unique-PDF digestion Batch 1 (token-efficient two-stage protocol)"
authority: "External Knowledge (not Grounded Experience, not Paper D evidence)"
---

# U004: Patent Prior Art Search using Deep Learning Language Model

**Unique ID:** U004 · **Priority tier:** B · **SHA-256:** `bcb2a772…e0b7289c`
**Canonical path:** `research/ref-paper/is1/pdfs/04_patent_prior_art_search_using_deep_2020.pdf`

## Bibliographic Identity

- **Title:** Patent Prior Art Search using Deep Learning Language Model
- **Authors:** Dylan Myungchul Kang, Charles Cheolgi Lee, Suan Lee (VOICE AI Institute), Wookey Lee — Inha University & VOICE AI Institute, Incheon, South Korea
- **Year:** 2020 · **Venue:** IDEAS 2020 (ACM, 5-page short paper) · **DOI:** 10.1145/3410566.3410597

## Research Problem

Patent examination cannot keep pace with rising application volume. The paper frames prior art search as a **recall-critical** task (unlike precision-focused web search: missing a relevant patent is costly) and tackles it as a **binary classification** problem — distinguishing "valid/relevant" patents from "noise" patents — using a deep-learning language model, deliberately avoiding the hierarchical multi-label pitfalls of IPC/CPC code classification (partial-match ambiguity, e.g., getting `G02B` right but the subgroup wrong).

## Dataset and Evaluation Setting

- **Source:** WIPS patent database, fetched March 2016; US/CN/EP/PCT patents on plural/dual/transfer/barrel/signal (dual-camera technology) via a Boolean query. Each record: nation code, title, abstract, first claim, application number, main IPC code. Label 1 = relevant, 0 = irrelevant.
- **Two setups:** Non-uniform (9,093 total; valid patents only ~4.4% — realistic imbalance) and Uniform (804 total; valid:noise balanced 1:1 to measure model capability). Split 8:1:1 train/val/test.
- **Metric:** primarily **recall** (plus precision/F1 and validation loss over the 10 experiments in Table 1).

## Method

Fine-tune **`bert-base-uncased`** (12 transformer layers, scaled dot-product attention) as a binary classifier on patent bibliographic components. Text fields (title, abstract, first claim, and combinations — the component set P) are tokenized (WordPiece, `[CLS]`/`[SEP]`), fed to BERT; the `[CLS]` representation drives the valid/noise decision. Preprocessing strips special characters/numbers. Ten experiments sweep different field combinations.

## Main Findings

1. **Best recall 94.29%** on the *uniform* dataset using **title + first claim** together.
2. **First claim alone** gives 86.11% recall — the claim is a strong standalone representation of patent content, consistent with claims' legal centrality.
3. On the **non-uniform** (realistic, imbalanced) set, validation loss sometimes failed to decrease — BERT struggles with heavily skewed data (or simply too few positives). Uniform-set loss decreased steadily (no overfitting).
4. Authors argue a well-designed recall-oriented classifier on imbalanced real data could accelerate examination.

## Limitations

1. **Tiny, narrow dataset** (uniform n=804; single tech area — dual-camera; March 2016 snapshot). Generalization unproven.
2. **Binary classification ≠ ranked retrieval:** no ranking metric (nDCG/MAP/Precision@k), no candidate-pool retrieval — it classifies a pre-fetched set, so recall figures are not comparable to retrieval Recall@100.
3. **Balanced-set headline (94.29%)** is on an artificially 1:1 set; the realistic 4.4%-positive setup underperforms and shows training instability.
4. Bibliographic fields only (title/abstract/first claim); no full-text, no dense retrieval index, no reranking.
5. Extraction note: Table 1's numeric column ordering is garbled in the PDF→text conversion; only recall values cited in prose (94.29%, 86.11%) are reliable.

## Track C Relevance (candidate-exposure — proposed, NOT AUTHORIZED)

**Moderate.** Recall-centric and claim-driven — thematically aligned with Track C's exposure focus and with KNO-20DDBF1D30A0's H2 (claim-element query expansion). But this is a *classification filter over a pre-fetched set*, not candidate generation/expansion, so it does not directly test exposure@K.

## Track R Relevance (fixed-pool ranking — proposed, NOT AUTHORIZED)

**Low.** Binary relevance classification, no reranking of a frozen top-K, no ranking metric. Not comparable to Paper D's scalar-instruction reranking surface.

## Track S Relevance (SkillOpt — revision-stage, EXECUTION CLOSED)

**None.** No prompt/skill optimization.

## Relationship to Papers A–D

- **Adjacent, not closest prior art.** Shares patent-domain BERT fine-tuning with early Paper-D lineage, but at the wrong granularity (binary classification vs family-level frozen-pool reranking) and on a different, tiny corpus (WIPS dual-camera vs DAPFAM pharma).
- **Recall-priority framing echoes DAPFAM/Paper D** OUT-domain candidate-exposure concern (Recall@100 ≈ 0.1655), but U004 reports balanced-set classification recall, which is not the same measurement — do NOT cross-compare the 94.29% to DAPFAM recall.
- Not DAPFAM, GEPA, MIPROv2, or prompt-optimization related. Cite as external methodological context (early BERT-for-patent-relevance).

## Verification Warnings

1. **94.29% recall is on a balanced n=804 set** — not a retrieval benchmark; do not present as prior-art-search Recall@100.
2. Table 1 column values are PDF-mangled; trust only prose-quoted numbers.
3. Single narrow tech domain, 2016 data — low external validity.
4. "Recall > precision in patent search" is asserted, echoing U003; treat as domain framing, not a measured claim about this dataset's precision.

## Experience Brain Cross-Check (READ-ONLY)

- **experience_brain_match:** no
- **matched_knowledge_ids:** none specific to Kang 2020; nearest returns were KNO-20DDBF1D30A0 (candidate-exposure synthesis), KNO-528A290EA2E4 (PatenTEB), KNO-384DFF3E3AC0 (DAPFAM), KNO-3D43C4514725 (IS1 research-gaps context).
- **memory_conflict:** none
- **query mode:** read-only; no record created or modified.
- **recommended_ingestion_action:** ingest_new (low priority; a minor early BERT-for-patent classification reference).

## Status

✅ **completed** — Token-efficient two-stage protocol: extracted once to `extraction-cache/U004.md` (5 pages, 3,805 words); targeted reads of abstract, intro/related §1–2, methodology §3, dataset §4.2, results §4.3, conclusion §5, Tables 1–2. Full markdown not loaded wholesale.

---
*Digest prepared 2026-07-24. Source repository unmodified. Experience Brain queried read-only.*
