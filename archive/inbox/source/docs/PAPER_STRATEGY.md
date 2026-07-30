# Paper Strategy and Reviewer Stress Test

## 1. Paper-first objective

The project should be memorable for one methodological idea:

> A patent representation is not fixed preprocessing. A patent-native AutoIndex agent loop can learn a grounded, budget-constrained specification and compile it across retrieval tasks.

The paper should not be presented as a bundle of AutoIndex, PageIndex, SkillOpt, and three LLM agents.

AutoIndex should be named clearly as the closest methodological lineage and the inspiration for the optimization loop. The paper's distinct method story is:

1. an Analysis Agent diagnoses cross-domain retrieval failures;
2. a Structure Agent searches a patent-native grounded representation DSL;
3. a deterministic compiler, retriever, and evaluator score candidates;
4. a read-only Auditor challenges only eligible incumbents;
5. the selected compact structure is frozen on held-out data;
6. the frozen compiler is tested on fine-grained evidence retrieval;
7. ablations explain which structural choices changed exposure.

## 2. Working title

Primary:

> **SCOPE: Learning Grounded Evidence Compilers for Cross-Domain Patent Retrieval**

Alternative if the graph formulation becomes central:

> **SCOPE: Structured Compiler Optimization for Patent Evidence**

Do not put model or framework names in the title.

### Publication-impact target

Use this ladder as an internal readiness assessment, not an Owner gate:

| Tier | Evidence package | Publication ceiling |
|---|---|---|
| `T1` | DAPFAM-only learned chunking | Application/benchmark extension; below target |
| `T2` | DAPFAM held-out gains, equal-budget controls, ablations, grounded compiler | Strong specialized IR study |
| `T3` | Patent-native AutoIndex loop, DAPFAM flagship, FiNE-Patents zero-retuning transfer, reproducible harness | iSAI-NLP high-impact target |
| `T4` | `T3` plus dense/hybrid, PatenTEB, and separate SkillOpt factorial | Extended-study target |

The active iSAI-NLP plan targets `T3`. `T4` must not delay it. Impact cannot be guaranteed by architecture alone; it requires positive, interpretable external evidence.

## 3. Formal method statement

For a canonical patent record \(d\), a grounded DSL specification \(\theta\) and frozen compiler \(C\) produce a bounded set of searchable units:

\[
U_d = C(d;\theta), \qquad 1 \le |U_d| \le 4.
\]

Each unit is reconstructable from source spans in \(d\). A frozen retriever \(r\) scores units for query \(q\), and a fixed aggregator \(A\) returns a family score:

\[
s(q,d) = A\left(\{r(q,u): u \in U_d\}\right).
\]

Structure search selects \(\theta\) on the train split:

\[
\max_\theta\ \operatorname{Recall@100}_{OUT}(\theta)
\]

subject to:

\[
\begin{aligned}
\operatorname{Recall@100}_{ALL}(\theta)
&\ge
\operatorname{Recall@100}_{ALL}(\text{flat}) - 0.01,\\
|U_d| &\le 4,\\
\operatorname{Grounded}(U_d) &= 1,\\
\operatorname{Cost}(\theta) &\le B.
\end{aligned}
\]

The scientific object is the portable pair \((\theta, C)\), not the optimizer model.

## 4. Contribution stack

### C1 — Patent-native constrained AutoIndex loop

An Analysis Agent and Structure Agent optimize what a patent index exposes while the retriever, answer key, and evaluator remain fixed. A deterministic harness remains the metric authority and a high-reasoning Auditor is read-only.

This is a constrained, patent-specific adaptation of AutoIndex, not an attempt to obscure prior lineage.

### C2 — Patent representation DSL

A constrained, versioned language over claim graphs, limitation spans, description sections, compact views, and record aggregation.

Unlike unrestricted generated preprocessing code, the DSL is schema-valid, enumerable, auditable, and portable across dataset adapters.

This is stronger than generic chunk optimization only if the implementation proves that patent-specific constraints matter.

### C3 — Grounded irregular-structure compiler

A deterministic compiler that retains character-level provenance, parser confidence, and fallbacks for flattened claims and inconsistent descriptions.

This matters because the actual DAPFAM files do not expose page/XML structure and are not reliably segmented by simple rules.

### C4 — Cross-domain family-level objective

Optimization targets `OUT Recall@100`, not generic retrieval average. The design explicitly tests whether structure exposes relevant prior art outside the query's IPC three-character domain.

### C5 — Independent evidence-task transfer

The selected structure is frozen and tested on FiNE-Patents feature/claim-to-passage retrieval without representation retuning. Dense/hybrid and selected PatenTEB tasks are extension evidence.

### Artifact contribution

One manifest-driven harness evaluates the same compiler against native DAPFAM and FiNE-Patents protocols without redefining their answer keys. PatenTEB support is added only if the required package is safe.

### Protocol contribution, not novelty claim

The independent Auditor, protected splits, MLflow, and freeze package make the result credible. They should not be sold as the primary algorithmic novelty.

## 5. Novelty test

Before implementation, fill this matrix with direct citations and code evidence:

| Capability | AutoIndex | PageIndex | Existing patent benchmarks | SCOPE must demonstrate |
|---|---|---|---|---|
| Learns document representation | Yes, executable programs | No | No | Yes, constrained DSL |
| Patent claim dependency graph | No | Generic hierarchy only | Evaluated indirectly | Yes |
| Character-level source grounding | Partial document identity | Page ranges | Dataset-specific | Yes |
| Handles flattened irregular claims | No patent evidence | No | Windows/full text | Yes |
| Strong deterministic passage control | Generic chunk baselines | No | DAPFAM searches 64–8,192-token windows | Required `R0-W` |
| Family-level aggregation | Document MaxP | Within-document traversal | DAPFAM supports it | Yes, fixed and explicit |
| Feature-to-passage evidence | No | Traversal without patent labels | FiNE-Patents evaluates it | Zero-retuning transfer |
| Cross-domain/asymmetric transfer | Heterogeneous generic tasks | No | PatenTEB evaluates it | Extended version |
| Sparse-to-dense/hybrid transfer | Limited pilot | Not the focus | Baselines only | Deadline-safe stretch |
| Budget-matched search control | Limited | Not applicable | Not applicable | Required |

If SCOPE cannot fill the last column with measured evidence, narrow the claim instead of inflating the narrative.

## 6. Minimum paper experiment

The iSAI-NLP high-impact core contains:

1. frozen flat BM25 baseline;
2. train-selected deterministic-window BM25 control with fixed `maxP`;
3. AutoIndex-style Analysis and Structure Agents;
4. learned SCOPE-DSL representation with the same BM25;
5. budget-matched random or enumerated search control;
6. held-out selection and once-only final confirmation;
7. claim-parser and description-parser coverage;
8. index-size, latency, and cost;
9. three structural ablations;
10. zero-retuning FiNE-Patents passage-retrieval transfer;
11. a versioned DSL, compiler, adapters, and reproducible harness.

No human-tree arm is required.

One dense/hybrid transfer pair and selected PatenTEB tasks are stretch experiments. SkillOpt belongs to the extended study unless all core evidence and the six-page draft are already safe.

## 7. Structural ablations

Run ablations only on a frozen selected representation:

| Ablation | Question |
|---|---|
| Remove claim dependency paths | Does graph structure matter beyond claim text? |
| Remove limitation segmentation | Do fine-grained elements expose cross-domain matches? |
| Remove description sections/support view | Is long-description evidence responsible for recall? |
| Replace learned view selection with all permitted views | Is compact selection better than index expansion? |
| Replace learned family aggregation with fixed `max` | Does aggregation contribute independently? |
| Use fallback-only parsing | Are gains merely robust windowing? |

Ablations must not reopen representation search on selection or final.

## 8. Search control

Reviewers may argue that agent search wins because it receives more evaluations.

Use the same:

- candidate count;
- evaluator calls;
- train examples;
- retriever;
- wall-time or cost envelope;
- eligibility rules.

Compare against:

- random sampling from the same declarative search space;
- a small enumerated or grid control where feasible.

Report optimization variance across seeds if budget allows. Do not claim optimizer superiority from one lucky trajectory.

## 9. Reviewer stress test

### Objection 1 — “This is AutoIndex applied to patents.”

Required answer:

- patent-native graph compiler;
- actual DAPFAM irregularity audit;
- family-level aggregation;
- cross-domain objective;
- patent-specific ablations;
- transfer evidence.

If those are missing, the objection is correct.

### Objection 2 — “Recall improved only because the index became larger.”

Required answer:

- maximum four units per family;
- index bytes and units reported;
- flat and train-selected deterministic-window baselines;
- budget-matched compact search controls;
- Pareto analysis of recall, size, and latency;
- all-views ablation.

### Objection 3 — “The LLM overfit 250 queries.”

Required answer:

- protected selection/final roles;
- frozen shortlist;
- random/grid control;
- DSL-specification simplicity;
- no query-specific vocabulary hard-coding;
- held-out and transfer results.

### Objection 4 — “Claim parsing is unreliable.”

Required answer:

- measured coverage;
- confidence and fallback;
- source-span validation;
- error taxonomy by formatting pattern;
- fallback-only ablation.

### Objection 5 — “Family text has invalid publication provenance.”

Required answer:

- family-only claims;
- no invented publication IDs;
- source-field provenance;
- explicit DAPFAM consolidation limitation.

### Objection 6 — “The method works only for BM25.”

Required answer:

- frozen dense/hybrid transfer if Phase 2 succeeds;
- otherwise narrow the conclusion to sparse retrieval.

### Objection 7 — “The auditor is another optimizer.”

Required answer:

- read-only blinded packet;
- no candidate edit;
- deterministic metric authority;
- auditor ablation is protocol analysis, not a performance contribution.

### Objection 8 — “The DSL merely sanitizes AutoIndex.”

Required answer:

- acknowledge the AutoIndex lineage directly;
- measure patent-specific graph operations and grounding constraints;
- explain the exchange of unrestricted-code flexibility for enumeration, safety, and transfer;
- use equal-budget simple search to test whether the agent loop adds value;
- use FiNE transfer to test whether the compiler represents patent evidence rather than DAPFAM labels.

## 10. Kill and pivot criteria

Pivot rather than extending infrastructure if:

- the flat baseline cannot be reproduced;
- parser structure adds no exposure beyond deterministic windows;
- eligible learned candidates do not improve train OUT Recall after the bounded pilot;
- selection gain disappears;
- gains require index expansion beyond the cap;
- the optimizer does not beat budget-matched simple search;
- provenance constraints remove the apparent gain.

Possible honest pivots:

- a DAPFAM representation audit and robust parsing benchmark;
- a negative study of learned chunking under family-level patent retrieval;
- sparse-specific representation learning without dense-transfer claims;
- claim-element coverage analysis on a dataset with feature-level evidence.

Do not keep adding agents, gates, or retrievers to rescue a failed central hypothesis.

## 11. Six-page paper outline

1. Introduction and contributions.
2. Related work and the gap beyond AutoIndex.
3. Method: agent loop, SCOPE-DSL, grounded compiler, and Auditor boundary.
4. Protocol: DAPFAM, FiNE transfer, protected splits, controls, and metrics.
5. Results: held-out comparison, transfer, mechanism, and efficiency.
6. Limitations and conclusion.

Use the page budget and anonymous-submission checklist in `docs/ISAI_NLP_2026.md`.

## 12. Abstract skeleton

Use only after results exist:

> Patent-family retrieval systems usually treat document representation as fixed preprocessing, despite long descriptions, interdependent claims, and cross-domain terminology. We introduce SCOPE, a patent-native constrained AutoIndex method in which Analysis and Structure Agents search a grounded representation language while a deterministic compiler, retriever, and evaluator remain fixed. On DAPFAM, SCOPE changes cross-domain family Recall@100 by [measured result] under protected splits and equal-budget search controls. The frozen compiler changes FiNE-Patents feature-to-passage retrieval by [measured result] without retuning. Structural ablations attribute the effect to [validated mechanism] while preserving [grounding/efficiency result].

Never fill bracketed claims from train-only results.

## 13. “Sexy” acceptance test

The paper direction is strong when a reviewer can answer all four in one sentence each:

1. What new object is learned? — A grounded patent representation specification compiled into compact index views.
2. What hard problem does it target? — Cross-domain candidate exposure.
3. What distinguishes it from AutoIndex? — A constrained patent DSL, grounded graph compiler, family semantics, and evidence-task transfer.
4. What single experiment could falsify it? — Frozen flat versus learned representation under identical retrieval and evaluation budgets.

The agent loop should be visible and understandable, but the contribution must not depend on listing several framework names.
