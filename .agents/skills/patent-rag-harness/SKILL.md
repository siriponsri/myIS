---
name: patent-rag-harness
description: Design, implement, review, or evaluate IS1 Research V0.1 patent retrieval, CrossRoute candidate exposure, frozen-pool ranking, claim/passage evidence, DAPFAM experiments, or the governed harness around those systems.
---

# Patent RAG Harness for IS1 Research V0.1

Use this skill for patent corpus retrieval, family normalization, multi-route
candidate generation, ranking/evidence, DAPFAM evaluation, and optional A0-A3
adaptation studies. Read `AGENTS.md`, `PLAN.md`, the scientific/build plans, and
the applicable Owner Gate first.

## Identity and operating stance

- Active identity is `IS1 Research V0.1`; `Paper E` is historical only.
- Paper D is frozen historical evidence.
- DAPFAM is family-level retrieval relevance, not novelty/FTO legal truth.
- Optimize candidate exposure before ranking and evidence fluency.
- Git and validated artifacts are canonical; MLflow and Brain are mirrors/pointers.
- Do not access confirmation membership, qrels, payloads, or per-query outcomes.

## Architecture contract

Keep source, normalization, structure, query planning, retrieval, fusion,
ranking, evidence, verification, evaluation, and observation explicit. Preserve
both `family_id` for evaluation and `publication_id` for exact evidence. Never
silently merge families/publications or lose passage offsets/provenance.

The deterministic kernel owns identity, approvals, schemas, splits/hashes,
budgets, family dedup, tie-breaking, metrics/statistics, immutable manifests,
redaction, protection, and confirmation boundaries. The typed policy may propose
only grounded views, allowlisted routes, route depth/quota, fixed candidate
budget, fusion, ranking/evidence depth, and bounded stopping.

## Required workflow

1. Verify Git state, IS1 identity, dependency lock, active Phase/Task, and Gate.
2. Inspect corpus/query/qrels/split/family/evaluator commitments without opening
   protected confirmation data.
3. Reproduce BM25, dense, and Hybrid RRF under one protocol.
4. Run OUT-positive availability/count, exposure/oracle, and prospective
   MDE/power audits before freezing the split.
5. State one falsifiable hypothesis and exact editable surface.
6. Build grounded title/abstract/claim views with source-span IDs; quarantine
   ungrounded terms.
7. Retrieve through complementary lexical/dense and eligible citation/metadata
   routes with declared depth/quota.
8. Fuse and deduplicate at family level under identical final K while retaining
   every component rank/score/view/publication/passage.
9. During selection accept only a strictly greater preregistered primary score;
   reject ties.
10. Freeze the selected candidate pool before ranking. Rerank only the identical
    pool hash and attach publication-level verbatim evidence.
11. Classify failures at the layer that failed and retain transparent negative
    results.
12. Freeze all code/config/prompt/skill/model/environment/pool hashes before an
    external Owner-run confirmation request.

## Gate metrics and estimation

- Gate C primary: `OUT Recall@100` against one preregistered protocol-matched
  reproduced baseline.
- Gate R primary: `OUT nDCG@100` against no rerank on the identical frozen pool.
- Gate C and R are independent claims.
- MDE is prospective design sensitivity and not an observed-result threshold.
- Confirmation reports exact n, point estimates, paired delta, deterministic
  10,000-resample paired-bootstrap 95% CI, rank-biserial effect, and W/L/T.
- Delta > 0 is observed improvement. CI lower > 0 is statistically supported
  superiority. Positive delta with CI crossing zero is a higher measured score
  with uncertain superiority. Delta <= 0 is no observed improvement.
- Holm applies only to preregistered additional confirmatory comparisons.

## Protected-data and split rules

Freeze seed, membership hashes, qrels snapshot, and OUT-positive counts before
development. Expose only adaptation/selection qrels to the optimizer. Disable
network re-download during measured optimization. Keep confirmation membership,
qrels, payloads, and per-query outcomes outside the workspace.

Confirmation is a one-command Owner-run evaluator outside this repository. The
repo emits only a hash-only request and accepts only a schema-validated aggregate
package. A qrels-informed all-1,247-query result is descriptive, not unseen
confirmation.

## A0-A3 adaptation study

A0 is frozen baseline; A1 human seed skill; A2 optimized skill with frozen
harness; A3 optimized skill plus declared typed policy. Start optimizer
calibration with GPT-5.6 Sol Medium and escalate to High only on qrels-blind
validity failure. Freeze model/provider/effort/budget, initial state, data,
evaluator, modules, repeats, and stopping identically for A2/A3. Luna is support
or a separate cost ablation. Third-party providers are development-only by
default. Silent fallback invalidates measured work.

## PageIndex boundary

PageIndex may be piloted only for BM25/dense-routed within-document evidence
after large-corpus retrieval selects publications. Compare it with a
section-aware BM25/dense locator and report traceability, hit rate, latency, cost,
and repeat agreement. Never use it automatically as first-stage DAPFAM retrieval.

## Evidence package

Return structured evidence before prose:

```text
query_id, family_id, publication_id, priority/publication dates,
routes and ranks, matched claim limitation, verbatim evidence span,
page/section/offset, supports|partial|contradicts|unclear,
source identifier, confidence, unresolved gaps
```

Every material statement points to exact evidence. Missing support produces
abstention or `unclear`. Do not express novelty, infringement, validity, or FTO
as a legal opinion.

## Dependency, dashboard, and mirror boundaries

Require Python 3.11 and use `pyproject.toml + uv.lock` as sole dependency
authority. Record exact patch/uv/OS/architecture/accelerator/CUDA/groups/extras/
lock hash in measured manifests and replay with `uv sync --locked`.

The dashboard is loopback-only and read-only for experiment artifacts. Owner
decisions are immutable typed ledger records. PDF streaming requires an exact
allowlist and creates a local tamper-evident receipt. MLflow accepts explicit
validated/redacted allowlisted files and rejects PDFs, qrels, membership,
confirmation outcomes, credentials, and protected per-query data.

## Delivery checklist

- show the protocol-matched baseline and exact hashes;
- show candidate exposure, oracle headroom, route overlap/unique recovery;
- prove frozen pool equality for ranking;
- report paired uncertainty, costs, all repeats, and failure taxonomy;
- label fixture, development, descriptive, and confirmation evidence correctly;
- preserve historical evidence and state that the system is decision support,
  not legal advice.
