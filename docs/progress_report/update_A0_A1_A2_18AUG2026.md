---
title: "ArmIndex advisor update: migration, common screening, and per-arm AutoIndex"
audience: "Academic advisor and presentation use"
report_date: "2026-08-18"
reporting_cutoff_utc: "2026-08-18T18:00:00Z"
status: "A0 complete; A1 complete; A2 measured closeout passed; A3 not measured"
numeric_authority: "Aggregate-safe validated receipts, closeout projections, and derived EDA tables"
evidence_boundary: "Development evidence only; Selection and Final remain closed"
---

# ArmIndex advisor update: A0 through A2

## Executive message

ArmIndex tests a focused scientific question: does the best document
representation depend on the retriever that scores it, and can the resulting
arm-specific programs later transfer or combine into a useful quality,
latency, and cost frontier? The project is staged so that governance and
reproducibility are established before measurement, common screening precedes
per-arm search, and transfer is measured only on a separately bound input
package.

The evidence available on 18 August 2026 supports these statements:

1. **Migration Foundation (A0) is complete.** The study has canonical controls,
   frozen schemas, five registered retrieval arms, license declarations,
   protected-data rules, evidence projections, and validated feasibility
   fixtures. A0 generated no retrieval-quality result.
2. **Common Multi-Arm Screening (A1) is complete.** All 25 combinations of
   five retrieval arms and five deterministic representation programs were
   measured on the fixed representation-development split. The patent-domain
   PatEmbed arm had the highest mean held-out-domain Recall at 100 results;
   Arctic Embed and Qwen3 Embedding also passed the prespecified advancement
   rule.
3. **Per-Arm AutoIndex (A2) has a passed measured closeout.** The frozen search
   accounted for 52 candidates: 40 matched candidates, four activated
   conditional reserves, and eight dormant reserves. Forty-four candidates
   were measured, none failed, safe return passed, workers were reaped, and
   measured cost was USD 54.52666666666665948 against a USD 60 hard stop.
4. **Transfer and HarnessOpt (A3) is prepared but not measured.** Only
   ARM-03, ARM-04, and ARM-05 are eligible to advance. A3 still requires an
   Owner-authorized, hash-bound 250-query training package and fresh provider
   admission; the idle provider instance is not treated as reusable evidence.

The defensible publication message is therefore about **retriever-conditioned
representation and auditable search**, not a universal model win. ARM-04 is a
strict A2 improvement, ARM-03 is a high-quality numerical tie at the reported
precision, ARM-05 is retained as a useful no-gain transfer control, and
ARM-01/ARM-02 are preserved as diagnostic no-winner evidence.

## Plain-language terminology

The phase labels are retained because they are the study's preregistered
identifiers, but every term is expanded here.

| Term | Full meaning in this report |
|---|---|
| A0 | Migration Foundation: controls, schemas, evidence boundaries, and feasibility. |
| A1 | Common Multi-Arm Screening: five representation programs evaluated on five retrieval arms. |
| A2 | Per-Arm AutoIndex: constrained representation-candidate search performed independently for each arm. |
| A3 | Transfer, Complementarity, and Harness Optimization: self-transfer, cross-arm transfer, fixed unions, and operational search adaptation. |
| DAPFAM | Domain-Aware Family-level Patent Retrieval benchmark and dataset. The evaluation unit is a patent family. |
| GEPA | Reflective Prompt Evolution Can Outperform Reinforcement Learning; the methodological lineage used to motivate auditable reflection, not a measured ArmIndex baseline. |
| AutoIndex | The representation-program search idea that changes document representation while holding the retriever and evaluator fixed. |
| OUT-domain | The held-out technical domain partition defined by the benchmark protocol. |
| Recall at 100 | The fraction of relevant patent families appearing in the first 100 retrieved families. |
| nDCG | Normalized discounted cumulative gain, a ranking-quality measure that gives more credit to relevant results appearing earlier. This report uses ranks 100 and 10. |
| p95 latency | The 95th percentile search latency: 95 percent of measured searches completed within this time. |
| REP-DEV | Representation-development role: the fixed 150-query subset used for A1 and A2 development measurement. |
| HDEV-100 | Harness-development role: the reserved 100-query subset intended for A3 harness adaptation and not used adaptively in A1 or A2. |
| EDA | Exploratory data analysis performed only on aggregate-safe values. |
| GPU, CPU, RAM, and VRAM | Graphics processing unit, central processing unit, system memory, and graphics memory. |
| TTL | Time to live: the authorized lifetime of a paid provider allocation. |
| CSV, PNG, SVG, and PDF | Comma-separated values, portable network graphics, scalable vector graphics, and portable document format. |

No abbreviation in the tables changes the scientific unit or expands the
evidence boundary.

## Study question and frozen design

The unit of evaluation is a DAPFAM patent family. A retrieval arm consists of
one frozen retriever, model revision, tokenizer behavior, pooling rule,
normalization rule, similarity function, maximum input length, and query/document
prompt behavior. A representation program changes only the deterministic view
or unitization of the family document; it does not change model weights.

The primary development metric is held-out-domain Recall at 100 results.
Secondary ranking metrics are held-out-domain normalized discounted cumulative
gain at 100 and at 10. Operational measurements include search latency,
throughput, total wall time, charged cost, index size, system memory, and
graphics memory. All A1 and A2 values are development evidence. The protected
Selection and Final partitions were not opened.

### Exact split hierarchy

The original protocol is not a generic three-way ``development/validation/test``
split. It is a two-level, role-specific split:

| Level | Role | Count | How it is used |
|---|---|---:|---|
| Campaign level | Train | 250 | The full development training pool committed by the benchmark protocol. |
| Campaign level | Selection | 125 | Protected future selection exposure; not opened in A0, A1, A2, or current A3 preparation. |
| Campaign level | Final | 872 | Protected final confirmation exposure; remains Owner-gated and unopened. |
| Within Train-250 | Representation-development role | 150 | The only train subset used adaptively for A1 common screening and A2 representation search. |
| Within Train-250 | Harness-development role | 100 | Reserved for A3 aggregate diagnostics; it cannot be used to tune transfer or HarnessOpt decisions. |

Thus, the shorthand remembered as **100 / 150 / the rest** corresponds to the
100-query harness-development role, the 150-query representation-development
role, and the remaining 997 queries (125 Selection plus 872 Final). It is not a
100-query validation set followed by a 150-query development set and an
unqualified test set. The exact parent Train-250 commitment has its own frozen
algorithm, seed 42, and split hash.

This distinction explains the current A3 blocker. A3's adaptive scope is bound
to the Train-250 commitment, while the 100-query harness role is non-adaptive
and aggregate-only. The Owner Store currently contains only the 150-query
representation-development copies, so it is impossible to construct the
hash-bound Train-250 evaluator/runtime package without the missing 100-query
payload and corresponding handoff. Re-labelling the 150 queries as Train-250
would change the scientific unit and is not an admissible repair.

### Registered retrieval arms

| Identifier | Retrieval identity | License and operational role | Plain-language purpose |
|---|---|---|---|
| ARM-01 | BM25 lexical retrieval | Commercial-capable transparent lexical anchor | A CPU-only reference that exposes the value of exact lexical overlap. |
| ARM-02 | BAAI/bge-m3 dense encoder | MIT license; commercial-capable multilingual dense comparator | A generic multilingual dense baseline. |
| ARM-03 | datalyes/patembed-large | CC BY-NC-SA 4.0; research/non-commercial | A patent-domain quality candidate. |
| ARM-04 | Snowflake/snowflake-arctic-embed-m-v2.0 | Apache-2.0; commercial-capable long-context dense candidate | A practical long-context production candidate. |
| ARM-05 | Qwen/Qwen3-Embedding-0.6B | Apache-2.0; commercial-capable instruction-aware candidate | A modern instruction-aware production candidate. |

### Frozen model and prompt bindings

These bindings were fixed before measurement and were not tuned after observing
results.

| Arm | Exact model revision | Query template | Document template and scoring behavior |
|---|---|---|---|
| ARM-01 | BM25 implementation version 0.3.10 | No neural prompt. Unicode normalization and case folding are fixed. | Tokenized lexical matching with fixed parameters k1 = 1.2 and b = 0.75; deterministic document-identifier tie ordering. |
| ARM-02 | BAAI/bge-m3, revision 5617a9f61b028005a4858fdac845db406aefb181 | The query text is passed without an instruction prefix. | The document text is passed without an instruction prefix; official dense pooling and normalization; 1,024 dimensions; cosine-equivalent normalized dot product. |
| ARM-03 | datalyes/patembed-large, revision 2d5c0f92a3e5dc3d5415c08e612c57543c0e03ad | `encode query for different document retrieval: {query}` | `encode document for different retrieval: {document}`; mean pooling over non-padding tokens; L2 normalization; cosine similarity; explicit truncation at the frozen limit. |
| ARM-04 | Snowflake/snowflake-arctic-embed-m-v2.0, revision 95c2741480856aa9666782eb4afe11959938017f | `query: {query}` | No document prefix; first-token/CLS pooling; L2 normalization; normalized dot product; 768 dimensions; remote-code hashes frozen. |
| ARM-05 | Qwen/Qwen3-Embedding-0.6B, revision 97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3 | `Instruct: Retrieve patent families containing technical information relevant to prior-art search for the query patent family.\nQuery:{query}` | No document instruction; last-token pooling with left padding; L2 normalization; normalized dot product; 1,024 dimensions. |

### Five deterministic representation programs

| Identifier | Full representation | Why it is measured |
|---|---|---|
| P00 title-abstract-claims document | Concatenate title, abstract, and claims in the prescribed family order as one document. | Full-information baseline. |
| P01 title-abstract document | Use title and abstract only. | Compact view that removes claim text and reduces cost. |
| P02 first-claim representation | Use the first structured independent claim in family order. | Tests whether legally central technical language is a strong anchor. |
| P03 fixed passages | Split the title-abstract-claims stream into 384-token passages with 64-token overlap and retain the final partial passage. | Limits long-document truncation; family score is the maximum passage score. |
| P04 section multi-view | Keep title, abstract, and claims as labelled views and aggregate family evidence with reciprocal-rank fusion using k = 60. | Tests whether section identity preserves complementary signals. |

Every program applies Unicode normalization, canonical whitespace, ordered
family membership, explicit field labels, and a fail-closed rule for silent
truncation. These are deterministic programs, not generated prose.

## A0: Migration Foundation

### Work completed

A0 converted the research repository into a controlled scientific environment
before any retrieval-quality measurement. It established canonical authority,
versioned schemas, the five-arm registry, model and license declarations,
evidence projection rules, protected-data policy, provider controls, and
reproducible feasibility fixtures. The migration also synchronized the Brain,
read-model, Obsidian, MLflow, Dashboard, and Owner-gate projections without
making any of them independent scientific authorities.

The protected-data policy keeps raw queries, split membership, relevance
judgements, rankings, per-query outcomes, credentials, and raw provider
payloads out of Git, Brain, Paper, Obsidian, MLflow, Dashboard, presentation
slides, and chat. Only aggregate-safe counts, hashes, manifests, receipts,
figures, and derived metrics can leave the Owner-local store.

### A0 validation evidence

The A0 closeout recorded five registered arms, one runnable fixture arm, zero
asset-registry errors, 44 targeted ArmIndex tests, 387 full-suite tests, and 66
Dashboard/API policy tests. An independent migration review recorded 20 focused
tests, 14 verified source components, six projection lifecycle events, and zero
report drift.

These values support engineering readiness and provenance only. A0 performed
zero retrieval-quality runs, zero scientific graphics-processing-unit runs, and
zero paid provider calls. The appropriate presentation visual is a methods and
evidence-boundary diagram, not a performance chart.

## A1: Common Multi-Arm Screening

### Protocol and terminal run

A1 measured every combination of five representation programs and five
retrieval arms: 25 logical cells. Each cell used the fixed 150-query
representation-development role, the same evaluator, the same held-out-domain
metrics, and no access to Selection or Final membership. The terminal run
covered all 25 cells, passed its instrumentation checks, and charged USD
11.161632. A prior incomplete attempt was retained separately and was not mixed
with the terminal evidence.

### Aggregate A1 results

| Arm | Recall at 100 | Normalized discounted cumulative gain at 100 | Normalized discounted cumulative gain at 10 | 95th-percentile search latency (ms) | Total wall time (s) | Disposition |
|---|---:|---:|---:|---:|---:|---|
| ARM-01 BM25 lexical | 0.191200 | 0.172717 | 0.160011 | 441.520 | 762.533 | Diagnostic, non-advancing |
| ARM-02 BAAI/bge-m3 | 0.269933 | 0.231377 | 0.198497 | 235.203 | 19,847.315 | Diagnostic, non-advancing |
| ARM-03 PatEmbed | 0.413400 | 0.347812 | 0.289856 | 212.062 | 29,444.640 | Advanced |
| ARM-04 Arctic Embed | 0.340667 | 0.284546 | 0.235538 | 214.207 | 15,878.488 | Advanced |
| ARM-05 Qwen3 Embedding | 0.363733 | 0.307930 | 0.256706 | 217.099 | 40,309.513 | Advanced |

### Complete A1 cell-level results

The following aggregate table is sufficient to reproduce the presentation
chart without exposing query identifiers or relevance judgements.

| Arm | Program | Recall at 100 | Normalized discounted cumulative gain at 100 | Normalized discounted cumulative gain at 10 | 95th-percentile latency (ms) | Wall time (s) |
|---|---|---:|---:|---:|---:|---:|
| BM25 lexical | P00 title-abstract-claims | 0.1980 | 0.1813 | 0.1728 | 190.5 | 111.7 |
| BM25 lexical | P01 title-abstract | 0.1247 | 0.1109 | 0.0999 | 190.5 | 54.4 |
| BM25 lexical | P02 first claim | 0.1870 | 0.1703 | 0.1599 | 203.6 | 82.6 |
| BM25 lexical | P03 fixed passages | 0.2347 | 0.2108 | 0.1950 | 771.1 | 269.4 |
| BM25 lexical | P04 section multi-view | 0.2117 | 0.1903 | 0.1725 | 851.9 | 244.4 |
| BAAI/bge-m3 | P00 title-abstract-claims | 0.2733 | 0.2363 | 0.2004 | 156.0 | 2,629.8 |
| BAAI/bge-m3 | P01 title-abstract | 0.2590 | 0.2255 | 0.1966 | 158.5 | 1,712.9 |
| BAAI/bge-m3 | P02 first claim | 0.2510 | 0.2158 | 0.1882 | 181.2 | 2,560.5 |
| BAAI/bge-m3 | P03 fixed passages | 0.2887 | 0.2510 | 0.2216 | 295.1 | 7,187.7 |
| BAAI/bge-m3 | P04 section multi-view | 0.2777 | 0.2284 | 0.1856 | 385.1 | 5,756.4 |
| PatEmbed | P00 title-abstract-claims | 0.4147 | 0.3549 | 0.3031 | 149.5 | 5,723.2 |
| PatEmbed | P01 title-abstract | 0.4010 | 0.3373 | 0.2827 | 153.8 | 1,709.3 |
| PatEmbed | P02 first claim | 0.4163 | 0.3542 | 0.3049 | 150.2 | 5,201.4 |
| PatEmbed | P03 fixed passages | 0.4230 | 0.3593 | 0.3015 | 241.7 | 8,485.1 |
| PatEmbed | P04 section multi-view | 0.4120 | 0.3333 | 0.2570 | 365.0 | 8,325.7 |
| Arctic Embed | P00 title-abstract-claims | 0.3443 | 0.2849 | 0.2340 | 140.9 | 2,159.0 |
| Arctic Embed | P01 title-abstract | 0.3237 | 0.2728 | 0.2294 | 143.0 | 1,180.1 |
| Arctic Embed | P02 first claim | 0.3303 | 0.2820 | 0.2393 | 144.3 | 2,209.8 |
| Arctic Embed | P03 fixed passages | 0.3527 | 0.3031 | 0.2588 | 270.2 | 5,727.0 |
| Arctic Embed | P04 section multi-view | 0.3523 | 0.2800 | 0.2162 | 372.8 | 4,602.6 |
| Qwen3 Embedding | P00 title-abstract-claims | 0.3663 | 0.3131 | 0.2643 | 149.7 | 5,084.9 |
| Qwen3 Embedding | P01 title-abstract | 0.3497 | 0.3033 | 0.2622 | 156.1 | 3,844.0 |
| Qwen3 Embedding | P02 first claim | 0.3577 | 0.3079 | 0.2591 | 159.4 | 5,083.7 |
| Qwen3 Embedding | P03 fixed passages | 0.3800 | 0.3224 | 0.2730 | 270.7 | 14,715.6 |
| Qwen3 Embedding | P04 section multi-view | 0.3650 | 0.2931 | 0.2250 | 349.6 | 11,581.4 |

### A1 interpretation

PatEmbed is highest on the three aggregate quality metrics, but its license is
research/non-commercial. Qwen3 Embedding is the second-highest quality arm and
has the largest total wall time. Arctic Embed is a strong commercial-capable
dense arm with lower wall time than the other dense arms. BM25 is the lowest
quality reference but remains important because it is transparent and CPU-only.

Fixed passages are the strongest A1 representation in all five arms. This is a
descriptive common-screen result, not permission to assume one representation
is universal: A2 deliberately searches independently within each arm.

### A1 failure evidence

An earlier run stopped before any dense-cell receipt because mandatory
performance, resource, and reliability instrumentation was missing. Its five
lexical cells and zero dense cells remain preserved as a failed-closed attempt.
Only the compatible 25-of-25 terminal run enters the aggregate result. This
separation is publication-relevant because it demonstrates that incomplete
measurement was not silently converted into a result.

## A2: Per-Arm AutoIndex

### Objective and exact accounting

A2 searched the frozen representation-candidate universe independently for each
arm. The accounting is exact and receipt-bound:

| Category | Count | Meaning |
|---|---:|---|
| Candidate universe | 52 | All candidate slots authorized by the frozen A2 contract. |
| Matched candidates | 40 | Candidates with a complete matched comparison. |
| Activated conditional reserves | 4 | Reserve candidates admitted by the prespecified decision path. |
| Measured candidates | 44 | 40 matched plus four activated reserves. |
| Dormant conditional reserves | 8 | Valid reserved slots that remained unmeasured because activation was not triggered. |
| Failed candidates | 0 | No candidate failed the measured run. |

The arithmetic is therefore **52 = 40 matched + 4 activated reserves + 8
dormant reserves = 44 measured + 8 dormant**. The measured workload cost was
USD 54.52666666666665948 under the USD 60 hard stop. Safe return, worker
reaping, exact coverage, and the independent aggregate-only integrity audit all
passed.

### A2 arm outcomes

| Arm | Program outcome | Recall at 100 | Normalized discounted cumulative gain at 100 | Normalized discounted cumulative gain at 10 | 95th-percentile latency (ms) | Charged cost (USD) | Comparison with A1 | A3 disposition |
|---|---|---:|---:|---:|---:|---:|---|---|
| ARM-01 BM25 lexical | Diagnostic three-way top tie | 0.2346666667 | 0.2107836237 | 0.1950241409 | 1,387.940057 | 0.0000000000 | Diagnostic tie, no winner | Excluded from A3 |
| ARM-02 BAAI/bge-m3 | Diagnostic three-way top tie | 0.2900000000 | 0.2499193095 | 0.2200574939 | 1,139.044918 | 0.2172489253 | Diagnostic tie, no winner | Excluded from A3 |
| ARM-03 PatEmbed | matched-b2-orthogonal | 0.4230000000 | 0.3576360657 | 0.2994437535 | 1,686.804176 | 0.3080191566 | Numerical tie at reported precision | Primary transfer input |
| ARM-04 Arctic Embed | matched-b1-orthogonal | 0.3586666667 | 0.3018675218 | 0.2532294396 | 1,115.051996 | 0.1592182057 | Strict improvement of 0.0060 | Primary transfer input |
| ARM-05 Qwen3 Embedding | matched-b1-matched-ablation | 0.3736666667 | 0.3212617218 | 0.2736642420 | 816.054961 | 0.2109004291 | No strict improvement | Primary transfer input |

### A2 interpretation

The evidence supports four bounded conclusions:

1. PatEmbed remains the highest-quality arm and its A2 result is a numerical
   tie with the frozen A1 comparator at the reported precision.
2. Arctic Embed is the strict A2 improvement and is the clearest
   commercial-capable transfer input.
3. Qwen3 Embedding does not show a strict A2 improvement, but retaining it for
   transfer and complementarity prevents positive-result selection bias.
4. BM25 and BAAI/bge-m3 produce diagnostic three-way no-winner ties; they are
   useful negative evidence and are not promoted into A3 optimization.

The conclusion is about arm-specific constrained search and transfer
eligibility. It is not a claim that AutoIndex improves every arm, that one
representation is universally best, or that a production profile has been
selected.

## Prompts and candidate-generation controls

The retrieval templates above are the prompts used by the embedding models.
A2 also used an Official Codex proposer and an independent reviewer before
measurement. Both received aggregate-safe operation metadata only. They never
received query identifiers, membership, relevance judgements, rankings,
per-query outcomes, credentials, provider payloads, or measured results.

### Proposer prompt contract (complete operational wording)

> You are the Official Codex representation proposer for a pre-measurement,
> five-arm patent-retrieval study. Return only JSON matching the supplied output
> schema. Use only the frozen aggregate-safe payload. Propose exactly the four
> requested candidate slots. Preserve every candidate identifier and role
> exactly. Make each hypothesis falsifiable, retriever-conditioned, compatible
> with the listed source fields, and distinct from the other candidates. Do not
> use or request protected data or measured results. For program fields, use
> only allowed source fields and ensure field order contains each field exactly
> once. Keep passage sizes within the declared arm limit. Diagnostic arms remain
> non-advancing when the payload says so. Each hypothesis must identify one
> deterministic representation intervention, the frozen within-arm comparator,
> the expected direction that can later be falsified, and a concrete failure
> condition without claiming improvement. Conditional reserves remain dormant
> unless the frozen activation predicate is satisfied. On revision rounds,
> accepted candidate identifiers are immutable and must be copied byte-for-byte.

### Independent reviewer prompt contract (complete operational wording)

> You are the independent Official Codex reviewer for a frozen pre-measurement
> representation-candidate batch. Return only JSON matching the supplied output
> schema. Review only the frozen aggregate-safe context and candidate payload.
> Preserve every candidate identifier. Check falsifiability, role fit,
> duplication, protected-boundary safety, arm compatibility, deterministic
> interpretability, and publication interpretability. Accept only candidates
> that satisfy every check. Required changes must not alter the evaluator,
> metrics, model weights, protected split, advancement rule, or diagnostic
> non-advancement. Previously accepted candidates must remain byte-identical;
> reject one only for a concrete newly observed safety, determinism,
> duplication, or contract defect.

These prompt contracts make candidate generation auditable and prevent the
language model from freely changing the retrieval runtime or seeing evaluation
signal.

## Figures and aggregate-safe data files

The following artifacts are presentation-ready. They contain aggregate counts,
metrics, hashes, and captions only; they do not contain raw patent text,
query identifiers, split membership, relevance judgements, rankings,
per-query outcomes, credentials, or provider payloads.

### CSV files

| File name | Purpose | Evidence scope |
|---|---|---|
| A0_A1_A2_phase_summary_figure_20260818.csv | Phase status, evidence class, headline metric, and A2 accounting for the phase overview figure. | A0 engineering validation; A1 and A2 development evidence; A3 pending. |
| A1_common_screen_aggregate_eda_20260818.csv | One aggregate row per retrieval arm for quality and operational comparison. | Complete 25-cell A1 terminal run. |
| A2_per_arm_autoindex_outcomes_eda_20260818.csv | One aggregate row per arm for A2 result, comparison class, cost, and A3 route. | Passed A2 closeout and integrity audit. |
| A1_A2_quality_frontier_figure_20260818.csv | Long-form Recall at 100 values for A1 and A2 comparison plotting. | Aggregate-safe development evidence. |
| A0_A1_A2_figure_index_20260818.csv | Figure identifiers, full takeaways, source datasets, and recommended presentation use. | Figure provenance and narration aid. |
| A0_A1_A2_metric_dictionary_20260818.csv | Full metric names, units, interpretation, and claim cautions. | Reproducible EDA vocabulary. |

### Figures

| Figure file | Takeaway for an advisor | Recommended use |
|---|---|---|
| a0-a2-publication-timeline.svg | The evidence sequence moves from governance to common screening to per-arm search; transfer remains gated. | Opening roadmap. |
| a1-common-screen-quality.png | Quality changes with both the retriever and the document representation. | Main A1 result. |
| a1-common-screen-efficiency.png | Quality, latency, wall time, and graphics-memory demand are different trade-offs. | Operational interpretation. |
| a1-development-role-split.png | Representation development and later harness adaptation use separate predefined roles. | Leakage-control methods slide. |
| a2-coverage-recovery.png | All 52 authorized candidates are accounted for: 44 measured, eight dormant, none failed. | A2 completeness slide. |
| a2-per-arm-outcomes.png | Three arms advance to transfer analysis while two remain diagnostic no-winner outcomes. | Main A2 result. |
| a2-quality-latency-cost-frontier.png | Quality must be read together with operational latency and cost. | Trade-off slide or appendix. |
| a2-matched-reserve-decision-path.png | Conditional reserves were activated only by the prespecified decision path. | Methods audit. |
| a2-evidence-chain.png | Advisor-facing claims trace to closeout, integrity, and safe-return evidence. | Trust and reproducibility slide. |

Each figure has one central claim, direct labels, a visible evidence qualifier,
and a caption-level limitation. Null, diagnostic, and pending states are shown
as states rather than hidden.

## A3 status and next controlled question

A3 is **prepared but not measured**. The planned measurement contains a 3 by 3
self-transfer and cross-transfer matrix for ARM-03, ARM-04, and ARM-05, fixed
equal-depth complementarity controls, and at most three complete four-role
HarnessOpt batches covering quality exploitation, cost/latency ablation,
routing hypothesis, and diversity profile.

Measurement is blocked by missing authorized inputs, not by a scientific null
result. The required next evidence is an Owner-authorized hash-bound package
containing the full 250-query training scope, the reserved 100-query harness
scope, corpus and evaluator bindings, and a fresh runtime package. Fresh
provider identity, an all-fee quote no older than 900 seconds, a 48-hour target
time-to-live, and an admission under the USD 35 A3 hard cap and USD 180 campaign
ceiling are also required. The existing provider observation is idle capacity,
not valid A3 admission.

Until those inputs and admission exist, no transfer score, complementarity
score, HarnessOpt winner, A4 production profile, Selection result, or Final
result may be reported.

## Advisor-ready presentation sequence

1. **Why patent retrieval is difficult:** introduce DAPFAM family-level
   retrieval and the distinction between a patent family, a document view, and
   a retriever.
2. **Research lineage:** connect the question to GEPA's reflective optimization
   perspective and AutoIndex's representation-program search while stating that
   ArmIndex measures its own frozen protocol.
3. **A0 control plane:** show canonical controls, protected-data boundaries,
   and the fact that governance preceded quality measurement.
4. **Retrieval stack:** show tokenization or embedding, indexing, ranking, and
   family-level evaluation.
5. **A1 common screen:** show the five-by-five quality surface and the fixed
   representation programs.
6. **A1 operational trade-off:** show quality beside latency and wall time.
7. **A1 failure discipline:** contrast the incomplete failed-closed attempt
   with the complete 25-of-25 terminal run.
8. **A2 search logic:** explain matched candidates, activated reserves, and
   dormant reserves.
9. **A2 outcomes:** highlight the strict Arctic Embed improvement, the PatEmbed
   numerical tie, the retained Qwen3 no-gain transfer input, and the two
   diagnostic no-winner arms.
10. **A3 next question:** present transfer and complementarity as a new
    hash-bound experiment, not as an observed result.

## References and claim discipline

- Ayaou, Cavallucci, and Chibane, *DAPFAM: A Domain-Aware Family-level Dataset
  to Benchmark Cross-Domain Patent Retrieval*, arXiv:2506.22141. Used for
  family-level retrieval design and held-out-domain evaluation.
- *GEPA: Reflective Prompt Evolution Can Outperform Reinforcement Learning*,
  arXiv:2507.19457. Used as methodological lineage; no GEPA numerical result
  is claimed here.
- O'Nuallain et al., *AutoIndex: Learning Representation Programs for
  Retrieval*, arXiv:2607.18603. Used to motivate constrained representation
  search while holding the retriever fixed.
- *PatenTEB* and related patent-embedding benchmark work, arXiv:2510.22264 and
  arXiv:2605.24297. Used to motivate patent-specific encoders and interactions
  among model family, document view, prompting, and aggregation.
- BAAI/bge-m3 model card, datalyes/patembed-large model card, Snowflake Arctic
  Embed model card, and Qwen3 Embedding model card. Used for official model
  identity, declared limits, and license statements.
- RouterRetriever, arXiv:2409.02685. Used only to motivate the future routing
  and complementarity question.

### Claim boundary

This report is an advisor-facing synthesis of aggregate-safe evidence. A0 is
engineering validation. A1 and A2 are measured development evidence. The report
does not establish a Selection result, a Final result, a legal conclusion,
infringement or novelty, a causal mechanism, or a commercial deployment
guarantee. ARM-03 must retain its research/non-commercial license qualifier.

The current phase state is: **A0 complete; A1 complete; A2 closeout passed; A3
pending a hash-bound 250-query input and fresh admission; A4 through A6 locked
by protocol gates.**
