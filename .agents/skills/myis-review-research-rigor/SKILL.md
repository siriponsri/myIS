---
name: myis-review-research-rigor
description: Audit a myIS research plan, experiment bundle, or claim-evidence package for governance, evidentiary relevance, falsifiability, scope, coherence, exploration integrity, and methodological rigor. Use before manifest finalization, held-out confirmation, publication, or when a severity-ranked independent research-quality review is requested.
---

# Review myIS Research Rigor

Perform an artifact-only semantic review. Do not execute experiments, fetch external evidence, reveal protected payloads, or repair the package during the review.

## Establish the review boundary

1. Read `AGENTS.md`, `00_governance/OWNER_GATES.md`, and `PLAN.md`.
2. Identify the package, claim set, dataset split, stage, and requested decision.
3. Require structural validation before semantic scoring. If structural validation failed or is absent, mark the review `blocked_structural` and list the missing prerequisites.
4. Verify that reading the package does not cross a protected-split boundary. Stop when authorization is absent or ambiguous.

## Read evidence in fixed order

Record the actual read order in the report:

1. Approval record, goal specification, and run specification.
2. `manifest.json`, if the package is finalized.
3. `validation_report.json` and MLflow receipts.
4. `prompt.json` and `flow.json`.
5. `progress.jsonl` and `runtime.jsonl`.
6. `result.json`, `metrics.json`, and `per_query_metrics.jsonl`.
7. Split manifest, config/prompt/skill hashes, relevant code revision, and claim-evidence mapping.

Take reported evidence at face value but check internal consistency. Missing evidence is not evidence of failure; mark it `not_assessable` and explain the consequence.

## Run governance checks first

Treat any of these as a blocking or critical finding, as appropriate:

- Missing or out-of-scope Owner approval.
- Protected data used for design, tuning, prompt optimization, or path selection.
- Split ID/hash mismatch, unpinned model/provider/skill/prompt, or undeclared fallback.
- Budget or gate-order violation.
- Result values that disagree across per-query artifacts, metrics, manifest, and MLflow.
- A finalized manifest that was mutated or does not bind all required artifacts.
- Paper claims sourced from logs or MLflow instead of validated scientific artifacts.

## Score six semantic dimensions

Read [references/rigor-review-schema.md](references/rigor-review-schema.md) for anchors and the report shape.

Score each dimension from 1 to 5:

1. **Evidence relevance**: Does the experiment design and metric substantively test the claim type?
2. **Falsifiability**: Are rejection thresholds concrete, scoped, and independently executable?
3. **Scope calibration**: Do conclusions match the dataset, split, model, seed, and budget actually evaluated?
4. **Argument coherence**: Do question, path choice, method, result, and claim form one traceable chain?
5. **Exploration integrity**: Are alternatives, failed paths, pivots, and stopping decisions documented honestly?
6. **Methodological rigor**: Are baselines, ablations, repeated seeds, metric definitions, latency/cost, and reproducibility adequate?

For DAPFAM, enforce the IS1 V0.1 contract:

- Treat retrieval relevance as retrieval evidence only, never legal novelty or freedom-to-operate evidence.
- Gate C uses one preregistered protocol-matched primary baseline and OUT Recall@100. Gate R uses the frozen no-rerank baseline and OUT nDCG@100 on the identical pool hash. Review the claims independently.
- During development/selection, accept only a strictly greater preregistered primary score and reject ties.
- On confirmation, classify positive point delta as observed improvement; use CI lower > 0 only for statistically supported superiority. A positive delta with a CI crossing zero is a higher measured score with uncertain superiority. MDE is prospective design sensitivity, not a pass threshold.
- Require exact n, point estimates, paired delta, deterministic 10,000-resample paired-bootstrap 95% CI, rank-biserial effect, W/L/T, comparison-family metadata, and input/output hashes.
- Apply Holm only to preregistered additional confirmatory comparisons. Verify that confirmation membership/qrels/per-query outcomes never entered the agent workspace.
- For optional A0-A3 work, require matched A2/A3 model/provider/effort/budget/data/evaluator/repeats/stopping and no silent fallback; do not substitute Track S for Gate C/R.

## Compile findings

For every finding, include severity, dimension, target artifact/entity, exact evidence locator or quote, factual observation, why it matters, and a concrete remediation. Sort `critical`, `major`, `minor`, then `suggestion`.

Calibrate grades conservatively. A score of 5 requires unusually complete evidence; a score of 1 indicates a fundamental flaw. Do not average away a governance-critical failure.

## Write without mutating evidence

- Before an active run is finalized, write `validation_report.json` and let the harness validate it before writing `manifest.json` last.
- For an already finalized bundle, write the review under `04_outputs/audits/rigor/<run_id>/rigor_review.json`; do not alter the bundle.
- For a plan or non-run package, write a uniquely named review under `04_outputs/audits/rigor/`.

Do not alter Git state, write to the Brain, or present an approval recommendation as Owner approval.

## Upstream attribution

This project-specific review adapts the six semantic dimensions and constructive finding format from Orchestra Research's `ara-rigor-reviewer`. The pinned source and adaptation record are in `00_governance/config/tools.lock.yaml`; the upstream MIT notice is preserved in `LICENSE.upstream`.
