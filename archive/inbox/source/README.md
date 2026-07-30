# SCOPE / myIS

SCOPE stands for **Structured Compiler Optimization for Patent Evidence**. It is a patent-native, constrained AutoIndex method: agents learn how patent records should be represented before retrieval, with cross-domain prior-art discovery as the flagship task and fine-grained evidence retrieval as the publication-level transfer test.

> Learn what the index should expose, then learn how the retrieval policy should search it.

The main experiment keeps the AutoIndex idea visible and central. An Analysis Agent diagnoses retrieval failures, a Structure Agent proposes bounded `SCOPE-DSL` representation specifications, a frozen deterministic compiler produces grounded evidence graphs and compact searchable views, and an independent read-only Auditor challenges only eligible incumbents.

The active submission target is iSAI-NLP 2026, Track 1: Natural Language Processing. The selected compiler must be tested without retuning on:

- DAPFAM family-level cross-domain retrieval;
- FiNE-Patents feature/claim-to-passage evidence retrieval.

Selected PatenTEB tasks and dense/hybrid transfer are stretch experiments only after the six-page core paper is complete.

## Current status

This package is a proposed repository simplification and research reset. It does not retroactively change historical approvals, experiment ledgers, or Paper A-D evidence.

Known historical state at the time of this proposal:

- `F0`: closed
- `G0`: approved
- `F1`: waiting for gate
- `G1`: pending
- No new measured SCOPE campaign has been authorized or run by this package.

## Research objective

Primary objective:

> Improve family-level `OUT Recall@100` on DAPFAM by learning a compact, grounded patent representation while holding the retriever and evaluator fixed, then test whether the representation transfers across retrieval models and patent retrieval tasks.

Companion outcomes:

- `ALL` and `IN` Recall@100
- `OUT`, `ALL`, and `IN` nDCG@100
- searchable units per family
- index size, latency, runtime, and cost
- parser coverage, fallback rate, and provenance coverage

DAPFAM names nDCG@100 as its primary benchmark metric. SCOPE deliberately optimizes `OUT Recall@100` to isolate first-stage candidate exposure, while reporting nDCG@100 prominently as a confirmatory ranking outcome.

The structure is not a pure tree. It is a typed evidence graph with a hierarchical containment spine:

```text
patent_record
├── metadata
├── title
├── abstract
├── claims
│   └── claim_group
│       └── claim
│           └── limitation
└── description
    └── section
        └── passage
```

Cross-links represent `depends_on`, `narrows`, `supported_by`, and `derived_from`. Every derived node points back to an original DAPFAM field and character span. Low-confidence parsing falls back to grounded text blocks or deterministic windows.

The graph is an internal representation. It compiles to at most four searchable units per family so that the index does not expand into millions of independently ranked nodes.

## Start here

### Inbox handoff

If this package and the research source files are staged under `/inbox`, do not copy them blindly over the repository. Tell Codex to read `INBOX_MANIFEST.md` and `INSTRUCTION.md` from the staged package, inventory the real repository, propose a migration map, and then perform only the authorized local migration.

`/inbox` is an input area, not the project root, experiment workspace, data store, or historical archive.

### Repository read order

Read these files in order:

1. `README.md` — orientation
2. `PLAN.md` — research protocol and execution phases
3. `docs/PATENT_STRUCTURE.md` — evidence behind the representation
4. `docs/OPTIMIZER_DECISION.md` — AutoIndex, agent-loop, and SkillOpt decision
5. `docs/PAPER_STRATEGY.md` — contribution, novelty, and reviewer stress test
6. `docs/ISAI_NLP_2026.md` — venue-specific scope, sprint, page budget, and compliance
7. `docs/ARCHITECTURE.md` — target repository and storage layout
8. `docs/RULES.md` — the three Owner decisions and protected boundaries
9. `docs/RUBRIC.md` — independent auditor contract
10. `INSTRUCTION.md` — one-time migration and implementation brief
11. `AGENTS.md` — persistent Codex operating rules
12. `NAMING.md` — compact identifiers and artifact names

`config/project.yaml` is the executable policy once implementation begins. JSON Schemas in `schemas/` define the agent-written SCOPE-DSL candidate, compiled representation, and run-manifest contracts.

## Target repository

```text
myIS/
├── README.md
├── PLAN.md
├── INSTRUCTION.md
├── NAMING.md
├── AGENTS.md
├── pyproject.toml
├── uv.lock
├── config/
│   └── project.yaml
├── docs/
│   ├── ARCHITECTURE.md
│   ├── PATENT_STRUCTURE.md
│   ├── OPTIMIZER_DECISION.md
│   ├── PAPER_STRATEGY.md
│   ├── ISAI_NLP_2026.md
│   ├── RULES.md
│   └── RUBRIC.md
├── schemas/
│   ├── scope-dsl.schema.json
│   ├── patent-representation.schema.json
│   ├── run-manifest.schema.json
│   └── examples/
├── src/myis/
│   ├── data/
│   ├── benchmarks/
│   ├── structure/
│   ├── retrieval/
│   ├── optimize/
│   ├── evaluate/
│   ├── observe/
│   └── report/
├── tests/
│   ├── fixtures/
│   ├── unit/
│   └── integration/
├── experiments/
│   ├── configs/
│   ├── fixtures/
│   ├── notebooks/
│   └── registry/
├── evidence/
│   ├── catalog/
│   └── literature/
├── dashboard/
├── reports/
│   ├── obsidian/
│   ├── manuscripts/
│   ├── figures/
│   └── presentations/
└── archive/
    └── README.md
```

Large data, qrels, indexes, models, raw runs, and the MLflow backend live outside Git under `MYIS_STORE`. Git contains code, small fixtures, schemas, configs, run manifests, aggregate reports, and publication assets.

## Primary experiment

The mandatory comparison is deliberately small:

| Arm | Representation | Retriever | Purpose |
|---|---|---|---|
| `R0` | Frozen flat DAPFAM view | Frozen BM25 | Reproducible baseline |
| `R0-W` | Train-selected deterministic windows | Same BM25 + fixed `maxP` | Strong DAPFAM passage control |
| `R1` | Patent-native AutoIndex search over SCOPE-DSL | Same BM25 | Isolate representation leverage |
| `R2` | Frozen `R1` representation | Dense/hybrid | Conditional transfer test |
| `X1` | Frozen SCOPE compiler | FiNE-Patents official retrieval evaluator | Fine-grained evidence transfer |
| `X2` | Frozen SCOPE compiler | Selected PatenTEB retrieval tasks | Deadline-safe stretch only |

There is no scored human-tree arm. Patent standards, PageIndex, and claim-structure research define the safety envelope, not a manually tuned competitor.

SkillOpt is a conditional second axis and starts only after frozen representation leverage and ranking headroom are demonstrated. It must not dilute or delay the primary AutoIndex-and-agent story. The exact admission rule and optional four-arm factorial are in `docs/OPTIMIZER_DECISION.md`.

## Owner involvement

The Owner is asked for only three scientific or external decisions:

1. Start the measured campaign and approve its total budget.
2. Open the final 872-query split after the freeze package is complete.
3. Release, submit, or publish externally.

Deterministic checks, parser fallbacks, candidate rejection, no-cost local tests, and iterations within an approved budget do not require another Owner gate.

## Observability and reporting

- Structured logs explain each run and failure.
- MLflow remains the canonical run registry and metric store.
- The dashboard remains a loopback-only, read-only projection of canonical results.
- Obsidian reports remain generated, citation-linked research summaries.
- Presentation assets remain under `reports/presentations/`.

No dashboard, notebook, or report may silently become the metric authority.

## Planned command interface

These commands are the target interface; Codex must implement and test them before they are treated as available:

```bash
uv run myis preflight
uv run myis data inspect --dataset dapfam --role train
uv run myis baseline run --config experiments/configs/r0-flat-bm25.yaml
uv run myis structure search --config experiments/configs/r1-structureopt.yaml
uv run myis evaluate selection --candidate <candidate-id>
uv run myis freeze create --candidate <candidate-id>
uv run myis evaluate final --freeze <freeze-id>
uv run myis report build --run <run-id>
```

## Source basis

The design is grounded in the [DAPFAM dataset](https://huggingface.co/datasets/datalyes/DAPFAM_patent), the [DAPFAM paper](https://arxiv.org/abs/2506.22141), [EPO claim guidance](https://www.epo.org/en/legal/guidelines-epc/2026/f_iv_3_4.html), [WIPO ST.96](https://www.wipo.int/standards/en/st96/v10-0/), [Patent Claim Structure Recognition](https://publikationen.bibliothek.kit.edu/1000069936/4168126), [FiNE-Patents paper](https://arxiv.org/abs/2605.02392), [FiNE-Patents artifacts](https://github.com/boschresearch/fine-patents), [PatenTEB](https://github.com/iliass-y/patenteb), [PageIndex](https://github.com/VectifyAI/PageIndex), [AutoIndex](https://arxiv.org/abs/2607.18603), and [SkillOpt](https://arxiv.org/abs/2605.23904).

See `docs/PATENT_STRUCTURE.md` for the full structure comparison, `docs/OPTIMIZER_DECISION.md` for the AutoIndex/agent/SkillOpt decision, and `docs/ISAI_NLP_2026.md` for the venue-specific publication plan.
