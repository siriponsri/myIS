# SCOPE Research Plan

## 1. One-sentence direction

Use a patent-native AutoIndex agent loop to learn a grounded patent evidence compiler that exposes cross-domain prior art to a fixed retriever, then test whether the frozen compiler transfers to fine-grained patent evidence retrieval.

## 2. Main claim

The project does not claim that a larger hierarchy is automatically better. It tests whether an AutoIndex-style Analysis-and-Structure Agent loop can discover a compact declarative representation that improves family-level candidate exposure without changing qrels, family mapping, the evaluator, or the first-stage retrieval budget. The declarative SCOPE-DSL is the controlled candidate surface inside that loop.

Working paper framing:

> **SCOPE: Learning Grounded Evidence Compilers for Cross-Domain Patent Retrieval**

Working contribution:

> Patent structure becomes a portable, grounded, and reproducible optimization target rather than fixed preprocessing.

## 3. Research questions

### RQ1 — Representation leverage

Can an AutoIndex-style search over grounded patent representations improve DAPFAM `OUT Recall@100` over a frozen flat representation and remain competitive with a train-selected deterministic-window control under the same BM25 retriever?

### RQ2 — Generalization

Does the selected representation improve a held-out selection split and a once-only final split, rather than only the optimization queries?

### RQ3 — Retriever transfer

Does a representation selected with BM25 retain value when frozen and reused with dense or hybrid retrieval?

### RQ4 — Task transfer

Does the DAPFAM-selected compiler improve feature/claim-to-passage retrieval on FiNE-Patents without retuning, and does it show broader transfer on selected PatenTEB tasks if the submission core is already complete?

### RQ5 — Mechanism

Which structural choices explain gains or regressions: claim grouping, dependency paths, description sections, indexed views, field repetition, or family aggregation?

### Optional RQ6 — Search policy

After representation leverage is established, can a separately optimized retrieval skill improve nDCG without materially reducing candidate recall?

## 4. Hypotheses

- `H1`: A learned grounded representation improves `OUT Recall@100` over flat BM25 and is Pareto-competitive with deterministic-window BM25 in effectiveness, index size, and latency.
- `H2`: The gain survives the hidden selection split and is not explained solely by index expansion.
- `H3`: At least part of the gain transfers to a frozen dense or hybrid retriever.
- `H4`: A DAPFAM-selected compiler improves at least one independent evidence or asymmetric retrieval task without retuning.
- `H5`: Compact claim-path and section-aware views outperform indiscriminate fine-grained chunking.
- `H6` is optional: Skill optimization improves ordering after candidate exposure has improved.

Failure to support a hypothesis is a valid research result. SOTA is a stretch target, not an execution requirement.

## 5. Scope

### Included

- DAPFAM family-level prior-art retrieval
- FiNE-Patents feature- and claim-level passage retrieval as external transfer
- selected PatenTEB cross-domain and asymmetric retrieval tasks as deadline-safe stretch transfer
- a declarative patent representation language and deterministic compiler
- grounded parsing of titles, abstracts, claims, and descriptions
- typed evidence graphs and compact searchable views
- frozen BM25 baseline and representation search
- family-level aggregation
- `ALL`, `IN`, and `OUT` evaluation
- parser, cost, index-size, and latency diagnostics
- MLflow, a read-only dashboard, Obsidian reports, and presentation assets
- a read-only independent protocol and representation auditor

### Excluded from the minimum viable paper

- legal novelty opinions
- unrestricted web or production prior-art search
- LLM extraction over every patent solely to create the corpus
- publication-level provenance where the source dataset does not provide it
- a scored human-designed tree
- simultaneous joint optimization of representation, retriever, reranker, and skill
- changing qrels, family mapping, or evaluator behavior
- claiming cross-paper SOTA from non-matching protocols

### Submission contract

The active submission target is iSAI-NLP 2026, Track 1: Natural Language Processing. The anonymous manuscript is limited to six pages under the official IEEE format. The required DAPFAM-plus-FiNE vertical slice takes precedence over broad repository cleanup, PatenTEB, dense/hybrid breadth, and SkillOpt. See `docs/ISAI_NLP_2026.md` for the page budget, dates, anonymous-review rules, and submission checklist.

## 6. Dataset and protocol

### 6.1 DAPFAM

DAPFAM contains 1,247 query families, 45,336 target families, and 49,869 relevance judgments. Evaluation is family-level and distinguishes:

- `IN`: query and target share at least one IPC three-character class.
- `OUT`: query and target share no IPC three-character class.
- `ALL`: the complete relevance set.

The current Hugging Face dataset card declares `CC-BY-NC-SA-4.0`. Record the exact repository revision and license in every data manifest; do not assume that a public benchmark permits unrestricted redistribution.

The implementation must bind:

- dataset repository and revision
- SHA-256 for every downloaded file
- normalized schema version
- family mapping version
- evaluator version
- query and target views
- random seed

The public DAPFAM paper is a benchmark reference. Published numbers may be compared directly only after reproducing the same corpus, query/target views, family mapping, and evaluator.

### 6.2 Frozen split

Use seed `42` and one persisted split assignment:

| Role | Queries | Access |
|---|---:|---|
| Train | 250 | Optimizer and evaluator |
| Selection | 125 | Evaluator only; open once for a frozen shortlist |
| Final | 872 | Evaluator only; open once after full freeze |

The split file is generated once, hashed, and never regenerated because a result is inconvenient. Candidate specs, agents, prompts, and reports must not receive selection or final qrels.

### 6.3 Representation unit

The canonical retrieval target is a DAPFAM family record. Do not invent publication IDs or imply that the selected title, claims, and description came from one coherent publication. Every derived node records:

- `family_id`
- source field
- character start and end offsets
- source-field hash
- parser strategy and confidence
- fallback status

### 6.4 Query and corpus views

Phase 1 must reproduce and freeze a named DAPFAM view before optimization. The initial protocol in `config/project.yaml` is `TAC -> FULL`:

- query: title + abstract + claims
- corpus: title + abstract + claims + description

The current DAPFAM dataset card registers this as an MTEB task, but it is not one of the six configurations marked as directly evaluated in the original paper. Reproduce it with the native MTEB-compatible evaluator and do not mix its results with published scores from a different view.

The required baselines are:

- one full-family flat view;
- one deterministic-window passage control using `maxP`, with window length selected on train under a declared simple-search budget.

The DAPFAM paper evaluates passage lengths from 64 to 8,192 tokens and reports that BM25 passage retrieval is stronger than document retrieval. The window control is therefore mandatory; the learned structure must show value beyond ordinary passage segmentation.

`R0-W` may emit more than four passages because it reproduces the strong conventional regime rather than entering the SCOPE candidate space. It must report passage count, index bytes, and latency. The four-unit cap remains mandatory for every learned SCOPE candidate, so the main interpretation is effectiveness plus the efficiency Pareto frontier.

If a different registered protocol is selected during baseline reproduction, update the config once, record the reason, and restart every measured arm. Do not mix results across protocols.

### 6.5 External transfer registry

External datasets are confirmation surfaces, not optimizer feedback.

| Dataset | Role | Frozen tasks | Tuning |
|---|---|---|---|
| FiNE-Patents | Fine-grained evidence transfer | Feature-level and claim-level prior-art passage retrieval using the official evaluator | None after SCOPE freeze |
| PatenTEB | Stretch cross-task representation transfer | `retrieval_OUT`, `title2full`, `problem2full`, and `effect2full`, subject to schema/license verification | None |

FiNE-Patents publicly releases 3,658 first claims, feature-level references, code, and official splits. PatenTEB publicly releases test data for 15 tasks; its retrieval tasks use nDCG@10. Bind exact revisions and licenses before use.

Sources: [FiNE-Patents paper](https://arxiv.org/abs/2605.02392), [FiNE-Patents repository](https://github.com/boschresearch/fine-patents), [PatenTEB paper](https://arxiv.org/abs/2510.22264), and [PatenTEB repository](https://github.com/iliass-y/patenteb).

Dataset adapters may map native fields into the canonical patent-record interface. They may not contain task labels, dataset-specific score hacks, or SCOPE representation choices.

## 7. Outcomes and candidate selection

### 7.1 Primary endpoint

`OUT Recall@100` at the family level is the representation-search objective.

This endpoint tests candidate exposure in the cross-domain setting, the bottleneck that representation learning is intended to address.

DAPFAM treats nDCG@100 as its primary benchmark metric. SCOPE deliberately uses recall for candidate selection because AutoIndex changes first-stage exposure; the manuscript must still report `OUT nDCG@100` prominently as a confirmatory benchmark endpoint and must not imply that DAPFAM itself changed its primary metric.

### 7.2 Companion endpoints

- `ALL Recall@100`
- `IN Recall@100`
- `OUT`, `ALL`, and `IN` nDCG@100
- Recall@10 and Recall@50 for diagnostic curves
- searchable units per family
- total indexed units and bytes
- indexing and query latency
- parser coverage and fallback rates
- LLM, compute, and storage cost

### 7.3 Automatic eligibility rules

A candidate is eligible only if deterministic checks confirm:

1. schema validity and full source provenance;
2. no protected-file, split, qrel, family-map, or evaluator change;
3. reproducibility from the same inputs, DSL spec, and compiler hash;
4. no more than four searchable units per family;
5. no more than `0.01` absolute loss in `ALL Recall@100` versus the frozen flat baseline;
6. approved campaign budget not exceeded.

Among eligible candidates:

1. maximize train `OUT Recall@100`;
2. if candidates differ by less than `0.005`, prefer fewer searchable units;
3. if still tied, prefer lower p95 query latency;
4. if still tied, prefer the simpler representation spec.

These are harness decisions, not Owner gates. Values are frozen in `config/project.yaml` before the measured campaign.

### 7.4 Statistics

- persist per-query metrics;
- report paired bootstrap confidence intervals for the frozen comparisons;
- report absolute differences, not only relative percentages;
- show `ALL`, `IN`, and `OUT` together;
- do not tune a candidate because a confidence interval is visually appealing;
- treat selection and final evaluation as confirmation, not another search loop.

### 7.5 Published context, not a gate

Contextual published results include:

| System/source | ALL nDCG@100 | OUT nDCG@100 | ALL Recall@100 | OUT Recall@100 |
|---|---:|---:|---:|---:|
| DAPFAM RRF hybrid, `K=30` | 0.3475 | 0.0625 | 0.4171 | 0.1653 |
| PatenTEB `patembed-large` external DAPFAM evaluation | — | 0.069 | — | — |

Sources: [DAPFAM](https://arxiv.org/abs/2506.22141) and [PatenTEB](https://arxiv.org/abs/2510.22264).

These numbers are stretch context only. Prompting, query/target views, model checkpoints, corpus versions, and evaluators may differ. They are not candidate-selection thresholds and must not be labeled as directly beaten until reproduced under the frozen SCOPE protocol.

## 8. Proposed system

### 8.1 Typed evidence graph

The internal representation uses hierarchical containment plus typed cross-links. It is detailed in `docs/PATENT_STRUCTURE.md`.

Required grounding:

- all text originates from bound source-dataset fields;
- derived text is extractive or an exact concatenation by default;
- every derived unit maps to source spans;
- abstractive summaries are disabled in the baseline and primary search;
- low-confidence parsing activates a deterministic fallback rather than fabricating structure.

### 8.2 Searchable view compiler

The graph compiles to one to four family-level searchable units selected from:

- `core`: title, abstract, and optional claim context
- `claims`: independent/dependent claim paths and limitations
- `mechanism`: grounded component, function, process, or relation spans
- `support`: description sections or deterministic description windows
- `fallback`: grounded blocks when structural parsing is unreliable

The first-stage index ranks units, then deterministically aggregates unit scores to families. The evaluator always receives family IDs.

For FiNE-Patents, the same compiler may expose passages within one cited prior-art document; the official evaluator receives passage IDs rather than family IDs. Dataset adapters define identity, while the representation specification remains frozen.

### 8.3 SCOPE-DSL

The primary search artifact inside the AutoIndex-style loop is a declarative JSON representation specification, not arbitrary generated Python.

Every candidate must validate against `schemas/scope-dsl.schema.json` before the frozen compiler reads it.

The DSL selects only allowlisted operations:

- grounded field selection and exact repetition;
- claim and section parser strategies;
- claim-path and limitation views;
- deterministic window parameters;
- compact-view composition;
- fixed-vocabulary path labels;
- unit-to-record aggregation from a fixed list.

A versioned deterministic compiler converts the spec and a canonical patent record into a validated evidence graph and searchable units. This preserves AutoIndex's learned-representation premise while making the candidate space auditable, enumerable for random/grid controls, and portable across DAPFAM, FiNE-Patents, and PatenTEB.

### 8.4 Patent-native AutoIndex / StructureOpt

The Analysis Agent diagnoses train successes, misses, and regressions. The Structure Agent proposes a bounded SCOPE-DSL specification. A deterministic harness validates, compiles, builds, retrieves, aggregates, and scores it. This is the primary AutoIndex-style optimization loop, not a generic prompt-optimization loop.

The complete AutoIndex-versus-SkillOpt decision and equal-budget control are frozen in `docs/OPTIMIZER_DECISION.md`.

Optimizable:

- claim-boundary strategy
- enabled node and view types
- section-boundary strategy
- deterministic window size and overlap
- hierarchy/path serialization
- exact source-field repetition
- searchable-unit selection
- unit-to-family score aggregation

Immutable:

- source text
- family IDs and mapping
- split assignments
- qrels
- `IN`/`OUT` labeling
- metric code
- cost accounting
- source offsets and hashes
- maximum searchable units

### 8.5 Independent auditor

The Auditor receives a blinded packet only after a candidate passes deterministic checks. It may return `PASS`, `REVISE`, or `REJECT`. It is read-only and cannot propose or edit the winning structure.

The auditor is a protocol-control mechanism, not the scientific judge and not the paper's novelty claim.

## 9. Agents and model profiles

| Role | Requested profile | Responsibility | Authority |
|---|---|---|---|
| Analysis Agent | GPT-5.6 Sol, medium | Diagnose train failures and form bounded hypotheses | Read-only |
| Structure Agent | GPT-5.6 Sol, medium | Produce candidate SCOPE-DSL specs | Write one schema-valid candidate spec |
| Protocol & Representation Auditor | GPT-5.6 Sol, high | Check evidence, leakage, grounding, overfit risk, and reproducibility | Read-only verdict |
| Deterministic harness | No LLM | Validate, index, score, select, log, and freeze | Metric authority |

The model name and reasoning effort are run configuration, not a scientific contribution. A measured campaign must not silently substitute a different model or effort.

## 10. Experiment plan

### Phase 0 — Repository migration and preflight

Deliver:

- minimum submission-critical module layout;
- preserved historical evidence and migration map;
- working environment setup;
- data-store boundary and `.gitignore`;
- schema validation;
- structured logging;
- MLflow smoke test;
- loopback dashboard smoke test;
- Obsidian report smoke test;
- small synthetic or public fixture tests.

Defer unrelated repository cleanup. Existing MLflow, dashboard, Obsidian, and presentation paths may use compatibility adapters until the vertical slice is stable.

No paid model call, protected qrel access, or measured claim occurs.

Exit condition:

- `uv run myis preflight` succeeds locally;
- tests prove that source spans, hashes, and family aggregation are deterministic.

### Phase 1 — Dataset contract and flat baseline

Deliver:

- DAPFAM file manifest and schema audit;
- frozen seed-42 split;
- parser coverage report without optimization;
- flat `TAC -> FULL` BM25 baseline;
- deterministic-window BM25 control with `maxP`;
- family-level evaluator reproduction;
- headroom and candidate-exposure analysis.

Exit condition:

- baseline reruns within deterministic tolerance;
- metric definitions and family IDs match the frozen protocol;
- no selection or final feedback has entered the optimizer.

### Phase 2 — Bounded StructureOpt pilot

Default pilot:

- three iterations;
- three candidates per iteration;
- train split only;
- BM25 frozen;
- at most four searchable units per family;
- Auditor invoked only for a new eligible incumbent.

Deliver:

- candidate journal with spec and compiler hashes;
- diagnostic deltas by `ALL`, `IN`, and `OUT`;
- parser and index-growth analysis;
- chosen incumbent or an evidence-backed no-go decision.

Automatic stop:

- stop if three consecutive iterations produce no new eligible incumbent;
- stop at the approved budget cap;
- stop if every surviving representation is equivalent to flat retrieval;
- stop on leakage, unverifiable provenance, or evaluator mutation.

No Owner response is needed for a scientifically negative pilot.

### Phase 3 — Frozen selection

Before opening the 125-query selection split, freeze:

- candidate SCOPE-DSL specs and compiler;
- retriever and aggregator;
- prompts and model profiles;
- dependency lock;
- container/environment manifest;
- canonical patent-record interface and fixture adapters;
- SCOPE-DSL schema and deterministic compiler;
- split hash;
- evaluator hash;
- cost and latency measurement code.

Run the frozen shortlist once on selection. Choose by the predeclared eligibility and tie-break rules. Do not edit a candidate after viewing selection results.

### Phase 4 — Required evidence transfer and conditional breadth

If the selected representation shows credible held-out leverage, dense or hybrid transfer may be run after the required submission core is safe:

- freeze it;
- run the same representation with a dense retriever;
- run a budget-matched hybrid arm if feasible;
- compare to matched flat dense/hybrid baselines.

Apply the same frozen DSL and compiler without representation retuning:

- to FiNE-Patents feature- and claim-level passage retrieval as the required independent transfer;
- to `retrieval_OUT` and selected asymmetric PatenTEB retrieval tasks only as deadline-safe stretch;
- against flat and deterministic-window baselines under each official evaluator.

FiNE-Patents transfer is required for the iSAI-NLP high-impact core. PatenTEB and dense/hybrid breadth are valuable but must not delay that core. No transfer experiment may reopen StructureOpt. Dataset-specific adapters may be corrected only for schema or evaluator conformance before labels are viewed.

### Phase 5 — Mechanism, robustness, and artifact readiness

Deliver:

- structural ablations on the frozen compiler;
- budget-matched random/enumerated search controls;
- seed variance if affordable;
- index-size, latency, and cost Pareto analysis;
- parser error taxonomy;
- cross-dataset adapter and license manifests;
- one compact reproduction command for every result intended for the six-page paper.

A broader open evaluation suite is post-submission or extended-version work. It must not delay the final freeze.

### Phase 6 — Optional SkillOpt

Only after Phase 3 succeeds:

- freeze the representation;
- optimize the retrieval policy separately;
- target nDCG@100 while preserving candidate recall;
- include budget-matched random or grid search;
- keep the final split closed.

Joint representation-plus-policy optimization is deferred unless both axes show independent leverage.

### Phase 7 — Final confirmation and reporting

After the Owner approves the final opening:

- run the frozen selected system and frozen baselines once on 872 queries;
- compute paired confidence intervals;
- generate MLflow records and immutable run manifests;
- build dashboard, Obsidian, figure, manuscript, and presentation projections;
- document negative and positive results;
- prohibit post-final tuning.

## 11. Minimal measured arms

| ID | Representation | Retrieval policy | Retriever | Required |
|---|---|---|---|---|
| `R0` | Flat frozen view | Fixed | BM25 | Yes |
| `R0-W` | Train-selected deterministic windows | Fixed `maxP` | Same BM25 | Yes |
| `R1` | Patent-native AutoIndex search over SCOPE-DSL | Fixed | Same BM25 | Yes |
| `R0-D` | Flat frozen view | Fixed | Dense | Conditional |
| `R1-D` | Frozen `R1` | Fixed | Same dense | Conditional |
| `R0-H` | Flat frozen view | Fixed | Hybrid | Conditional |
| `R1-H` | Frozen `R1` | Fixed | Same hybrid | Conditional |
| `P1` | Frozen `R1` | SkillOpt | Frozen best retriever | Optional |
| `X1-F` | Flat/window baseline | Fixed | FiNE-Patents official retrieval | High-impact target |
| `X1-S` | Frozen SCOPE compiler | Fixed | Same FiNE-Patents retrieval | High-impact target |
| `X2-F` | Native flat baseline | Fixed | Selected PatenTEB tasks | Stretch |
| `X2-S` | Frozen SCOPE compiler | Fixed | Same PatenTEB tasks | Stretch |

PageIndex and patent standards shape the representation contract. They are not separate measured arms. This removes the human-tree bottleneck while keeping the experiment interpretable.

## 12. Cost and compute

Default campaign targets:

- preferred total cost: at most USD 100;
- absolute ceiling without a new Owner decision: USD 200;
- CPU-first parsing, BM25, evaluation, and reporting;
- GPU only for the explicitly approved dense/hybrid transfer phase;
- GPT-5.6 Sol medium for candidate analysis and generation;
- GPT-5.6 Sol high only for preflight audit, eligible incumbents, and the freeze package.

Every run logs estimated and actual cost. A cap stops execution automatically; it does not create repeated micro-approval requests.

## 13. Owner decisions

Only these decisions are planned:

| Decision | Owner approves | When |
|---|---|---|
| `D1 START_CAMPAIGN` | Bound data, provider/model profiles, time, egress, and total spend | Before measured or paid work |
| `D2 OPEN_FINAL` | Once-only evaluation of the frozen 872-query final split | After freeze audit |
| `D3 RELEASE` | Submission, public release, deployment, or external sharing | After final report |

Safety, credential, destructive-action, or unexpected legal constraints may still require a pause. Routine implementation and scientific checkpoints do not.

## 14. Canonical records

- Git: source, configs, schemas, compact manifests, aggregate reports, paper assets
- External store: datasets, qrels, indexes, models, raw predictions, detailed run artifacts, MLflow backend
- MLflow: canonical run registry and metrics
- JSON run manifest: immutable reconstruction record
- Dashboard: read-only projection
- Obsidian: generated research narrative
- Presentation: generated communication artifact

## 15. Definition of success

The core project succeeds if it produces:

1. a reproducible DAPFAM family-level baseline;
2. an inspectable and grounded patent representation compiler;
3. a budget-matched test against both flat-family and deterministic-window representations;
4. a valid held-out conclusion, positive or negative;
5. complete cost, latency, parser, and provenance diagnostics;
6. synchronized MLflow, dashboard, Obsidian, manuscript, and presentation outputs.

The high-impact publication package additionally requires:

7. a constrained, versioned SCOPE-DSL and deterministic compiler;
8. budget-matched simple-search controls;
9. zero-retuning transfer to FiNE-Patents;
10. structural mechanism ablations and efficiency Pareto analysis;
11. a compact reproducible harness with license-aware adapters for every claimed result.

Selected PatenTEB tasks, dense/hybrid transfer, and SkillOpt are publication extensions after this core is safe. Beating a published score is valuable but not sufficient by itself. A DAPFAM-only gain is not considered the high-impact target.

## 16. Immediate next action

Codex should follow `INSTRUCTION.md`: inspect the existing repository, preserve historical evidence, and immediately implement the smallest no-cost submission-critical vertical slice. Broad migration may continue incrementally, but it must not block the DAPFAM baseline, SCOPE-DSL compiler, AutoIndex agent loop, or FiNE adapter. Stop before `D1` if measured or paid execution would begin.
