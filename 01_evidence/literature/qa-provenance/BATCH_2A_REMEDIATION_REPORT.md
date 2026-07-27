# Batch 2A Artifact Remediation Report

**Scope:** U021–U040 only. **Date:** 2026-07-25. **Authority:** Owner-authorized artifact-remediation pass (execution boundary respected — see §9).

---

## 1. Problem statement

Batch 2A's original digestion pass (U021–U040) completed all 20 papers, but the persistent extraction-cache protocol was not followed consistently: only U021–U023 had real files under `extraction-cache/`. U024–U028 pointed at transient tool-call artifacts (`tool-results/*.json`, a markdownify temp file, a placeholder string); U029–U040 described "inline extraction" with no file at all. Separately, 4 untracked digest files (U026–U029) were found in the canonical (read-only) repo, and the original `BATCH_2A_INGESTION_CANDIDATES.csv` had 5 stale `digest_path` values and was built via string concatenation rather than a real CSV writer.

## 2. Cache counts, before/after

| State | Persistent caches present | Missing |
|---|---|---|
| Before remediation | 3 (U021, U022, U023) | 17 |
| After remediation | 20 (U021–U040) | 0 |

## 3. Backfilled IDs

U024, U025, U026, U027, U028, U029, U030, U031, U032, U033, U034, U035, U036, U037, U038, U039, U040 (17 total) — each regenerated via `_extract_cache.py extract`, each SHA-256-verified against the manifest, each confirmed idempotent (re-run reports `CACHE_HIT`).

## 4. Digest verification outcome

All 20 papers targeted-verified against their new persistent caches. Outcome tally:

| Classification | Count | IDs |
|---|---|---|
| verified_no_change | 20 | U021–U040 (all) |
| corrected_minor | 0 | — |
| corrected_substantive | 0 | — |
| hold_conflict | 0 | — |

No factual conflict was found between any digest's claims and its underlying cache/PDF text. One structural gap was fixed (not a factual correction): U026's digest had no YAML frontmatter block at all; a full frontmatter block was added, and one inline placeholder (`**PDF SHA-256:** \`[To be computed from cache file]\``) was filled in with the verified SHA-256.

## 5. CSV repair and validation

Original CSV had 20 rows with 5 stale `digest_path` values (U031–U035 pointed at filenames that don't exist on disk) and unnormalized `cache_path` values. During repair, a first script attempt corrupted the file to 12 rows via a `csv.DictWriter` failure; this was caught (via `wc -l` + raw `csv.reader` inspection) and fixed by a full from-scratch reconstruction using `csv.DictWriter`, with `cache_path` normalized to `extraction-cache/U0XX.md` and `digest_path` corrected for U031–U035.

**Corrected digest_path mismatches:**

| ID | Stale (original CSV) | Corrected (actual filename) |
|---|---|---|
| U031 | `digests/U031_report_clef_ip_2011_digest.md` | `digests/U031_clef_ip_2011_pattextiling_digest.md` |
| U032 | `digests/U032_comparative_embedding_models_digest.md` | `digests/U032_embedding_models_patent_similarity_digest.md` |
| U033 | `digests/U033_survey_automated_ai_patent_digest.md` | `digests/U033_survey_automated_ai_patent_retrieval_digest.md` |
| U034 | `digests/U034_survey_patent_analysis_digest.md` | `digests/U034_survey_patent_analysis_nlp_multimodal_digest.md` |
| U035 | `digests/U035_beir_benchmark_digest.md` | `digests/U035_beir_heterogeneous_benchmark_digest.md` |

**CSV parser result:** `BATCH_2A_CSV_VALIDATION.json` — 11/11 checks pass, 0 issues, `overall_pass: true`.

## 6. Checkpoint and index normalization

`BATCH_2A_CHECKPOINT.md`'s artifact-tracking table and `PDF_DIGEST_INDEX.md`'s per-paper `[cache: ...]` annotations were rewritten to reference only `extraction-cache/U0XX.md` for all 20 papers. Both files retain a "Historical Remediation Note" / "Batch 2A remediation pass" paragraph documenting the prior state and what changed, rather than silently erasing the history.

## 7. Filesystem-backed artifact validator

`validate_batch_2a_artifacts.py` (new script) checks: persistent-cache existence/count/no-extras/non-empty, digest existence/count/no-duplicates/every-ID-covered, frontmatter `extraction_cache` normalization, absence of active stale references in digests/checkpoint/index (historical narrative exempted), CSV structural validity, SHA-256 uniqueness across IDs, and the U041 hard-stop boundary.

**Result:** `BATCH_2A_ARTIFACT_VALIDATION.json` — 13/13 checks pass, 0 issues, `overall_pass: true`.

## 8. Stray canonical-repo file audit

4 untracked files in the read-only canonical repo (`U026`–`U029` digests, confirmed via `git status --porcelain` → `?? source-packet/03-priority-papers/digests/`) were SHA-256-compared against their workspace counterparts. **Classification: byte_identical, all 4.** A directory listing confirms no other untracked files exist in that directory. Full detail: `CANONICAL_REPO_STRAY_DIGEST_AUDIT.md`. Proposed cleanup (deletion of the 4 duplicates) is documented but **not executed** — pending owner authorization, since the canonical repo is read-only for this task.

## 9. Governance / write confirmations

| Constraint | Status |
|---|---|
| Experience Brain writes | **0** — no `record_event`/`save_knowledge_digest`/`record_outcome_feedback`/`process_inbox` calls made during remediation |
| Obsidian writes | **0** — no Obsidian tool invoked |
| Canonical-repo writes | **0** — canonical repo accessed read-only throughout (directory listing + SHA computation only) |
| Subagents / parallel work | **0** — all work performed directly, sequentially |
| Web search / deep research | **0** — none performed |
| Track C/R/S execution | **0** — no track work executed; all digest Track sections remain labeled "proposed, NOT AUTHORIZED" |
| Experiments / GPU / commits / pushes | **0** — none performed |
| U041+ started | **No** — confirmed via validator check `u041_not_started: true` |

## 10. Files created or modified in this remediation

**Created:**
- `BATCH_2A_PRE_REMEDIATION_INVENTORY.md`
- `extraction-cache/U024.md` … `U040.md` (17 files)
- `CANONICAL_REPO_STRAY_DIGEST_AUDIT.md`
- `validate_batch_2a_artifacts.py`
- `BATCH_2A_ARTIFACT_VALIDATION.json`
- `BATCH_2A_CSV_VALIDATION.json`
- `BATCH_2A_REMEDIATION_REPORT.md` (this file)

**Modified:**
- 20 digest files under `digests/` (frontmatter `extraction_cache` field normalized; U026 given a full new frontmatter block + SHA placeholder filled in)
- `BATCH_2A_INGESTION_CANDIDATES.csv` (rebuilt: 5 digest_path corrections, cache_path normalization)
- `BATCH_2A_CHECKPOINT.md` (artifact-tracking table cache-path column normalized, historical note added)
- `PDF_DIGEST_INDEX.md` (per-paper `[cache: ...]` annotations normalized, historical note added)
- `BATCH_2A_QA_REPORT.md` (post-remediation sections + corrected verdict appended; original content preserved for audit trail)

## 11. Final verdict

**PASS AFTER REMEDIATION.**

All 20 papers (U021–U040) now have real, SHA-verified, persistent extraction caches. All digest/checkpoint/index/CSV cross-references are normalized and independently validated by two filesystem-backed scripts with zero outstanding issues (13/13 and 11/11 checks respectively). No digest content required a factual correction. The canonical repo was never written to. All governance boundaries held throughout. The only open item — cleanup of 4 confirmed-duplicate stray files in the canonical repo — is a proposal awaiting separate owner approval and does not affect this workspace's artifact correctness.

**Next undigested ID:** U041 (not started, not authorized in this task).
