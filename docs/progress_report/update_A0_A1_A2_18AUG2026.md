---
title: "ArmIndex advisor update: A0 through A2"
audience: "Academic advisor and presentation use"
report_date: "2026-08-18"
reporting_cutoff_utc: "2026-08-18T18:00:00Z"
status: "A0 complete; A1 complete; A2 measured closeout passed; A3 pending hash-bound Train-250 input"
numeric_authority: "Validated aggregate receipts and closeout projections only"
evidence_boundary: "Development evidence; Selection and Final remain closed"
---

# ArmIndex advisor update: A0 through A2

## One-minute summary

ArmIndex asks whether the best representation program depends on the retriever,
and whether the resulting arm-specific programs can later transfer or combine
into a useful quality-latency-cost frontier. The work is deliberately staged:
governance and reproducibility are established first, common screening is run
before per-arm search, and transfer is held for a separate hash-bound split.

- **A0 is complete.** The migration foundation established the canonical
  controls, five-arm registry, scientific schemas, license declarations,
  protected-data boundary, and reproducible feasibility fixtures. A0 ran no
  retrieval-quality experiment.
- **A1 is complete with measured development evidence.** The clean terminal
  screen covered all 25 representation-by-retriever cells. PatEmbed (ARM-03)
  had the highest aggregate OUT Recall@100, while Arctic Embed (ARM-04) and
  Qwen3 Embedding (ARM-05) also passed the frozen advancement rule.
- **A2 is closed with an integrity-audited measured result.** The frozen
  AutoIndex search accounts for 52 candidates: 40 matched candidates, four
  activated conditional reserves, and eight dormant reserves. Forty-four were
  measured and none failed. Safe return and worker reaping passed; the whole
  workload cost was USD 54.52666666666665948 against a USD 60 hard stop.
- **A3 is prepared but not started.** Only ARM-03, ARM-04, and ARM-05 may enter
  transfer analysis. Measurement waits for an Owner-authorized hash-bound
  Train-250 query, corpus, and evaluator package plus fresh admission evidence.

The current scientific message is therefore bounded and useful: common
screening shows strong retriever-dependent quality differences; per-arm search
changes the selected representation for some arms; transfer and complementarity
remain an open, separately controlled question.

## Terminology used in this report

The phase labels A0, A1, A2, and A3 identify the migration foundation, common
multi-arm screening, per-arm representation search, and transfer plus harness
optimization phases, respectively. "OUT-domain" means the held-out domain
partition defined by the study protocol. Recall@100 is the proportion of
relevant patent families retrieved within the first 100 results; normalized
discounted cumulative gain at ranks 100 and 10 measures ranking quality with
greater weight on early ranks. The representation-development subset is the
fixed portion of the 250-query training pool used for A1 and A2; the separate
harness-development subset is reserved for A3. These names describe split
roles, not new results.

## The study in one slide

| Phase | Question | Current answer | Evidence boundary |
|---|---|---|---|
| A0 Migration Foundation | Can the work be reproduced and governed? | Yes: controls, schemas, arm registry, protected boundary, and fixtures are in place. | Engineering validation only. |
| A1 Common Screening | Does representation choice matter across retrievers? | Yes descriptively: the five-arm means differ substantially, with ARM-03 highest. | Measured development evidence on REP-DEV. |
| A2 Per-arm AutoIndex | Does each arm select the same representation? | No single representation is assumed; arm-specific winners and diagnostic ties are recorded under frozen rules. | Measured development evidence; exact closeout passed. |
| A3 Transfer and HarnessOpt | Do winners transfer or combine profitably? | Not measured yet. | Pending hash-bound Train-250 input and fresh admission. |
| A4-A6 | Can a production profile, Selection result, and release claim be made? | Locked until the required scientific and Owner gates open. | No Selection or Final evidence. |

The compact phase data for figures is in
[A0-A3 phase summary CSV](A0_A1_A2_phase_summary_figure_20260818.csv).

## Research design and frozen choices

The evaluation unit is the DAPFAM patent family. The primary development metric
is OUT Recall@100; secondary metrics are OUT nDCG@100 and OUT nDCG@10. Operational
measurements include search latency, throughput, charged cost, index size, RAM,
and VRAM. The development split is REP-DEV; Selection and Final are not opened.

The five registered arms are:

| Arm | Retriever family | Model/license class | Role in the story |
|---|---|---|---|
| ARM-01 | BM25 lexical | Commercial-capable | CPU lexical anchor and diagnostic baseline. |
| ARM-02 | BGE-M3 | Commercial-capable | Multilingual dense anchor and diagnostic baseline. |
| ARM-03 | PatEmbed | Research/non-commercial | Research quality champion candidate. |
| ARM-04 | Arctic Embed | Commercial-capable | Long-context dense production candidate. |
| ARM-05 | Qwen3 Embedding | Commercial-capable | Instruction-aware dense production candidate. |

All A1 representation programs and model adapters were frozen before the common
screen. A2 then searched the frozen candidate universe independently per arm.
No later phase is allowed to reinterpret an A1/A2 winner using an unregistered
metric or a post-hoc tie break.

### Frozen model bindings and representation programs

The following names are the complete public-facing description of the measured
retrieval arms. Model identity, tokenizer revision, pooling, normalization,
dimension, similarity function, maximum length, and prompt text were frozen
before measurement; they were not tuned after observing the A1 or A2 results.

| Arm | Official model or retrieval identity | License/role | Frozen query and document behavior |
|---|---|---|---|
| ARM-01 | BM25 lexical retrieval | Transparent lexical anchor; commercial-capable | Tokenized lexical matching with the frozen BM25 parameters; no neural prompt or embedding step. |
| ARM-02 | `BAAI/bge-m3` dense encoder | MIT; commercial-capable generic dense comparator | Dense-only mode, official pooling and normalization, 1,024 dimensions, no query instruction for the standard dense configuration. |
| ARM-03 | `datalyes/patembed-large` | CC BY-NC-SA 4.0; research/non-commercial champion candidate | Query prefix: `encode query for different document retrieval: {query}`. Document prefix: `encode document for different retrieval: {document}`. Mean pooling over non-padding tokens, L2 normalization, cosine similarity, and explicit truncation. |
| ARM-04 | `Snowflake/snowflake-arctic-embed-m-v2.0` | Apache-2.0; commercial-capable long-context dense comparator | Query prefix: `query: `. No document prefix. First-token/CLS pooling, L2 normalization, normalized dot product, 768 dimensions, and remote-code hashes frozen. |
| ARM-05 | `Qwen/Qwen3-Embedding-0.6B` | Apache-2.0; commercial-capable instruction-aware dense comparator | Query instruction: `Instruct: Retrieve patent families containing technical information relevant to prior-art search for the query patent family.\nQuery:{query}`. Documents have no instruction. Last-token pooling, left padding, L2 normalization, normalized dot product, and 1,024 dimensions. |

The common representation grammar contained five deterministic programs. They
change the document view or unitization, not the model weights:

| Program | Plain-language definition | Why it is measured |
|---|---|---|
| P00, title-abstract-claims document | Concatenate title, abstract, and claims in their prescribed order as one family document. | Tests whether the broadest full-text view provides enough context for matching. |
| P01, title-abstract document | Use title and abstract only. | Tests a compact, lower-cost document view that removes claim text. |
| P02, first-claim representation | Use the first claim segment as the document representation. | Tests whether the legally central claim language is a stronger retrieval anchor. |
| P03, fixed passages | Split the document into model-valid fixed passages and aggregate family evidence with maximum passage score. | Tests long-document decomposition and limits the effect of truncation. |
| P04, section multi-view | Keep title, abstract, and claims as separately labelled views, then aggregate their family-level scores. | Tests whether section identity helps a retriever preserve complementary signals. |

This design is the direct operationalization of the AutoIndex idea that
document representation can be optimized while the retriever remains fixed. It
also follows the DAPFAM family-level evaluation convention and the patent
embedding literature's warning that model family, text view, prompting, and
aggregation interact. A1 therefore screens every frozen program on every arm;
A2 then searches independently per arm instead of assuming that the best common
program is universal.

## A0: migration foundation

### What A0 delivered

A0 converted the project into a controlled research environment before any
retrieval-quality measurement. It established canonical authority, schemas,
model and arm declarations, evidence-projection rules, and a protected-data
policy that keeps raw queries, memberships, qrels, rankings, per-query outcomes,
credentials, and provider payloads out of publication-facing projections.

The completed task range covered repository/evidence migration; canonical source
of truth; Brain, read-model, Obsidian, MLflow, Dashboard, and Owner-gate
migration; scientific contracts; model and license declarations; CPU/storage
feasibility; validation/safety closeout; and legacy-code harvest.

### Evidence and interpretation

The A0 closeout recorded five registered arms, one runnable fixture arm, zero
asset-registry errors, 44 targeted ArmIndex tests, 387 full-suite tests, and 66
Dashboard/API policy tests. The independent migration review recorded 20 focused
tests, 14 verified source components, six projection lifecycle events, and zero
report drift.

These numbers support engineering readiness and provenance only. A0 performed
zero measured retrieval runs, zero scientific GPU runs, and zero paid API calls.
No A0 figure should be presented as a performance result; a methods slide showing
the control plane and evidence boundary is the appropriate use.

## A1: common multi-arm screening

### Protocol and terminal attempt

A1 evaluated the same five frozen representation programs against all five
retriever arms: 25 logical cells in total. The terminal attempt completed with
PASS 25/25 coverage and charged USD 11.161632. The arm-level aggregate table
below is the primary advisor-facing EDA view; the underlying cell-level values
remain available in the project evidence package.

### Aggregate quality and operational results

| Arm | OUT Recall@100 | OUT nDCG@100 | OUT nDCG@10 | Search p95 (ms) | Total wall time (s) | A1 disposition |
|---|---:|---:|---:|---:|---:|---|
| ARM-01 BM25 | 0.191200 | 0.172717 | 0.160011 | 441.520 | 762.533 | Diagnostic/non-advancing |
| ARM-02 BGE-M3 | 0.269933 | 0.231377 | 0.198497 | 235.203 | 19,847.315 | Diagnostic/non-advancing |
| ARM-03 PatEmbed | 0.413400 | 0.347812 | 0.289856 | 212.062 | 29,444.640 | Advanced |
| ARM-04 Arctic Embed | 0.340667 | 0.284546 | 0.235538 | 214.207 | 15,878.488 | Advanced |
| ARM-05 Qwen3 Embedding | 0.363733 | 0.307930 | 0.256706 | 217.099 | 40,309.513 | Advanced |

The complete aggregate-safe table is available as
[A1 common-screen EDA CSV](A1_common_screen_aggregate_eda_20260818.csv).

### Figures ready for use

| Figure | Single-sentence takeaway | Presentation role |
|---|---|---|
| [Common-screen quality](figures/a1-common-screen-quality.png) | Quality changes with both retriever and document representation. | Main A1 result. |
| [Common-screen efficiency](figures/a1-common-screen-efficiency.png) | Latency, wall time, and video-memory demand vary independently from quality. | Operational trade-off. |
| [Development-role split](figures/a1-development-role-split.png) | Representation search and later harness adaptation use separate predefined development roles. | Methods and leakage control. |

Each figure shows only aggregate-safe information. The corresponding CSV is
the numeric source for any re-rendered chart; neither the figures nor the CSV
contains query identifiers, relevance labels, rankings, or per-query outcomes.

### What the A1 pattern means

ARM-03 is highest on all three aggregate quality metrics, but its license class
is research/non-commercial. ARM-05 is the second-highest quality arm and has
the largest total wall time. ARM-04 is a strong commercial-capable dense arm
with the shortest total wall time among the dense arms. ARM-01 is the lowest
quality reference but remains valuable as a transparent lexical anchor.

The cell-level EDA shows that representation choice changes quality within each
retriever. Fixed passages were the strongest representation in every arm in the
published cell table. That is descriptive evidence, not evidence that a single
program should be reused across arms; A2 exists to test that assumption under a
separate frozen candidate search.

### Failed-closed attempt and why it matters

An earlier A1 attempt stopped before any dense-cell receipt because mandatory
performance, resource, and reliability instrumentation was missing. Its five
lexical cells and zero dense cells were not mixed with the later clean attempt.
This is an important methodological result for the presentation: incomplete
measurement is retained as failure evidence, while only the compatible terminal
attempt enters the aggregate result.

## A2: per-arm AutoIndex

### Objective and accounting

A2 searched the frozen representation-candidate universe independently for each
arm. The exact accounting is:

| Quantity | Count |
|---|---:|
| Candidate universe | 52 |
| Matched candidates | 40 |
| Activated conditional reserves | 4 |
| Measured candidates | 44 |
| Dormant conditional reserves | 8 |
| Failed candidates | 0 |

The primary metric remained OUT Recall@100. The measured workload cost was USD
54.52666666666665948 under the USD 60 hard stop. The closeout passed safe return,
worker reaping, exact coverage, and an independent aggregate-only integrity audit.

### Winner and diagnostic outcomes

| Arm | Selected or diagnostic program | Recall@100 | Comparison with frozen A1 comparator | A3 route |
|---|---|---:|---|---|
| ARM-01 | Diagnostic three-way top tie | 0.23467 | No winner under the frozen rule | Excluded |
| ARM-02 | Diagnostic three-way top tie | 0.29000 | No winner under the frozen rule | Excluded |
| ARM-03 | `matched-b2-orthogonal` | 0.42300 | Numerical tie at presentation precision | Transfer input |
| ARM-04 | `matched-b1-orthogonal` | 0.35867 | Strict improvement (+0.0060) | Transfer input |
| ARM-05 | `matched-b1-matched-ablation` | 0.37367 | No strict improvement | Transfer input |

The machine-readable aggregate outcomes are in
[A2 AutoIndex EDA CSV](A2_per_arm_autoindex_outcomes_eda_20260818.csv), and the
long-form quality values for plotting are in
[A1-A2 frontier CSV](A1_A2_quality_frontier_figure_20260818.csv).

### Interpretation for an advisor or reviewer

A2 does not support the claim that AutoIndex improves every arm. It supports a
more precise statement:

1. ARM-03 retains the strongest quality result, but its A2 value is a numerical
   tie with its frozen A1 comparator at the reported precision.
2. ARM-04 shows a strict improvement over its frozen A1 comparator and is a
   credible commercial-capable transfer input.
3. ARM-05 remains valuable for transfer and complementarity despite no strict
   A2 improvement; retaining this boundary result prevents positive-result
   selection bias.
4. ARM-01 and ARM-02 are diagnostic no-winner outcomes and cannot enter A3
   optimization.

The A2 conclusion is therefore about arm-specific selection and bounded transfer
eligibility, not about a universal representation winner.

### Figures ready for use

| Figure | Single-sentence takeaway | Presentation role |
|---|---|---|
| [Coverage and recovery](figures/a2-coverage-recovery.png) | All 52 candidates are accounted for: 44 measured, eight dormant, none failed. | Execution completeness. |
| [Per-arm outcomes](figures/a2-per-arm-outcomes.png) | The three advancement inputs and two diagnostic no-winner arms remain visibly distinct. | Main A2 result. |
| [Quality-latency-cost frontier](figures/a2-quality-latency-cost-frontier.png) | Quality must be read with operational cost and latency, not alone. | Trade-off interpretation. |
| [Matched-reserve decision path](figures/a2-matched-reserve-decision-path.png) | Conditional reserves were activated only by the prespecified decision path. | Method audit. |
| [Evidence chain](figures/a2-evidence-chain.png) | Publication-facing interpretation is traceable to closeout and integrity evidence. | Appendix or trust slide. |

The figures are derived from validated aggregate closeout evidence and are
provided here for advisor presentation. They do not establish Selection or
Final performance.

## A3 and the next controlled question

A3 is prepared but not measured. The planned scope contains a 3x3 transfer matrix
for ARM-03, ARM-04, and ARM-05, fixed equal-depth complementarity controls, and at
most three complete four-role HarnessOpt batches. Adaptive work is limited to
Train-250; HDEV-100 remains aggregate-only and non-adaptive.

The next scientific input is an Owner-authorized, hash-bound Train-250 package
covering the query/corpus/evaluator commitments and fixed runtime bindings. Fresh
provider identity, quote, TTL, and budget admission are required before any
remote contact, spend, transfer evaluation, or HarnessOpt measurement. The A2
provider is not treated as reusable merely because it existed previously.

Until that input and admission exist, A3 remains a preparation state. A4 is
locked until A3 produces valid transfer and frontier evidence. Selection and
Final remain unopened, and no publication claim should imply otherwise.

## Recommended advisor presentation sequence

1. **Methods slide:** show the A0 control plane, frozen contracts, and protected
   evidence boundary. Emphasize that A0 has no performance result.
2. **Main result slide:** show A1 arm-level Recall@100 with the companion
   nDCG/latency table. Use the A1 EDA CSV for a reproducible plot.
3. **Reliability slide:** show the failed-closed A1 attempt and the clean 25/25
   terminal attempt as separate evidence paths.
4. **AutoIndex slide:** show A2's 52-candidate accounting and the five arm
   outcomes. Highlight ARM-04's strict gain and ARM-05's retained no-gain
   transfer input.
5. **Next-experiment slide:** show A3 as a gated transfer/complementarity test,
   not as an already-observed improvement.

The CSVs in this folder are intentionally aggregate-only and contain no query
identifiers, membership records, qrels, rankings, per-query outcomes,
credentials, or raw provider payloads.

## Research rationale and references

The study design is grounded in the following published lines of work. AutoIndex
motivates searching over executable document representations while holding the
retriever fixed (arXiv:2607.18603). DAPFAM motivates family-level patent
retrieval with explicit in-domain and held-out-domain evaluation and ranking
metrics (arXiv:2506.22141). PatenTEB and the broader patent-embedding benchmark
motivate a patent-specific encoder and the expectation that model family,
document view, prompting, and aggregation can interact (arXiv:2510.22264 and
arXiv:2605.24297). BGE-M3, Qwen3 Embedding, and Arctic Embed provide the generic,
instruction-aware, and long-context commercial-capable comparison families
(arXiv:2402.03216, arXiv:2506.05176, and arXiv:2412.04506). RouterRetriever
motivates the later complementarity and routing question (arXiv:2409.02685).

These references support the hypotheses and design choices; they do not turn the
development measurements in this report into a Selection or Final result.

## Claim boundary and evidence pointers

This report is an advisor-facing synthesis of aggregate-safe evidence. A0 is
engineering validation; A1 and A2 are measured development evidence. The report
does not establish a Selection result, Final result, legal conclusion,
infringement conclusion, novelty conclusion, causal mechanism, or commercial
deployment guarantee.

The numerical basis is the validated A0 closeout, the A1 complete common-screen
aggregate, and the A2 execution-closeout and result-integrity records. The
CSV files and figures in this report folder are the presentation-ready,
aggregate-safe extracts of those sources; no project-internal path is required
to interpret the report.

The current phase statement is: A0 complete, A1 complete, A2 closeout passed,
A3 pending a hash-bound Train-250 input, and A4-A6 locked by protocol gates.
