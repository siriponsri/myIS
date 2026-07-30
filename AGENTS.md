# myIS Research Agent Contract

This repository is `myIS Research` (`myis-research`), protocol `1.0`, research
version `0.1`. `01_Research` is the active control plane and the only place
where canonical plans, schemas, manifests, receipts, and publication facts are
written.

## Read order

1. `PLAN.md`
2. `control/assets/reusable_assets.yaml`
3. `control/assets/REUSABLE_ASSET_MAP.md`
4. `control/campaigns/scope-autoindex-v1.yaml`
5. `control/execution-envelope.yaml`
6. `control/source-of-truth.yaml`
7. files owned by the active task

## Active vocabulary

Use only `P0_FOUNDATION`, `P1_CPU_BASELINE`, `P2_SCOPE_DEVELOPMENT`,
`P3_FINAL`, and `P4_PUBLICATION`. Use arms `R0`, `R0-W`, and `R1`.
`D1_START_CAMPAIGN` is the one-time standing campaign authorization;
`D2_OPEN_FINAL` and `D3_SUBMIT_RELEASE` are the only writable Owner decisions.
Do not add micro-gates. Historical vocabulary remains under `archive/` only.

## Safety boundary

- CPU-only, zero paid API, no GPU, no network model download, and no provider
  fallback through P1.
- Final split, qrels, membership, query IDs, per-query outcomes, credentials,
  and raw provider payloads stay in the Owner-local protected store.
- Git, MLflow, Dashboard, Brain, Obsidian, and Paper receive only validated
  aggregates, hashes, counts, and pointers.
- Never treat fixture evidence as measured evidence or a dashboard preview as
  authorization. This is decision support, not legal advice.

## Engineering rules

- `control/`, schemas, deterministic kernel, manifests, and receipts are
  canonical. MLflow is an additive mirror; Dashboard and Obsidian are
  projections.
- Use the reusable-asset registry before adapting App material. Keep App data
  in place and use pointers.
- Use canonical JSON and SHA-256 commitments. Stable IDs and lexical tie-breaks
  are mandatory for deterministic output.
- One report sync builds one read-model object and passes that object to every
  projection writer. Never copy metric values into manually edited notes.
- Preserve history. Archive before removing. Delete only exact, verified paths.
- Before commit/push run tests, layout, report drift, MLflow doctor, Brain
  literature validation when touched, and `git diff --check`.

## Agent responsibilities

Logical responsibilities are: Kernel, SCOPE/adapter, CPU baseline, Projection,
MLflow, Brain/memory, and Paper. Use actual agents only when a bounded task is
independent. The Owner only decides D2 and D3; routine defaults are encoded in
the campaign file and execution envelope.

## Memory lifecycle

Brain memory is pointer-only and has five kinds: `decision`, `evidence`,
`lesson`, `failed_attempt`, and `active_context`. Every note carries a source
URI, source SHA-256, evidence IDs, creation time, review time, and supersession
pointer. Stale active context is archived; failed attempts remain searchable but
cannot override run facts.

## Closeout

Report the exact phase, task, status, checks, changed files, untouched
protected surfaces, evidence class, blockers, and next automatic action. Do not
claim P1 measured completion unless a protected Owner-local run actually
completed. Keep the next action reversible and CPU-only until D2 is requested.
