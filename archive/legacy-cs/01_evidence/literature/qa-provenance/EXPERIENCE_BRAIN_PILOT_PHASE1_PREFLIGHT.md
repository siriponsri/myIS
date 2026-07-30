# Experience Brain Pilot — Phase 1 Read-Only Preflight

**Status:** Phase 1 preflight only. Read-only inspection and design. No Experience Brain, Obsidian, or canonical-repository writes were performed to produce this report.
**Prepared:** 2026-07-25
**Scope:** Four representative pilot papers (U011, U013, U017, U018) drawn from the 40 digested papers (4 `link_existing` matches, 36 `ingest_new` candidates).

---

## 1. Preflight Verdict

**READY WITH CONDITIONS.**

The Experience Brain codebase supports everything Phase 1 needed to verify: an explicit External-Knowledge-vs-Grounded-Experience model, append-only hash-chained storage, deterministic content-hash-based Knowledge IDs, and read-only query tools that work end-to-end against the live `thaiphalex-is1` store (verified live via two `query_knowledge` MCP calls this session). It is **not** ready for an unconditional Phase 2 write pass because of two structural gaps (full detail in §10):

1. There is no store-level "attach digest to existing Knowledge record" primitive for `link_existing`. The only write-capable operations are full new-record writes (`save_knowledge_digest` / `process_inbox`) or full lineage-revision writes (`review_knowledge`). Executing U011's `link_existing` recommendation as an EB write would either require no EB write at all (recommended) or a Dashboard-only revision write, which is a stronger action than "linking."
2. Duplicate protection is **content-hash-only**. No automatic DOI/arXiv/title/near-duplicate check exists anywhere in the codebase. The `experience_brain_match` / `matched_knowledge_id` correlation used throughout the digest workflow is a manual, human/agent-performed comparison against `query_knowledge` results — not a store-enforced guarantee.

Both gaps are addressed procedurally (no new EB code proposed) in §11–§12.

## 2. Interfaces Inspected

Two front-ends over one shared library; no separate service or database:

| Front-end | Entry point | Backing module(s) |
|---|---|---|
| CLI (Typer) | `experience = "experience_brain.cli:app"` | `cli.py` → `knowledge.py`, `store.py`, `capture.py`, `consolidate.py`, `retrieve.py` |
| MCP server (FastMCP, stdio) | `experience-brain-mcp = "experience_brain.mcp_server:main"` | `mcp_server.py` → same modules |
| Dashboard (Streamlit) | `experience dashboard` | `dashboard.py` → same modules, **and the only caller of `review_knowledge` / `review_experience`** |

CLI and MCP call the identical underlying Python functions in `knowledge.py` / `store.py` / `capture.py`; there is no divergent write path between them. The store is three flat, append-only JSONL files under a project root (`data/events.jsonl`, `data/experiences.jsonl`, `data/knowledge.jsonl`) plus a config-selected root directory — no network service, no external DB.

**No write-capable command was invoked in this preflight.** Only `query_knowledge` (MCP, called twice, read-only) plus direct file reads / `grep` of source code, digests, and the raw `knowledge.jsonl` were performed.

## 3. Canonical Write Interface

- **`ingest_new`, clean path:** `experience_brain.knowledge.save_knowledge_digest(...)` — MCP tool `save_knowledge_digest`. No CLI equivalent for a pre-written digest exists; this is the recommended path for the three `ingest_new` pilot papers (U013/U017/U018) *when and if* Phase 2 is separately authorized.
- **`ingest_new`, bulk/heuristic path:** `process_inbox()` — CLI `process-inbox` / MCP `process_inbox`. Not recommended for these papers: it runs a naive first-lines summary and word-frequency tagger, which is lower quality than the hand-curated digests already produced.
- **`link_existing`:** **no dedicated function exists.** The only two options are (a) write nothing to EB and keep the linkage only in review-workspace files — recommended, see §9/§11 — or (b) call `review_knowledge(..., action="confirm")`, which appends a full lineage-revision record onto the matched Knowledge record. Option (b) is a materially stronger action than "linking a digest" and is not recommended for a link_existing case with no new factual content to confirm.
- **Correction / supersession:** `review_knowledge()` / `review_experience()`. **Confirmed exposed only from `dashboard.py`** — absent from `cli.py`'s command table and from `mcp_server.py`'s tool list. Executing a correction today requires running the Streamlit dashboard by hand.

All writes funnel through `store.JsonlStore.append()`, which enforces append-only semantics (raises `ValueError` if an existing record ID is resubmitted with a different `payload_hash`) and is independently checked by `lint_store()`'s hash-chain validation (`payload_hash` → `previous_hash` → `record_hash` continuity across the file).
## 4. Knowledge Schema (as implemented)

From `models.py` (`Knowledge` Pydantic model, `SCHEMA_VERSION = "v0.3.1"`):

- **Required (non-empty, validated):** `id`, `title`, `source_filename`, `source_content_hash`, `source_type`.
- **Optional:** `summary`, `key_facts`, `suggested_applicability`, `tags`, `source_mime_type`, `source_location`, `supersedes`, `invalidates`, `metadata` (free-form dict — this is where `matched_knowledge_id`-style provenance pointers would live if ever pushed into EB).
- **Defaults:** `project="general"`, `source_project="general"`, `external_project=False`, `status=KnowledgeStatus.proposed`, `extractor=ExtractorMetadata(name="unknown")`.
- **System-derived (not author-set):** `payload_hash`, `previous_hash`, `record_hash`, `ingested_at`, `schema_version`.
- **No dedicated field for DOI, arXiv ID, publication year, authors, or venue.** These would have to be folded into `metadata` (free-form) or `summary`/`key_facts` text — there is no first-class bibliographic schema. This is a real mapping gap for all 4 pilot papers' DOI/arXiv/year/authors fields (see §9, "unresolved fields").
- **Provenance** is a separate nested model (`agent`, `experiment_id`, `run_id`, `software_version`, `source`, `extra`, `redactions`) attached to every stored record — confirmed present on the live `KNO-E0520C4384CF` exemplar record.
- **No field is inherently reserved for "protected/evaluator-only data"** — the schema has no concept of a restricted-field type. Redaction (`capture.py` / `_redact_digest()` in `knowledge.py`) is a text-pattern scrub applied to summary/key_facts/tags/metadata/provenance.extra at write time (secrets, PEM keys, patient identifiers, hidden-reasoning text, benchmark-solution text) — it does not know about "held-out qrels" or "protected evaluation identities" as a category. Per `PDF_DIGEST_SCHEMA_V1.md`'s own binding governance statement, protected/held-out material must never be copied into any digest or the Experience Brain in the first place — this must be enforced at the digest-authoring layer (already true for U011/U013/U017/U018: none of the four digests quote protected qrels or held-out material).

## 5. External Knowledge Classification

Explicitly, structurally supported — confirmed at three layers:

1. **Model layer:** `Knowledge` and `Experience` are separate Pydantic models, stored in separate JSONL files, with separate MCP query tools (`query_knowledge` vs `query_experience`).
2. **Semantic layer (README):** Knowledge = "what the agent has read or received from an external source" (needs source filename/hash/location/extractor metadata); Experience = "what the agent has done and learned from an observed outcome" (requires ≥1 `evidence_event_ids` entry — enforced by a Pydantic validator, so an Experience record cannot even be constructed without linked Events).
3. **Review-workspace governance layer (`PDF_DIGEST_SCHEMA_V1.md` §8):** binding statement that a paper digest is External Knowledge and "never becomes Grounded Experience merely by virtue of being read, digested, or ingested."

Because `Experience` requires real `evidence_event_ids`, and none of U011/U013/U017/U018 have any associated Events in this project, it is structurally impossible for any of the four to be miscategorized as Grounded Experience via `save_knowledge_digest` (which only ever writes to the Knowledge store). Risk is effectively zero for these four papers specifically.

## 6. Duplicate-Protection Behavior

- **Automatic:** SHA-256 content-hash match only. `process_inbox()` builds `existing_by_hash` keyed on `source_content_hash`; a repeat hash is marked `"duplicate"` with no new record written (unless the prior record was itself a failed extraction, which is retried). `save_knowledge_digest()` derives a deterministic ID via `_knowledge_id(source_hash) = f"KNO-{source_hash[:12].upper()}"` — identical bytes always produce the identical ID, so a second `save_knowledge_digest()` call on the same source hash would collide at the `JsonlStore.append()` level and raise (append-only enforcement), rather than silently duplicating.
- **Not automatic:** DOI, arXiv ID, exact title, normalized title, source path, content similarity. Confirmed via `grep -n "doi|arxiv|title ==|normalize" src/experience_brain/*.py` → zero matches. The digest workflow's own `experience_brain_match` / `matched_knowledge_id` fields are populated by a human/agent manually running `query_knowledge` and eyeballing the result — not a store guarantee. This is the primary unresolved risk carried into §10.
- **`link_existing` mechanics:** confirmed live — U011's digest states `experience_brain_match: yes`, `matched_knowledge_id: KNO-384DFF3E3AC0`; a live `query_knowledge("DAPFAM domain-aware family-level dataset cross-domain patent retrieval")` call this session returned `KNO-384DFF3E3AC0` with `source_content_hash` exactly equal to U011's frontmatter `sha256` (`384dff3e3ac0…7120c27`) — the match is a genuine SHA-256 identity, not a fuzzy one. Since no store primitive exists to "attach an analytical note to a Knowledge record without revision," the correct `link_existing` execution is: **write nothing to EB**; keep the pointer only in the digest's own frontmatter (already present) and in `PDF_DIGEST_INDEX.md`.

## 7. Correction / Supersession Behavior

- `review_knowledge(root, id, action=confirm|invalidate|retire)` and `review_experience(root, id, action=confirm|edit_confirm|invalidate|retire)` both **append** a new record with a derived revision ID (`{id}-REV-{timestamp}-{digest8}`), set `supersedes` (confirm/retire) or `invalidates` (invalidate) to the prior record's ID, and force `provenance.agent="owner"` / `provenance.source="owner_dashboard"`.
- The original record is **never deleted or mutated** — `current_knowledge()` / `current_experiences()` filter it out of "current" views by checking whether its ID appears as any other record's `supersedes`/`invalidates` target, but the full JSONL history is retained.
- **Confirmed exposed only via the Streamlit Dashboard** (`dashboard.py`'s `_apply_review()` / `_apply_knowledge_review()`), not via CLI or MCP. No correction/supersession action was invoked in this preflight.
- Live store check: all 17 existing Knowledge records in `thaiphalex-is1/data/knowledge.jsonl` are `status="proposed"` with **zero** `supersedes`/`invalidates` set anywhere — no owner review action has ever been executed against this store.

## 8. Safe Read-Only Validation Queries (exercised this session)

Both calls below were run live against the connected `thaiphalex-experience-brain` MCP server and returned successfully, confirming the read path works end-to-end (not just against raw JSONL):

- `query_knowledge(question="rethinking patent retrieval with language models scalable efficient search", project="thaiphalex-is1")` → top hit `KNO-E0520C4384CF` (score 44) — matches U014's `matched_knowledge_id`.
- `query_knowledge(question="DAPFAM domain-aware family-level dataset cross-domain patent retrieval", project="thaiphalex-is1")` → top hits included `KNO-384DFF3E3AC0` (score 44, hash-confirmed match to U011).

Additional read-only queries available for later verification, none executed with side effects: `query_experience`, `query_memory`, `review_latest`, `list_inbox_files`, `inspect_inbox_file`, `extract_inbox_file`, plus CLI `status`/`lint`. All four target KNO IDs from the task's verified-state list (`KNO-92F3E83D2CBF`, `KNO-384DFF3E3AC0`, `KNO-528A290EA2E4`, `KNO-E0520C4384CF`) were independently confirmed present in the raw store via `grep`, with titles matching U009/U011/U012/U014 respectively.
## 9. Four-Paper Dry-Run Mapping (inspection only — no writes)

### U011 — DAPFAM (`link_existing`)

| Field | Value |
|---|---|
| Proposed operation | **No EB write.** Digest frontmatter (`matched_knowledge_id: KNO-384DFF3E3AC0`) + `PDF_DIGEST_INDEX.md` already carry the link. |
| Expected Knowledge ID behavior | N/A — record already exists as `KNO-384DFF3E3AC0`; deterministic ID derives from `source_content_hash` which matches exactly. |
| Proposed title / knowledge_type / source_type | N/A (no new record) |
| Provenance fields | N/A |
| Source digest path | `source-packet/03-priority-papers/digests/U011_dapfam_digest.md` |
| Source PDF SHA-256 | `384dff3e3ac0fe6d2064572bb0322ef4b059c82fcbd703e680a3b524e7120c27` — **confirmed equal** to `KNO-384DFF3E3AC0`'s live `source_content_hash`. |
| DOI / arXiv | doi: null · arxiv: `2506.22141` |
| Tags | N/A (no new record); existing KNO record's own tags unaffected |
| Verification status | digest `digest_status: completed`; EB record `status: proposed` (unchanged) |
| Unresolved fields | None material — hash match is exact, no schema gap since nothing new is written. |
| Duplicate risk | None (this *is* the duplicate-avoidance case). |
| Leakage / protected-data risk | None — no write occurs. |
| **Readiness verdict** | **READY** to execute as "no-write link" once Phase 2 is separately authorized. Lowest-risk of the four. |

### U013 — Patent Representation Learning via Self-Supervision (`ingest_new`, Tier A)

| Field | Value |
|---|---|
| Proposed operation | `save_knowledge_digest(...)` — new Knowledge record. |
| Expected Knowledge ID | `KNO-39AACD435C9A` (deterministic, derived from `source_content_hash[:12].upper()`) — confirmed no collision in live store (17 existing IDs checked; none match). |
| Proposed title | "Patent Representation Learning via Self-supervision" |
| knowledge_type / source_type | External Knowledge / `pdf` |
| Provenance | agent = digest author/session owner; source = review-workspace digest pipeline; experiment_id per task's execution contract |
| Source digest path | `source-packet/03-priority-papers/digests/U013_self_supervised_patent_representation_digest.md` |
| Source PDF SHA-256 | `39aacd435c9acc78a744b6e818b142e5ff76cd2ab40fedf8ac371da6891d3214` |
| DOI / arXiv | doi: null · arxiv: `2511.10657` |
| Tags | e.g. `patent-retrieval`, `self-supervised`, `contrastive-learning`, `embedding` (reuse existing tag vocabulary — not verified against live `tags` list in this preflight) |
| Verification status | digest `digest_status: completed`; new EB record would default to `status: proposed` |
| Unresolved fields | **No first-class schema field for DOI/arXiv/year/authors/venue** — must go into `metadata` (free-form) if preserved at all; needs an explicit field-mapping decision before Phase 2A (§13). |
| Duplicate risk | Low — confirmed no existing hash match via manual `query_knowledge` cross-check (per digest's own EB Cross-Check section) and via live MCP query this session. |
| Leakage / protected-data risk | Low — digest quotes only prose-verified figures; no protected qrels. |
| **Readiness verdict** | **READY WITH CONDITIONS** — needs the metadata-field-mapping decision (§13) before a real write. |

### U017 — Needle in a Haystack (`ingest_new`, Tier C)

| Field | Value |
|---|---|
| Proposed operation | `save_knowledge_digest(...)` — new Knowledge record. |
| Expected Knowledge ID | `KNO-23AFD72319F0` (deterministic; not present in live store's 17 records). |
| Proposed title | "Needle in a haystack: Harnessing AI in drug patent searches and prediction" |
| knowledge_type / source_type | External Knowledge / `pdf` |
| Source digest path | `source-packet/03-priority-papers/digests/U017_needle_haystack_drug_patent_digest.md` |
| Source PDF SHA-256 | `23afd72319f09b3b25f39ad58ad18f6f3a4fc54c3d68da44539cdf72d40e7028` |
| DOI / arXiv | doi: null · arxiv: null (PLOS ONE; DOI not yet confirmed per digest's own Verification Warnings) |
| Tags | e.g. `pharma-patents`, `classification`, `bert`, `drug-approval-prediction` |
| Verification status | digest `digest_status: completed`; DOI explicitly flagged "confirm before citing" in the digest itself |
| Unresolved fields | Same DOI/arXiv/authors schema gap as U013; additionally **DOI itself is unresolved at the source** (digest flags it, not just an EB-mapping question). |
| Duplicate risk | Low — no hash match found. |
| Leakage / protected-data risk | Low — Table 3 per-applicant figures are flagged as extraction-damaged and are correctly *not* quoted in the digest. |
| **Readiness verdict** | **READY WITH CONDITIONS** — same metadata-mapping condition as U013, plus the DOI should be resolved (or explicitly left null) before write. |

### U018 — Enhancing Patent Retrieval using Text and KG Embeddings (`ingest_new`, Tier B)

| Field | Value |
|---|---|
| Proposed operation | `save_knowledge_digest(...)` — new Knowledge record. |
| Expected Knowledge ID | `KNO-4B1023EF0C1E` (deterministic; not present in live store's 17 records). |
| Proposed title | "Enhancing Patent Retrieval using Text and Knowledge Graph Embeddings: A Technical Note" |
| knowledge_type / source_type | External Knowledge / `pdf` |
| Source digest path | `source-packet/03-priority-papers/digests/U018_patent_retrieval_text_kg_embeddings_digest.md` |
| Source PDF SHA-256 | `4b1023ef0c1e63256232782d5d72aa189133fd510bf282d21680ebfeb730b9cb` |
| DOI / arXiv | doi: null · arxiv: null (lab technical note; venue confirmed as SUTD DDI Lab, not a journal DOI) |
| Tags | e.g. `knowledge-graph`, `TransE`, `multi-view-retrieval`, `patent-embeddings` |
| Verification status | digest `digest_status: completed` |
| Unresolved fields | Same DOI/arXiv/authors schema-mapping gap; no other unresolved facts (method fully verified against cache per digest). |
| Duplicate risk | Low — no hash match found. |
| Leakage / protected-data risk | Low — digest explicitly separates this paper's dataset counts from cited related-work counts (2.75M/0.8M) to avoid misattribution; no protected material. |
| **Readiness verdict** | **READY WITH CONDITIONS** — same metadata-mapping condition as U013/U017. |

**Net effect of a completed pilot (if later authorized):** 1 of 4 `link_existing` matches resolved (U011; 3 remaining — U009, U012, U014 already have KNO IDs and need no action). 3 of 36 `ingest_new` candidates resolved (U013/U017/U018; **33 remain untouched** — 13 from Batch 1, 20 from Batch 2A). Pilot approval scope is therefore explicitly 3 new records + 0-or-1 revision action, not 36.
## 10. Unresolved Risks

1. **No first-class DOI/arXiv/year/authors/venue fields in the Knowledge schema.** All four papers would need these folded into free-form `metadata` (or dropped) — needs an owner decision on a fixed sub-key convention before any write, so future queries can rely on a stable shape.
2. **No store-level dedup beyond exact SHA-256.** The `link_existing` vs `ingest_new` classification for all 40 digested papers rests on a manual `query_knowledge` comparison performed by whoever authored each digest. A near-duplicate paper (same content, different PDF encoding → different hash) would not be automatically caught.
3. **No `link_existing` primitive.** Confirmed the only path that touches the matched record is `review_knowledge(action=confirm)`, which is a stronger action (owner-review revision) than what "attach an analytical digest" should mean. Recommendation (§6, §9): perform `link_existing` as a zero-EB-write, workspace-only pointer.
4. **Correction/supersession is Dashboard-only.** If Phase 2B ever needs a correction, it cannot be scripted via CLI/MCP today — it requires launching Streamlit by hand. Not a blocker for Phase 2A (pure new-record ingest_new + no-write link_existing), but relevant to owner expectations for Phase 2B.
5. **Obsidian pointer update (mentioned in the task's own Phase 2B framing) has no implemented capability today.** README lists Obsidian export under "Planned For Phase 1" of the Experience Brain's *own* roadmap (not yet built), and no Obsidian code exists in `src/experience_brain`. Any Phase 2B design must either drop this step or substitute a manual/external mechanism.
6. **`knowledge/digests` and `knowledge/sources` directories exist in the Experience Brain repo but are empty** (glob returned no files) — minor, but worth owner awareness; not currently used by any inspected code path.
7. **Protected/held-out material has no schema-level guard inside Experience Brain itself** — the redaction regexes catch secrets/PII/hidden-reasoning/benchmark-leakage patterns, not "protected qrels" as a category. Enforcement for that specific risk currently depends entirely on digest-authoring discipline (per `PDF_DIGEST_SCHEMA_V1.md`'s binding statement), which held for all four pilot digests on inspection, but is not a technical control inside the store.

## 11. Proposed Phase 2 Procedure (design only — not executed)

**Phase 2A — Dry-run + owner sign-off (still zero EB writes):**
1. Finalize the metadata-field-mapping convention for DOI/arXiv/year/authors/venue (resolves risk 1).
2. For U011: prepare the "no-write" link — confirm digest frontmatter + `PDF_DIGEST_INDEX.md` are the sole record of the link; no EB action drafted for owner approval beyond this confirmation.
3. For U013/U017/U018: draft the exact `save_knowledge_digest()` call arguments (title, summary, key_facts, suggested_applicability, tags, source_filename, source_content_hash, source_type, project, agent, model, reasoning_effort, experiment_id, run_id) per paper, using only the curated digest text — never the raw PDF or extraction cache.
4. Present the exact 3 draft calls (not 36) to the owner for explicit, itemized sign-off — one line per paper, no blanket "approve ingest_new" language.
5. Re-run `query_knowledge` immediately before write time to catch any record added to the store since this preflight (staleness check).

**Phase 2B — Owner-authorized writes (only after explicit Phase 2A sign-off):**
1. Execute the 3 sign-off approved `save_knowledge_digest()` calls, one at a time, concurrency 1.
2. After each write, run a read-only `query_knowledge` for that paper's title/hash and confirm: record exists, correct Knowledge ID, `status=proposed`, no leaked raw-cache content, expected tags/summary present.
3. Run `lint_store()` / CLI `lint` after all 3 writes to confirm hash-chain integrity.
4. Write an audit note (in the review workspace, not in EB) recording: timestamp, the 3 Knowledge IDs created, the operator, and a link back to this preflight report.
5. Explicitly log that U011's `link_existing` required **zero** EB writes, and that **33 `ingest_new` candidates and 3 `link_existing` matches remain untouched** — this scope statement must appear in the Phase 2B closeout so a single approval is never read as covering the remaining backlog.
6. Obsidian pointer update: **out of scope until the capability exists** (risk 5) — Phase 2B closeout should state this explicitly rather than skip it silently.

## 12. Draft Ingestion Contract — `EXPERIENCE_BRAIN_INGESTION_CONTRACT_V1.md` (draft only, not created)

- **Permitted source artifacts:** curated digest files (`digests/<ID>_*.md`) that are `digest_status: completed` or `partial`-with-only-non-blocking-flags, per `PDF_DIGEST_SCHEMA_V1.md`. 
- **Prohibited source artifacts:** raw PDFs, `extraction-cache/*.md`, legacy/archived digests, any protected/held-out evaluation material referenced by a paper.
- **Record classification:** every ingested record is `Knowledge`, `authority: External Knowledge`. Never `Experience`/Grounded Experience for a third-party paper, regardless of how many times it is read or digested.
- **Provenance requirements:** `provenance.source` must identify the review-workspace pipeline (not `owner_dashboard`, which is reserved for correction actions); `provenance.agent`/`experiment_id`/`run_id` per the task's execution contract.
- **Duplicate checks (pre-write, mandatory, manual):** (a) exact SHA-256 against all `source_content_hash` values in the live store via `query_knowledge`/direct read; (b) cross-check digest's own `experience_brain_match`/`matched_knowledge_id` fields; (c) re-check immediately before write (staleness).
- **`link_existing` semantics:** zero EB writes. The link lives only in the digest frontmatter and `PDF_DIGEST_INDEX.md`. Never call `review_knowledge(action=confirm)` for a link_existing case unless the owner is deliberately issuing a correction, which is a distinct, separately authorized action.
- **`ingest_new` semantics:** exactly one `save_knowledge_digest()` call per paper, itemized and pre-approved per Knowledge ID, never batched under one blanket approval.
- **Correction/supersession rules:** owner-only, Dashboard-only, must reference the specific prior record ID being superseded/invalidated; append-only — no history is ever deleted.
- **Post-write validation:** mandatory read-only re-query (§8 pattern) plus `lint_store()` after every batch.
- **Owner gates:** Phase 2A sign-off is per-paper, itemized; Phase 2B execution requires that exact sign-off, no broader inference.
- **Rollback limitations:** none exist beyond appending a superseding/invalidating revision (Dashboard-only) — there is no delete. Owners must treat every write as effectively permanent history.
- **Audit requirements:** every ingest batch logged in the review workspace (not EB) with timestamp, Knowledge IDs, operator, and source preflight/authorization reference.

## 13. Exact Owner Decisions Required Next

1. Confirm the metadata sub-key convention for DOI/arXiv/year/authors/venue before any `save_knowledge_digest()` call is drafted for real (currently undecided — risk 1).
2. Confirm that U011's `link_existing` should be executed as a **zero-EB-write, workspace-pointer-only** action (recommended in this report) rather than a `review_knowledge` revision.
3. Explicitly authorize (or decline) Phase 2A (dry-run drafting only, still zero writes) as the next step — this report does not request that authorization itself, per the stop condition below.
4. Decide whether U017's unresolved DOI should be tracked down before ingest or explicitly recorded as `doi: null`.
5. Decide how (or whether) to handle the Obsidian-pointer-update step given it has no implemented capability today (risk 5).

---
*Prepared under Phase 1 read-only preflight constraints. Experience Brain writes: 0. Obsidian writes: 0. Canonical-repository writes: 0. Only this report file was created or modified.*

