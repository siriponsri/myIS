# Experience Brain Pilot — Phase 2A Dry-Run Report

**Prepared:** 2026-07-25. **Scope:** U011, U013, U017, U018 only. **Experience Brain writes performed:** 0.

---

## 1. Verdict

**READY FOR PHASE 2B, PENDING SEPARATE ITEMIZED OWNER SIGN-OFF.** No conflicts were found between the Phase 1 preflight report and the live codebase (Task 1). No credible duplicate was found for any of the three `ingest_new` candidates (Task 6). All three dry-run payloads parse cleanly against the actual Pydantic `Knowledge` model with zero unsupported fields (Task 7). Phase 2A performed zero Experience Brain writes, zero store mutations, zero Obsidian writes, and zero canonical-repository modifications.

## 2. Contract Status

`EXPERIENCE_BRAIN_INGESTION_CONTRACT_V1.md` created with all 20 required sections (scope/authority; permitted/prohibited source artifacts; External Knowledge classification; provenance requirements; bibliographic metadata convention; deterministic content construction; tag convention; source-path convention; SHA convention; link_existing semantics; ingest_new semantics; duplicate checks; correction/supersession rules; post-write validation; audit-log requirements; Obsidian pointer behavior; owner gates; rollback limitations; batch-expansion prohibition). Revalidated against the live codebase — no conflicts.

## 3. Manifest Status

`EXPERIENCE_BRAIN_PILOT_MANIFEST_V1.yaml` created with exactly 4 entries: U011 (`link_existing_zero_write`), U013/U017/U018 (`ingest_new_dry_run`). Each entry carries only planning metadata (paper_id, proposed_operation, existing_knowledge_id, digest_path, source_pdf_sha256, title, knowledge_class, verification_status, doi, arxiv_id, publication_year, authors, duplicate_checks_required/performed, readiness, unresolved_fields). No Knowledge ID was fabricated; U013/U017/U018 carry `knowledge_id_generation: pending_write_time_generation` with the deterministically-computable ID shown only as `predicted_knowledge_id_if_generated_now` (a read-only computation of `_knowledge_id(source_hash)`, not a store write).

## 4. U011 Zero-Write Link Result

`U011_link_existing_plan.md` created. Exact SHA-256 match confirmed: U011's digest hash `384dff3e3ac0fe6d2064572bb0322ef4b059c82fcbd703e680a3b524e7120c27` equals live record `KNO-384DFF3E3AC0`'s `source_content_hash`, byte-for-byte. Filename, source_type, and the independently-derived ID (`KNO-{sha256[:12].upper()}`) all agree. No discrepancies found. Result: **link confirmed, zero Experience Brain writes required or performed.**

## 5. Dry-Run Payload Summary (U013 / U017 / U018)

All three payloads live at `source-packet/03-priority-papers/experience-brain-pilot-dry-run/`:

| Paper | Predicted Knowledge ID | Tags | Bibliographic block present | Prohibited content found |
|---|---|---|---|---|
| U013 | KNO-39AACD435C9A | patent-level, representation, embedding, self-supervised, multi-view, retrieval, candidate-exposure, not-grounded-experience | yes | none |
| U017 | KNO-23AFD72319F0 | patent, classification, prediction, pharmaceutical, not-grounded-experience | yes | none |
| U018 | KNO-4B1023EF0C1E | patent, retrieval, embedding, multi-view, knowledge-graph, candidate-exposure, not-grounded-experience | yes | none |

Each payload's `agent`/`model`/`reasoning_effort`/`experiment_id`/`run_id` fields are placeholders (`PENDING_PHASE2B_ASSIGNMENT`) — per the contract, these are per-write-time values, not decidable in a dry run, and must be filled in at the moment of an authorized Phase 2B write.

## 6. Schema Validation Results

Performed in-memory in the runtime Python environment (`experience-brain-is1-runtime\.venv`) using the actual `make_knowledge_record()` / `Knowledge.model_validate()` functions — no CLI/MCP write call, no `append()`, no store mutation.

| Paper | Parse result | Required-field completeness | Unsupported-field count | ID matches deterministic derivation | status field |
|---|---|---|---|---|---|
| U013 | OK | complete | 0 | true | proposed |
| U017 | OK | complete | 0 | true | proposed |
| U018 | OK | complete | 0 | true | proposed |

`Knowledge.model_config = ConfigDict(extra="forbid")` means a nonzero unsupported-field count would have raised a `ValidationError` at parse time; all three parsed without error, confirming zero unsupported fields structurally, not just by count.

## 7. Duplicate-Query Results

Performed per Ingestion Contract §13, against the live `knowledge.jsonl` (17 records as of 2026-07-25) plus prior-session read-only `query_knowledge` MCP calls:

- **U013:** no exact SHA-256, title, normalized-title, DOI (not verified/null), or arXiv match. Narrow keyword search returned only DAPFAM/PatenTEB/PAECTER/literature-matrix/candidate-exposure synthesis records — related topic area, not this paper. **No credible duplicate. Not blocked.**
- **U017:** no exact SHA-256, title, normalized-title, DOI, or arXiv match (DOI/arXiv not verified/null for this paper). Narrow keyword search returned only the IS1 project plan/north-star record (KNO-9F9F212D663E) — project scope, not this paper. **No credible duplicate. Not blocked.**
- **U018:** no exact SHA-256, title, normalized-title, DOI, or arXiv match. Nearest semantic return is U012 PatenTEB (KNO-528A290EA2E4), a different paper by different authors. **No credible duplicate. Not blocked.**

No candidate was set to `BLOCKED_PENDING_LINK_REVIEW`.

## 8. Predicted Knowledge ID / ID-Generation Behavior

IDs are derived deterministically as `KNO-{sha256(pdf_bytes)[:12].upper()}` via `_knowledge_id()` in `knowledge.py`. This derivation was computed read-only (no store write) and independently confirmed by round-trip parsing each payload through `make_knowledge_record()` in the runtime environment:

- U013 → `KNO-39AACD435C9A`
- U017 → `KNO-23AFD72319F0`
- U018 → `KNO-4B1023EF0C1E`

These match the IDs already recorded in the Phase 1 preflight report and the manifest. Actual ID assignment happens only inside a real `append_knowledge()` call (Phase 2B) — this dry run only reproduces the deterministic function locally.

## 9. Predicted Content Hashes

`source_content_hash` for each candidate is taken verbatim from the digest frontmatter's `sha256` field (itself `hashlib.sha256(pdf_bytes).hexdigest()`, per Task 1 code confirmation):

- U013: `39aacd435c9acc78a744b6e818b142e5ff76cd2ab40fedf8ac371da6891d3214`
- U017: `23afd72319f09b3b25f39ad58ad18f6f3a4fc54c3d68da44539cdf72d40e7028`
- U018: `4b1023ef0c1e63256232782d5d72aa189133fd510bf282d21680ebfeb730b9cb`

Additionally, an in-memory `payload_hash` was computed for each candidate using the store's own `canonical_json`/`sha256_text` functions over the fully-assembled (but placeholder-provenance) record. These values are **not** the final store `payload_hash` — they will change once real `agent`/`model`/`reasoning_effort`/`experiment_id`/`run_id` values replace the `PENDING_PHASE2B_ASSIGNMENT` placeholders at actual write time — and are reported here only to demonstrate the hash pipeline runs cleanly end to end:

- U013 (placeholder-provenance): `71c4aa45797cd0eefe7bc0d5da2cd9b1f46b96d772890aabc2c298f4c87272e1`
- U017 (placeholder-provenance): `92dcfc8e26e63bcaf0e169d37e44e875bd2a2b3f85e23d196b740575d0bc04e1`
- U018 (placeholder-provenance): `3ab3ed80eb3245cff36aa216f1917a9e54edba7a4bd9464dd8ea5114fb3a0711`

## 10. Unresolved Metadata

- U011: DOI not verified (preprint has no DOI).
- U013: DOI not verified (arXiv-only preprint).
- U017: DOI not verified; arXiv ID not applicable (not an arXiv preprint); venue inferred from header/affiliations, not independently confirmed.
- U018: DOI not verified; arXiv ID not applicable; exact publication venue (lab technical note) not independently confirmed beyond the digest's own framing.

All of the above are recorded as `not verified` in the Bibliographic Metadata blocks per the locked convention — none were inferred or guessed.

## 11. Risks

- No first-class Knowledge schema field exists for DOI/arXiv/year/authors/venue — mitigated by the Bibliographic Metadata block convention, but this remains a workaround, not a schema-level guarantee, and future schema changes could require migrating these blocks.
- Duplicate protection beyond exact SHA-256 is manual/procedural only (Contract §13) — no automated near-duplicate or title/DOI collision detection exists in the store. A future preprint-vs-published-version pair or re-encoded copy would not be automatically caught.
- `link_existing` has no dedicated store primitive; relying on digest frontmatter + `PDF_DIGEST_INDEX.md` as the only pointer mechanism means there is no store-level enforcement that the link stays consistent if the live record is ever superseded.
- Correction/supersession is Dashboard-only and owner-only — if a Phase 2B write is later found to be wrong, fixing it requires a distinct, separately-authorized action, not a simple edit.
- The predicted `payload_hash` values in §9 use placeholder provenance and will not match the real Phase 2B write's hash — a downstream reader must not treat them as final.

## 12. Exact Phase 2B Operations (If Later Authorized)

If Phase 2B is separately authorized per paper, the exact operation for each candidate would be:

- **U011:** no operation — `link_existing` is already fully satisfied by existing digest frontmatter + `PDF_DIGEST_INDEX.md`; zero Experience Brain writes.
- **U013 / U017 / U018:** exactly one `save_knowledge_digest()` MCP call per paper (never batched), using the exact `args` block already drafted in each `*_knowledge_payload.json` file, with the `PENDING_PHASE2B_ASSIGNMENT` placeholders replaced by the real operator/session `agent`, `model`, `reasoning_effort`, `experiment_id`, and `run_id` values in force at write time.

## 13. Exact Files/Store Structures Phase 2B Would Modify

- `C:\Users\Siripon Sri\Desktop\ResearchStores\thaiphalex-is1\data\knowledge.jsonl` — one new appended line per authorized `ingest_new` write (up to 3 new lines total for U013/U017/U018; 0 lines for U011).
- No other file in the Experience Brain store (`events.jsonl`, `experiences.jsonl`) would be touched, since these are Knowledge-only writes with no associated Event/Experience.
- No file in the canonical ThaiPhaLex repository, this review workspace's digests, or Obsidian would be modified by the write itself (only this workspace's own audit-log documentation, per Contract §16, would be updated afterward).

## 14. Post-Write Validation Checklist (For Phase 2B, Not Yet Performed)

Per Ingestion Contract §15, after any future authorized write:
- [ ] Re-run a read-only `query_knowledge` for the paper's title/hash and confirm the record exists with the expected Knowledge ID.
- [ ] Confirm `status=proposed` on the new record.
- [ ] Confirm no leaked raw-cache or raw-PDF content in the stored `summary`/`key_facts`.
- [ ] Confirm the expected tags and Bibliographic Metadata block are present verbatim.
- [ ] Run `lint_store()` (hash-chain integrity check) after the batch of writes.
- [ ] Update the audit log in this review workspace (Contract §16) with timestamp, new Knowledge ID(s), operator, and a reference back to this report.

## 15. Exact Owner Decisions Required Before Phase 2B

1. Separate, itemized sign-off for **U013** referencing predicted Knowledge ID `KNO-39AACD435C9A`.
2. Separate, itemized sign-off for **U017** referencing predicted Knowledge ID `KNO-23AFD72319F0`.
3. Separate, itemized sign-off for **U018** referencing predicted Knowledge ID `KNO-4B1023EF0C1E`.
4. Confirmation that no sign-off is needed for U011 (zero-write link_existing) — for the record, not an action item.
5. Assignment of real `agent`/`model`/`reasoning_effort`/`experiment_id`/`run_id` values to replace the `PENDING_PHASE2B_ASSIGNMENT` placeholders in each payload, per whatever execution contract governs the Phase 2B session.
6. Explicit confirmation that Phase 2B authorization does **not** extend to any of the remaining 36 `ingest_new` candidates or 3 other `link_existing` matches (U009, U012, U014) — those require their own future, separately-enumerated owner authorization (Contract §20).

---
*This report documents Phase 2A only. Experience Brain writes performed: 0. Store mutations: 0. Obsidian writes: 0. Canonical-repository writes: 0. U041: not started. No Phase 2B action was taken or proposed for execution — sign-off items in §15 are listed for the owner's future decision only.*
