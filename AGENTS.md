# myIS Research Agent Contract

This contract applies to every agent and adapter operating in this repository.

## Read order

1. `PLAN.md` - canonical Phase -> Task execution authority.
2. `FULL_RESEARCH_TRACK_PLAN.md` - scientific protocol and claim boundaries.
3. `LOCAL_RESEARCH_HARNESS_BUILD_PLAN.md` - implementation contracts.
4. `00_governance/OWNER_GATES.md` - approval boundaries.
5. `00_governance/OPERATIONS.md` - local commands and recovery.
6. Files owned by the active task.

## Identity and versioning

- Active program: `myIS Research`; machine ID: `myis-research`; protocol: `1.0`.
- Track C and Track S research version: `0.1`. Package version remains `0.1.0`.
- Earlier program labels remain only in frozen evidence and legacy provenance;
  active emitters use the identity above.
- Measured manifests bind identity through `ResearchVersionSpec`. Package release
  versions and the research protocol are independent.

## Authority and safety

- The Owner is final decision maker; silence is not approval.
- Stop on conflicting instructions, drift, ambiguous scope, or a failed hash or
  provenance check that can change scientific interpretation.
- Preserve user work and history. Delete only exact Owner-approved paths.
- Do not access paid APIs, GPU jobs, qrels evaluation, protected confirmation
  data, external publication surfaces, or the App repository without approval.
- Git and validated immutable artifacts are canonical. Brain, Linear, dashboard,
  and MLflow are projections and pointers.

## Scientific invariants

- Paper D is frozen historical evidence.
- DAPFAM measures family-level retrieval relevance, not novelty, infringement,
  freedom to operate, validity, or other legal truth.
- Active causal path: `Track C -> frozen C1 harness -> Track S`.
- There is no independent active ranking/evidence lane. Ranking/headroom is a
  Track C diagnostic on the identical frozen pool. Evidence transfer is deferred.
- Track C arms are C0 zero-tuned CrossRoute and C1 metric-tuned CrossRoute.
- Track C primary comparison is C1-C0 on `OUT Recall@100`. C0-B1 and C1-B1 are
  the preregistered additional Holm family.
- Track S arms A2, A2L, and A3 are mandatory matched-budget parallel descendants
  of the same A1 state. Primary comparison is A3-A2 on the untouched joint test.
- Development selection requires a strictly greater primary score; ties reject.
- Confirmation reports paired delta, exact n, 95% paired-bootstrap CI,
  rank-biserial effect, and win/loss/tie counts. CI strength is not a hard gate;
  MDE is prospective sensitivity, never an observed threshold.

## Data and confirmation boundary

- Shared membership commitment: seed `42`, `C_TRAIN=250`, `C_SELECTION=125`,
  untouched joint test `872`. Estimated OUT-positive counts `181/91/633` are not
  frozen facts; the protected Owner process must compute and commit exact values.
- Track C and Track S use separate evaluators, optimizers, budgets, manifests,
  artifacts, and data firewalls despite shared IDs.
- Confirmation membership, qrels, payloads, and per-query outcomes stay outside
  the agent workspace; measured optimization cannot re-download them.
- This repo emits only a hash-only `ConfirmationRequest` and ingests only a
  schema-validated aggregate package.
- A qrels-informed full-1,247 DAPFAM result is descriptive, not unseen confirmation.

## Locked Track C protocol

- B0: `Llama-Embed-Nemotron-8B` TAC dense top-400 at revision
  `aa3b43a495a9b280d1bdb716da37c54bb495d630`; B1 adds BM25 min-max
  `0.7/0.3`; B2 is naive TAC/Abstract/Claim1 RRF. Pure BM25 and
  `patembed-base` are secondary controls.
- C0 uses six atomic routes: TAC BM25/dense, independent-claim BM25/dense, and
  grounded-mechanism BM25/dense. Quotas are `100/100/50/50/50/50`, raw budget
  `400`, RRF `k=60`, final top-100.
- C1 may change only route enablement, quotas, fusion, RRF, and pool/rerank depth
  under raw budget 400. Prompts, query views, encoder, and reranker instructions
  are frozen. Search at most 100 valid C_TRAIN configurations and submit exactly
  five Pareto finalists to C_SELECTION once.

## Locked Track S protocol

- Target `qwen/qwen3-30b-a3b-instruct-2507`, non-thinking, OpenRouter CoreWeave
  BF16 provisional, with no routing, fallback, or parameter dropping.
- CoreWeave preflight is a hard gate. One identical retry is allowed only for a
  transport error.
- A2 uses SkillOpt `v0.2.0` commit
  `51d0a4d96e88558c84dee637f98e24e3fb2d1547`; A2L derives from
  `4cb4eeef1f95375a9179737ab94cf5e64b9647c6`.
- Seeds `11,23,47`; rollout cap `160/seed`, `480/arm`; USD 20/arm, USD 30 shared,
  USD 90 target, USD 100 hard stop. A3 uses only the typed allowlist. A2L-P and
  broad A3X are future exploratory lanes.

## Harness, dependency, and projection rules

- The deterministic kernel owns schemas, lifecycle, approvals, identity,
  splits/hashes, budgets, family deduplication, tie-breaking, metrics,
  statistics, manifests, redaction, protection, and immutable writes.
- LLM output remains a proposal until typed validation passes. No silent
  model/provider fallback is allowed.
- Python 3.11 and `pyproject.toml + uv.lock` are sole dependency authority.
- Dashboard is loopback-only, aggregate/hash/count-only, and read-only for run
  artifacts. Owner decisions remain immutable hash-chained records.
- MLflow experiments are additive mirrors:
  `myis-research-{bootstrap,catalog,track-c,track-s,joint,publication}`.
- Brain has one serial writer. Linear mirrors PLAN and never opens gates.

## Required execution loop

1. Inspect Git, active Phase/Task, approval, and latest valid manifest.
2. Validate identity, lock, integrity, protected surfaces, and budget.
3. Reproduce the protocol-matched baseline before proposing a new method.
4. State one falsifiable hypothesis and exact editable surface.
5. Make the smallest bounded change and run deterministic tests first.
6. Evaluate only the authorized development/selection surface.
7. Compare paired outputs and classify failures by layer.
8. Keep a candidate only on strict primary-score improvement.
9. Stop at budget, invalidity, leakage, flat surface, or missing headroom.
10. Freeze code/config/prompt/skill/model/environment/pool hashes before an
    Owner confirmation request.

## Completion

List changed files and untouched protected surfaces; run restructure, integrity,
literature, relevant test, MLflow doctor, and `git diff --check` checks; state the
exact environment; separate fixture, development, descriptive, and confirmation
evidence; report blockers without claiming success from partial work; and state
that this system is decision support, not legal advice.
