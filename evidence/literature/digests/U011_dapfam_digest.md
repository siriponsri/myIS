---
unique_id: U011
priority_tier: A
sha256: 384dff3e3ac0fe6d2064572bb0322ef4b059c82fcbd703e680a3b524e7120c27
canonical_path: research/ref-paper/is1/pdfs/11_dapfam_domain_aware_family_level_dataset_2025.pdf
size_bytes: 96085
title: "DAPFAM: A Domain-Aware Family-level Dataset to benchmark cross-domain patent retrieval"
authors: "Iliass Ayaou; Denis Cavallucci; Hicham Chibane"
year: 2025
venue: "Preprint submitted to Elsevier (12 Sep 2025); arXiv:2506.22141v2; INSA Strasbourg, ICUBE Laboratory"
doi: null
arxiv: "2506.22141"
extraction_cache: source-packet/03-priority-papers/extraction-cache/U011.md
experience_brain_match: yes
recommended_ingestion_action: link_existing
digest_status: completed
digest_prepared: 2026-07-24
pass_type: "Unique-PDF digestion Batch 1 (token-efficient two-stage protocol)"
authority: "External Knowledge (not Grounded Experience, not Paper D evidence)"
secondary_context: "source-packet/03-priority-papers/DAPFAM_EXTRACTION_AUDIT.md (pre-existing full audit — NOT recreated here)"
---

# U011: DAPFAM — A Domain-Aware Family-level Dataset to Benchmark Cross-Domain Patent Retrieval

**Unique ID:** U011 · **Priority tier:** A · **SHA-256:** `384dff3e…7120c27`
**Canonical path:** `research/ref-paper/is1/pdfs/11_dapfam_domain_aware_family_level_dataset_2025.pdf`

> **Secondary context:** a full read-only extraction audit already exists at `DAPFAM_EXTRACTION_AUDIT.md` (100% line coverage, reviewer-correction layer). This digest does **not** recreate it — it provides the standardized digest layer and records which audit claims were re-verified against the cache. Where they overlap, the audit's Reviewer-Correction section (§10) takes precedence on causal/interpretive caveats.

## Bibliographic Identity

- **Title:** DAPFAM: A Domain-Aware Family-level Dataset to benchmark cross-domain patent retrieval
- **Authors:** Iliass Ayaou, Denis Cavallucci, Hicham Chibane — INSA Strasbourg, ICUBE Laboratory, France
- **Venue:** Preprint to Elsevier, 12 Sep 2025 · **arXiv:** 2506.22141v2 · Same lab as PatenTEB (U012)

## Research Problem

How well do retrieval systems cope with **cross-domain (out-of-domain) patent prior-art search**, and which design choices (granularity, field representation, passage length, aggregation, hybrid fusion) most reduce the OUT gap **at the patent-family level**? Existing benchmarks lack explicit domain partitions, so cross-domain difficulty cannot be measured systematically.

## Method (re-verified against cache)

- **Domain scheme:** IN-domain = ≥1 shared IPC3 code between query and target family; OUT-domain = none shared.
- **249 controlled configurations** (verified line 13: "We conduct 249…"): BM25 (`bm25s`, k₁=1.2, b=0.75) vs dense (`Snowflake/snowflake-arctic-embed-m-v2.0`, int8); document vs passage granularity (windows 64–8192 tokens); query rep T / T+A / T+A+C / Keywords; corpus rep Full/T+A/T+A+C/Description; aggregation maxP / avg_top3 / avgP / sumP; **RRF** fusion (K grid {10,30,60,100}).
- **Metrics (verified line 976):** **NDCG@100 (primary), Recall@100 (secondary)**, macro-averaged over ALL / IN / OUT subsets, cutoff k=100.
- Hardware: 24-core CPU + RTX 4090 (consumer-scale).

## Dataset and Evaluation Setting (re-verified against cache)

Counts confirmed exact against PDF lines 12/564/567/570:
- **1,247 query families** · **45,336 target families** · **49,869 evaluation rows** (query, target, relevance score, domain label).
- Source Lens.org JSONL; family-level aggregation; English only; query earliest-claim ≥ 2000, targets 1964–2023; query inclusion ≥100 combined fwd+bwd citations.
- **Relevance = citation-based** (examiner-proxy). OUT ≈26% of relevant pairs; US-dominant jurisdictions (~78%).

## Main Findings (numbers per audit §6 — provisional, table artifacts)

1. **Severe ~5× domain gap:** OUT NDCG@100 falls to ~15–20% of IN across every method.
2. **Dense loses its edge at OUT** (dense vs BM25 ≈ 0.0003 NDCG on OUT vs ~0.056 on IN); **BM25 is relatively more robust** to domain shift.
3. **Passage-level > document-level** (+0.020–0.036 NDCG@100); best query rep **T+A+C**; optimal passage 1024–2048 (dense) / 4096+ (BM25).
4. Best single config: **Hybrid RRF K=30 passage** (NDCG ALL 0.3475 / OUT 0.0625); **document-only RRF K=60** = best effectiveness–efficiency trade-off.

*(Full result matrix and OUT/ALL retention table live in the audit; not duplicated. All table cells flagged provisional — PDF→text artifacts.)*

## Limitations (verified line 1629–1632)

- English/Lens.org → jurisdictional bias; IPC3 is one partition scheme (CPC/text clusters could differ); **single fixed encoder** → no model-specific insight; consumer hardware.
- **Crucial (verified verbatim, line 1630):** *"Citation-based relevance labels reflect examiner judgments but do not capture all forms of technical relatedness or legal sufficiency for invalidity analysis."*

## Track C Relevance (candidate-exposure — proposed, NOT AUTHORIZED)

**Core / highest.** DAPFAM **is** the project's cross-domain benchmark and the empirical anchor for KNO-20DDBF1D30A0's candidate-exposure thesis. **Recall@100 is the Track-C exposure metric** (per audit §10.2, NDCG@100 conflates exposure + ordering). The OUT gap appears at the candidate stage; best observed candidate strategy = dense-passage + RRF hybrid. This is the fixed evaluation surface (family-level, IPC3 domains) for any H1/H2/H3 ablation.

## Track R Relevance (fixed-pool reranking — proposed, NOT AUTHORIZED)

**Medium, with a caveat.** DAPFAM supplies the candidate sets a reranker operates on, and Paper D used it to test instruction-aware GEPA reranking → recorded OUTCOME-BOUNDARY. **Per audit §10.3, RRF is NOT a clean fixed-pool Track-R experiment** (fusion changes both membership and ordering). Fixed-pool reranking cannot recover families absent from the pool.

## Track S Relevance (SkillOpt — EXECUTION CLOSED)

**None (verified).** DAPFAM provides no evidence for prompt-optimization; audit §10.4 confirms any Track-S expectation is hypothesis, not result.

## Relationship to Papers A–D

- **The central benchmark for Papers A–D**; the OUT-domain gap it quantifies motivates Paper D's reranking hypothesis. Sibling to **PatenTEB (U012)** from the same lab (family-level retrieval vs embedding-task benchmark).
- Dense encoders U005/U008/U009 and query-expansion U010 are all **candidate methods to be evaluated on DAPFAM's OUT split** — but none of their in-paper numbers are DAPFAM numbers; never cross-compare absolute values.
- **Preserve the citation-relevance vs legal distinction:** DAPFAM relevance = examiner citation proxy. It is **not** a novelty, infringement, claim-equivalence, invalidity, or freedom-to-operate judgment (authors state this at line 1630). Never cite DAPFAM results as legal/FTO conclusions.

## Verification Warnings

1. **All table numbers provisional** — automated PDF→markdown introduced stray pipes / merged cells (audit caveat + §10.5). Re-verify any cell against the source PDF before citation.
2. Re-verified in this pass: dataset counts (1,247/45,336/49,869 — exact), 249 configs, NDCG@100/Recall@100 primary/secondary, and the citation-relevance limitation text. Result-table cells were **not** re-transcribed here (rely on audit + PDF).
3. Figures 2–10 are graphical; extraction has captions only.
4. HuggingFace dataset URL renders as "this repository" — unresolved in extraction.

## Experience Brain Cross-Check (READ-ONLY)

- **experience_brain_match:** **yes** — this exact PDF is Knowledge **KNO-384DFF3E3AC0** (source hash `384dff3e3ac0…` = U011 SHA). Also referenced across KNO-20DDBF1D30A0 (candidate-exposure synthesis), KNO-5449A7642CF9 (literature matrix, DAPFAM = A1 Tier 1), KNO-3D43C4514725 (local KM, DAPFAM OUT-gap context).
- **memory_conflict:** none. EB records consistently treat DAPFAM as the core benchmark and separate candidate exposure from reranking — matches this digest.
- **query mode:** read-only; no record created or modified.
- **recommended_ingestion_action:** **link_existing** — already ingested (KNO-384DFF3E3AC0); attach this digest + the existing audit as the analytical layer.

## Status

✅ **completed** — Token-efficient two-stage protocol: reused pre-extracted `extraction-cache/U011.md` (35 pages, 96,085 B); consulted `DAPFAM_EXTRACTION_AUDIT.md` as secondary context; targeted re-verification greps for dataset counts, config count, metrics, and the citation-relevance limitation. Full markdown not loaded wholesale; audit not recreated.

---
*Digest prepared 2026-07-24. Source repository unmodified. Experience Brain queried read-only. Existing DAPFAM audit consulted, not modified.*
