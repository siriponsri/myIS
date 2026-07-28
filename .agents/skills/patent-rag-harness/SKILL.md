---
name: patent-rag-harness
description: Govern myIS Research 1.0 patent retrieval, CrossRoute candidate exposure, frozen-pool diagnostics, claim/passage evidence, DAPFAM evaluation, and the governed harness around those systems.
---

# Patent RAG Harness for myIS Research

Use this skill for family normalization, multi-route candidate generation,
frozen-pool diagnostics, evidence tracing, DAPFAM evaluation, and the governed
kernel around Track C/S. Read `AGENTS.md`, `PLAN.md`, the scientific/build plans,
and the applicable Owner Gate first.

## Identity and operating stance

- Active identity is `myIS Research` / `myis-research`, protocol `1.0`.
- Earlier program labels remain frozen provenance only.
- DAPFAM is family-level retrieval relevance, not legal truth.
- Optimize candidate exposure before ranking and evidence fluency.
- Git and validated artifacts are canonical; MLflow and Brain are mirrors.
- Never access confirmation membership, qrels, payloads, or per-query outcomes.

## Architecture contract

Keep source, normalization, structure, query planning, retrieval, fusion,
diagnostic ranking, evidence, verification, evaluation, and observation explicit.
Preserve `family_id` and `publication_id`, passage offsets, route provenance,
and exact source spans. The deterministic kernel owns identity, approvals,
schemas, splits/hashes, budgets, family deduplication, tie-breaking,
metrics/statistics, manifests, redaction, protection, and immutable writes.

## Required workflow

1. Verify Git state, identity, lock, active phase, and Owner Gate.
2. Inspect only authorized corpus/query commitments and non-protected views.
3. Reproduce protocol-matched B0/B1/B2 before a new C arm.
4. Audit OUT availability, exposure/oracle headroom, and prospective MDE/power.
5. State one falsifiable hypothesis and exact editable surface.
6. Build grounded TAC/claim/mechanism views with source-span IDs.
7. Retrieve through declared lexical/dense routes under fixed budgets.
8. Fuse and deduplicate at family level while retaining every component rank.
9. Accept selection only on a strictly greater preregistered primary score.
10. Freeze the pool before any Track C ranking diagnostic.
11. Classify failures at the layer that failed and retain negative outcomes.
12. Freeze all code/config/prompt/skill/model/environment/pool hashes before
    an external Owner confirmation request.

## Gate metrics and estimation

- Track C primary: C1-C0 OUT Recall@100 against one local comparator.
- Ranking/headroom nDCG is a non-gating diagnostic on the identical frozen pool.
- Track S primary: A3-A2 paired OUT Recall@100 on the untouched joint test.
- Confirmation reports exact n, paired delta, deterministic 10,000-resample CI,
  rank-biserial effect, and W/L/T. MDE is design sensitivity only.
- Holm applies only to each preregistered additional comparison family.

## Protected-data and split rules

Freeze seed, membership hashes, qrels snapshot, and OUT-positive counts before
development. C and S share planned IDs `250/125/872` but have separate evaluators,
optimizers, budgets, manifests, artifacts, and firewalls. Confirmation data stay
outside the workspace and network re-download is disabled during optimization.

## Evidence package

Return structured evidence with query/family/publication IDs, route/rank,
matched limitation, verbatim span, locator, support status, source identifier,
confidence, and unresolved gaps. Missing support produces abstention or
`unclear`. Never express novelty, infringement, validity, or freedom to operate
as a legal opinion.

## Dependency and projection boundaries

Require Python 3.11 and `pyproject.toml + uv.lock`. Measured manifests record
the exact runtime, lock hash, model/provider, evaluator, split, and artifact
hashes. Dashboard is loopback-only and aggregate/hash-only. MLflow accepts only
validated allowlisted files and rejects protected data. Brain and Linear are
human-readable projections and cannot decide scientific gates.
