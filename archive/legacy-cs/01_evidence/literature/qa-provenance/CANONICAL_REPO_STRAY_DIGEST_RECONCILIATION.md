# Canonical Repo Stray Digest Reconciliation Report

**Scope:** 4 untracked stray digest files in the canonical repo (U026–U029 digests). **Date:** 2026-07-25. **Authority:** Owner-authorized post-remediation reconciliation and conditional cleanup.

---

## 1. Background

The original stray-file audit (`CANONICAL_REPO_STRAY_DIGEST_AUDIT.md`) found 4 untracked digest files in the canonical repo byte-identical to their workspace counterparts. Batch 2A remediation subsequently modified the workspace copies (frontmatter `extraction_cache` normalization; a full new frontmatter block added to U026; U026's SHA placeholder filled in). This reconciliation determines whether the resulting raw-byte mismatch is remediation-only (metadata/structure) or reflects a substantive factual content divergence, and authorizes deletion of the canonical stray copies only if it is the former.

## 2. Pre-condition checks

- **Task 1 (workspace integrity):** `validate_batch_2a_artifacts.py` re-run — 13/13 checks pass, `overall_pass: true`, 0 issues. U026–U029 workspace digests exist with normalized `extraction_cache` fields. No `U041` artifact exists in either digests/ or extraction-cache/.
- **Task 2 (canonical file status):** All 4 files confirmed present in canonical repo at `source-packet/03-priority-papers/digests/`; each is untracked (`git status --porcelain` → `??`) and unstaged (`git diff --cached --name-only` empty for each path); `git ls-files --error-unmatch` confirms none are tracked.

## 3. Per-file comparison and classification

Raw SHA-256 mismatches for all 4 pairs, as expected post-remediation. CRLF normalization (`tr -d '\r'`) applied to both sides before diffing; normalized SHA equaled raw SHA for all 8 files, confirming no line-ending artifacts — differences are pure content.

| ID | Canonical digest SHA-256 | Workspace digest SHA-256 | Frontmatter diff | Body diff | Classification | Eligible |
|---|---|---|---|---|---|---|
| U026 | `8fe089754998832219af5860cd13dffc3f49247455cf98e1de32eb9b34c82b9b` *(corrected — see §6)* | `2010f8524a2e51c8f406192a4763080b2253c205fdde54f62e8d8e804d25a0c5` | Full YAML frontmatter block added (canonical had none) | One line: `**PDF SHA-256:** \`[To be computed from cache file]\`` → `\`36375d5310c4ebee73a73453aba880a5babdedfe7ec2ca40c83ffed8f662b02f\`` (this is the *source PDF* SHA-256, distinct from the digest-file SHA-256 in the columns above) | Allowed B (frontmatter addition) + Allowed C (SHA placeholder fill-in). No other body change. | Yes |
| U027 | `30cd78c4...b7842d36` | `c3f8b51d...ecb32c7f02` | `extraction_cache: "tool-results/[to_be_filled]"` → `"extraction-cache/U027.md"` | None — identical | Allowed A (extraction_cache path normalization) | Yes |
| U028 | `76885c0d...19012438c2` | `55f8f5cd...ee26c1805562befcc1d47d70ff` | `extraction_cache: "tool-results/mcp-markdownify-pdf-to-markdown-1784933543013.txt"` → `"extraction-cache/U028.md"` | None — identical | Allowed A | Yes |
| U029 | `3504e3b0...799f166be99eb1e7b` | `c10eb5b3...df72d32b3c6a7e491` | `extraction_cache: "[extraction_output, inline, ~13 pages]"` → `"extraction-cache/U029.md"` | None — identical | Allowed A | Yes |

No file contains any change to title/authors/year/venue, research problem/method, datasets/metrics/numeric findings, limitations/warnings, tier/EB recommendation, or any deleted section or new unsupported claim. For U027/U028/U029 the substantive Markdown body is byte-identical after frontmatter-strip and line-ending normalization. For U026 the substantive body is identical except for the single allowed SHA-placeholder replacement.

## 4. Conditional deletion decision

All six required conditions hold for all four files simultaneously:
1. Validator passes (13/13, `overall_pass: true`).
2. All 4 canonical files untracked and unstaged.
3. All observed differences fall within the allowed remediation-only list (A/B/C).
4. No substantive factual body difference in any file.
5. Each workspace copy is confirmed the post-remediation version.
6. No `U041` artifact exists anywhere in scope.

**Decision: DELETE all 4 canonical stray files** — U026, U027, U028, U029 digests at `source-packet/03-priority-papers/digests/` in the canonical repo (`C:\Users\Siripon Sri\Desktop\My Project\thaipha-lex`). No other file touched. No `git clean`, no recursive deletion, no staging/commit/push.

## 5. Post-deletion validation

Deletion executed via exact literal paths (`rm` on the 4 named files only — no `git clean`, no recursive/directory deletion, no other file touched).

- **Canonical paths absent:** confirmed — all 4 files no longer exist at `source-packet/03-priority-papers/digests/` in the canonical repo.
- **Workspace copies intact:** confirmed — all 4 workspace digest files still present and unmodified.
- **`git status --short` (canonical repo) after deletion:**
  ```
   M .codex/config.toml
  ?? research/ref-paper/is1/pdfs/84_skillopt_executive_strategy_for_self_evolving_agent_skills.pdf
  ```
  The 4 deleted files no longer appear (they were untracked, so their removal produces no git-status entry at all — a deletion of a tracked file would show as `D `, but these were never tracked). No new entries introduced.
- **No tracked file modified:** confirmed — the only tracked-file entry (`.codex/config.toml`) is pre-existing and unrelated to this task; it was not opened, edited, restored, staged, or otherwise touched during this reconciliation.
- **No commit/push:** confirmed — no `git add`, `git commit`, or `git push` was executed at any point.
- **Batch 2A validator re-run (workspace):** 13/13 checks pass, 0 issues, `overall_pass: true` — unaffected by the canonical-repo cleanup, as expected since only canonical files were touched.

**Final cleanup status: COMPLETE.** All 4 authorized stray files deleted from the canonical repo; workspace artifacts and Batch 2A validation state unaffected.

## 6. Audit Metadata Correction

**Identified:** 2026-07-25, post-deletion, via owner review.

**The error:** §3 of this report (original version) recorded the canonical-repo U026 digest SHA-256 as `36375d5310c4ebee73a73453aba880a5babdedfe7ec2ca40c83ffed8f662b02f`. That value is the **source PDF's** SHA-256 — the same value that appears in `validate_batch_2a_artifacts.py`'s `MANIFEST_SHA["U026"]`, in the workspace digest's frontmatter `sha256:` field, and (post-remediation) inline in the digest body as the filled-in `PDF SHA-256` line. It is **not** the SHA-256 of the canonical-repo U026 **Markdown digest file** itself.

**Correct values, distinguished:**

| Quantity | Value |
|---|---|
| U026 source PDF SHA-256 (per manifest, workspace frontmatter, filled-in body line) | `36375d5310c4ebee73a73453aba880a5babdedfe7ec2ca40c83ffed8f662b02f` |
| U026 canonical-repo **digest file** SHA-256 (per original `CANONICAL_REPO_STRAY_DIGEST_AUDIT.md`, §Byte-Identity Verification, prior to deletion) | `8fe089754998832219af5860cd13dffc3f49247455cf98e1de32eb9b34c82b9b` |
| U026 workspace **digest file** SHA-256, current | `2010f8524a2e51c8f406192a4763080b2253c205fdde54f62e8d8e804d25a0c5` |

**Root cause:** transcription/labeling error in the reconciliation report the comparison in this report's §3 table for U026 transcribed the source-PDF SHA (which happens to also appear inline in the U026 digest body text, and in the validator's `MANIFEST_SHA` table, both under generic labels like "SHA-256") into the "canonical SHA-256" column, instead of the actual canonical digest-file SHA-256 that had been independently computed and correctly recorded in the prior read-only audit (`CANONICAL_REPO_STRAY_DIGEST_AUDIT.md` line 28: `8fe08975...4c82b9b`). This was a transcription/labeling error in this report, not a re-run of the wrong command against the wrong file — the original audit's own computation (`sha256sum` against the canonical digest file) was correct; only this report's later restatement of that value was wrong. U027, U028, and U029's canonical SHA-256 values in §3 are unaffected — each was independently verified against the corresponding value in the original audit and matches (`30cd78c4...`, `76885c0d...`, `3504e3b0...` respectively, all confirmed consistent between the original audit and this report).

**Does the substantive structured comparison remain valid?** Yes, in full. The corrected canonical digest SHA (`8fe08975...4c82b9b`) still does not match the current workspace digest SHA (`2010f852...4d25a0c5`) — a mismatch was expected and correctly anticipated for U026 regardless of which SHA value was mistakenly transcribed, because the frontmatter-addition and SHA-placeholder-fill-in changes are real content-level edits to the digest file. The actual basis for the deletion decision was never the raw file-SHA comparison (which was always expected to mismatch for all 4 files, per the Request B framing) — it was the **frontmatter/body structural diff and classification** in §3's diff columns, which correctly compared the canonical digest's real body/frontmatter content against the workspace digest's real body/frontmatter content, independent of this SHA transcription error. That diff was generated directly from the canonical and workspace digest files themselves (via `diff -u` on CRLF-normalized copies of the actual files), not from the mistranscribed SHA value. The classification (Allowed B + Allowed C, no other body change) and the resulting eligibility determination for U026 are therefore unaffected and remain correct.

**Conclusion:** This was a reporting/transcription error confined to one table cell in this reconciliation report. It did not affect the comparison logic, the diff evidence, the classification, or the deletion decision for U026 or any other file. No digest, cache, CSV, checkpoint, index, validator, or canonical-repository file was involved in or affected by this error, and none were modified in this correction. The deleted canonical file cannot be and was not reconstructed or restored as part of this correction — the correction is metadata-only, applied to this report.
