# myIS Agent Contract

## Mission

Build and evaluate SCOPE as a reproducible patent-family retrieval study centered on a patent-native AutoIndex agent loop:

> Learn a compact, grounded representation that improves cross-domain candidate exposure without changing the benchmark answer key.

Optimize for completed evidence, not procedural volume. Keep the Owner informed without making routine engineering or candidate-selection work depend on repeated approval.

## Read order

At the repository root, read:

1. `README.md`
2. `PLAN.md`
3. `config/project.yaml`
4. `docs/PATENT_STRUCTURE.md`
5. `docs/OPTIMIZER_DECISION.md`
6. `docs/PAPER_STRATEGY.md`
7. `docs/ISAI_NLP_2026.md`
8. `docs/ARCHITECTURE.md`
9. `docs/RULES.md`
10. `docs/RUBRIC.md`
11. `NAMING.md`
12. relevant schemas, source, tests, and experiment configs

Use `INSTRUCTION.md` for the one-time migration or rebuild. Do not repeatedly execute migration steps after the target layout is established.

Codex loads `AGENTS.md` from the root toward the working directory. Avoid nested agent files unless a subdirectory truly needs narrower instructions; keep repository-wide scientific invariants here.

## Authority

Use this precedence:

1. current user instruction;
2. safety, credentials, licensing, and destructive-action constraints;
3. frozen data, split, evaluator, and schema contracts;
4. `config/project.yaml`;
5. this file;
6. `PLAN.md`;
7. supporting docs;
8. archived historical plans.

If repository evidence conflicts with a status statement, preserve both and report the discrepancy. Never rewrite history to simplify a narrative.

## Default autonomy

Proceed without asking the Owner for:

- repository inspection;
- reversible local edits within the requested scope;
- deterministic preprocessing and validation;
- fixture creation;
- unit and integration tests;
- parser fallback selection defined by config;
- candidate rejection by predeclared rules;
- no-cost local smoke runs;
- iterations within an already approved campaign envelope;
- MLflow, dashboard, Obsidian, and presentation projections;
- anonymous manuscript scaffolding and venue-compliance checks;
- documentation and manifest updates.

Ask only for:

- `D1 START_CAMPAIGN`: paid or measured work under a bound budget, provider, data, time, and egress envelope;
- `D2 OPEN_FINAL`: once-only access to the frozen 872-query final evaluation;
- `D3 RELEASE`: submission, publication, deployment, or external sharing;
- an otherwise required destructive, credential, licensing, legal, or materially out-of-scope action.

Do not turn candidate failures, missing optional features, or ordinary implementation choices into Owner gates. Choose the documented safe default and record it.

## Paper-first redesign

The current plan and module tree are proposals, not sacred architecture.

Codex may restructure or re-plan the project when an evidence-backed redesign:

- makes the scientific contribution easier to state;
- removes framework stacking;
- improves falsifiability or ablation clarity;
- reduces confounds or leakage risk;
- lowers implementation burden without weakening evidence;
- preserves the immutable benchmark and authorization boundaries.

Before a major build, conduct one explicit novelty and reviewer stress test using `docs/PAPER_STRATEGY.md`. Record the decision and continue; do not ask the Owner to select among routine architecture variants.

Preserve prior evidence and decisions even when replacing the active architecture. Never preserve a weak design merely because code already exists.

The current evidence-backed decision keeps AutoIndex-style representation search and the Analysis/Structure/Auditor architecture central. Do not demote them to optional infrastructure without recorded empirical or implementation evidence. SCOPE-DSL is the controlled candidate surface within that loop, not a replacement story.

Prioritize the submission-critical vertical slice over complete repository migration. Preserve legacy assets, but do not wait for unrelated cleanup before implementing the DAPFAM baseline, compiler, agent loop, or FiNE-Patents adapter.

## Scientific invariants

- DAPFAM evaluation is family-level.
- `OUT Recall@100` is the representation-search objective; report DAPFAM-primary nDCG@100 prominently as a confirmatory endpoint.
- Report `ALL`, `IN`, and `OUT` together.
- Bind dataset revision, file hashes, split hash, family map, query/corpus views, evaluator, config, code, and environment.
- Keep representation search, retrieval policy search, and retriever changes separate.
- Hold the retriever fixed when testing representation leverage.
- Use a budget-matched flat baseline.
- Include the train-selected DAPFAM deterministic-window `maxP` control and report its larger index honestly; it is an efficiency comparator outside the four-unit candidate cap.
- Compare the agent loop with random or enumerated search under the same candidate-evaluation budget.
- Freeze the DAPFAM-selected compiler before FiNE-Patents transfer.
- Keep SkillOpt separate and conditional on frozen representation leverage plus ranking headroom.
- Do not compare published scores as if protocols match until they are reproduced under the same evaluator.
- Preserve per-query results for paired analysis.
- Treat a negative result as valid; never move thresholds after seeing protected results.
- Do not use a scored human-tree arm. Standards and prior work define the safety envelope only.

## Data and leakage

Split roles:

- train 250: optimizer and evaluator;
- selection 125: evaluator only, once for a frozen shortlist;
- final 872: evaluator only, once after full freeze and `D2`.

Protected surfaces:

- qrels outside the authorized role;
- final query identities and metrics before freeze;
- family mappings;
- `IN`/`OUT` labels;
- metric code;
- selection rules;
- evaluator configuration.

Agents must not receive raw selection or final feedback. Logs and prompts must not contain protected examples, credentials, or full environment dumps.

If protected access occurs accidentally:

1. stop the affected run;
2. preserve the access log;
3. mark the candidate contaminated;
4. do not use its result for confirmation;
5. report the incident and recovery plan.

## Representation contract

Use a typed evidence graph with hierarchical containment and typed cross-links.

Every indexed unit must:

- belong to the benchmark-native `record_id`; DAPFAM records also carry `family_id`;
- point to one or more original source fields and character spans;
- carry source hashes;
- record parser strategy, confidence, and fallback status;
- validate against `schemas/patent-representation.schema.json`.

Do not invent publication IDs. DAPFAM consolidates family fields and does not provide publication provenance for each selected text field.

Do not assume:

- line breaks are claim boundaries;
- claims form a strict tree;
- headings are always present or ordered;
- family members share identical claim text.

When confidence is insufficient, use grounded unparsed blocks or deterministic windows. Never fabricate structure.

The compiler may emit at most four searchable units per family. Abstractive summaries are disabled in the primary experiment.

FiNE-Patents is an external, zero-retuning confirmation surface. Its adapter preserves native cited-document and passage identities. It may map fields into the canonical record interface but may not change the frozen SCOPE-DSL specification or official evaluator.

## Agent roles

### Analysis Agent

- requested profile: GPT-5.6 Sol with medium reasoning;
- read-only;
- reads train diagnostics only;
- analyzes successes, misses, regressions, parser behavior, and index cost;
- produces one bounded, falsifiable hypothesis.

### Structure Agent

- requested profile: GPT-5.6 Sol with medium reasoning;
- writes only to a new candidate workspace;
- converts the current hypothesis into one schema-valid SCOPE-DSL JSON specification;
- edits only that candidate specification;
- cannot change dependencies, evaluator, qrels, split, family map, or budget rules.

### Protocol & Representation Auditor

- requested profile: GPT-5.6 Sol with high reasoning;
- read-only;
- receives a blinded packet only for eligible incumbents and the freeze package;
- returns `PASS`, `REVISE`, or `REJECT` under `docs/RUBRIC.md`;
- cannot edit the candidate or select by metric;
- if it suggests a new hypothesis, queue it as a budgeted future candidate rather than silently changing the incumbent.

### Deterministic harness

- validates schema and grounding;
- compiles candidate specifications with the frozen deterministic compiler;
- builds indexes;
- retrieves and aggregates to families;
- computes metrics and cost;
- applies eligibility and tie-break rules;
- writes manifests and MLflow records;
- creates freeze packages.

The harness is the metric authority.

## Candidate boundary

The Structure Agent may read only:

- bounded train diagnostics and prior candidate summaries;
- explicit non-secret config;
- their own candidate workspace.

It may write only one declarative JSON specification inside the candidate workspace. It may not write or modify executable code.

Enforce:

- SCOPE-DSL schema and semantic validation before compilation;
- frozen compiler and validator hashes;
- process timeout;
- memory and output limits;
- no uncontrolled network;
- no dependency installation;
- no shell expansion over broad paths;
- no evaluator import or modification;
- maximum four searchable units per family;
- deterministic seeds;
- complete source provenance.

Reject the candidate automatically on violation. Do not ask the Owner how to handle it.

## Work loop

For implementation:

1. inspect current state and Git diff;
2. state a short plan;
3. implement the smallest coherent change;
4. test the changed behavior;
5. update docs, schemas, and manifests when behavior changed;
6. report outcome, evidence, and next step.

For the patent-native AutoIndex loop:

1. Analysis Agent diagnoses train evidence;
2. Structure Agent creates one bounded SCOPE-DSL candidate;
3. deterministic checks reject invalid candidates;
4. harness builds and evaluates valid candidates;
5. selection rules identify an eligible incumbent;
6. Auditor reviews only a new incumbent;
7. journal records the outcome and cost;
8. stop by convergence or budget rules.

Do not optimize multiple scientific axes in one candidate.

## Repository and storage

Git contains:

- code and tests;
- configs and schemas;
- small synthetic fixtures;
- compact run and freeze manifests;
- aggregate reports, figures, and publication assets;
- literature metadata and useful digests.

`MYIS_STORE` contains:

- raw and normalized datasets;
- qrels and protected split material;
- indexes and models;
- raw rankings and per-query artifacts;
- candidate workspaces;
- caches;
- MLflow database and artifacts.

Never commit secrets, corpora, qrels, model weights, raw indexes, MLflow databases, or large transient outputs.

## Observability

- Use structured JSON logs with run, candidate, stage, and event IDs.
- MLflow is the canonical run registry and metric store.
- Every MLflow run links to a validated run manifest.
- The dashboard is read-only, loopback-only, and derives from canonical records.
- Obsidian reports are generated, source-linked projections.
- Presentation tables and figures use the same manifest and metric export.
- Notebooks may explore or visualize but may not define canonical metrics.

## Validation

Run the narrowest relevant checks during development and the full configured suite before handoff.

At minimum validate:

- formatting and lint;
- unit and integration tests;
- all three JSON Schemas and example instances;
- deterministic representation hashes;
- source-span bounds and hashes;
- family aggregation;
- metric fixtures;
- config and manifest completeness;
- no protected-data access;
- no large or secret tracked file;
- loopback-only dashboard binding;
- report consistency with MLflow and manifests.

Do not state that a command passed if it was not run. If a dependency or service prevents validation, report the exact unverified surface.

## Results and claims

Every measured result must have:

- immutable run ID;
- status: `complete`, `failed`, `invalid`, or `superseded`;
- protocol, data, split, code, config, and environment identity;
- representation, retriever, policy, and seed;
- `ALL`, `IN`, and `OUT` metrics;
- index, latency, parser, provenance, and cost diagnostics;
- artifact hashes;
- any audit verdict.

Do not use `best`, `final`, or `SOTA` as an unsupported status. `final` requires a freeze manifest and authorized final evaluation.

## iSAI-NLP submission

The active target is iSAI-NLP 2026 Track 1. Follow `docs/ISAI_NLP_2026.md`.

For the review package:

- use the official IEEE conference manuscript format;
- remain at or below six pages including references and visual material;
- maintain double anonymity in text, URLs, acknowledgements, and PDF metadata;
- generate every result table from canonical metric exports;
- keep PatenTEB, dense/hybrid, and SkillOpt work from delaying the required DAPFAM-plus-FiNE core;
- do not submit or externally share the manuscript before `D3`.

## Code review rules

Flag:

- any path by which an agent, candidate workspace, or compiler can see protected qrels or evaluator feedback;
- any ungrounded text entering the primary index;
- any invented publication provenance;
- metric or family-aggregation changes mixed with a representation candidate;
- result files without complete manifests;
- dashboard or notebook calculations that disagree with canonical evaluator output;
- silent model, prompt, dependency, or dataset substitution;
- a new approval gate for a deterministic or reversible action.

Prefer a concrete safe fix and a regression test.

## Stop conditions

Stop the current scientific run on:

- leakage or protected-split access;
- provenance failure;
- nondeterminism that changes rankings;
- evaluator, qrel, split, or family-map mutation;
- cost or resource-cap breach;
- missing required model in a measured campaign;
- destructive or external action outside current authorization.

A normal candidate regression is not a stop condition for the project; record it and continue within the campaign rules.

## Session closeout

End with:

- outcome first;
- changed files;
- tests and exact results;
- spend and protected-split access;
- unresolved risks;
- the next automatic step;
- a decision request only if `D1`, `D2`, `D3`, or a safety boundary is actually reached.
