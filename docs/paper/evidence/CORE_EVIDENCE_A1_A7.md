# Core Scientific Evidence for the Conference Manuscript

Source program: myIS / ArmIndex, repository snapshot `d0d6039a04eda97d7696a1b86ab4b1adf94d6595`.

This file is a lean manuscript-facing extraction. It intentionally excludes protected/raw data and operational history that does not affect the conference claims.

## Benchmark and protocol
- Evaluation unit: patent family.
- Benchmark: 1,247 query families, 45,336 target families, 49,869 judged relations.
- Development partitions: 150 representation-development queries + 100 system-composition queries.
- One-time Selection: 125 queries.
- Final confirmation: 872 queries.
- Primary endpoint: cross-domain Recall@100.
- Secondary endpoints: cross-domain nDCG@100 and nDCG@10.
- Confirmation: paired query-level analysis, 10,000 paired bootstrap resamples, 95% percentile intervals.
- Model weights were frozen; no fine-tuning, adapters, distillation, or continued pretraining.

## Frozen retrieval systems
1. BM25 (`bm25s`) — lexical reference.
2. BGE-M3 — general multilingual dense reference.
3. PatEmbed-large — patent-specific dense retriever; research/non-commercial license boundary.
4. Snowflake Arctic Embed M v2.0 — multilingual long-context dense retriever.
5. Qwen3 Embedding 0.6B — instruction-aware dense retriever.

## Shared deterministic representations
1. Title + abstract + claims as one family document.
2. Title + abstract only.
3. First structured independent claim.
4. Fixed 384-token passages with 64-token overlap, family-level max aggregation.
5. Separate labeled title/abstract/claims views combined by family-level rank fusion.

## A1 — Common multi-system screening
Five systems × five shared representations = 25 logical cells on the 150-query representation-development population.

Aggregate development summaries across shared views:
| System | Recall@100 | nDCG@100 | nDCG@10 | Development disposition |
|---|---:|---:|---:|---|
| BM25 | 0.191200 | 0.172717 | 0.160011 | Diagnostic; did not advance |
| BGE-M3 | 0.269933 | 0.231377 | 0.198497 | Diagnostic; did not advance |
| PatEmbed-large | 0.413400 | 0.347812 | 0.289856 | Advanced |
| Arctic Embed M v2.0 | 0.340667 | 0.284546 | 0.235538 | Advanced |
| Qwen3 Embedding 0.6B | 0.363733 | 0.307930 | 0.256706 | Advanced |

Interpretation: A1 is development evidence, not a universal leaderboard or confirmatory superiority result.

## A2 — Per-system representation search
Frozen search universe: 52 configurations; 44 measured, 8 dormant, zero failures.

| System | Recall@100 | nDCG@100 | nDCG@10 | Predeclared decision |
|---|---:|---:|---:|---|
| BM25 | 0.234667 | 0.210784 | 0.195024 | Diagnostic tie; no per-system winner |
| BGE-M3 | 0.290000 | 0.249919 | 0.220057 | Diagnostic tie; no per-system winner |
| PatEmbed-large | 0.423000 | 0.357636 | 0.299444 | Unique within-search winner; tied A1 incumbent at displayed precision |
| Arctic Embed M v2.0 | 0.358667 | 0.301868 | 0.253229 | Strict improvement; retained for transfer |
| Qwen3 Embedding 0.6B | 0.373667 | 0.321262 | 0.273664 | No strict improvement; retained as transfer control |

Defensible interpretation: response to representation search was heterogeneous; improvement was not uniform across retrievers.

## A3 — 3×3 representation-transfer matrix
All operations covered all 250 development queries.

| Representation source | Target system | Recall@100 | nDCG@100 | nDCG@10 |
|---|---|---:|---:|---:|
| PatEmbed | PatEmbed | 0.418436 | 0.347098 | 0.290589 |
| PatEmbed | Arctic | 0.337430 | 0.288876 | 0.248091 |
| PatEmbed | Qwen3 | 0.362570 | 0.306168 | 0.259749 |
| Arctic | PatEmbed | 0.418715 | **0.352416** | 0.295553 |
| Arctic | Arctic | 0.341341 | 0.286975 | 0.239140 |
| Arctic | Qwen3 | 0.359497 | 0.305476 | 0.258884 |
| Qwen3 | PatEmbed | **0.419274** | 0.351428 | 0.296279 |
| Qwen3 | Arctic | 0.338268 | 0.280557 | 0.229009 |
| Qwen3 | Qwen3 | 0.360615 | 0.306579 | 0.261546 |

Key measured observations:
- Highest Recall@100: Qwen3-derived representation → PatEmbed (0.419274).
- Highest nDCG@100: Arctic-derived representation → PatEmbed (0.352416).
- No source representation retained a consistent diagonal/universal advantage.
- Target-system identity remained strongly associated with quality.

Defensible claim: **representation advantages did not transfer consistently across retrievers on development data.**
Do not claim formal paired-bootstrap superiority for the transfer matrix; A3 did not establish that.

### A3 fixed composition control (secondary/background)
| Configuration | Recall@100 | nDCG@100 | nDCG@10 |
|---|---:|---:|---:|
| Strongest single | 0.418436 | 0.347098 | 0.290589 |
| Two-system fusion | 0.418715 | 0.352747 | 0.293716 |
| Three-system fusion | 0.415084 | 0.346250 | 0.284772 |
| All-primary fusion | 0.415084 | 0.346250 | 0.284772 |
| Commercial-only fusion | 0.369274 | 0.308967 | 0.258116 |

Use only briefly if space allows: adding more retrieval systems did not monotonically improve quality.

## A4 — One-time selection bridge
The sealed 125-query selection set was opened once. All four frozen profiles produced rankings for all 125 scoped queries with no failures. Cross-domain paired statistics used the 90 queries with positive cross-domain relations.

Research vs balanced Recall@100 difference: +0.055556; 95% CI [0.029986, 0.081667].
Research vs quality-oriented: +0.055556; 95% CI [0.029986, 0.081667].
Research vs speed-oriented: +0.107778; 95% CI [0.081111, 0.135000].

After this exposure, the research configuration and static/common comparator were frozen.

## A5 — Final-872 confirmation (scientific climax)
Exactly two complete frozen systems were compared. Model/program/representation/prompt/runtime bindings were fixed before access. Both processed all 872 queries, with zero failures and deterministic replay.

| Cross-domain outcome | Static comparator | Research system | Difference |
|---|---:|---:|---:|
| Recall@100 | 0.331097 | **0.442476** | **+0.111379** |
| nDCG@100 | 0.279253 | **0.365595** | **+0.086342** |
| nDCG@10 | 0.233666 | 0.297459 | +0.063794 (descriptive) |

Uncertainty:
- Recall@100 difference 95% bootstrap CI: **[0.102294, 0.120438]**.
- Recall wins/ties/losses: **619 / 158 / 95**.
- nDCG@100 difference 95% CI: **[0.078673, 0.094077]**.
- nDCG@10 has no canonical CI in the frozen evidence; report descriptively only.

Mandatory claim boundary: this estimates the effect of choosing the **complete research configuration**, not the isolated causal effect of representation alone.

Operational detail is mixed and secondary: median latency/throughput favored the research system, while p99 latency favored the comparator. Do not claim uniformly better efficiency.

## A6 — Full-benchmark scale bridge
After confirmation, the selected system was permanently fixed and applied alone to the complete benchmark.

Coverage/materialization:
- Candidate families: 45,336
- Query families: 1,247
- Representations/chunks: 188,944
- Candidate depth: 200/query
- Ranked rows: 249,400
- Coverage: 100%
- Failures: 0
- Duplicate-family errors: 0

Depth characterization:
| Population | Recall@10 | Recall@20 | Recall@50 | Recall@100 | Recall@200 | nDCG@100 |
|---|---:|---:|---:|---:|---:|---:|
| All relations | 0.136795 | 0.214697 | 0.336358 | 0.438965 | 0.546832 | 0.362497 |
| In-domain | 0.187048 | 0.277872 | 0.413145 | 0.528164 | 0.645077 | 0.406513 |
| Strict cross-domain | 0.034023 | 0.070933 | 0.133994 | **0.188450** | **0.260167** | 0.070644 |

Important: A5 and A6 cross-domain values use different population definitions. They are **not** a before/after performance trend.

## A7 — Post-confirmatory candidate-exposure diagnosis (aftershock)
A7 analyzed the immutable A6 Top-200 pool on CPU. It did not retrieve new candidates, change the winner, select a reranker, or reopen selection/confirmation data.

Candidate-exposure anatomy:
| Population | Relevant pairs | Found 1-100 | Found 101-200 only | Absent from Top-200 |
|---|---:|---:|---:|---:|
| All relations | 24,929 | 10,938 | 2,689 | 11,302 |
| In-domain | 19,736 | 10,142 | 2,357 | 7,237 |
| Strict cross-domain | **5,193** | **796** | **332** | **4,065** |

Among 905 judged strict cross-domain queries:
- 67 had all relevant evidence exposed by rank 200.
- 297 had partial relevant evidence exposed.
- 86 had relevant evidence only at ranks 101-200.
- **455 had no relevant candidate in Top-200.**

Analytical perfect-ordering bound within the existing Top-200 pool:
| Population | Observed Recall@100 | Perfect-ordering bound | Headroom |
|---|---:|---:|---:|
| All | 0.438965 | 0.546832 | +0.107868 |
| In-domain | 0.528164 | 0.645077 | +0.116913 |
| Strict cross-domain | **0.188450** | **0.260167** | **+0.071717** |

Interpretation: ordering headroom exists, but most strict cross-domain relevant pairs are outside the candidate pool. A downstream ranker cannot recover a family that first-stage retrieval never supplies.

Boundary: the oracle is an analytical upper bound, **not an implemented reranker**.

## Three-tier claim hierarchy for the paper
1. **Development:** representation behavior was heterogeneous; advantages did not transfer consistently across frozen retrievers.
2. **Confirmation:** the selected complete research configuration clearly outperformed the frozen comparator on Final-872.
3. **Diagnosis:** after full-scale materialization, candidate exposure remained a major limitation under strict cross-domain evaluation.
