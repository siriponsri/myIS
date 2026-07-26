# PDF Digest Schema — v1

**Status:** Review-workspace governance artifact. Applies to all `digests/*.md` files under `source-packet/03-priority-papers/`. Established 2026-07-24 during the Batch 1 stabilization pass; U001–U020 conform to this schema as of that pass.

---

## 1. Required YAML frontmatter fields

Every digest file MUST open with a `---`-delimited YAML block containing exactly these fields (order not significant, but recommended for consistency):

`unique_id`, `priority_tier`, `sha256`, `canonical_path`, `size_bytes`, `title`, `authors`, `year`, `venue`, `doi`, `arxiv`, `extraction_cache`, `experience_brain_match`, `matched_knowledge_id`, `recommended_ingestion_action`, `digest_status`, `digest_prepared`, `pass_type`, `authority`.

A field with no applicable value MUST be present with `null` (bare, unquoted) — never omitted, and never invented. `doi` and `arxiv` are commonly `null` for one or the other depending on venue; both `null` is valid for slide decks or non-indexed artifacts.

## 2. Allowed enum values

- `priority_tier`: `A` | `B` | `C`
- `experience_brain_match`: `yes` | `no`
- `recommended_ingestion_action`: `ingest_new` | `link_existing` | `hold` — **`create_new` is deprecated and MUST NOT appear in any active (non-historical-narrative) field or sentence.**
- `digest_status`: `pending` | `in-progress` | `completed` | `partial` | `failed`
- `authority`: `External Knowledge` | `Grounded Experience` (see §9 — a digest is virtually always the former)

## 3. Tier A/B/C criteria

- **Tier A** — directly on-topic for patent prior-art retrieval/embeddings/reranking with a quantitative retrieval-relevant metric (Recall@k, MAP, NDCG, RFR, MRR) or a canonical dataset/benchmark contribution. Highest citation priority.
- **Tier B** — adjacent method or domain (e.g., biomedical IR, KG-augmented retrieval, efficiency/config studies) with retrieval-relevant findings but not a primary patent-prior-art contribution, OR a patent-domain paper whose evaluation is narrower/smaller-scale than Tier A peers.
- **Tier C** — classification-only, dataset-construction-only, or domain-adjacent papers with no direct retrieval metric; cited for a specific supporting point (e.g., claims-alone signal sufficiency, structured-metadata availability) rather than as retrieval evidence.

## 4. Tier length / depth guidance

Digest depth should scale with tier, not with source length: Tier A digests should cover method, dataset, baselines, main findings, limitations, and all four "Track"/"Relationship to Papers A–D" sections in full. Tier B/C digests may compress the Track-relevance sections to one or two sentences each when relevance is low, but must never omit the Verification Warnings or Experience Brain Cross-Check sections.

## 5. Digest / verification status vocabulary

- `digest_status: completed` — digest body written, cross-checked against extraction cache, all required sections present.
- `digest_status: partial` — extraction succeeded but digest body is incomplete (e.g., pending visual-check resolution before a section can be finalized).
- `digest_status: failed` — extraction or digest authoring could not be completed (e.g., corrupted PDF).
- A digest is never marked `completed` while a **blocking** visual-check flag (§6) is open.

## 6. Visual-check warnings vs. blockers

- **Non-blocking visual-check flag** — a table/figure grid lost structure in PDF→text extraction, but the prose/abstract/results-text values needed for the digest's main claims are independently confirmed reliable. Digest proceeds to `completed`; flag is logged in a Verification Warnings section for future precise-cell citation.
- **Blocking visual-check flag** — the digest's *headline* claim itself cannot be confirmed without visual inspection (no reliable prose fallback exists). Digest stays `partial` until resolved. **A visual-check flag affecting only optional/supplementary table-cell precision — not the paper's main claim — is never sufficient grounds to mark a paper ineligible for ingestion.**

## 7. Experience Brain (EB) match / action vocabulary

- `experience_brain_match: yes` + `matched_knowledge_id: KNO-XXXX` → `recommended_ingestion_action: link_existing`. The PDF is already represented in the Experience Brain as a Knowledge record; the review-workspace digest is attached as an additional analytical layer, and the PDF itself is **not** re-ingested.
- `experience_brain_match: no` + `matched_knowledge_id: null` → `recommended_ingestion_action: ingest_new`. No existing EB record for this SHA/title; the digest is a candidate for future ingestion as a new External Knowledge record.
- `recommended_ingestion_action: hold` — reserved for cases needing owner review before either path (e.g., ambiguous SHA collision, disputed authorship) — not used in Batch 1.
- All EB queries performed while producing a digest are **read-only** (lookup/query only). No digest-authoring step may create, update, or delete an Experience Brain record.

## 8. External Knowledge vs. Grounded Experience boundary

A paper digest — however thorough, however many times it is read, cross-checked, or cited — is **External Knowledge**: a structured summary of a third-party publication. It never becomes **Grounded Experience** (first-party experimental results produced by this project's own runs, e.g. Paper D's frozen DAPFAM evidence) merely by virtue of being read, digested, or ingested into the Experience Brain. `authority: External Knowledge` is therefore the default and near-universal value for every digest in this schema; `authority: Grounded Experience` would only ever apply to a note documenting this project's own experiment output, never a third-party PDF digest.

## 9. Track C / R / S governance boundary

Any "Track C Relevance" (candidate-exposure/candidate-generation), "Track R Relevance" (fixed-pool reranking), or "Track S Relevance" (SkillOpt/prompt evolution) section in a digest is speculative connective tissue between the external paper and this project's own roadmap — it MUST be labeled **"proposed, NOT AUTHORIZED"** (Track C/R) or **"revision-stage, EXECUTION CLOSED"** (Track S) and must never be read as an approved program decision. These labels are inherited from the project's own governance documents, not invented per-digest.

## 10. Legal/novelty/invalidity/infringement/claim-equivalence/FTO boundary

Citation-based, classification-based, or embedding-similarity-based "relevance" as reported in any digested paper (e.g., X/A-citation prior art, CPC-subclass co-membership, semantic similarity score) is a **retrieval-relevance signal only**. No digest may characterize such relevance as, or imply equivalence to, a legal novelty determination, an invalidity finding, an infringement or claim-equivalence conclusion, or a freedom-to-operate (FTO) clearance. Where a paper's own framing risks this conflation, the digest must add an explicit disambiguating note (as seen in U011/DAPFAM's "citation-relevance ≠ legal/FTO" caveat).

## 11. Source-authority order

When a digest's claims could be sourced from more than one artifact, prefer in this order: (1) the source PDF itself (direct read), (2) the `extraction-cache/<ID>.md` machine extraction of that same PDF, (3) prior digests of the same paper, (4) Experience Brain records referencing the same SHA. Never prefer a secondary summary (e.g., a slide deck's own headline bullets) over the underlying paper when both are available and cataloged as distinct manifest entries (see U006 vs. U069).

## 12. Duplicate-by-SHA handling

When two or more manifest rows share an identical SHA-256, only the **canonical** path (the one referenced by `PDF_DIGEST_INDEX.md`) is digested as a unique paper. All other paths sharing that SHA are logged as `duplicate-of` the canonical `unique_id` and are never digested, counted, or ingested a second time. A `duplicate-of` relationship is a filesystem/copy fact, not a content judgment.

## 13. Canonical vs. duplicate paths

The **canonical path** is the single `manifest`-designated filesystem location for a given unique paper, and is the only path recorded in `canonical_path` frontmatter and in `PDF_DIGEST_INDEX.md`. Any other digest file describing the same `unique_id`/SHA that is not the index-referenced canonical digest (e.g., an earlier draft digest superseded by a later one) is a **legacy/duplicate digest**, not a duplicate PDF path, and must be archived under `digests/archive/` with an explicit superseded-status notice rather than left active or silently deleted.

## 14. Extraction-cache vs. curated-digest distinction

`extraction-cache/<ID>.md` is a **machine-oriented raw extraction** of the source PDF (plain markdownified text, page-by-page, no analysis, no governance framing) — it is a convenience artifact for token-efficient re-reads, not a Knowledge note in its own right, and is never itself the target of an Experience Brain ingestion decision. The **curated digest** (`digests/<ID>_*.md`) is the analytical artifact: bibliographic identity, method, findings, limitations, Track relevance, verification warnings, and EB cross-check, cross-checked against the extraction cache. Only the curated digest — never the raw extraction cache — is eligible for `ingest_new`/`link_existing` classification.

## 15. No cross-comparing incompatible metrics

Digests must never present two metrics from different papers, datasets, or relevance definitions as directly comparable without an explicit caveat, even when the metric names look similar. Concrete recurring cases in this corpus: RFR (lower-is-better rank-of-first-relevant) is not Recall@k/MAP/MRR; CPC-subclass co-membership recall is not citation-based prior-art recall; classification accuracy/F1 is not retrieval Recall@100; document-level single-jurisdiction results are not directly comparable to family-level cross-domain results (e.g., DAPFAM OUT Recall@100 ≈0.1655). Every such adjacency must carry a "do not cross-compare" note.

## 16. Visual table verification before precise citation

When a digest's Verification Warnings note that a table/figure grid was damaged in PDF→text extraction (a non-blocking visual-check flag per §6), any future use of that digest for a **precise numeric table-cell citation** (as opposed to the prose-quoted headline figures already cross-checked at digest time) MUST first involve opening the source PDF to visually confirm the cell value. The digest's prose-quoted figures may be cited directly without this step; only additional, more granular cells from the damaged grid require it.

---

## Explicit governance statements (binding)

- An `extraction-cache/*.md` file is machine-oriented source text, **not** a curated Knowledge note, and is never itself ingested or cited as an analytical claim.
- A paper digest is **External Knowledge**. It cannot become **Grounded Experience** merely by being read, digested, cross-checked, or ingested — Grounded Experience is reserved for this project's own first-party experimental output.
- Citation-based (or classification-based, or similarity-based) relevance, as reported by any digested paper, is **never** a legal conclusion — not novelty, not invalidity, not infringement, not claim-equivalence, not freedom-to-operate.
- Protected qrels, held-out evaluation identities, or any other access-restricted evaluation material referenced by a digested paper must **never** be copied into, summarized into, or otherwise made retrievable via the Experience Brain or any digest artifact. A digest may cite that such material exists and how a paper used it, but must not reproduce its contents.

---
*Established 2026-07-24 as part of the Batch 1 stabilization pass. Applies retroactively to U001–U020 and prospectively to all future Batch digests (U021 onward).*
