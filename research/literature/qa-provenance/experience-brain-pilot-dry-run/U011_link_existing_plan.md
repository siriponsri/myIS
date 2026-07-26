# U011 — link_existing Plan (Zero Experience Brain Writes)

**Status:** Phase 2A dry-run planning artifact only. No Experience Brain write is authorized or performed by this document. Prepared 2026-07-25.

## 1. Mapping

- **Paper:** U011 — "DAPFAM: A Domain-Aware Family-level Dataset to benchmark cross-domain patent retrieval" (Ayaou, Cavallucci, Chibane; INSA Strasbourg ICUBE; arXiv:2506.22141v2).
- **Existing Knowledge record:** `KNO-384DFF3E3AC0`.
- **Proposed operation:** `link_existing` — zero-write. No `append()`, no `review_knowledge()`, no store mutation of any kind.

## 2. Evidence of Match

Exact SHA-256 identity between the digest's declared source hash and the live record's `source_content_hash`:

| Field | U011 digest frontmatter | KNO-384DFF3E3AC0 (live store) |
|---|---|---|
| `sha256` / `source_content_hash` | `384dff3e3ac0fe6d2064572bb0322ef4b059c82fcbd703e680a3b524e7120c27` | `384dff3e3ac0fe6d2064572bb0322ef4b059c82fcbd703e680a3b524e7120c27` |
| Source filename | `11_dapfam_domain_aware_family_level_dataset_2025.pdf` | `11_dapfam_domain_aware_family_level_dataset_2025.pdf` |
| `source_type` | pdf | `pdf` |
| Derived ID check | `KNO-{sha256[:12].upper()}` = `KNO-384DFF3E3AC0` | `KNO-384DFF3E3AC0` |

The SHA-256 match is byte-exact and the deterministic ID derivation (`_knowledge_id()`) independently reproduces the same record ID from the hash. This is the strongest possible match category under this store's duplicate-detection model (§13 of the Ingestion Contract) — it is not a title/DOI/near-duplicate inference, it is the store's own primary key.

Supporting cross-references found in the live store (informative, not required for the match):
- `KNO-20DDBF1D30A0` (candidate-exposure synthesis) lists `KNO-384DFF3E3AC0` among its 10 External Research Knowledge inputs.
- The digest's own frontmatter already declares `experience_brain_match: yes` / `recommended_ingestion_action: link_existing`, consistent with this independent re-verification.

## 3. Exact Read-Only Queries Used

1. Full read of the live store file `C:\Users\Siripon Sri\Desktop\ResearchStores\thaiphalex-is1\data\knowledge.jsonl` (17 records) — no CLI/MCP write path invoked, plain file read.
2. `grep -n "KNO-384DFF3E3AC0"` against that same file to isolate the exact record line.
3. Field-by-field comparison of `source_content_hash`, `source_filename`, `source_type`, and `id` between the digest frontmatter and the isolated record — performed in memory, no store mutation.
4. Prior-session `query_knowledge` (MCP, read-only) calls for DAPFAM / cross-domain patent retrieval topics, which surfaced `KNO-384DFF3E3AC0` and related synthesis records (`KNO-20DDBF1D30A0`, `KNO-5449A7642CF9`, `KNO-3D43C4514725`) as semantic backstop, consistent with the hash-based finding.

No write-capable command (`append`, `capture`, `save_knowledge_digest`, `review_knowledge`) was called at any point.

## 4. Discrepancies

None found. Title, filename, source type, and hash are all consistent. The live record's `title` field stores the raw filename stem (`11_dapfam_domain_aware_family_level_dataset_2025`) rather than the paper's formal title — this is a pre-existing store convention from the original `process_inbox` ingestion (`provenance.source = "process_inbox"`), not a discrepancy introduced by this digest or this plan.

## 5. Proposed Future Obsidian Pointer Representation (NOT EXECUTED)

Obsidian export has no implemented capability in the current `experience_brain` codebase (confirmed in Task 1 revalidation — listed only as "Planned"). If and when that capability exists and is separately authorized, the proposed pointer shape would be a simple cross-reference note linking the digest file path (`source-packet/03-priority-papers/digests/U011_dapfam_digest.md`) to `KNO-384DFF3E3AC0`, without duplicating record content. This plan does not create, stage, or simulate any Obsidian file.

## 6. Confirmation: No Experience Brain Write Required

`link_existing` for U011 is fully satisfied by artifacts that already exist:
- The digest's own frontmatter (`experience_brain_match: yes`, and — per Ingestion Contract §11 convention — a `matched_knowledge_id: KNO-384DFF3E3AC0` pointer already present in the digest).
- The `PDF_DIGEST_INDEX.md` cross-reference (pre-existing).

There is no store primitive that "attaches" this digest to `KNO-384DFF3E3AC0` short of a full `review_knowledge()` revision, and per the Ingestion Contract (§11) and the Phase 2A locked owner decision, that stronger action is explicitly out of scope for routine link_existing bookkeeping. Therefore the correct — and zero-write — action is: do nothing to the store; treat the digest as the analytical layer over the existing record.

## 7. Conditions That Would Invalidate This Match

This link_existing mapping should be re-examined (and not treated as settled) if any of the following becomes true in the future:
- The live record `KNO-384DFF3E3AC0`'s `source_content_hash` changes (only possible via a superseding revision under `review_knowledge`, which is owner-only and Dashboard-only).
- A different PDF with a colliding first-12-hex-character hash prefix is ever ingested (astronomically unlikely given SHA-256, but the derived ID `KNO-{sha256[:12].upper()}` only uses the first 12 hex characters, not the full 64-character hash — a theoretical collision surface worth naming for completeness).
- The digest's own frontmatter is later edited to change `sha256` or `canonical_path` in a way that no longer matches the original PDF bytes (would indicate the digest itself was corrupted or mis-sourced, not that the EB record is wrong).
- A future audit finds the live record's `source_filename`/`source_type` were altered by an unrelated correction, breaking the field-level agreement documented in §2.

## 8. Summary

- Experience Brain writes performed by this plan: **0**.
- Store mutations: **0**.
- Obsidian writes: **0**.
- Recommended disposition: treat U011 as **link_existing, zero-write, match confirmed**; no Phase 2B action needed for this paper.

---
*Prepared under Phase 2A dry-run authorization. Read-only. No repository, store, or Obsidian modification performed.*
