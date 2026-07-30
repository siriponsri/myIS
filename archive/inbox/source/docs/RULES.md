# Research Rules and Decision Boundaries

## 1. Purpose

These rules replace a large chain of routine Owner gates with three meaningful decisions and deterministic internal checks.

The Owner should decide scope, spend, final opening, and external release. The harness should decide whether a candidate is valid, reproducible, within budget, and better under the frozen metric.

## 2. The three Owner decisions

### D1 — START_CAMPAIGN

One approval binds:

- dataset and revision;
- train/selection/final split manifest;
- provider and model profiles;
- maximum spend;
- maximum elapsed time;
- permitted compute;
- permitted data egress;
- primary protocol and endpoint.

After `D1`, routine candidate iterations may continue without more approval until a bound is reached.

### D2 — OPEN_FINAL

One approval permits the frozen system and frozen baselines to evaluate the final 872 queries once.

Required packet:

- freeze manifest;
- code, dependency, config, data, split, evaluator, prompt, and model hashes;
- selected candidate and baseline IDs;
- selection result;
- audit verdict;
- planned final commands and expected maximum cost.

No tuning is allowed after final metrics are visible.

### D3 — RELEASE

One approval permits:

- paper submission;
- public repository or artifact release;
- public dashboard;
- external data or result sharing;
- deployment.

Drafting local manuscripts, reports, and presentation assets does not require `D3`.

## 3. Internal checkpoints, not Owner gates

The harness handles:

- data integrity;
- schema validity;
- parser confidence and fallback;
- provenance coverage;
- deterministic reruns;
- metric computation;
- index-unit and storage caps;
- latency and cost measurement;
- candidate eligibility;
- convergence;
- Auditor invocation;
- freeze-package completeness.

A failed checkpoint rejects or invalidates a candidate and records the reason. It does not block the Owner or require a meeting.

## 4. Scientific firewalls

Never permit candidate or agent access to:

- selection or final qrels;
- final metrics before freeze;
- evaluator source as an editable surface;
- family-map mutation;
- `IN`/`OUT` labels as representation features;
- hidden baseline outputs used to shape a candidate;
- unrestricted external search during a measured run.

Keep separate:

- representation search;
- retriever selection;
- retrieval-policy optimization;
- reranking;
- final confirmation.

The primary representation search is the patent-native AutoIndex loop. The Structure Agent writes only schema-valid SCOPE-DSL; it cannot modify executable compiler code. SkillOpt is admitted only after frozen held-out structure leverage, ranking headroom, an equal-budget simple-search control, and a safe iSAI-NLP core.

## 5. Grounding rules

- Every primary indexed text unit must map to exact source spans.
- Every span must validate against a source-field hash.
- Parser uncertainty must be explicit.
- Failed parsing must preserve text through a fallback.
- Do not invent publication provenance.
- Abstractive summaries are disabled in the primary study.
- A future summary arm requires explicit grounding diagnostics and a separate protocol ID.

## 6. Automatic defaults

Unless frozen config says otherwise:

- prefer the smallest valid representation;
- use deterministic parsing before LLM extraction;
- use CPU for preprocessing, BM25, evaluation, and reporting;
- cap learned SCOPE candidates at four searchable units per family; the declared `R0-W` passage control is exempt and must report its full index cost;
- invoke the high-reasoning Auditor only for eligible incumbents and freeze;
- stop after three iterations without a new eligible incumbent;
- stop at the cost cap;
- preserve a failed or invalid run rather than deleting it;
- choose a fallback rather than asking the Owner to repair an individual record.

## 7. Cost and resource rules

- Preferred campaign cost is at most USD 100.
- Absolute ceiling without a new `D1` is USD 200.
- Log estimated and actual cost for every run.
- Do not silently change model, reasoning effort, hardware, or provider.
- Dense/hybrid GPU work is conditional on representation leverage and the `D1` envelope.
- A cost cap stops execution automatically.

## 8. Result rules

A measured claim requires:

- complete run manifest;
- validated protocol ID;
- dataset and split identity;
- code/config/environment identity;
- family-level metrics;
- parser, index, latency, cost, and provenance diagnostics;
- immutable artifacts;
- valid status.

Cross-paper scores are contextual benchmarks until reproduced under the same protocol.

The iSAI-NLP submission core requires DAPFAM plus zero-retuning FiNE-Patents transfer. PatenTEB, dense/hybrid, and SkillOpt are stretch work and cannot delay the required six-page anonymous manuscript. Local drafting is automatic; actual submission requires `D3`.

## 9. History and correction

- Never rewrite prior approvals, negative results, or frozen evidence.
- Corrections create a new version and a `supersedes` link.
- Archived plans remain citable but are not active authority.
- If current repository state differs from this proposal, preserve and explain the difference.

## 10. When to pause outside D1-D3

Pause only for:

- destructive or hard-to-recover action;
- credential or permission failure;
- unresolved data license or legal constraint;
- unexpected protected-data exposure;
- a scientific change that would invalidate the frozen protocol;
- work materially outside the user's request.

Do not pause for lint choices, folder names already defined here, parser fallbacks, a negative candidate, or an optional feature that can be deferred.
