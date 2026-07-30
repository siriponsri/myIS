# Codex Migration and Implementation Instruction

## 1. Inbox staging mode

This package may arrive under `/inbox` together with PDFs, research reports, and older plans.

Treat the directory containing this file as `INBOX_ROOT`.

Rules:

- treat `INBOX_ROOT` as read-only input;
- inventory files recursively and record hashes before acting;
- locate the actual Git repository separately;
- do not run experiments, create environments, or place large outputs in `/inbox`;
- do not copy `AGENTS.md`, plans, configs, or schemas over existing repository files without a conflict-aware migration;
- do not assume `AGENTS.md` in `/inbox` was automatically loaded by Codex;
- explicitly read this package before planning;
- preserve every unclassified source until its role is resolved;
- use `INBOX_MANIFEST.md` as the handoff inventory;
- update repository files with normal Git-aware edits, not by treating `/inbox` as the repository.

The inbox handoff manifest itself is not an active repository contract and does not need to be installed after migration.

## 2. Assignment

Transform the existing myIS research repository into a submission-ready SCOPE project while immediately implementing the smallest no-cost, locally testable vertical slice. Preserve and migrate legacy assets incrementally; do not make a complete repository reorganization a prerequisite for the DAPFAM baseline, compiler, agent loop, or FiNE-Patents adapter.

Do not treat this file as permission to run paid models, rent GPUs, access protected selection/final qrels, publish externally, or rewrite historical evidence.

## 3. Required read order

Before editing:

1. the actual repository-root `AGENTS.md`, if present;
2. inbox `INBOX_MANIFEST.md`;
3. inbox `README.md`;
4. inbox `PLAN.md`;
5. inbox `config/project.yaml`;
6. inbox `docs/PATENT_STRUCTURE.md`;
7. inbox `docs/OPTIMIZER_DECISION.md`;
8. inbox `docs/PAPER_STRATEGY.md`;
9. inbox `docs/ISAI_NLP_2026.md`;
10. inbox `docs/ARCHITECTURE.md`;
11. inbox `docs/RULES.md`;
12. inbox `docs/RUBRIC.md`;
13. inbox `NAMING.md`;
14. all three inbox JSON Schemas and their examples in `schemas/`;
15. relevant source reports and papers identified by the inbox manifest;
16. the existing repository tree, current Git status, current plans, ledgers, experiment manifests, MLflow integration, dashboard, Obsidian generator, and Paper A-D artifacts.

Do not assume that the proposed package describes files that already exist in the repository. Verify first.

## 4. Authority order

When instructions conflict, use this order:

1. user instruction in the current task;
2. safety, credentials, licensing, and destructive-action constraints;
3. frozen dataset, split, evaluator, and schema contracts;
4. `config/project.yaml`;
5. repository-root `AGENTS.md`;
6. `PLAN.md`;
7. supporting documentation;
8. historical plans, which remain evidence but are not active implementation authority.

Never alter historical records to make them appear consistent with the new plan.

## 5. First response and continuation

After inspection, report:

- the actual current state;
- the proposed file moves and replacements;
- assets that will be preserved unchanged;
- conflicts or missing dependencies;
- a short implementation plan with verification commands;
- whether any requested work crosses `D1`, `D2`, or `D3`.

Then begin reversible, local, no-cost implementation unless the user limited the task to planning. Do not wait for the Owner to acknowledge the status report.

Do not ask the Owner to choose routine filenames, module boundaries, parser defaults, test fixtures, formatting tools, or retry behavior. Use the documented defaults, record assumptions, and continue.

## 6. Historical state

Preserve the original ledgers and artifacts that establish:

- `F0` closed;
- `G0` approved;
- `F1` waiting for gate;
- `G1` pending;
- prior Paper A-D claims and evidence;
- prior prompts, reports, decisions, and benchmark notes.

Represent the new plan as a migration with a date and source commit. Do not relabel an old gate as approved, delete a negative result, or overwrite a frozen artifact.

If the repository has advanced since this instruction was written, trust inspected repository evidence over this status summary and document the difference.

## 7. Paper-first redesign

The proposed tree and plan are a strong starting hypothesis, not a requirement to preserve weak architecture.

Before substantial measured implementation:

1. reconstruct the strongest claims and failures from Paper A-D;
2. compare SCOPE against AutoIndex, DAPFAM, PageIndex, FiNE-Patents, Patent Claim Structure Recognition, and patent embedding benchmarks;
3. write a one-page novelty matrix;
4. state the strongest reviewer objection;
5. preserve AutoIndex and the Analysis/Structure/Auditor architecture as the active lineage while testing whether the patent-specific extension is more than “AutoIndex applied to patents”;
6. simplify or redesign the method, experiment matrix, phases, and repository ownership where that improves the paper;
7. keep the immutable scientific boundaries in this package;
8. record the resulting active design and why alternatives were rejected.

Codex may replace the proposed module tree, phase order, method name, or optional arms if the redesign produces a clearer contribution and remains compatible with:

- family-level DAPFAM evaluation;
- protected split roles;
- grounded source provenance;
- frozen evaluator and family mapping;
- budget-matched comparisons;
- retained MLflow, dashboard, Obsidian, and presentation outputs;
- the three Owner decisions.

This is a compact internal design review, not an Owner gate and not a reason to postpone the vertical slice. Continue with the best evidence-backed design unless the primary research objective or authorization boundary would change.

Do not overbuild infrastructure before the paper thesis, minimum experiment, and falsification criteria are explicit. Use `docs/ISAI_NLP_2026.md` to prioritize submission-critical work over broad cleanup.

## 8. Migration strategy

Use a non-destructive migration:

1. create the target structure alongside current files;
2. move only files whose ownership is clear;
3. preserve history with `git mv` when operating in Git;
4. leave a compact archive index for superseded active documents;
5. update internal links;
6. validate the new structure;
7. remove duplication only after the canonical replacement is verified.

Do not delete or rewrite user changes in a dirty worktree. Do not use destructive Git reset or checkout operations.

### Suggested mapping

| Existing material | Target |
|---|---|
| active Python packages | `src/myis/` |
| tests and smoke fixtures | `tests/` |
| active experiment configs | `experiments/configs/` |
| experiment registry and compact manifests | `experiments/registry/` |
| literature catalog and useful digests | `evidence/` |
| historical gates, approvals, and superseded plans | `archive/` with an index |
| MLflow adapters | `src/myis/observe/` |
| dashboard application | `dashboard/` |
| Obsidian report generator | `src/myis/report/` |
| generated Obsidian Markdown | `reports/obsidian/` |
| figures and manuscripts | `reports/figures/`, `reports/manuscripts/` |
| dashboard or paper presentations | `reports/presentations/` |
| large datasets, indexes, models, raw predictions | external `MYIS_STORE`, never Git |

Do not flatten the 153-paper evidence catalog into one untraceable summary. Preserve source identity and citation metadata even if the active documentation becomes smaller.

## 9. Minimal implementation order

### Step 1 — Environment and package

- confirm the supported Python version from `pyproject.toml`;
- keep `uv.lock` authoritative;
- avoid adding dependencies unless the existing stack cannot satisfy the contract;
- add a `myis` CLI entry point;
- ensure configuration loads without credentials;
- create a tiny local fixture independent of DAPFAM qrels.

### Step 2 — Contracts

- validate `config/project.yaml`;
- validate all three JSON Schemas and their examples;
- implement run-manifest creation;
- implement content hashing and environment capture;
- implement the external-store path resolver using `MYIS_STORE`;
- fail clearly if protected data is requested without authorization.

### Step 3 — DAPFAM inspection

- bind repository revision and file hashes;
- preserve the dataset's actual field name `earliest_claim_jusrisdiction`;
- normalize it internally only through an explicit mapping;
- inspect schema, nulls, IDs, text lengths, and family counts;
- do not open qrels beyond the authorized split role;
- produce a machine-readable audit plus an Obsidian projection.

### Step 4 — Representation

- implement source-span records;
- implement a deterministic flat representation first;
- implement claim and description parsers with confidence and fallbacks;
- build the typed evidence graph;
- compile one to four searchable units per family;
- validate that every indexed unit is grounded;
- forbid publication-level assertions not supported by DAPFAM.

### Step 5 — Retrieval and evaluation

- implement or reuse the frozen BM25 baseline;
- implement the train-selected deterministic-window BM25 control with `maxP`;
- aggregate unit scores to family scores deterministically;
- reproduce family-level Recall and nDCG;
- report `ALL`, `IN`, and `OUT`;
- add tests with hand-checkable rankings and qrels;
- ensure evaluator code cannot be modified through candidate specifications or compiler configuration.

### Step 6 — Patent-native AutoIndex loop

- implement `SCOPE-DSL` as the allowlisted candidate surface;
- keep the compiler versioned, deterministic, and outside agent write authority;
- make the Analysis Agent read-only;
- let the Structure Agent write only one schema-valid JSON specification inside a new candidate directory;
- run deterministic validation before indexing;
- invoke the Auditor only for eligible incumbents;
- log every proposal, rejection reason, specification hash, compiler hash, metric, and cost;
- compare the agent loop with random or enumerated search under the same candidate-evaluation budget;
- never send selection or final examples to any agent.

### Step 7 — Independent evidence transfer

- implement the FiNE-Patents adapter and official evaluator path;
- freeze the DAPFAM-selected specification before transfer;
- compare the frozen compiler with flat/window evidence baselines without representation retuning;
- bind dataset revision, license, native IDs, and evaluator;
- treat PatenTEB, dense/hybrid, and SkillOpt as stretch work until the six-page core is safe.

### Step 8 — Observability and submission assets

- keep structured logs;
- retain MLflow as the canonical run and metric registry;
- make the dashboard read-only and loopback-only;
- generate Obsidian reports from manifests and MLflow;
- generate presentation-ready tables and figures from the same records;
- create the anonymous iSAI-NLP manuscript path and compliance checklist;
- label projections as generated and non-authoritative.

## 10. DAPFAM-specific requirements

The source data is family-level and contains flattened text fields. Therefore:

- use `family_id`, not an invented `publication_id`;
- do not assume all fields come from the same publication;
- do not assume line breaks identify claim boundaries;
- treat claim references as graph edges, not a strict tree;
- record claim-parser confidence;
- fall back to `claim_block_unparsed` when parsing is unreliable;
- detect description headings only with confidence and order checks;
- fall back to deterministic windows for irregular descriptions;
- keep exact source character offsets and hashes;
- cap learned SCOPE candidates at four searchable units per family; allow the declared `R0-W` passage baseline to exceed the cap while logging its cost;
- keep abstractive summaries disabled for the primary experiment.

The full rationale and measured query-file observations are in `docs/PATENT_STRUCTURE.md`.

## 11. AutoIndex and SCOPE-DSL requirements

Candidate specifications may change only:

- claim and section segmentation strategy;
- enabled structural nodes and searchable views;
- deterministic window size and overlap;
- path serialization;
- exact source-field repetition;
- unit-to-family aggregation from an allowlist.

Candidate specifications may not:

- read selection or final qrels;
- change query IDs, family IDs, or relevance labels;
- change `IN`/`OUT` assignment;
- change metric code;
- call external search;
- use uncontrolled network access;
- contain or invoke arbitrary executable code;
- write outside the candidate workspace;
- install dependencies or modify the frozen compiler;
- create more than four searchable units per family;
- insert ungrounded text into the primary index;
- access secrets or environment dumps.

Validate candidate JSON before compilation. Run the frozen compiler and indexing process with time, memory, output-size, and file-write limits. The Structure Agent never receives write access to executable source.

## 12. Agent role separation

### Analysis Agent

- requested profile: GPT-5.6 Sol, medium reasoning;
- reads train diagnostics and prior candidate summaries;
- must inspect successes, misses, and regressions;
- writes hypotheses only;
- cannot write code.

### Structure Agent

- requested profile: GPT-5.6 Sol, medium reasoning;
- converts one bounded hypothesis into a candidate SCOPE-DSL specification;
- writes only one JSON candidate in the candidate workspace;
- cannot access evaluator internals or protected splits.

### Protocol & Representation Auditor

- requested profile: GPT-5.6 Sol, high reasoning;
- receives a blinded audit packet;
- checks evidence, grounding, leakage, novelty of change, overfit risk, and reproducibility;
- returns `PASS`, `REVISE`, or `REJECT`;
- cannot edit code, choose by metric, or propose a replacement structure.

### Deterministic harness

- owns schema validation, retrieval, family aggregation, metrics, cost accounting, selection rules, and freeze artifacts;
- is the only metric authority.

If the requested model is unavailable, stop before a measured campaign and report the blocker. A cheaper model may be used only for explicitly labeled smoke tests.

## 13. Verification

Before declaring the migration complete:

- run formatting and lint checks configured by the repository;
- run unit and integration tests;
- validate all three JSON Schemas and example records;
- verify all Markdown links and referenced paths;
- scan tracked files for large artifacts and secrets;
- prove that external-store paths remain outside Git;
- rerun a fixture representation twice and compare hashes;
- rerun a fixture retrieval twice and compare rankings;
- verify the dashboard binds only to loopback;
- verify Obsidian and presentation outputs derive from the same run manifest;
- summarize any unimplemented planned command as unimplemented.

Do not claim a test passed unless its command was actually run.

## 14. Completion report

Report:

- files added, moved, superseded, and preserved;
- tests and exact outcomes;
- remaining blockers;
- current spend and protected-split access;
- next automatic step;
- whether the next step requires `D1`, `D2`, or `D3`.

The report must be understandable without reading terminal logs.

## 15. Stop boundaries

Stop and ask only when:

- a destructive or irreversible action is required;
- credentials, licensing, or data rights are unresolved;
- paid/measured execution needs `D1`;
- final evaluation needs `D2`;
- external release needs `D3`;
- the task would exceed the approved cost, time, or egress envelope;
- an inspected repository conflict cannot be resolved without changing the scientific claim.

Do not create a new gate merely because a candidate fails, a parser uses a documented fallback, or a routine engineering choice is needed.
