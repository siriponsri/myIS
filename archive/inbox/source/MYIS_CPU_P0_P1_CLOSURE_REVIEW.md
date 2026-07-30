# myIS CPU P0–P1 Closure Review and Execution Contract

**Prepared:** 2026-07-30 (Asia/Bangkok)

**Repository:** `siriponsri/myIS`

**Audited branch:** `main`

**Audited head:** `aff150ef9f6c14618d3d78bb9da2f617fb457e0f`

**Execution target:** GPT-5.6 Sol xhigh via `/goal`

**Required final state:** `P0_CLOSED` and `P1_CPU_EXECUTABLE`

---

## 1. Purpose

This file is both:

1. a review of the current repository state; and
2. an implementation contract for closing the structural work and preparing a
   reliable CPU-only P1 lane.

The goal is not to add more planning documents. The goal is to finish the
active cutover, make the repository internally consistent, implement the
missing deterministic kernel, and leave one reproducible path from raw local
inputs to validated manifests, MLflow, Dashboard, Obsidian/Brain, and Paper
projections.

Use the smallest coherent architecture that satisfies this contract. Prefer
one agent plus deterministic tools. “Agent responsibilities” are logical
responsibilities, not a requirement to create many sub-agents.

This document intentionally contains the detailed instructions so the `/goal`
prompt can remain short.

---

## 2. Executive verdict

Current verdict:

```text
REVISE — STRUCTURAL CUTOVER INCOMPLETE
```

The repository has a good target direction and should not be rolled back. The
filesystem cutover to `control/`, `campaigns/`, `src/`, `tests/`,
`projections/`, `dashboard/`, and `archive/` is useful. The SCOPE/AutoIndex
research direction, CPU-first budget, protected-data boundary, and
projection-first design are also appropriate.

However, the active runtime is still split between two systems:

- the new SCOPE campaign with D1–D3 and V0–V4 language; and
- the archived Track C/S system with F0–PS and G0–G8 language.

The latest three commits after the original cutover repaired only a small
portion of the review findings:

| Commit | What it changed | Audit effect |
|---|---|---|
| `ee67ece` | Added projection launchers | Convenience only; did not close authority/runtime gaps |
| `7b75a62` | Bound reports to stable read-model revision | Partially fixed report hash mismatch |
| `aff150e` | Replaced shell launchers with Windows `.cmd` launchers | Better for the Owner’s Windows workflow, but launchers still lack full health and input validation |

The following blockers remain at the audited head:

- active `D1_START_CAMPAIGN=approved` has no valid evidence, actor, timestamp,
  scope, or record hash;
- active Dashboard, harness, MLflow, asset registry, and projection code still
  use G0–G8 / F0–PS / Track C–S;
- `PLAN.md` is a short pointer, but Dashboard still parses the removed
  13-phase/22-task legacy plan;
- `control/source-of-truth.yaml` points to
  `src/myis_research/kernel` and `src/myis_research/scope`, which do not exist;
- the SCOPE schema accepts nearly arbitrary objects and applies the four-unit
  cap globally, which violates the FiNE-Patents native-passage contract;
- the owner-local runner accepts a precomputed aggregate instead of computing
  protected aggregates itself;
- MLflow bootstrap still depends on code under `archive/old-layout`;
- the MLflow doctor checks declarations and paths rather than opening and
  validating the real database and lineage;
- report sync still builds the read model twice, even though the stable
  revision patch now masks the immediate timestamp mismatch;
- archive provenance points to a migration inventory that is ignored and
  absent from Git;
- the missing historical audit JSON is not represented by a typed
  missing-evidence receipt;
- the three required scientific preflight patches are still absent:
  PHAGE/section-self-supervision positioning, FiNE native passage IDs, and a
  deterministic overlap/near-duplicate audit;
- no GitHub status checks or workflow runs are attached to the audited head.

Therefore, local smoke-test claims such as “16 passed” or three HTTP 200
responses are insufficient evidence of an end-to-end cutover.

---

## 3. Terminology to freeze

Use one active phase vocabulary throughout the repository:

| Phase | Meaning | Scientific status |
|---|---|---|
| `P0_FOUNDATION` | Authority cutover, schemas, kernel, protected boundary, projections, tests | No scientific result |
| `P1_CPU_BASELINE` | Deterministic CPU baseline lane: R0 and R0-W on train/selection only | Baseline or readiness evidence |
| `P2_SCOPE_DEVELOPMENT` | R1 SCOPE/AutoIndex development and selection | Future work after P1 |
| `P3_FINAL` | One frozen final evaluation | Requires D2 |
| `P4_PUBLICATION` | Manuscript/package and external release | Release requires D3 |

Freeze the research arms separately:

| Arm | Role |
|---|---|
| `R0` | Flat family-level BM25 baseline |
| `R0-W` | Deterministic passage/window maxP efficiency control |
| `R1` | Patent-native SCOPE/AutoIndex method |

Do not use active `V0–V4`, `F0–PS`, `G0–G8`, or Track C/S phase language after
the migration. Historical files may retain their original terminology under
`archive/`, but active code must not import or parse it.

In this document, “P1 complete” has two distinct states:

- `P1_CPU_EXECUTABLE`: implementation, fixtures, dry run, owner-local launcher,
  manifests, validators, and projections are ready;
- `P1_CPU_MEASURED_COMPLETE`: a real owner-local train/selection baseline has
  run and produced valid aggregate-only evidence.

Never report the second state when only fixtures or synthetic data ran.

---

## 4. Owner-decision simplification

### 4.1 Active Owner decisions

Reduce active Owner decisions to exactly two:

1. `D2_OPEN_FINAL` — one decision to expose and evaluate the frozen final split.
2. `D3_SUBMIT_RELEASE` — one decision to submit or release material externally.

Do not keep `D1` as an active Owner gate.

The Owner’s act of placing this file in `./inbox` and invoking `/goal` is the
standing authorization for repository-local, reversible, CPU-only, zero-paid-
API work through `P1_CPU_EXECUTABLE`. It also authorizes an owner-local
train/selection CPU run when the protected bundle is already available and the
runner can operate without exposing protected contents to the agent.

This authorization does **not** permit:

- opening the 872-query final split;
- GPU execution;
- paid API calls;
- uploading protected data;
- exposing qrels, split membership, query IDs, per-query outcomes, credentials,
  or raw provider payloads to the agent, Git, Dashboard, Brain, Paper, or
  MLflow;
- submitting or releasing a paper.

If GPU or paid API becomes scientifically necessary later, request one resource
envelope only when it is actually needed. Do not create speculative gates now.

### 4.2 Replace the invalid D1 authority safely

Do not silently edit the existing D1 line and do not treat it as valid.

Perform an authority migration:

1. preserve the old `control/decisions/ledger.jsonl` bytes and SHA-256 under a
   dated archive path;
2. record that its D1 entry was structurally invalid and is not active
   authorization;
3. create a strict active decision ledger that permits only D2 and D3;
4. create a typed `control/execution-envelope.yaml` whose evidence includes the
   SHA-256 of this inbox instruction;
5. make Dashboard, read model, AGENTS.md, and validators consume the execution
   envelope plus the D2/D3 ledger;
6. never infer a D2 or D3 approval.

The execution envelope must explicitly state CPU-only, train/selection-only,
zero paid API, no GPU, aggregate-only protected outputs, the allowed phases,
the hard resource limits, and the prohibited actions.

### 4.3 Inbox lifecycle

The current layout forbids a permanent root `inbox/`, but this file will arrive
there intentionally.

Treat `./inbox` as a transient ingestion surface:

1. read this file completely;
2. compute and record its SHA-256;
3. copy or move it to `archive/inbox/source/` with provenance;
4. bind the active execution envelope to that hash;
5. remove the now-empty root `inbox/` before final layout validation.

Do not fail merely because the Owner supplied the requested inbox file.

---

## 5. Required implementation sequence

Complete the work packages in order. Do not skip directly to Dashboard polish
or a measured run.

### WP0 — Establish a safe baseline

1. Confirm the current branch, HEAD, remote, and worktree state.
2. Preserve unrelated Owner changes. Do not reset, overwrite, or delete them.
3. Record the audited starting commit and whether the tree was dirty.
4. Read the active control files in the order specified by `AGENTS.md`, then
   inspect every active consumer before changing the schemas.
5. Treat historical Paper A–D reports and artifacts as evidence or engineering
   references only. They must not become new SCOPE metrics.
6. Create a concise migration checklist tied to tests, not a second sprawling
   planning system.

Exit condition: the exact migration surface and tests are known, with no
protected data opened and no scientific run started.

### WP1 — Finish the authority/runtime cutover

Update the active authority so every component uses the terminology and
decisions in Sections 3–4.

At minimum, reconcile:

- `PLAN.md`
- `README.md`
- `AGENTS.md`
- `control/program.yaml`
- `control/layout.v2.yaml`
- `control/source-of-truth.yaml`
- `control/migration-map.v2.yaml`
- `control/campaigns/scope-autoindex-v1.yaml`
- `control/assets/reusable_assets.yaml`
- active decision and execution-envelope schemas
- Dashboard contracts and projections
- MLflow stage/experiment/tag contracts
- harness CLI and status vocabulary
- read model and report templates

Rewrite the active reusable-asset registry so it uses P0–P4, R0/R0-W/R1, D2,
D3, and policy preconditions. Old phase/task/gate IDs may remain only in a
clearly historical archive copy.

Set `cutover_complete` only after an automated validator proves:

- every path named by the source-of-truth file exists;
- no active runtime imports or executes files under `archive/`;
- no active file uses G0–G8 or F0–PS as current authority;
- the Dashboard and MLflow consume the same read-model and manifest contracts;
- D2/D3 are the only active Owner decisions.

Exit condition: there is one active authority and one status vocabulary.

### WP2 — Implement the deterministic kernel and SCOPE compiler

Create the missing active paths referenced by the source-of-truth contract:

```text
src/myis_research/kernel/
src/myis_research/scope/
```

Keep the module count small and cohesive. Required capabilities are:

- canonical JSON serialization and SHA-256 commitments;
- strict schema loading and validation;
- immutable run-manifest construction;
- deterministic family/publication/source identifiers;
- metric and ranking interfaces without hidden fallback behavior;
- SCOPE spec parsing and deterministic compilation;
- dataset-specific adapter contracts;
- lineage and artifact-index generation;
- explicit failure categories.

Replace permissive placeholder schemas with strict contracts. A SCOPE view must
at least name:

- view ID and kind;
- source field/section/claim references;
- family and publication identity;
- stable source span or passage identity;
- compiler and normalization versions;
- deterministic ordering;
- searchability and aggregation behavior;
- source and output hashes.

#### DAPFAM adapter invariant

The maximum of four searchable units is a **DAPFAM adapter constraint**, not a
global SCOPE constraint. The DAPFAM compiler must preserve family identity,
publication provenance, source spans, deterministic order, and the hash of
every contributing source field.

#### FiNE-Patents adapter invariant

The FiNE adapter must preserve the official answer universe exactly:

- never merge official passages;
- never drop official passages;
- never renumber official passage IDs;
- never rewrite an official ID into a generated ID;
- preserve official order and passage text commitment;
- keep generated SCOPE units as an additional indexed view only;
- map every generated unit back to one or more unchanged official passage IDs;
- evaluate against the official IDs, not generated units.

Add contract tests that intentionally attempt merge/drop/renumber operations
and require fail-closed behavior.

Exit condition: strict positive and negative fixtures prove that the compiler
is deterministic and dataset adapters cannot change the evaluation universe.

### WP3 — Implement integrity and leakage preflight

Implement a deterministic preflight that runs before any protocol freeze or
measured baseline. It must check:

- corpus, query, qrels, split, family mapping, parser, evaluator, and
  normalization commitments;
- row counts and required-field coverage;
- identifier uniqueness;
- query-family versus corpus-family identity overlap;
- cross-split query/family duplicates;
- normalized exact-text duplicates;
- deterministic near-duplicate candidates;
- temporal or source leakage where the data permits;
- consistency between family-level evaluation IDs and publication-level
  evidence IDs.

Use a documented, deterministic near-duplicate method with fixed normalization,
shingling/tokenization, seed, threshold, and version. Store the detailed
candidate pairs only in the protected owner-local store. Git receives only:

- aggregate counts;
- pass/fail states;
- algorithm/config hashes;
- input commitments;
- receipt hash;
- failure category and recovery action.

Fail closed when identity, split, or family mapping cannot be reconciled. A
zero-count aggregate is not enough; the receipt must prove which checks and
commitments produced it.

Exit condition: synthetic fixtures include clean, exact-leak, family-leak, and
near-duplicate cases, and all expected outcomes are deterministic.

### WP4 — Make owner-local execution real

Replace the current “precomputed aggregate source” design. The Owner must not
have to calculate JSON aggregates by hand.

The owner-local runner must:

1. accept a signed/hash-bound request and protected data root;
2. validate expected files, sizes, hashes, schemas, and versions;
3. open protected corpus/query/qrels/split inputs locally;
4. run integrity checks, retrieval, and evaluation inside the protected
   boundary;
5. retain per-query details outside Git;
6. emit a strict aggregate/count/hash receipt;
7. scan the receipt for forbidden identifiers and fields;
8. bind the receipt to the Git commit, execution envelope, request, evaluator,
   and environment;
9. never overwrite an existing valid measured receipt.

Provide a Windows-friendly dry-run and one-click CPU launcher. A launcher must
validate ports/paths/arguments, poll service or job health, show actionable
errors, and avoid a fixed sleep as proof of readiness.

The agent may run the synthetic end-to-end path. For a real protected run, it
may invoke the owner-local command without reading protected files or emitting
their contents.

Exit condition: one command can go from protected local inputs to a safe
receipt; no manually prepared aggregate file is required.

### WP5 — Complete the P1 CPU baseline lane

P1 is a credibility and reproducibility milestone, not a positive-result gate.

Implement these CPU-only arms under one frozen evaluator:

1. `R0`: flat BM25 over the frozen DAPFAM text view;
2. `R0-W`: deterministic window/passage BM25 with maxP family aggregation.

Requirements:

- same train/selection split contract;
- final 872 queries remain closed;
- same family-level evaluator and cutoff;
- query view, corpus view, tokenization, BM25 parameters, windowing, and
  aggregation are explicit and hashed;
- top-100 rankings and per-query metrics stay protected;
- Git/MLflow/Dashboard receive only allowed aggregates and commitments;
- all reported ALL/IN/OUT metrics originate from the owner-local evaluator;
- existing FTS5 indexes may be reused read-only only when schema and corpus/view
  hashes match exactly;
- incompatible historical embeddings or Paper D rankings remain references,
  not P1 results;
- no dense model, GPU, remote endpoint, or paid API is required for P1;
- cost is measured even when USD cost is zero;
- latency, CPU time, memory, cache behavior, and failures are recorded.

Prepare R1 compiler fixtures and interface compatibility during P0/P1, but do
not require a measured R1 result to declare `P1_CPU_EXECUTABLE`. Measured R1
belongs to `P2_SCOPE_DEVELOPMENT`.

Each immutable run manifest must include at least:

- run and parent IDs;
- timestamp;
- Git commit and dirty-state commitment;
- corpus/query/qrels/split/family-map/parser/evaluator commitments;
- method/config/compiler/environment hashes;
- deterministic flags and seeds;
- route, top-k, BM25, window, and aggregation settings;
- resource use, latency, failure counts, and cost;
- artifact IDs, locations, sizes, and hashes;
- owner-local receipt hash;
- evidence class: fixture, train, selection, final, or report;
- status: valid, invalid, exploratory, blocked, or superseded.

If protected data is absent, finish `P1_CPU_EXECUTABLE`, generate a typed
`BLOCKED_EXTERNAL_DATA` handoff, and do not fabricate a measured manifest. If
the protected bundle is available and all integrity checks pass, run R0 and
R0-W on train/selection and report `P1_CPU_MEASURED_COMPLETE`.

Exit condition: two identical CPU fixture runs produce byte-equivalent stable
artifacts after excluding explicitly nondeterministic timestamps, and the real
owner-local lane is one command away or complete.

### WP6 — Rebuild Dashboard around the canonical read model

The Dashboard is a projection, not an alternative planner or decision ledger.

Required changes:

- remove legacy `parse_plan()` dependence on 13 phases and 22 tasks;
- remove G0–G8, F1/G1 readiness, Track C/S, and legacy Linear assumptions from
  active endpoints and frontend state;
- read P0–P4, R0/R0-W/R1, the execution envelope, D2/D3, manifests, and
  aggregate receipts from the canonical read model;
- use one decision ledger and one append path;
- permit write UI only for D2 and D3, with preview/confirm, typed scope,
  evidence hashes, actor, timestamp, prior hash, and record hash;
- make all other views read-only;
- show the difference between fixture readiness, CPU executable readiness, and
  measured completion;
- show cost, integrity, evidence class, blockers, and projection revision;
- never recompute scientific metrics in the Dashboard;
- ensure a single failed optional panel does not hide the failure while making
  the page appear healthy.

Replace the three-endpoint smoke test with a complete browser/API refresh test
covering every request made by `dashboard.js`. Validate the response schema and
the absence of legacy authority terms, not only HTTP 200.

Exit condition: opening the Dashboard from a clean checkout completes one full
refresh with no rejected promise, legacy gate, stale phase, or second ledger.

### WP7 — Finish MLflow as a rebuildable mirror

Simplify the active MLflow hierarchy. Prefer one campaign experiment with
stage/arm/run tags over the current mixture of bootstrap, catalog, Track C,
Track S, joint, publication, and SCOPE experiments unless a distinct experiment
has a demonstrated need.

Required changes:

- remove active Track C/S and F1/G1 stage vocabulary;
- move/bootstrap the required script into active `scripts/`; no archive runtime
  dependency is allowed;
- build mirror runs only from validated canonical manifests and receipts;
- enforce one serialized writer and read-only viewer;
- validate the real SQLite header, required tables, expected experiment/run
  lineage, artifact roots, and external-store boundary;
- verify that MLflow initialization does not mutate the database in read-only
  mode;
- verify artifact allowlisting and protected-content filtering;
- test rebuild into a temporary store from canonical fixtures;
- ensure `open-mlflow.cmd` validates its port and store, waits for a real health
  response, and reports a useful error when startup fails.

The MLflow doctor must open and inspect the database. Merely checking that files
and constants exist is not a PASS.

Exit condition: a temporary real MLflow database can be created from fixtures,
validated, viewed read-only, quarantined, and rebuilt without consulting
`archive/`.

### WP8 — Make reporting, Obsidian/Brain, and Paper projections reproducible

Build the read model once per sync and pass that exact in-memory object to every
writer. Do not rebuild it between writing the canonical file and generating
reports.

Required checks:

- validate the read model against a strict schema;
- compute a stable projection revision from canonical facts;
- write all projections atomically;
- store the exact source revision in every generated report;
- make `myis-report check` rebuild into a temporary location and detect schema,
  source-hash, revision, and content drift;
- keep metrics and decisions out of manually edited Obsidian notes;
- keep Dashboard, Brain, and Paper numbers traceable to the same run manifests;
- generate an Obsidian MOC for program status, experiments, evidence,
  decisions, failures/lessons, publication readiness, and active context;
- define a small memory lifecycle: active decision, evidence, lesson, failed
  attempt, superseded item, archive;
- prevent Brain memory from overriding run facts;
- generate sibling `02_Brain` and `03_Paper` projections when those roots are
  available, but do not make their absence invalidate the Git repository’s
  canonical read-model build.

Exit condition: two consecutive sync/check cycles with unchanged inputs have
the same projection revision and no unexplained drift.

### WP9 — Close archive and provenance gaps

1. Remove every active runtime dependency on `archive/`.
2. Either commit a compact migration inventory or change `archive/INDEX.md` to
   point to a committed hash/receipt that explains where the full local
   inventory lives.
3. Record the missing
   `04_outputs/audits/rigor/paper-d-submission-docs-primary-20260730.json` as a
   typed known-missing-evidence receipt with expected origin, last-known
   reference, search performed, recovery status, and effect on claims.
4. Preserve historical evidence and approvals; do not delete them merely to
   make validators pass.
5. Archive this transient inbox instruction and bind its hash to the execution
   envelope.

Exit condition: every active provenance pointer resolves, or resolves to a
typed known-missing receipt, and archive bytes are not executable dependencies.

### WP10 — Add the scientific preflight patches

Update the novelty/positioning matrix with current primary sources:

- [PHAGE: Patent Heterogeneous Attention-Guided Graph Encoder](https://arxiv.org/abs/2605.10073)
- [Patent Representation Learning via Self-supervision](https://arxiv.org/abs/2511.10657)
- [FiNE-Patents](https://arxiv.org/abs/2605.02392)
- [DAPFAM](https://arxiv.org/abs/2506.22141)

The contribution must not be framed as the first use of patent structure.
Freeze the distinction as:

> SCOPE is a non-parametric, deterministic index-compiler optimization layer
> evaluated with a fixed retriever, grounded source spans, family/publication
> traceability, leakage controls, and efficiency measurements.

PHAGE learns claim-graph-aware representations. Section self-supervision learns
parametric patent embeddings from document views. SCOPE compiles grounded,
auditable searchable units without training the encoder. FiNE evaluates
feature-level passage retrieval and requires preservation of the official
passage answer universe.

This literature update is a positioning requirement, not permission to copy
unverified performance values into the paper.

Exit condition: the novelty matrix and adapter contracts make these boundaries
explicit and citation-ready.

---

## 6. Test and validation contract

Add focused tests first, then a full CPU-only suite. Do not use a fallback or a
fixture path to report that a production path passed.

### 6.1 Required test layers

| Layer | Minimum proof |
|---|---|
| Schema | Valid examples pass; missing hashes, unknown fields, wrong IDs, merge/drop/renumber FiNE cases fail |
| Kernel | Canonical serialization, hashing, manifest immutability, ranking tie order, failure taxonomy |
| Compiler | Same input/spec produces same IDs, units, order, spans, and hashes |
| Integrity | Clean, exact duplicate, family overlap, cross-split overlap, and near-duplicate fixtures |
| Owner-local | Synthetic raw inputs to safe receipt without precomputed aggregate JSON |
| P1 | R0 and R0-W deterministic fixture runs; strict family-level top-k and aggregation |
| Dashboard | Full frontend refresh; every requested endpoint and schema; D2/D3 round trip |
| MLflow | Real temporary SQLite store, lineage, artifact filter, read-only viewer, rebuild |
| Reports | One-model sync, stable revision, drift detection, atomic outputs |
| Layout | Source-of-truth paths exist; root inbox removed; no active legacy roots |
| Archive | No active import/launcher path under archive; provenance pointers resolve |
| Security | Protected-key/path/content scan; no query IDs, qrels, membership, per-query rows, or secrets in projections |
| Windows UX | `.cmd` launchers validate parameters, detect failed startup, and use the active root |

### 6.2 Required repository checks

Run and record the exact output of:

```text
uv sync --all-extras
uv run --no-sync pytest -q
uv run --no-sync python scripts/validate_layout_v2.py
uv run --no-sync myis-report sync --repository-root .
uv run --no-sync myis-report check --repository-root .
uv run --no-sync python scripts/mlflow_doctor.py --repository-root . --store-root <safe temp or configured external store>
git diff --check
```

Add a repository-owned validation command that also checks:

- active legacy identifier/import scan;
- strict schema validation;
- source-of-truth path resolution;
- protected-content scan;
- archive independence;
- read-model/report drift;
- execution-envelope and D2/D3 ledger consistency;
- P1 fixture determinism.

Do not use test count as the main proof. Report which invariants are covered.

### 6.3 CI

Add a small GitHub Actions CPU workflow for:

- Python 3.11 locked dependency replay;
- unit/contract/integration tests using synthetic fixtures only;
- layout, schema, legacy-authority, protected-content, and `git diff --check`
  validation;
- no secrets, network model downloads, protected data, GPU, or paid service.

A pushed commit is not considered fully validated until the workflow exists and
the resulting status is reported. If the connector cannot observe the new run
immediately, report the local evidence and the CI state separately.

---

## 7. Completion states and acceptance criteria

### 7.1 `P0_CLOSED`

All must be true:

- [ ] one active P0–P4 authority vocabulary;
- [ ] D2 and D3 are the only active Owner decisions;
- [ ] execution envelope is hash-bound to this Owner instruction;
- [ ] invalid D1 authority is archived and excluded from active projections;
- [ ] `kernel/` and `scope/` exist and have strict deterministic contracts;
- [ ] DAPFAM four-unit rule is adapter-specific;
- [ ] FiNE official passage IDs cannot be merged, dropped, or renumbered;
- [ ] leakage preflight exists and passes synthetic adversarial fixtures;
- [ ] source-of-truth paths all resolve;
- [ ] no active runtime depends on archive;
- [ ] Dashboard, MLflow, Obsidian/Brain, and Paper share one read-model revision;
- [ ] archive pointers resolve or have typed missing-evidence receipts;
- [ ] full local CPU test suite passes;
- [ ] synthetic-only CI exists.

### 7.2 `P1_CPU_EXECUTABLE`

All must be true:

- [ ] R0 and R0-W CPU implementations exist under one frozen evaluator;
- [ ] dry run prints exact data commitments, methods, parameters, cost, and
      output targets without opening final data;
- [ ] owner-local runner computes aggregates itself;
- [ ] one-click Windows CPU launcher exists;
- [ ] synthetic end-to-end run produces strict immutable manifests and a safe
      receipt;
- [ ] repeated fixtures prove deterministic rankings and stable hashes;
- [ ] real protected run can be started with one command when the bundle is
      available;
- [ ] no dense model, GPU, API, or final-set access is required;
- [ ] Dashboard/MLflow/report projections correctly distinguish readiness from
      measured evidence.

### 7.3 `P1_CPU_MEASURED_COMPLETE` — conditional

Report this only when:

- [ ] protected inputs were present and validated owner-locally;
- [ ] integrity/leakage preflight passed;
- [ ] train/selection-only R0 and R0-W completed;
- [ ] receipts and manifests validate;
- [ ] aggregate results are mirrored without protected rows;
- [ ] no final split was opened.

Missing protected data is not a reason to leave structural work incomplete.

---

## 8. Stop conditions

Do not stop for routine architecture, naming, parser, fallback, test, UI, or
reporting choices. Use the recommended defaults in this contract.

Stop and report only when:

- unrelated Owner changes overlap the same files and cannot be preserved;
- repository or connector access is unavailable;
- a required protected bundle is absent for the optional measured P1 run;
- completing the requested action would require GPU, paid API, final-set
  access, credential handling, or external release;
- a deterministic integrity failure makes the protocol invalid.

When stopping, finish all independent work first and return one concise blocker
with the exact next command or decision. Do not create a new Owner gate.

---

## 9. Forbidden shortcuts

- Do not claim “cutover complete” from directory existence.
- Do not mark a decision approved from prose inference.
- Do not retain G0–G8 as a hidden compatibility runtime.
- Do not make `archive/` executable.
- Do not accept hand-precomputed protected aggregates.
- Do not use fixtures as scientific results.
- Do not run the final 872 queries.
- Do not download or run GPU/dense models for P1.
- Do not use paid APIs.
- Do not add SkillOpt/GEPA execution; it remains conditional future work.
- Do not copy Paper A–D metrics into the new campaign as if reproduced.
- Do not weaken schemas to make existing files pass.
- Do not create dozens of files, agents, or governance records when a cohesive
  module and one typed record suffice.
- Do not delete historical evidence merely because it is inconvenient.
- Do not force-push or rewrite Git history.

---

## 10. Required final report from the implementation agent

Return a concise but evidence-backed report containing:

1. starting and ending commit;
2. commits created and pushed to `main`;
3. files/modules added, rewritten, archived, and deliberately untouched;
4. authority migration and exact active Owner decisions;
5. P0 acceptance table;
6. P1 acceptance table;
7. tests and commands with real outcomes;
8. GitHub Actions status separated from local status;
9. protected surfaces that remained unopened;
10. actual CPU/cost/data use;
11. current state using exactly one of:
    - `P0_CLOSED / P1_CPU_EXECUTABLE`
    - `P0_CLOSED / P1_CPU_MEASURED_COMPLETE`
    - a truthful partial state with one exact blocker;
12. next automatic research action for P2, without opening D2.

Commit and push to `main` only after all required local checks pass. Use normal
fast-forward pushes only. If CI fails after push, diagnose and fix within this
same goal while remaining inside the CPU/no-cost/protected boundary.

---
## 11. Evidence basis

### Repository evidence

- Audited head:
  [aff150e](https://github.com/siriponsri/myIS/commit/aff150ef9f6c14618d3d78bb9da2f617fb457e0f)
- Initial SCOPE cutover:
  [b04fa31](https://github.com/siriponsri/myIS/commit/b04fa31e575573fc00fde798198fd4bf00721bf3)
- Report revision patch:
  [7b75a62](https://github.com/siriponsri/myIS/commit/7b75a62830ffeea113be67edc1f80afb57b999a4)
- Windows launcher patch:
  [aff150e](https://github.com/siriponsri/myIS/commit/aff150ef9f6c14618d3d78bb9da2f617fb457e0f)

### Historical local evidence reviewed

- patent database/DAPFAM report;
- Paper A advisor report;
- Paper B advisor report;
- Paper C stricter P1 re-verification report;
- Paper D plan, prompt decision report, and deterministic `mu_f` specification;
- supplied DAPFAM, FiNE-Patents, PatenTEB, patent-embedding, GEPA, and prompt
  evaluation papers.

These historical sources inform invariants and failure lessons. They do not
constitute new SCOPE measurements.

### Primary research sources

- [DAPFAM](https://arxiv.org/abs/2506.22141)
- [FiNE-Patents](https://arxiv.org/abs/2605.02392)
- [PHAGE](https://arxiv.org/abs/2605.10073)
- [Patent Representation Learning via Self-supervision](https://arxiv.org/abs/2511.10657)

---

**End of execution contract**
