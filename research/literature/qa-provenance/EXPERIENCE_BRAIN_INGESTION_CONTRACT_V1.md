# Experience Brain Ingestion Contract V1

**Status:** Draft contract for the Phase 2A pilot only. Prepared under owner authorization scoped to exactly four papers (U011, U013, U017, U018). Does not authorize any Experience Brain write. Revalidated 2026-07-25 against the live `experience_brain` codebase (`src/experience_brain/{models,knowledge,store}.py`) and the runtime Python at `experience-brain-is1-runtime/.venv` — no conflicts found with the Phase 1 preflight report.

---

## 1. Scope and Authority

This contract governs how curated paper digests may become Experience Brain (EB) `Knowledge` records for the THAIPHA-LEX IS1 project. It is scoped **only** to the four pilot papers named in the Phase 2A owner authorization: U011, U013, U017, U018. It has no effect on any other candidate paper.

Authority chain: Owner authorization (Phase 2A contract text) > this contract > `PDF_DIGEST_SCHEMA_V1.md` governance statements > individual digest files. Where this contract and a digest disagree on classification or process, this contract controls.

## 2. Permitted Source Artifacts

- Curated digest files under `source-packet/03-priority-papers/digests/<ID>_*.md` with `digest_status: completed` (or `partial` carrying only non-blocking flags).
- The digest's own YAML frontmatter (title, authors, year, doi, arxiv, sha256, canonical_path).
- The `PDF_DIGEST_INDEX.md` cross-reference for existing `matched_knowledge_id` pointers.

## 3. Prohibited Source Artifacts

- Raw PDF bytes or any text extracted directly from a PDF.
- `extraction-cache/*.md` cache files (`U013.md`, `U017.md`, `U018.md`, `U011.md`).
- Legacy or archived digest versions.
- Any protected, held-out, or evaluator-only material (e.g., Paper D held-out qrels, `OUTCOME-BOUNDARY` test-split data) referenced by a paper — never copied into a digest or a Knowledge payload regardless of pilot status.

## 4. External Knowledge Classification

Every record produced under this contract is `Knowledge`, never `Experience`. A third-party academic paper is External Knowledge by definition — it is never Grounded Experience "merely by virtue of being read, digested, or ingested" (`PDF_DIGEST_SCHEMA_V1.md` §8). This holds structurally: `Experience` requires ≥1 `evidence_event_ids` (Pydantic-enforced), and no paper digest has an associated Event, so misclassification as Experience is not constructible via `save_knowledge_digest`.

## 5. Exact Provenance Requirements

Every `Knowledge.provenance` (via MCP `save_knowledge_digest` args) must set:

- `agent` — the operator/session identity performing the (future) write.
- `experiment_id` / `run_id` — per the task's execution contract at write time.
- `source` — fixed to `"agent_knowledge_digest"` (the MCP tool's own default provenance source for this path). Never `"owner_dashboard"`, which is reserved for correction/supersession actions.

## 6. Bibliographic Metadata Convention

The `Knowledge` schema (`v0.3.1`) has no first-class field for DOI, arXiv ID, publication year, authors, or venue. These are represented as one deterministic Markdown block appended to the end of `summary` content construction (§7), never as ad hoc `metadata` keys:

```
## Bibliographic Metadata

- ThaiPhaLex Paper ID:
- Authors:
- Publication Year:
- DOI:
- arXiv ID:
- Verified Digest Path:
- Source PDF SHA-256:
- Verification Status: verified curated digest
```

Rules:
- Preserve this exact field order.
- Use `not verified` for any value not confirmed at the source (never invent or infer).
- Do not create ad hoc Pydantic fields for these values.
- Do not encode full bibliographic records in `tags` — tags stay short topical labels.
- Never include extraction-cache paths as ingested content, and never include raw PDF text anywhere in the record.

## 7. Deterministic Content Construction

For each `ingest_new` candidate, the `key_facts` field is built **only** from the digest's own verified prose (Main Findings / Method sections already marked "verified against cache" in the digest), never from the raw extraction cache. `summary` is a short synthesis of the digest's Research Problem + Main Findings, followed immediately by the Bibliographic Metadata block from §6. `suggested_applicability` states that the record is External Knowledge — planning input only, not tested evidence, not Grounded Experience — consistent with the schema-derived default applicability text used elsewhere in this store.

## 8. Tag Convention

Tags are drawn from the existing tag vocabulary where possible (checked via read-only `tags` query) plus paper-specific topical terms already used in the digest's own framing (e.g., `patent-retrieval`, `self-supervised`, `knowledge-graph`). No bibliographic values (DOI, year, authors) are ever placed in tags.

## 9. Source-Path Convention

`source_filename` is set to the digest's own `canonical_path` value from its frontmatter (the underlying PDF's repository-relative path), not the digest file path and not the extraction-cache path. This preserves traceability to the original PDF without ingesting its content.

## 10. SHA Convention

`source_content_hash` is set verbatim from the digest frontmatter's `sha256` field, which is the SHA-256 of the original source PDF bytes (verified in Task 1 of Phase 2A to be computed via `hashlib.sha256(path.read_bytes())` in `knowledge.py::content_hash`). This is also restated in the Bibliographic Metadata block's `Source PDF SHA-256` field for human-readability inside the record body.

## 11. `link_existing` Semantics

`link_existing` performs **zero** Experience Brain writes. There is no store primitive to "attach an analytical digest" to an existing Knowledge record without a full lineage revision. The only write-capable action that touches an existing record is `review_knowledge(action=confirm|invalidate|retire)`, which appends a full owner-review revision — a materially stronger action than linking, and reserved exclusively for genuine owner correction/confirmation decisions, never for routine link_existing bookkeeping. For `link_existing`, the pointer lives only in: (a) the digest's own frontmatter (`experience_brain_match: yes`, `matched_knowledge_id: <KNO-ID>`), and (b) `PDF_DIGEST_INDEX.md`. Both already exist for U011; this contract does not add a third mechanism.

## 12. `ingest_new` Semantics

Exactly one `save_knowledge_digest()` MCP call per paper. Never batched. Each call is itemized and requires separate, explicit owner sign-off referencing the specific predicted Knowledge ID for that paper — never a blanket "approve ingest_new" instruction covering multiple papers.

## 13. Duplicate Checks

Before any future `ingest_new` write, the operator must manually check the candidate against the live store by:
1. Exact SHA-256 (`source_content_hash`) — authoritative and store-enforced at append time (a collision raises `ValueError` in `JsonlStore.append`).
2. Exact title string match.
3. Normalized title (case-fold, whitespace-collapsed) match.
4. DOI match, when the digest's DOI is verified (not `null`).
5. arXiv ID match, when present.
6. ThaiPhaLex paper ID (`unique_id`) cross-referenced against any existing record's `metadata`/`source_filename`, if ever recorded.
7. Narrow keyword `query_knowledge` search as a semantic backstop (informative only — not authoritative given no near-duplicate detection exists in the store).

Exact content-hash matching alone is **insufficient**: it only catches byte-identical re-submission of the same PDF, not a differently-encoded copy of the same paper, a preprint-vs-published-version pair, or a title/DOI collision under a different hash.

## 14. Correction and Supersession Rules

`review_knowledge()` / `review_experience()` are owner-only and, per the live codebase, exposed only from `dashboard.py` (Streamlit) — absent from the CLI command table and the MCP tool list. Any correction or supersession must reference the specific prior record ID being superseded/invalidated. All writes are append-only; no record is ever deleted, and full JSONL history is retained even after supersession.

## 15. Post-Write Validation

After any future authorized write: re-run a read-only `query_knowledge` for the paper's title/hash and confirm the record exists with the correct Knowledge ID, `status=proposed`, no leaked raw-cache content, and the expected tags/summary. Run `lint_store()` (CLI `lint` / hash-chain integrity check) after each batch of writes.

## 16. Audit-Log Requirements

Every ingest batch is logged in the review workspace (this repository), never inside the EB store itself: timestamp, the Knowledge ID(s) created, the operator, and a reference back to the authorizing preflight/contract document. This document and the Phase 2A dry-run report constitute that log for the pilot.

## 17. Obsidian Pointer Behavior

Obsidian export has no implemented capability in the current `experience_brain` codebase (listed only as "Planned" in the project's own roadmap; no Obsidian code exists in `src/experience_brain`). This contract does not authorize or simulate any Obsidian write. Any future Obsidian pointer step is out of scope until the capability exists and is separately authorized.

## 18. Owner Gates

- Phase 2A (drafting + dry-run, zero writes) requires the explicit authorization already granted for this pilot.
- Phase 2B (actual writes) requires a **separate, itemized** owner sign-off per paper, referencing the exact predicted Knowledge ID — never inferred from Phase 2A approval.
- Any correction/supersession action requires a distinct owner decision, separate from both Phase 2A and Phase 2B.
- Any expansion beyond the four named pilot papers requires a new owner authorization enumerating the new paper list; this contract's approval does not extend to it.

## 19. Rollback Limitations

There is no delete operation anywhere in this store. The only "undo" mechanism is appending a superseding or invalidating revision (owner-only, Dashboard-only). Every write under this contract must be treated as effectively permanent history from the moment it lands.

## 20. Batch-Expansion Prohibition

Approval for this four-paper pilot does **not** authorize ingestion of any of the remaining 36 `ingest_new` candidates or the remaining 3 `link_existing` matches (U009, U012, U014) identified in the broader digest corpus. Each future batch requires its own separately enumerated paper list and its own owner authorization. This contract must not be read as a template that self-extends to future batches without that explicit step.

---
*Prepared under Phase 2A drafting authorization. Experience Brain writes: 0. This document itself is the only artifact this section describes.*
