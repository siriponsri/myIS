---
unique_id: U019
priority_tier: C
sha256: 12a08f0d9b1eb72a13d53bf6fa367e89dee8e55026e2269d3404095e87fde996
canonical_path: research/ref-paper/is1/pdfs/19_patent_classification_by_fine_tuning_bert_2019.pdf
size_bytes: 729224
title: "PatentBERT: Patent Classification by Fine-Tuning BERT Language Model"
authors: "Jieh-Sheng Lee; Jieh Hsiang"
year: 2019
venue: "National Taiwan University (arXiv preprint)"
doi: null
arxiv: "1906.02124"
extraction_cache: source-packet/03-priority-papers/extraction-cache/U019.md
experience_brain_match: no
recommended_ingestion_action: ingest_new
digest_status: completed
digest_prepared: 2026-07-24
pass_type: "Unique-PDF digestion Batch 1 (token-efficient two-stage protocol)"
authority: "External Knowledge (not Grounded Experience, not Paper D evidence)"
---

# U019: PatentBERT — Patent Classification by Fine-Tuning BERT

**Unique ID:** U019 · **Priority tier:** C · **SHA-256:** `12a08f0d…e996`
**Canonical path:** `research/ref-paper/is1/pdfs/19_patent_classification_by_fine_tuning_bert_2019.pdf`

## Bibliographic Identity
Lee & Hsiang (National Taiwan University), 2019, arXiv:1906.02124. One of the earliest BERT-for-patents papers ("PatentBERT").

## Research Problem
Can a fine-tuned pre-trained BERT beat prior deep-learning approaches (CNN + word embeddings, "DeepPatent") at large-scale patent classification, and is the claims text alone sufficient?

## Method (verified against cache)
Fine-tune pre-trained BERT for multi-label patent classification at the **CPC subclass level** (>630 labels, line 36). Input = **patent claims only** (no title/abstract/other fields, lines 13, 512, 547–548). Contributes dataset **USPTO-3M** at CPC subclass with SQL statements for reuse (lines 17–20).

## Dataset & Evaluation
USPTO-3M (>3M patents, CPC subclass). Metric = **F1@1** (micro). Baselines: DeepPatent (CNN, precision 73.88%@Top1 on USPTO-2M, no F1@1 disclosed, lines 161–166); also compares vs SVM/ULMFiT context (lines 189, 212 micro-F1 69.89% for a cited method).

## Main Findings (verified against cache)
- Fine-tuned BERT sets **new SOTA**, outperforming DeepPatent on large-scale patent classification (Abstract lines 6–12; Conclusion 539–547).
- **Claims alone are sufficient** for the classification task — replacing title+abstract with claims does not hurt (lines 13–14, 512, 547–548).
- Two-stage pre-train + fine-tune framework is promising for patent NLP broadly (549–558).

## Limitations
Task is **classification, not retrieval/ranking**; single-label-set (CPC subclass) focus; F1@1 only (no ranking metrics); no prior-art search / cross-domain evaluation; 2019-era BERT-base backbone.

## Track C Relevance (candidate-exposure — proposed, NOT AUTHORIZED)
**Low-Medium (indirect).** Load-bearing point for the project: **claims text alone is a sufficient signal** — supports claim-level chunking / claim-based representations for candidate generation. But this is a classifier, not a retriever; no candidate-set or coverage notion.

## Track R Relevance (fixed-pool reranking — proposed, NOT AUTHORIZED)
**None.** No ranking or reranking.

## Track S Relevance (SkillOpt — EXECUTION CLOSED)
**None.**

## Relationship to Papers A–D
**Foundational background**, not closest prior art. Establishes the BERT-for-patents lineage that later retrieval/embedding papers (PatentSBERTa U005, PatenTEB U012, PAECTER) build on, and empirically justifies **claims-centric** representations used across the project. Its "classification accuracy" is a CPC-label task, explicitly **not** any legal/novelty/infringement judgment.

## Verification Warnings
- SOTA + claims-sufficient claims verified against Abstract (lines 6–21) and Conclusion (529–558).
- Exact PatentBERT F1@1 headline number not cleanly isolated in the text extraction (results table fragmented; the clean numbers in-text — 73.88%, 69.89% — belong to *baselines* DeepPatent / a cited method, NOT to PatentBERT). ⚠️ Do not attribute 73.88%/69.89% to PatentBERT; open PDF Table for PatentBERT's own F1@1.
- Venue/arXiv id (1906.02124) inferred from author+title; confirm before citing.

## Experience Brain Cross-Check (READ-ONLY, narrow)
- **SHA query** (`12a08f0d…e996`): `no_match`.
- **Title query** ("PatentBERT … USPTO-3M"): returned only broad IS1 project-synthesis records (KNO-3D43C4514725, KNO-20DDBF1D30A0, KNO-9F9F212D663E) — none is this paper by hash or title.
- **experience_brain_match:** **no** · **memory_conflict:** none · **query mode:** read-only, nothing created/modified.
- **recommended_ingestion_action:** **ingest_new** (Tier-C foundational background).

## Status
✅ **completed** — CACHE_HIT on `extraction-cache/U019.md` (20,894 B); head + targeted greps + two line-range reads (155–172, 529–560). Full markdown not loaded wholesale.

---
*Digest prepared 2026-07-24. Source repository unmodified. Experience Brain queried read-only (SHA→title, ≤3 records).*
