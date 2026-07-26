# Canonical Repo Stray Digest Audit

**Audit date:** 2026-07-25
**Scope:** Read-only inspection of untracked files in the canonical (read-only) repo `C:\Users\Siripon Sri\Desktop\My Project\thaipha-lex\source-packet\03-priority-papers\digests\`
**Authority:** This audit performs NO writes to the canonical repo. All actions below are proposals only, pending explicit owner approval.

## Finding

`git status --porcelain` in the canonical repo shows:

```
?? source-packet/03-priority-papers/digests/
```

The entire `digests/` directory is untracked in the canonical repo. Four files overlap in name with Batch 2A digests produced in this review workspace:

- `U026_medcpt_biomedical_ir_pubmed_logs_digest.md`
- `U027_graph_transformer_patent_search_digest.md`
- `U028_contrastive_rag_fewshot_patent_classification_digest.md`
- `U029_clef_ip_2011_retrieval_digest.md`

## Byte-Identity Verification

SHA-256 computed independently for each stray file in the canonical repo and compared against the corresponding file in the review workspace (`source-packet/03-priority-papers/digests/`):

| File | Canonical-repo SHA-256 | Workspace SHA-256 | Match |
|---|---|---|---|
| U026_medcpt_biomedical_ir_pubmed_logs_digest.md | `8fe089754998832219af5860cd13dffc3f49247455cf98e1de32eb9b34c82b9b` | `8fe089754998832219af5860cd13dffc3f49247455cf98e1de32eb9b34c82b9b` | ✅ identical |
| U027_graph_transformer_patent_search_digest.md | `30cd78c46f37f0f6a2eda80150d0e186cf489ffcc2cc116e076ab4a2b7842d36` | `30cd78c46f37f0f6a2eda80150d0e186cf489ffcc2cc116e076ab4a2b7842d36` | ✅ identical |
| U028_contrastive_rag_fewshot_patent_classification_digest.md | `76885c0d9492be2d3db79d922e501e712fa71b04b254a5c0cd68fd19012438c2` | `76885c0d9492be2d3db79d922e501e712fa71b04b254a5c0cd68fd19012438c2` | ✅ identical |
| U029_clef_ip_2011_retrieval_digest.md | `3504e3b0c0b373732cf8dbe373e427737eabaf70486190b799f166be99eb1e7b` | `3504e3b0c0b373732cf8dbe373e427737eabaf70486190b799f166be99eb1e7b` | ✅ identical |

## Classification

All 4 stray files: **byte_identical**. Each is a verbatim, unmodified copy of the corresponding review-workspace digest. There is no divergence, no partial edit, no stale/superseded content risk — these are exact duplicates, not conflicting versions.

## Root Cause (inferred, not verified against tool logs)

These 4 files most likely originated from an earlier Batch 2A digest-authoring pass that wrote output directly under the canonical repo path before the review-workspace-only convention was established or enforced for this remediation task. Because they are untracked (`??`) and byte-identical to the current workspace copies, they appear to be an artifact of that earlier session rather than an intentional canonical-repo contribution.

## Proposed Cleanup Actions (NOT EXECUTED — owner approval required)

Since the canonical repo is read-only for this task, no deletion, edit, or git operation was performed. Recommended options for the owner to choose from:

1. **Delete the 4 untracked stray files** from the canonical repo (`git clean` scoped to `source-packet/03-priority-papers/digests/` or manual `rm`), since they are exact duplicates already safely present in the review workspace and were never committed.
2. **Leave them in place** if the owner intends the canonical repo's `digests/` directory to eventually house the authoritative copies (would require a separate, explicitly authorized canonical-repo write/commit action outside this task's scope).
3. **No action** until the owner reviews this audit.

This task recommends option 1 (safe deletion) given byte-identical status and untracked git state, but takes no action pending explicit authorization.

## Directory Completeness Check

A directory listing of the canonical repo's `source-packet/03-priority-papers/digests/` folder was taken (read-only `ls`) and confirms it contains **exactly these 4 files** — no additional untracked stray digests exist beyond U026-U029. The audit scope is therefore complete for this directory.
