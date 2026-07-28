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

For DAPFAM, enforce the project contract:

- Treat retrieval relevance as retrieval evidence only, never legal novelty or freedom-to-operate evidence.
- Compare the reproduced reference, fixed human harness, SkillOpt baseline, and HarnessOpt under shared evaluator, split hashes, budgets, model roles, and module pool.
- Require HarnessOpt to exceed both SkillOpt and the reproduced reference on OUT NDCG@100 and OUT Recall@100.
- Report three fixed-seed means plus absolute and relative deltas. Do not use confidence intervals as a pass/fail rule.
- Check IN NDCG@100 and Recall@100 drops are each no worse than 0.01 absolute and invalid-query rate is at most 1%.

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
