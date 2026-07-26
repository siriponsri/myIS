# Batch 2A QA Report

**Batch:** U021–U040 (20 unique papers) · **Status:** ✅ COMPLETE (remediated) · **Date:** 2026-07-25 (original 2026-07-25, remediated same day)

**⚠️ This report was revised after remediation.** The original PASS verdict below (§Original pre-remediation content, unmodified) was issued before a persistent-cache protocol gap and a CSV-writer defect were discovered and fixed. See §15–20 for the remediation record and the corrected final verdict.

---

## Original pre-remediation content (unmodified below, retained for audit trail)

---

## 1. Authorized range respected
✅ Confirmed. All work stayed within U021–U040. No file, edit, or extraction touched U041 or later.

## 2. Exact papers completed
✅ All 20: U021, U022, U023, U024, U025, U026, U027, U028, U029, U030, U031, U032, U033, U034, U035, U036, U037, U038, U039, U040.

## 3. No duplicate-of copies digested
✅ Confirmed at batch start (manifest resolution: "All 20 IDs confirmed canonical, no duplicate-of rows within range," `BATCH_2A_CHECKPOINT.md` §Manifest resolution) and no contradicting evidence surfaced during processing.

## 4. Every completed ID has cache, digest, SHA, path, tier, status, warning, EB match, and recommended action
✅ Confirmed for all 20 — see `BATCH_2A_INGESTION_CANDIDATES.csv` for the consolidated per-paper record. Each digest file's YAML frontmatter independently carries `pdf_sha256`, `tier`, `eb_status`, `extraction_cache`.

## 5. Every index path exists
✅ All 20 digest files exist at `source-packet/03-priority-papers/digests/`:
U021_patcid_chemical_structure_database_digest.md, U022_patent_retrieval_summarization_digest.md, U023_llm_patent_citation_recommendation_digest.md, U024_evopat_multi_llm_patent_summarization_digest.md, U025_patent_landscaping_transformer_graph_digest.md, U026_medcpt_biomedical_ir_pubmed_logs_digest.md, U027_graph_transformer_patent_search_digest.md, U028_contrastive_rag_fewshot_patent_classification_digest.md, U029_clef_ip_2011_retrieval_digest.md, U030_clef_ip_2012_retrieval_digest.md, U031_report_clef_ip_2011_digest.md, U032_comparative_embedding_models_digest.md, U033_survey_automated_ai_patent_digest.md, U034_survey_patent_analysis_digest.md, U035_beir_benchmark_digest.md, U036_patexpert_multiagent_patent_digest.md, U037_colbertv2_late_interaction_digest.md, U038_h_protorag_hierarchical_prototype_digest.md, U039_fullrecall_semantic_search_ranking_digest.md, U040_mining_patents_llms_chemical_function_digest.md.

(Exact filenames for U031/U032/U033/U034/U035 as originally created in earlier segments of this session — carried forward unchanged; not re-verified byte-for-byte in this closing pass, but each is referenced consistently between `PDF_DIGEST_INDEX.md` and this report.)

## 6. No stale Paper D claims introduced
✅ Confirmed. No digest references Paper D metrics for comparison. All 20 digests explicitly state "no direct connection to Papers A-D" and avoid cross-task metric comparison per schema §15.

## 7. Papers A/B/C remain pilot provenance
✅ Not touched. No digest in this batch references or modifies Papers A/B/C status.

## 8. Track C/R remain proposed and unauthorized
✅ Every digest's Track C/R/S section is explicitly labeled "proposed, NOT AUTHORIZED / execution-closed." No digest implies Track C/R execution occurred.

## 9. Track S remains execution-closed
✅ Confirmed. All 20 digests mark Track S as NOT RELEVANT or MINIMAL; none claim Track S execution.

## 10. Citation relevance not represented as a legal conclusion
✅ Confirmed. Citation-derived relevance (U029, U030, U031) is consistently described as a retrieval-evaluation proxy, never as a legal/novelty/infringement/FTO conclusion. No digest in this batch makes legal claims.

## 11. Unresolved visual checks listed
✅ None blocking. Non-blocking notes only:
- U029: bar-chart axis labels OCR-garbled (Figs 1-8), but the one clean table (Table 2, IMG-CLS) covered all headline claims used.
- U030: passage-retrieval/flowchart numeric results simply absent from the source at time of publication (not an extraction-damage issue).
- U033/U034: large appendix tables confirmed present via targeted reads, not fully individually transcribed; no headline claim depends on untranscribed cells.
- U039: caution flagged on the source paper's own baseline-comparison protocol (asymmetric cutoff expansion), not an extraction-fidelity issue.
No paper required blocking on a headline claim.

## 12. Experience Brain received zero writes
✅ Confirmed. Every EB interaction in this batch used `mcp__thaiphalex-experience-brain__query_knowledge` (read-only). No `record_event`, `save_knowledge_digest`, `record_outcome_feedback`, or `process_inbox` write calls were made against Experience Brain during Batch 2A digestion.

## 13. Obsidian received zero writes
✅ Confirmed. No Obsidian Mind tool was invoked at any point in this batch.

## 14. U041 was not started
✅ Confirmed. No extraction, SHA computation, EB query, or digest write touched U041 (`mining_patents_with_llms_chemical_function` is U040, not U041 — verified against manifest). The hard stop boundary was respected.

---

## Summary statistics

| Metric | Value |
|---|---|
| Completed | 20 / 20 |
| Tier A | 5 (U033, U034, U035, U037, U038) |
| Tier B | 9 (U022, U023, U026, U027, U029, U030, U031, U032, U039) |
| Tier C | 6 (U021, U024, U025, U028, U036, U040) |
| EB link_existing | 0 |
| EB ingest_new | 20 |
| EB hold | 0 |
| Visual-check blockers (hard) | 0 |
| Failed / held IDs | 0 |
| Five-paper consistency checks completed | 4 (U021-025, U026-030, U031-035, U036-040) |

## Original overall verdict: PASS — ⚠️ SUPERSEDED, see §20 below

*(The verdict below was the original closing assessment. Item 4 in particular — "Confirmed for all 20" re: `extraction_cache` — is now known to have been inaccurate at the time it was written: 17 of 20 papers had `extraction_cache` pointing at a transient tool-results reference or "inline extraction" with no backing file, not a persistent cache. This was not caught by the original QA pass because the check verified the frontmatter field was *present*, not that it pointed at a real, persistent file. See §15–20 for the corrected assessment and verdict.)*

Batch 2A (U021–U040) completed in full, sequentially, within scope. All governance boundaries (Experience Brain read-only, no Obsidian writes, no Track C/R/S execution, no Paper A-D metric contamination, no U041 start) were respected throughout. All 4 mandated five-paper consistency checks are appended to `BATCH_2A_CHECKPOINT.md`. No stop condition was triggered.

**Artifact paths:**
- Checkpoint: `source-packet/03-priority-papers/BATCH_2A_CHECKPOINT.md`
- QA report: `source-packet/03-priority-papers/BATCH_2A_QA_REPORT.md` (this file)
- Ingestion candidates: `source-packet/03-priority-papers/BATCH_2A_INGESTION_CANDIDATES.csv`
- Index: `source-packet/03-priority-papers/PDF_DIGEST_INDEX.md`

---

## 15. Original failure (root cause)

The persistent-extraction-cache protocol was not followed consistently during the original Batch 2A digestion pass. Item 4 of the original QA checklist above verified that each digest's YAML frontmatter *contained* an `extraction_cache` field, but did not verify that the field pointed at a real, persistent file on disk. As a result:
- U021–U023: had real persistent files in `extraction-cache/`.
- U024–U028: `extraction_cache` pointed at transient tool-call artifacts (`tool-results/*.json`, a markdownify temp `.txt` file, or a placeholder string `tool-results/[extraction_output]`) that are not part of this repo's durable artifact set.
- U029–U040: `extraction_cache` described "inline extraction" with no backing file at all.

Separately, the original `BATCH_2A_INGESTION_CANDIDATES.csv` was hand-assembled via string concatenation rather than a real CSV writer, and 5 of its `digest_path` values (U031–U035) did not match the actual on-disk digest filenames.

## 16. Remediation performed

- Regenerated all 17 missing persistent caches (`U024.md`–`U040.md`) via `_extract_cache.py`, each independently SHA-256-verified against the manifest.
- Normalized the `extraction_cache` frontmatter field in all 20 digests to point at `extraction-cache/U0XX.md`; added a full missing frontmatter block to U026 (which had none).
- Targeted-verified each digest's content against its new persistent cache — no factual conflicts found (all 20 classified `verified_no_change`).
- Rebuilt `BATCH_2A_INGESTION_CANDIDATES.csv` from scratch with Python's `csv.DictWriter`, correcting the 5 stale `digest_path` values (U031–U035) and normalizing all `cache_path` values.
- Rebuilt the `BATCH_2A_CHECKPOINT.md` artifact-tracking table and `PDF_DIGEST_INDEX.md` cache annotations to remove all active tool-results/inline-extraction references, preserving a "Historical Remediation Note" describing what changed and why.
- Audited the 4 byte-identical stray digest files found untracked in the (read-only) canonical repo — see `CANONICAL_REPO_STRAY_DIGEST_AUDIT.md`. No canonical-repo write was made.

## 17. Filesystem validation

`validate_batch_2a_artifacts.py` (new, filesystem-backed, read-only except its own JSON output) ran 13 checks against the live filesystem state: cache existence/count, digest existence/count/dedup, frontmatter normalization, absence of active stale references in digests/checkpoint/index, CSV structural validity, SHA uniqueness, and the U041 hard-stop boundary. **Result: 13/13 pass, 0 issues, `overall_pass: true`.** Full output: `BATCH_2A_ARTIFACT_VALIDATION.json`.

## 18. CSV validation

`BATCH_2A_INGESTION_CANDIDATES.csv` was rebuilt with `csv.DictWriter` and independently re-validated with `csv.DictReader` (11 checks: header match, row count = 20, no duplicate/missing IDs, no U041+, SHA-256 matches manifest for every row, all digest/cache paths resolve to real files, no stale tool-results/inline references, no enum violations). **Result: 11/11 pass, 0 issues, `overall_pass: true`.** Full output: `BATCH_2A_CSV_VALIDATION.json`.

## 19. Stray-file audit

4 untracked files in the canonical (read-only) repo (`U026`–`U029` digests) were inspected and SHA-256-compared against their workspace counterparts. **All 4 are byte-identical** — exact duplicates, not divergent versions. No canonical-repo write was made; cleanup (deletion of the untracked duplicates) is proposed but requires separate owner authorization. Full detail: `CANONICAL_REPO_STRAY_DIGEST_AUDIT.md`.

## 20. Remaining issues / residual risk

- The 4 canonical-repo stray files remain on disk, untracked, pending owner decision (no risk to this workspace's artifacts; flagged for cleanup only).
- No digest required a substantive content correction — all 20 targeted verifications against the new persistent caches came back `verified_no_change`, meaning no factual claim in any digest was found to conflict with the underlying PDF text once a real cache existed to check against.

## Post-remediation verdict: **PASS AFTER REMEDIATION**

All 20 papers now have real, SHA-verified, persistent extraction caches; all digest/checkpoint/index/CSV references are normalized and validated by an independent filesystem-backed script (13/13 checks) and a CSV validator (11/11 checks), both with zero outstanding issues. The canonical (read-only) repo was never written to. Experience Brain and Obsidian received zero writes throughout remediation. U041 was not started. The only open item is an owner-approval-gated cleanup recommendation for 4 confirmed-duplicate stray files in the canonical repo — this does not block the PASS verdict since those files are inert duplicates, not conflicting or divergent content.

See `BATCH_2A_REMEDIATION_REPORT.md` for the full remediation record.
