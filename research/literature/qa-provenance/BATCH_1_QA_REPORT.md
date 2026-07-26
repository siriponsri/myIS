# BATCH 1 QUALITY-CONTROL REPORT — U001–U020

**Prepared:** 2026-07-24 · **Scope:** Batch 1 unique-PDF digestion (U001–U020)
**Method:** Index + frontmatter + targeted file checks only. **No PDFs re-read.**
**Authority:** Review-workspace artifact. Source repo `thaipha-lex` unmodified. Experience Brain queried READ-ONLY; **zero writes**.

---

## VERDICT: ✅ PASS (stabilized — 3 non-blocking schema inconsistencies identified and resolved)

20 / 20 canonical papers completed and digested. All required artifacts present. No fabricated Paper-D claims. No Experience Brain writes. Three housekeeping schema inconsistencies were logged (§C) during the original QA pass; all three were resolved in the 2026-07-24 stabilization pass (see `BATCH_1_STABILIZATION_REPORT.md`). None ever blocked ingestion.

---

## A. Completeness matrix (12 required checks)

| # | Check | Result |
|---|-------|--------|
| 1 | Exactly 20 unique canonical papers completed | ✅ 20/20 canonical (`type=canonical`) |
| 2 | No duplicate-of copy digested as separate unique paper | ✅ 4 `duplicate-of` rows (U011/U012/U013/U016 alt paths) NOT digested separately |
| 3 | Every U001–U020 has cache+digest+SHA+path+tier+status+verif+EB+action | ✅ all 20 (U001/U002 YAML frontmatter incl. `priority_tier: A` added 2026-07-24, §C1 resolved) |
| 4 | Every index row points to existing digest AND cache | ✅ all 20 digests + 20 caches exist and are referenced |
| 5 | No stale current-Paper-D claims | ✅ Paper-D numerics appear ONLY as "do-NOT-cross-compare" guardrails (§D) |
| 6 | Papers A/B/C remain pilot provenance only | ✅ synthesis §hdr: "Papers A/B/C are pilot provenance and must NOT be cited as Paper D evidence" |
| 7 | Track C/R remain proposed + unauthorized | ✅ canonical digest: both "roadmap-only, NOT AUTHORIZED" |
| 8 | Track S proposed only in revision materials, not canonical, not owner-approved, execution closed | ✅ canonical digest §4: "NOT IN CANONICAL PROGRAM PLAN / NOT OWNER-APPROVED / EXECUTION CLOSED" |
| 9 | Citation-relevance not represented as legal validity/infringement/claim-equivalence/invalidity/novelty/FTO | ✅ each digest confines relevance to citation/retrieval; no legal-judgment language |
| 10 | All unresolved visual checks listed by ID | ✅ see §E |
| 11 | link_existing vs ingest_new separated | ✅ see §F |
| 12 | No Experience Brain write occurred | ✅ all queries READ-ONLY (query_knowledge only); no create/update calls |

---

## B. Per-paper inventory (U001–U020)

| ID | Tier | EB match | Action | matched KNO | Status | Cache | Digest |
|----|------|----------|--------|-------------|--------|-------|--------|
| U001 | A | no | ingest_new | — | ✅ | ✅ | ✅ |
| U002 | A | no | ingest_new | — | ✅ | ✅ | ✅ |
| U003 | A | no | ingest_new | — | ✅ | ✅ | ✅ |
| U004 | B | no | ingest_new | — | ✅ | ✅ | ✅ |
| U005 | A | no | ingest_new | — | ✅ | ✅ | ✅ |
| U006 | A | no | ingest_new | — | ✅ | ✅ | ✅ |
| U007 | A | no | ingest_new | — | ✅ | ✅ | ✅ |
| U008 | A | no | ingest_new | — | ✅ | ✅ | ✅ |
| U009 | A | **yes** | link_existing | KNO-92F3E83D2CBF | ✅ | ✅ | ✅ |
| U010 | A | no | ingest_new | — | ✅ | ✅ | ✅ |
| U011 | A | **yes** | link_existing | KNO-384DFF3E3AC0 | ✅ | ✅ | ✅ |
| U012 | A | **yes** | link_existing | KNO-528A290EA2E4 | ✅ | ✅ | ✅ |
| U013 | A | no | ingest_new | — | ✅ | ✅ | ✅ |
| U014 | B | **yes** | link_existing | KNO-E0520C4384CF | ✅ | ✅ | ✅ |
| U015 | B | no | ingest_new | — | ✅ | ✅ | ✅ |
| U016 | C | no | ingest_new | — | ✅ | ✅ | ✅ |
| U017 | C | no | ingest_new | — | ✅ | ✅ | ✅ |
| U018 | B | no | ingest_new | — | ✅ | ✅ | ✅ |
| U019 | C | no | ingest_new | — | ✅ | ✅ | ✅ |
| U020 | B | no | ingest_new | — | ✅ | ✅ | ✅ |

U001/U002 tier is now **explicit `priority_tier: A`** in YAML frontmatter (added 2026-07-24, §C1 resolved — no longer inferred). Tier distribution: **A ×12, B ×5, C ×3.**

---

## C. Schema inconsistencies (non-blocking) — ✅ ALL RESOLVED 2026-07-24

**C1 — U001/U002 lacked `priority_tier` frontmatter (and YAML frontmatter block). RESOLVED.**
`U001_patentmatch_digest.md` and `U002_prior_art_search_reranking_digest.md` originally used an older body-only digest format (no `---` YAML block; no `priority_tier:` field), while U003–U020 carried full YAML frontmatter. **Fix applied:** both files now have complete YAML frontmatter matching the U003–U020 schema exactly (`unique_id`, `priority_tier: A`, `sha256`, `canonical_path`, `size_bytes`, `title`, `authors`, `year`, `venue`, `doi`, `arxiv`, `extraction_cache`, `experience_brain_match`, `matched_knowledge_id`, `recommended_ingestion_action: ingest_new`, `digest_status: completed`, `digest_prepared: 2026-07-24`, `pass_type`, `authority: External Knowledge`). A targeted content audit against `extraction-cache/U001.md` and `extraction-cache/U002.md` during this same pass confirmed the digest **bodies** were already factually correct (see stabilization report §content-audit) — only the missing frontmatter needed adding, plus one arXiv-ID typo fixed in U002 (`2009.01932`→`2009.09132`).

**C2 — Duplicate legacy digest file for U001. RESOLVED.**
Two files existed: `U001_patentmatch_dataset.md` (legacy, unindexed) and `U001_patentmatch_digest.md` (canonical, index-referenced). The index always pointed only to `_digest.md`, so there was never a double-count. **Fix applied:** the legacy `_dataset.md` file — which was found on audit to contain incorrect figures ("87 applications" / "176 claims", unsupported MAP/Precision/Recall metrics, wrong venue) that conflict with the canonical digest's correct dataset stats — was moved (not deleted) to `digests/archive/U001_patentmatch_dataset.md` with an archived-status notice and inline superseded-figure annotations. It is explicitly excluded from all counts.

**C3 — Benign terminology split in `recommended_ingestion_action` vocabulary. RESOLVED.**
U001–U008 previously used `create_new`; U009–U020 used `ingest_new`/`link_existing`. Same meaning (add as new external Knowledge record) but inconsistent vocabulary. **Fix applied:** all `create_new` occurrences across canonical digest frontmatter/body text, `PDF_DIGEST_INDEX.md`, `BATCH_1_INGESTION_CANDIDATES.csv`, and this report were normalized to `ingest_new`. The 4 `link_existing` records and their Knowledge IDs were left unchanged.

---

## D. Stale Paper-D claim audit (check #5)

Searched all digests for the prohibited current-Paper-D numerics: `n=997`, `n=724`, primary OUT nDCG@100, optimized=generic, delta 0.0000, W/L/T 0/0/724, Holm p=1.0000, oracle diagnostic n=905, oracle headroom +0.1377, OUT Recall@100 ≈0.1655.

**Result: ✅ CLEAN.** None is asserted as a Batch-1 result. The only occurrences are **guardrail sentences** in U004/U005/U006/U007 explicitly warning *against* cross-comparing a paper's own (classification) metric to DAPFAM OUT Recall@100 ≈0.1655 — e.g. U005: "54% accuracy / F1>66% is multi-label CPC classification, NOT retrieval Recall@100 — do not cross-compare." U001 notes only that it "does not report oracle reordering gains." These preserve the citation-vs-measurement boundary rather than restating frozen Paper-D evidence.

---

## E. Unresolved visual-check flags (by paper ID)

Table/figure grids lost structure in PDF→text extraction. In every case the **prose-quoted numbers are reliable**; the flag means "open the PDF before citing precise table cells."

| ID | Visual-check flag | Affects main claims? |
|----|-------------------|----------------------|
| U004 | Table 1 (precision/recall/F1/loss) columns re-ordered; trust in-text recall 94.29% / 86.11% only | No |
| U005 | Table 3 CS-score column overlap; trust in-text cosine ≈0.92 | No |
| U006 | Slide deck — only headline deltas (+5.56% MAP etc.), no tables/CIs; use U069 journal follow-up for rigor | No |
| U007 | Tables 7–8 columns stacked vertically; RFR prose values reliable, grid needs PDF | No |
| U008 | Table 2/3 de-gridded; row-order mapped + prose cross-checked | No |
| U009 | Table 2/3 de-gridded; row-order mapped + prose cross-checked | No |
| U010 | Table 3 (En/Zh/Avg) de-gridded; ⚠️ PatentMatch **name collision** (Zuo MCQ ≠ U008 Risch pairs) — do not conflate | No (naming caution) |
| U017 | Table 3 (applicant counts) columns shifted; don't quote per-applicant numbers | No |
| U018 | No headline IR metric; related-work 2.75M/0.8M patents belong to *cited* work — do not misattribute | No |
| U019 | Results table fragmented; in-text 73.88%/69.89% are **baselines**, NOT PatentBERT's own F1@1 | No (attribution caution) |

**All 10 flags are cell-precision/attribution cautions. None invalidates a paper's main claim.** No paper is blocked.

---

## F. Ingestion-action separation (check #11)

**link_existing (already in Experience Brain — do NOT re-ingest PDF; attach digest as analytical layer) — 4 papers:**
- U009 → KNO-92F3E83D2CBF (PAECTER)
- U011 → KNO-384DFF3E3AC0 (DAPFAM)
- U012 → KNO-528A290EA2E4 (PatenTEB)
- U014 → KNO-E0520C4384CF (Rethinking Patent Retrieval w/ LMs)

**ingest_new (not in EB by SHA or title — add as new external Knowledge) — 16 papers:**
- U001, U002, U003, U004, U005, U006, U007, U008, U010, U013, U015, U016, U017, U018, U019, U020

---

## G. Duplicate-of provenance (check #2 detail)

Manifest carries 24 rows matching the U001–U020 IDs = **20 canonical + 4 `duplicate-of`**. Each duplicate shares its canonical's SHA-256 and is a different filesystem path; **none was digested as a separate unique paper**:

| ID | Canonical path | Duplicate (alt) path | Same SHA |
|----|----------------|----------------------|----------|
| U011 | is1/pdfs/11_dapfam… | is1/dapfam-pdfs/01_a_domain_aware_family… | 384dff3e3a ✅ |
| U012 | is1/pdfs/12_patenteb… | is1/dapfam-pdfs/02_a_comprehensive_benchmark… | 528a290ea2 ✅ |
| U013 | is1/pdfs/13_patent_representation… | shared/pdfs/42_section_based_patent_summarization… | 39aacd435c ✅ |
| U016 | is1/pdfs/16_bmretriever… | shared/pdfs/10_bmretriever… | 8107e65643 ✅ |

---

## H. Governance compliance

- ✅ Source repo `thaipha-lex` **unmodified** (writes confined to review workspace `source-packet/03-priority-papers/`).
- ✅ Experience Brain **READ-ONLY** — narrow SHA→title lookups (≤3 records), no create/update/delete.
- ✅ No web search, no Hyperresearch, no deep-research, no Obsidian Mind, no protected-qrels access, no experiments/GPU/commits/pushes.
- ✅ Citation-based relevance never framed as legal validity, infringement, claim equivalence, invalidity, novelty determination, or FTO clearance (checked per-digest; §check-9).
- ✅ Papers A/B/C = pilot provenance; Paper D = frozen; Track C/R = proposed/unauthorized; Track S = revision-stage/execution-closed.

---

## I. Cumulative progress

- **Batch 1: 20 / 20 ✅ complete.**
- **Corpus: 20 / 150 unique** (≈13%).
- **Next undigested: U021** (Batch 2 — not started; not initiated per instruction).

---
*QA pass performed 2026-07-24 via index/frontmatter/targeted checks only. No PDF re-reads. Companion manifest: `BATCH_1_INGESTION_CANDIDATES.csv`.*

