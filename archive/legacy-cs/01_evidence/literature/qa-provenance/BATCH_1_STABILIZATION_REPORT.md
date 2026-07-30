# Batch 1 Stabilization Report — U001–U020

**Prepared:** 2026-07-24 · **Scope:** Post-QA stabilization pass over Batch 1 (U001–U020) artifacts only.
**Method:** Targeted content audit vs. extraction caches + schema normalization. No PDFs re-read. No new PDFs digested. U021 not started.
**Authority:** Review-workspace artifact. Source repo `thaipha-lex` unmodified. Experience Brain queried READ-ONLY only where already recorded in prior digests; zero writes this pass.

---

## 1. U001 content audit — result: no factual correction needed to the canonical digest

The canonical, index-referenced `digests/U001_patentmatch_digest.md` was checked against `extraction-cache/U001.md` for all figures flagged by the task: 6,259,703 total samples; 3,492,987 X-doc; 2,766,716 A-doc; 31,238 applications; 33,195 cited docs; 297,147 claim texts; 520,376 cited paragraphs; 347,880 balanced-variation samples; 25,340 one-X/one-A variation; 54%/52% BERT accuracies. **All matched exactly** — the canonical digest body required no numeric correction.

The conflicting figures named in the task ("87 applications", "176 claims") were found, but in a **separate, non-canonical legacy file** — `digests/U001_patentmatch_dataset.md` — not in the canonical digest. That legacy file also carried unsupported MAP/Precision/Recall metrics and a wrong venue ("SIGIR 2020 Workshop" vs. the correct arXiv:2012.13919 preprint). It was never index-referenced and never counted as a separate unique paper, so it did not corrupt Batch 1 totals. Disposition: archived per §4 below with inline superseded-figure annotations rather than corrected in place, since it is being retired, not kept active.

**Only change made to the canonical U001 digest:** YAML frontmatter added (§3). No body text altered.

## 2. U002 content audit — result: one non-substantive typo fixed; no factual correction needed

The canonical `digests/U002_prior_art_search_reranking_digest.md` was checked against `extraction-cache/U002.md` for all seven characterization points flagged by the task: GPT-2-generated input; BM25 first-stage retrieval; BERT-embedding + cosine-similarity reranking; proof-of-concept/qualitative evaluation; mixed non-benchmark-superiority results; embedding-only false positives; long-span semantic-similarity difficulty. **All seven matched the source correctly** — no substantive correction needed.

One typo was found and fixed: the Bibliographic Identity section cited the arXiv ID as `2009.01932v2`; the correct ID (confirmed against the extraction-cache header, "arXiv:2009.09132v2 [cs.CL] 18 Jul 2021") is `2009.09132v2`. Corrected in place.

**Changes made to the canonical U002 digest:** (a) arXiv-ID typo fixed, (b) YAML frontmatter added (§3).

## 3. Files created / updated / moved / archived

**Created:**
- `source-packet/03-priority-papers/PDF_DIGEST_SCHEMA_V1.md` — 16-section schema definition (TASK 6).
- `source-packet/03-priority-papers/digests/archive/U001_patentmatch_dataset.md` — archived legacy digest with superseded-status notice.
- `source-packet/03-priority-papers/BATCH_1_STABILIZATION_REPORT.md` — this report.

**Updated:**
- `digests/U001_patentmatch_digest.md` — YAML frontmatter added; `create_new`→`ingest_new` in body.
- `digests/U002_prior_art_search_reranking_digest.md` — YAML frontmatter added; arXiv-ID typo fixed; `create_new`→`ingest_new` in body.
- `digests/U003_ai_patent_prior_art_digest.md` through `U008_searchformer_siamese_digest.md` (6 files) — `create_new`→`ingest_new` in frontmatter + body.
- `PDF_DIGEST_INDEX.md` — per-row stabilization notes added for U001/U002; footer stabilization-pass note added.
- `BATCH_1_INGESTION_CANDIDATES.csv` — full rewrite: `create_new`→`ingest_new` for U001–U008; U001/U002 `reason` column updated to reflect content-audit + frontmatter status.
- `BATCH_1_QA_REPORT.md` — verdict header, completeness-matrix row 3, per-paper table (U001–U008 Action column, tier column), §C (all 3 items marked resolved with fix descriptions), §F heading, tier-distribution footnote.

**Moved (not deleted):**
- `digests/U001_patentmatch_dataset.md` → `digests/archive/U001_patentmatch_dataset.md`.

**Not modified:** U009–U020 digest bodies (already `ingest_new`/`link_existing`); the 4 `link_existing` records/Knowledge IDs; any file in the source repository `thaipha-lex`.

## 4. Final schema version and status

`PDF_DIGEST_SCHEMA_V1.md` — version 1, established 2026-07-24. Applies retroactively to U001–U020 (now conformant) and prospectively to Batch 2 (U021 onward).

## 5. Final counts

- **Canonical unique papers:** 20 / 20.
- **link_existing:** 4 (U009 → KNO-92F3E83D2CBF; U011 → KNO-384DFF3E3AC0; U012 → KNO-528A290EA2E4; U014 → KNO-E0520C4384CF) — unchanged.
- **ingest_new:** 16 (U001, U002, U003, U004, U005, U006, U007, U008, U010, U013, U015, U016, U017, U018, U019, U020).
- **create_new remaining in active fields:** 0 (verified by grep; two remaining textual mentions are historical narrative describing the now-resolved inconsistency, not live field values).
- **Eligible for ingestion:** 16 (all `ingest_new` records); the 4 `link_existing` records are correctly marked not-separately-eligible (already in Experience Brain).
- **Remaining schema inconsistencies:** 0 (all 3 logged in the original QA report §C — C1 frontmatter, C2 duplicate digest, C3 terminology split — resolved this pass).

## 6. Archived duplicate path

`source-packet/03-priority-papers/digests/archive/U001_patentmatch_dataset.md` (superseded; shares SHA-256 `68dbc32b1cf5c86af2b0cf13da395c951387d4a038da14d1b928cd35f6a60583` with the canonical `U001_patentmatch_digest.md`; not counted in any Batch 1 total; contains inline annotations flagging its incorrect "87 applications"/"176 claims"/metrics figures as superseded and not to be cited).

## 7. Remaining visual-check cautions and blockers

- **Cautions (non-blocking, unchanged from original QA §E):** 10 flags across U004, U005, U006, U007, U008, U009, U010, U017, U018, U019 — all cell-precision/attribution cautions on damaged table grids; none affects a paper's main claim; none required action this pass.
- **Blockers:** none. No paper in Batch 1 is ineligible for ingestion.

## 8. Experience Brain and scope confirmation

- Experience Brain was not written to at any point in this stabilization pass — no create/update/delete calls were issued. Existing `matched_knowledge_id` values for the 4 `link_existing` records were read from existing digest content only, not re-queried.
- U021 was not started — no digest, no extraction cache, no index row, no candidate-CSV row was created for U021 or any Batch 2 paper.
- No PDFs were re-read in full; content audits used `extraction-cache/U001.md` and `extraction-cache/U002.md` plus targeted digest sections only.
- The source repository `thaipha-lex` was not modified (one read-only directory listing was taken to confirm this, no writes).
- No Experience Brain ingestion, Obsidian Mind setup, deep-research, web search, Hyperresearch invocation, experiments, GPU/paid services, or git operations were performed.

---

## Validation checklist (all confirmed before stopping)

1. ✅ Every changed Markdown file parses as readable text (spot-checked via Read/grep after each edit; no malformed syntax).
2. ✅ Every CSV row has the same column count — verified via Python `csv` module: all 21 rows (1 header + 20 data) have exactly 12 columns.
3. ✅ U001/U002 YAML frontmatter blocks are syntactically consistent with U003–U020 (same field set, same `---` delimiters, same quoting/null conventions) — verified via side-by-side `awk` extraction.
4. ✅ No two active digests represent U001 — `digests/` now contains exactly one U001 file (`U001_patentmatch_digest.md`); the legacy duplicate lives only under `digests/archive/`.
5. ✅ No `create_new` value remains in active Batch 1 artifacts — verified via recursive grep; the only 2 remaining textual matches are historical-narrative sentences describing the resolved inconsistency, not live field values.
6. ✅ The four `link_existing` Knowledge IDs are unchanged (KNO-92F3E83D2CBF, KNO-384DFF3E3AC0, KNO-528A290EA2E4, KNO-E0520C4384CF).
7. ✅ No source-repository (`thaipha-lex`) file was modified.
8. ✅ U021 has no digest, no cache, no index status, no candidate-CSV row — confirmed via grep; only "not started" references exist.

---
*Stabilization pass performed 2026-07-24. Stop condition reached — no further action taken pending owner review.*
