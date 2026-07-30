---
unique_id: U015
priority_tier: B
sha256: b557af2ad1743c17fe867108d2460f0158167637967be5c30b9dfdd9a480f19e
canonical_path: research/ref-paper/is1/pdfs/15_patent_retrieval_with_few_shot_fine_2025.pdf
size_bytes: 375045
title: "Patent Retrieval with Few-Shot Fine-Tuning and Quantized Embeddings"
authors: "Renukswamy Chikkamath; Linda Andersson; Markus Endres"
year: 2025
venue: "ICAAI 2025, Manchester, United Kingdom (Nov 14–16, 2025)"
doi: null
arxiv: null
extraction_cache: source-packet/03-priority-papers/extraction-cache/U015.md
experience_brain_match: no
recommended_ingestion_action: ingest_new
digest_status: completed
digest_prepared: 2026-07-24
pass_type: "Unique-PDF digestion Batch 1 (token-efficient two-stage protocol)"
authority: "External Knowledge (not Grounded Experience, not Paper D evidence)"
---

# U015: Patent Retrieval with Few-Shot Fine-Tuning and Quantized Embeddings

**Unique ID:** U015 · **Priority tier:** B · **SHA-256:** `b557af2a…f19e`
**Canonical path:** `research/ref-paper/is1/pdfs/15_patent_retrieval_with_few_shot_fine_2025.pdf`

## Bibliographic Identity

- **Title:** Patent Retrieval with Few-Shot Fine-Tuning and Quantized Embeddings
- **Authors:** Renukswamy Chikkamath (HM Munich), Linda Andersson (Univ. Vienna / artificialresearcher.com), Markus Endres (HM Munich)
- **Venue:** ICAAI 2025, Manchester, UK (Nov 14–16, 2025)
- **Companion paper** to U014 (same author team, same CLEF-IP 2011 + quantization program).

## Research Problem

Embedding-based semantic patent search is costly to deploy. Can **general-purpose** embeddings be specialized to the patent domain with **minimal training data** (few-shot), and can **quantization** make retrieval cheap enough for real-world scale — without the cost of large labeled patent corpora or European search-report citation pairs?

## Method (verified against cache)

- Introduces a **patent-pair dataset** built from **US patent first claims + abstracts** (self-supervised-style positive pairs) for fine-tuning general-purpose embeddings (lines 24–26).
- Few-shot fine-tuning sweeps: **5 → 250 → 10,000** training pairs; general-purpose backbones (incl. **STELLA**, BGE-base).
- **Embedding quantization:** binary retrieval + scalar rescoring (same pipeline as U014).
- Benchmark: **CLEF-IP 2011** English, metric **MAP@100**.

## Dataset and Evaluation Setting

CLEF-IP 2011 English test set. US-claim/abstract pairs for training. Comparison against European search-report-based citation pairs and existing patent retrieval models.

## Main Findings (verified against cache)

1. **Few-shot suffices:** even **5 training pairs** give a **6–14% MAP@100 gain**; STELLA improves **0.1221 → 0.1297** with just 5 samples (lines 29–30, 870–872). Qualitative pairs (5–250) improve general-purpose models by **≥30%** when adapted to the patent domain (lines 864–867).
2. **Best model: MAP@100 0.1321** on CLEF-IP 2011, surpassing existing patent semantic retrieval methods (line 867).
3. **Over-fine-tuning hurts:** BGE-base **drops 5–6% with 10,000 samples** — more data is worse past a small threshold (lines 35–37).
4. **Quantization:** binary + scalar rescoring cuts memory **32×** and is **30–40× faster**, outperforming float32 retrieval by ≥25% MAP; headline config also reports the same **+14.81% abs / +28.95% vs patent-specific** framing as U014 (lines 855–881).

## Limitations

- Single benchmark (CLEF-IP 2011); **low absolute MAP** (~0.13). Pairs derived from US claims/abstracts — construct validity of "relevance" is proxy, not examiner citation. Few-shot gains are model-dependent (STELLA-favourable). Quantization efficiency numbers are setup-dependent. Not peer-reviewed journal (workshop/conference).

## Track C Relevance (candidate-exposure — proposed, NOT AUTHORIZED)

**Medium-High (methodological).** The **few-shot fine-tuning + saturation** finding is the most transferable result: it suggests a Track-C encoder can be domain-adapted with tiny curated pair sets, and warns that large-scale fine-tuning can *degrade* retrieval — directly relevant to any candidate-generation encoder tuning. Still CLEF-IP not DAPFAM, and MAP conflates exposure with ordering.

## Track R Relevance (fixed-pool reranking — proposed, NOT AUTHORIZED)

**Low-Medium.** Quantized retrieval + rescoring is a retrieval/efficiency lever more than a reranking study; scalar rescoring is a lightweight re-rank stage worth noting but not a fixed-pool reranker experiment.

## Track S Relevance (SkillOpt — EXECUTION CLOSED)

**None.** No prompt-optimization content.

## Relationship to Papers A–D

- **Companion to U014**; same CLEF-IP/quantization program, adds the **few-shot data-efficiency** axis.
- The **"5 pairs beat 10k; excessive fine-tuning degrades"** result is a useful caution for the domain-specific embedding lineage (U005/U008/U009/U013) and connects to the **small-model-deployment gap** noted in KNO-3D43C4514725.
- Complements the self-supervised augmentation angle of U013 (both reduce labeled-data dependence).
- All numbers are **CLEF-IP MAP@100** — never cross-compare to DAPFAM NDCG@100 (U011/U012).
- Relevance = proxy US claim/abstract pairs + CLEF-IP judgments; not legal novelty/infringement/FTO.

## Verification Warnings

1. Headline numbers verified against Abstract (lines 20–37) and Conclusion (lines 853–881): MAP@100 0.1321 best; STELLA 0.1221→0.1297 at 5 shots; BGE-base −5–6% at 10k; 32× memory / 30–40× faster. Individual table cells (Tables 1–2) not transcribed — verify against PDF before quoting specific rows.
2. The +14.81%/+28.95% figures duplicate U014's framing — attribute carefully to avoid double-counting one program's result as two.
3. Year 2025 (ICAAI); filename `..._2025.pdf`. No DOI/arXiv located in cache.

## Experience Brain Cross-Check (READ-ONLY)

- **experience_brain_match:** **no** — no Knowledge record carries U015's hash (`b557af2a…`). Nearest returns are the IS1 gaps report (KNO-3D43C4514725) and literature matrix (KNO-5449A7642CF9), which are project-context, not this paper. (Contrast U014, which *is* ingested as KNO-E0520C4384CF.)
- **memory_conflict:** none.
- **query mode:** read-only; no record created or modified.
- **recommended_ingestion_action:** **ingest_new** — not yet in EB; companion to the already-ingested U014.

## Status

✅ **completed** — Token-efficient two-stage protocol: reused pre-extracted `extraction-cache/U015.md` (8 pages, 42,120 B); head + targeted greps + one line-range read (853–895) for conclusion/headline numbers. Full markdown not loaded wholesale.

---
*Digest prepared 2026-07-24. Source repository unmodified. Experience Brain queried read-only.*
