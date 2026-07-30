# myIS Research Agent Contract

## Read order

1. `PLAN.md`
2. `control/program.yaml`
3. `control/campaigns/scope-autoindex-v1.yaml`
4. `control/source-of-truth.yaml`
5. `control/assets/reusable_assets.yaml`
6. files owned by the active task

## Authority

- `01_Research` is the active control plane. Git and immutable validated artifacts are canonical.
- Dashboard, MLflow, Obsidian/Brain, Linear, and Paper are rebuildable projections and pointers.
- Owner decisions are limited to `D1_START_CAMPAIGN`, `D2_OPEN_FINAL`, and `D3_SUBMIT_RELEASE`. D1 is standing authorization; do not create micro-gates.
- AutoIndex/SCOPE is the core campaign. SkillOpt is disabled unless its admission criteria in the campaign config pass.
- Use Python 3.11 and `pyproject.toml + uv.lock` only.

## Protected boundary

Never open, copy, log, or project protected rows, qrels, split membership, query IDs, per-query outcomes, credentials, or raw provider payloads. Paid APIs, GPU jobs, final-set access, and external release require the applicable Owner decision and explicit resource authorization. Owner-local processing emits aggregate/count/hash receipts only.

## Execution

1. Validate Git state, campaign config, reusable assets, and latest valid session.
2. State one falsifiable hypothesis and the exact editable surface.
3. Reproduce the matched baseline before evaluating a method.
4. Run deterministic tests before any measured work.
5. Accept a candidate only on strict primary-score improvement; ties reject.
6. Freeze code, config, dataset, model, evaluator, artifact, and environment hashes.
7. Generate the canonical read model, then regenerate Dashboard/Obsidian/Paper projections.
8. Record a new `myis.research-session.v2` capsule; never edit historical capsules.

## Completion

Run focused and full tests, `myis-report check`, MLflow doctor, protected-content scan, archive/reference validation, and `git diff --check`. Report changed files, archived legacy roots, untouched protected surfaces, evidence class, current D1-D3 state, next resources, and blockers. This system is decision support, not legal advice.
