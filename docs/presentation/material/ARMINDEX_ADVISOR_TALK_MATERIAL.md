---
title: "ArmIndex Advisor Talk Material: Patent Retrieval, A0-A3"
audience: "Academic advisor"
language: "English"
created_utc: "2026-08-18"
current_state: "A0 complete; A1 measured development evidence; A2 measured closeout passed; A3 Extended pending hash-bound Train-250 input"
evidence_boundary: "Aggregate-safe controls and validated A1/A2 receipts only. No protected DAPFAM rows, qrels, raw IDs, rankings, per-query outcomes, provider payloads, Selection, or Final claims."
---

# ArmIndex: Advisor Talk Material

## Purpose and Claim Boundary

This copy-ready material tells one story: patent-family retrieval is difficult
under domain shift; document representation may interact with the retriever;
ArmIndex tests that interaction under a controlled, auditable protocol.

All slide text is English so it can be pasted into a deck. The presenter may
explain it in Thai. A1 and A2 numbers are validated aggregate development
evidence. A2 closeout passed exact candidate accounting, safe return, worker
reap, and independent integrity audit; the result remains outside Selection and
Final.

The requested real DAPFAM example requires a boundary: raw patent rows,
query/family IDs, qrels, rankings, and per-query outcomes are Owner-local. Do
not copy a real dataset row into Git-tracked slides. Use the safe field-anatomy
figure below; an Owner-local, license-compliant real-record rendering can be
substituted only after a separate release review.

## Figure Manifest

All paths are relative to this file unless noted otherwise.

| ID | Figure | Slide | Evidence status |
|---|---|---|---|
| F01 | [DAPFAM family record anatomy](figures/01_dapfam_family_record_anatomy.svg) | Dataset opening | Aggregate-safe schema/counts |
| F02 | [Retrieval system stack](figures/02_retrieval_system_stack.svg) | Retrieval foundations | Protocol schematic |
| F03 | [A0 split and leakage control](figures/03_a0_split_and_leakage_control.svg) | A0 | Aggregate-safe split counts |
| F04 | [A1 representation programs](figures/04_a1_representation_programs.svg) | A1 method | Frozen program grammar |
| F05 | [A1 mean OUT Recall@100](figures/05_a1_mean_out_recall.svg) | A1 result | Valid A1 REP-DEV aggregate |
| F06 | [A2 execution and reserve flow](figures/06_a2_execution_and_reserve_flow.svg) | A2 | Operational flow, not result evidence |
| F07 | [A3 transfer, complementarity, HarnessOpt](figures/07_a3_transfer_complementarity_harnessopt.svg) | A3 | Pending protocol schematic |
| F08 | [A1 quality cell EDA](../../../outputs/figures/armindex/a12-v16-20260811-r15.quality-cell-eda.v16.svg) | A1 detail | Valid A1 aggregate |
| F09 | [A1 efficiency cell EDA](../../../outputs/figures/armindex/a12-v16-20260811-r15.efficiency-cell-eda.v16.svg) | A1 trade-off | Valid A1 aggregate |
| F10 | [REP-DEV/HARNESS-DEV split](../../../outputs/figures/armindex/a1.2-rep-harness-split-eda-v1.svg) | A0 appendix | Split diagnostic |
| F11 | [Dense-overflow EDA](../../../outputs/figures/armindex/a1.2-dense-overflow-eda-v1.svg) | A1 appendix | Windowing diagnostic |
| F12 | [A2 coverage and recovery](../../../outputs/figures/armindex/a2-goal004/a2-goal004-coverage-recovery.svg) | A2 result | Validated closeout aggregate |
| F13 | [A2 arm outcomes](../../../outputs/figures/armindex/a2-goal004/a2-goal004-outcomes.svg) | A2 result | Validated OUT metrics |
| F14 | [A2 quality-latency-cost frontier](../../../outputs/figures/armindex/a2-goal004/a2-goal004-quality-latency-cost-frontier.svg) | A2 result | Validated operational aggregates |
| F15 | [A2 reserve decision path](../../../outputs/figures/armindex/a2-goal004/a2-goal004-matched-reserve-decision-path.svg) | A2 result | Dormant/activated reserve evidence |
| F16 | [A2 audit map](../../../outputs/figures/armindex/a2-goal004/a2-goal004-appendix-audit-map.svg) | A2 appendix | Hash and claim-boundary map |

The supplementary safe diagrams listed in [figures/README.md](figures/README.md)
may also be used. F01-F07 are the main narrative order.

## Main Deck: 15 Slides

### 1. ArmIndex

**Title:** `ArmIndex: Retriever-Conditioned Representation Search for Cross-Domain Patent Retrieval`

**On-slide text:**

- Research question: should a patent family be represented differently for different retrievers?
- Benchmark: DAPFAM family-level cross-domain patent retrieval.
- Current evidence: A0 complete; A1 measured on REP-DEV; A2 measured closeout passed; A3 Extended awaits a hash-bound Train-250 input package.

**Speaker note:** This is not a model leaderboard. The thesis is that the
best document representation may depend on the retrieval backbone, and any
gain must survive separated development, selection, and final confirmation.

**Visual:** title slide with F02 as a supporting visual. **Evidence:** [P1], [P2].

### 2. What is retrieved in DAPFAM?

**Title:** `The retrieval unit is a patent family, not an isolated document chunk`

**On-slide text:**

- A family supplies ordered English `title`, `abstract`, and `claims` fields.
- DAPFAM has 45,336 target families, 1,247 query families, and 49,869 evaluation rows.
- `IN`: at least one shared IPC3 code. `OUT`: no shared IPC3 code.
- Citation-based relevance is an examiner proxy, not a legal conclusion.

**Speaker note:** Show the schema rather than an unapproved raw patent row.
The important concept is that one family can contain long heterogeneous text,
so a single representation can discard useful evidence.

**Visual:** F01. **Evidence:** [P3], [R1].

### 3. Continuity from GEPA

**Title:** `From reflective prompt evolution to bounded representation-program search`

**On-slide text:**

- GEPA motivates reflective, evidence-driven optimization in a constrained text space.
- ArmIndex changes the target: an executable document representation, not a free-form answer prompt.
- A2 used an Official Codex proposer and independent reviewer before measurement.
- Production retrieval remains deterministic, hash-bound, and does not synchronously call an LLM.

**Speaker note:** This is methodological lineage, not a claim that ArmIndex
reproduces GEPA results. GEPA supplies the idea of bounded proposal and review;
ArmIndex applies it to a schema-valid representation program and frozen
evaluator.

**Visual:** F04 plus `proposal -> validation -> frozen program -> deterministic execution`. **Evidence:** [R2], [P1], [P14].

### 4. What ArmIndex will establish

**Title:** `ArmIndex separates representation search, transfer, and harness design`

**On-slide text:**

1. Search a constrained representation program for each frozen retriever.
2. Test whether that program transfers to other retrievers.
3. Measure complementary coverage at equal depth.
4. Optimize a bounded deterministic multi-arm harness under quality, latency, and cost constraints.

**Speaker note:** The stages turn one broad question into falsifiable ones:
is representation retriever-conditioned; do winners transfer; do multiple arms
recover unique families; and can the extra quality justify operational cost?

**Visual:** F07. **Evidence:** [P1].

### 5. Retrieval foundations

**Title:** `Retrieval quality depends on the path from patent fields to family ranking`

**On-slide text:**

- **Chunking/unitization:** family document, first independent claim, fixed passages, or field views.
- **Embedding/indexing:** each dense arm applies its own frozen query/document template, pooling, normalization, and similarity rule.
- **Aggregation:** passage MaxP or multi-view reciprocal-rank fusion yields one family ranking.
- **Evaluation:** OUT Recall@100 is primary; OUT nDCG@100/nDCG@10 are secondary; latency and cost remain operational outcomes.

**Speaker note:** Chunking is not mere preprocessing. It changes what is
indexed, how much a model sees, the number of physical units, aggregation, and
the quality-latency-cost trade-off.

**Visual:** F02. **Evidence:** [P4], [R1].

### 6. A0: prevent leakage before optimizing

**Title:** `A0 makes development, selection, and confirmation distinct scientific roles`

**On-slide text:**

- Train-250 is split once with seed 42 and protected deterministic membership.
- REP-DEV (150): A1 screening and A2 representation search.
- HARNESS-DEV (100): A3 transfer, complementarity, and HarnessOpt after representation freeze.
- Selection-125 is one atomic finalist exposure; Final-872 is the sole confirmation and remains closed.

**Speaker note:** The exact allocation is an ArmIndex protocol decision, not a
claim copied from an external paper. Its purpose is to prevent an optimizer
from tuning on data that should adjudicate a later decision. Membership and
qrels remain Owner-local; only counts and roles appear here.

**Visual:** F03; optionally F10 in appendix. **Evidence:** [P5], [P6].

### 7. A0: what was delivered

**Title:** `A0 delivered reproducibility infrastructure, not a retrieval-quality claim`

**On-slide text:**

- Canonical controls, schemas, a five-arm registry, source locks, and safe evidence paths.
- Protected boundaries for membership, qrels, raw identifiers, rankings, and provider payloads.
- CPU-only adapter/contract fixtures and integrity tests before measured retrieval.
- Zero measured retrieval runs in A0.

**Speaker note:** This slide earns trust for the rest of the talk. The absence
of an A0 result is intentional: provenance and safety were built before
scientific optimization.

**Visual:** F03. **Evidence:** [P7].

### 8. A1: a controlled 5 x 5 screen

**Title:** `A1 tests five representation programs against all five retrieval arms`

**On-slide text:**

- Programs: full TAC, title + abstract, first independent claim, fixed passages, and three field views.
- Arms: BM25, BGE-M3, PatEmbed, Arctic Embed, and Qwen3 Embedding.
- Each of 25 logical cells uses the same REP-DEV role and frozen evaluator.
- The valid terminal attempt completed 25/25 cells at USD 11.161632.

**Speaker note:** A1 is a common screen, not the final model decision. It asks
whether representation choice is a meaningful optimization surface and which
arms may advance under a frozen rule.

**Visual:** F04. **Evidence:** [P4], [P8].

### 9. A1: models and embedding templates

**Title:** `Five diverse retrievers make the interaction question testable`

**On-slide text:**

- Lexical baseline, generic dense, patent-specific dense, long-context commercial dense, and instruction-aware dense retrieval.
- Model IDs, revisions, pooling, token limits, licenses, and templates are frozen before measurement.
- Only the representation program changes inside the A1 comparison.

**Speaker note:** Use Appendix A. The models are not interchangeable: their
templates, pooling, context budgets, and licenses differ. This diversity is why
the universal representation assumption should be tested rather than assumed.

**Visual:** Appendix A compact table. **Evidence:** [P9], [P10].

### 10. A1: primary pattern

**Title:** `A1 finds a large quality spread across frozen retriever arms`

**On-slide text:**

- Mean OUT Recall@100 over common programs: BM25 0.191; BGE-M3 0.270; PatEmbed 0.413; Arctic 0.341; Qwen3 0.364.
- The highest individual Recall@100 cell in each arm was P03 fixed passages.
- ARM-03, ARM-04, and ARM-05 passed the frozen promotion rule; ARM-01 and ARM-02 remain diagnostic/non-advancing in A2.
- This is descriptive REP-DEV evidence, not Selection/Final confirmation.

**Speaker note:** The key result is not only the highest bar. The cell surface
shows that representation choice changes observed performance within every
arm. A2 tests a more targeted constrained search within an arm.

**Visual:** F05, then F08 for detailed follow-up. **Evidence:** [P8].

### 11. A1: quality versus operational cost

**Title:** `Passages improve the observed A1 quality surface but create more physical work`

**On-slide text:**

- P03 fixed passages obtains the highest A1 Recall@100 cell in all five arms.
- Passage indexing creates more physical units and can increase latency, wall time, memory, and index size.
- Deployment cannot use Recall alone.
- A3 will compare quality, latency, and cost under fixed-union and harness controls.

**Speaker note:** A quality winner can be operationally unacceptable. The
protocol preserves p95 latency, throughput, cost, RAM, VRAM, and index-size
receipts for that reason.

**Visual:** F09. **Evidence:** [P8].

### 12. A2: per-arm AutoIndex flow

**Title:** `A2 searches a pre-frozen candidate universe independently for each arm`

**On-slide text:**

- 52 frozen candidates: 40 matched plus 12 conditional reserve candidates.
- ARM-01 runs on CPU; ARM-02 through ARM-05 use separate GPUs.
- Each candidate has a durable checkpoint, process identity, and heartbeat.
- Reserve work requires the matched barrier and fresh budget/TTL admission; otherwise it receives a dormant receipt.

**Speaker note:** Dormant is not zero, null, failure, or baseline equality. It
means a preregistered reserve predicate did not admit the candidate for
evaluation, preventing untracked search expansion.

**Visual:** F06. **Evidence:** [P11], [P12].

### 13. A2: current status and interpretation gate

**Title:** `A2 closes with complete aggregate evidence and bounded winners`

**On-slide text:**

- Complete accounting: 52 candidates = 44 measured + 8 dormant, with 0 failures.
- ARM-03, ARM-04, and ARM-05 are the three primary transfer inputs.
- ARM-01/02 are diagnostic three-way ties with no winner.
- ARM-03 ties A1 at presentation precision; ARM-04 improves A1; ARM-05 is retained despite no strict improvement.

**Speaker note:** These values come from the A2 closeout projection, execution
closeout receipt, safe-return receipt, and independent result-integrity audit.
The negative/tie outcomes are part of the publication contribution and must not
be omitted. No Selection or Final interpretation is implied.

**Visual:** F13 with F12 as the coverage inset. **Evidence:** A2 closeout projection and figure manifest.

### 14. A3 Extended: the next experiment

**Title:** `A3 tests transfer, complementarity, and a bounded production harness after a fresh Train-250 admission`

**On-slide text:**

- Three self-winner reuse cells plus up to six compatible off-diagonal transfers.
- Equal-depth fixed-union controls precede adaptive work; the commercial-only union is ARM-04 plus ARM-05.
- At most three complete HarnessOpt batches, each with quality, cost/latency, routing, and diversity roles.
- A fresh hash-bound Train-250 query/corpus/evaluator package and provider admission are required. A3 cap: USD 35; campaign ceiling: USD 180.

**Speaker note:** A3 does not reinterpret A2. It receives only receipt-bound
ARM-03, ARM-04, and ARM-05 inputs after safe return and audit. It remains
pending a fresh Owner-authorized hash-bound Train-250 query/corpus/evaluator
package, followed by fresh provider admission. A negative result remains
publishable boundary evidence if a winner does not transfer or the harness cost
is not justified.

**Visual:** F07. **Evidence:** [P13], [P17].

### 15. What to remember

**Title:** `The contribution is an auditable test of retriever-conditioned representation, not a one-off model win`

**On-slide text:**

1. DAPFAM makes cross-domain family retrieval a difficult and relevant setting.
2. A0 protects the scientific sequence; A1 already shows a representation-by-retriever surface.
3. A2 measures per-arm constrained search under closeout gates.
4. A3 will test transfer and an operationally defensible multi-arm frontier.

**Speaker note:** The next meaningful update is a hash-bound Train-250 input
package and fresh A3 admission, not a reuse of the idle A2 provider instance.

**Visual:** compact A0 -> A1 -> A2 -> A3 timeline. **Evidence:** [P1], [P11], [P13].

## Appendix A - Frozen Retrieval Arms and Exact Templates

These are embedding/query templates, not generative prompts. `{query}` and
`{document}` represent protected runtime text and must not be filled with a
real DAPFAM record in a repository-visible slide.

| Arm | Frozen source and role | Template / prompt | Pooling and similarity | Limit / license | Rationale |
|---|---|---|---|---|---|
| ARM-01 | `bm25s==0.3.10`; lexical CPU anchor | No embedding prompt. Unicode NFKC/casefold; `k1=1.2`, `b=0.75`. | BM25 lexical score; deterministic document-ID ties. | No dense window; MIT package. | Transparent non-neural anchor. |
| ARM-02 | `BAAI/bge-m3` | Query: `{query}`. Document: `{document}`. No instruction in core adapter. | Official dense implementation parity; bound L2 behavior. | 1,024 dim; 8,192 tokens; MIT. | Generic multilingual dense comparison. |
| ARM-03 | `datalyes/patembed-large` | Query: `encode query for different document retrieval: {query}`. Document: `encode document for different retrieval: {document}`. | Mean non-padding tokens; L2; cosine. | 1,024 dim; 512 tokens; CC-BY-NC-SA-4.0. | Patent-domain research anchor; non-commercial. |
| ARM-04 | `Snowflake/snowflake-arctic-embed-m-v2.0` | Query: `query: {query}`. Document: `{document}`; no document prefix. | CLS/first-token; L2 dot product. | 768 dim; 8,192 tokens; Apache-2.0. | Commercial-capable long-context dense arm. |
| ARM-05 | `Qwen/Qwen3-Embedding-0.6B` | Query: `Instruct: Retrieve patent families containing technical information relevant to prior-art search for the query patent family.\nQuery:{query}`. Document: `{document}`; no document instruction. | Last-token, left-padding; L2 dot product. | 1,024 dim; declared 32,768 tokens; Apache-2.0. | Modern instruction-aware commercial arm. |

**Frozen public revisions:**

- `BAAI/bge-m3@5617a9f61b028005a4858fdac845db406aefb181`
- `datalyes/patembed-large@2d5c0f92a3e5dc3d5415c08e612c57543c0e03ad`
- `Snowflake/snowflake-arctic-embed-m-v2.0@95c2741480856aa9666782eb4afe11959938017f`
- `Qwen/Qwen3-Embedding-0.6B@97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3`

Sources: [P9], [P10], [R4]-[R7]. Preserve the ARM-03 non-commercial
qualifier whenever licensing is discussed.

## Appendix B - A1 Representation Programs

| Program | Exact logical representation | Family aggregation | Reason for the contrast |
|---|---|---|---|
| `P00-TAC-DOC` | Ordered `TITLE`, `ABSTRACT`, `CLAIMS` for all family publications. | Single unit. | Full-information document baseline. |
| `P01-TA-DOC` | Ordered title and abstract only. | Single unit. | Tests whether long claims add signal or noise/cost. |
| `P02-CLAIM1` | First structured independent claim in family/publication order; no raw-regex fallback. | Available unit with MaxP. | Tests a concise technical/legal statement. |
| `P03-PASSAGE` | TAC stream into 384-token logical passages, 64-token overlap; final partial retained. | Family MaxP. | Tests local evidence while respecting the 512-token PatEmbed envelope. |
| `P04-SECTION-MULTIVIEW` | Separate title, abstract, claims views. | Per-view depth 100; RRF `k=60`; lexical family-token ties. | Tests field-specific matching rather than one concatenated document. |

All programs apply Unicode NFKC/canonical whitespace, preserve ordered family
membership, forbid silent truncation, and retain explicit field labels. They
are deterministic representation programs, not LLM-generated prose. Source:
[P4].

## Appendix C - A1 Detailed REP-DEV Cell Results

Valid terminal attempt: `a12-v16-20260811-r15`; 25/25 logical cells; 150
REP-DEV queries per cell; no Selection/Final access; charged cost USD
11.161632. Values are aggregate-safe. `p95` is search latency in milliseconds
and `wall` is total cell wall time in seconds.

| Arm | Program | OUT Recall@100 | OUT nDCG@100 | OUT nDCG@10 | p95 | wall |
|---|---|---:|---:|---:|---:|---:|
| BM25 | P00 TAC | 0.1980 | 0.1813 | 0.1728 | 190.5 | 111.7 |
| BM25 | P01 TA | 0.1247 | 0.1109 | 0.0999 | 190.5 | 54.4 |
| BM25 | P02 Claim1 | 0.1870 | 0.1703 | 0.1599 | 203.6 | 82.6 |
| BM25 | P03 Passages | 0.2347 | 0.2108 | 0.1950 | 771.1 | 269.4 |
| BM25 | P04 Views | 0.2117 | 0.1903 | 0.1725 | 851.9 | 244.4 |
| BGE-M3 | P00 TAC | 0.2733 | 0.2363 | 0.2004 | 156.0 | 2,629.8 |
| BGE-M3 | P01 TA | 0.2590 | 0.2255 | 0.1966 | 158.5 | 1,712.9 |
| BGE-M3 | P02 Claim1 | 0.2510 | 0.2158 | 0.1882 | 181.2 | 2,560.5 |
| BGE-M3 | P03 Passages | 0.2887 | 0.2510 | 0.2216 | 295.1 | 7,187.7 |
| BGE-M3 | P04 Views | 0.2777 | 0.2284 | 0.1856 | 385.1 | 5,756.4 |
| PatEmbed | P00 TAC | 0.4147 | 0.3549 | 0.3031 | 149.5 | 5,723.2 |
| PatEmbed | P01 TA | 0.4010 | 0.3373 | 0.2827 | 153.8 | 1,709.3 |
| PatEmbed | P02 Claim1 | 0.4163 | 0.3542 | 0.3049 | 150.2 | 5,201.4 |
| PatEmbed | P03 Passages | 0.4230 | 0.3593 | 0.3015 | 241.7 | 8,485.1 |
| PatEmbed | P04 Views | 0.4120 | 0.3333 | 0.2570 | 365.0 | 8,325.7 |
| Arctic | P00 TAC | 0.3443 | 0.2849 | 0.2340 | 140.9 | 2,159.0 |
| Arctic | P01 TA | 0.3237 | 0.2728 | 0.2294 | 143.0 | 1,180.1 |
| Arctic | P02 Claim1 | 0.3303 | 0.2820 | 0.2393 | 144.3 | 2,209.8 |
| Arctic | P03 Passages | 0.3527 | 0.3031 | 0.2588 | 270.2 | 5,727.0 |
| Arctic | P04 Views | 0.3523 | 0.2800 | 0.2162 | 372.8 | 4,602.6 |
| Qwen3 | P00 TAC | 0.3663 | 0.3131 | 0.2643 | 149.7 | 5,084.9 |
| Qwen3 | P01 TA | 0.3497 | 0.3033 | 0.2622 | 156.1 | 3,844.0 |
| Qwen3 | P02 Claim1 | 0.3577 | 0.3079 | 0.2591 | 159.4 | 5,083.7 |
| Qwen3 | P03 Passages | 0.3800 | 0.3224 | 0.2730 | 270.7 | 14,715.6 |
| Qwen3 | P04 Views | 0.3650 | 0.2931 | 0.2250 | 349.6 | 11,581.4 |

Use F08 rather than this table in the main deck. Machine-readable source:
[A1 cell EDA CSV](../../../outputs/tables/armindex/a12-v16-20260811-r15.cell-eda.v16.csv).

## Appendix D - Official Codex A2 Candidate-Generation Prompts

**Model binding:** `gpt-5.6-sol`, high reasoning effort, before A2
measurement. The model receives only a frozen aggregate-safe operation payload
and returns schema-constrained JSON. It never receives qrels, query IDs,
memberships, rankings, per-query outcomes, protected text, credentials,
provider payloads, or measured results. Proposal/review is not A2 measurement.

### D.1 Proposer Prompt (exact template)

```text
You are the Official Codex representation proposer for a pre-measurement,
five-arm patent-retrieval study. Return only JSON matching the supplied output
schema.

Use only the frozen aggregate-safe payload below. Propose exactly the four
requested candidate slots. Preserve every candidate ID and role exactly. Make
each hypothesis falsifiable, retriever-conditioned, compatible with the listed
source fields, and distinct from the other candidates in the batch. Do not use
or request qrels, query IDs, membership, rankings, per-query outcomes, protected
text, credentials, provider payloads, or measured results. Do not claim that an
unmeasured candidate improves retrieval. Do not expose hidden reasoning.

For program fields, use only the allowed source fields and ensure field_order
contains exactly the same fields once. Keep logical passage sizes conservative
for the declared arm limit. ARM-01 and ARM-02 candidates are diagnostic only
when the payload says advancement_eligible=false.

Every hypothesis must identify one deterministic representation intervention,
the frozen within-arm comparator, the expected direction that can later be
falsified, and a concrete failure condition without claiming improvement.
Avoid learned, adaptive, data-dependent, ranking-dependent, or unspecified
processing. Keep each candidate attributable to its declared axis and explain
it in language suitable for a journal ablation. For conditional reserve slots,
state that the candidate remains dormant unless the frozen activation predicate
is satisfied. Apply every reviewer_required_changes item to its named candidate
while keeping the other slots independently valid. On revision rounds,
accepted_candidate_ids are immutable: copy those candidates from
previous_candidates byte-for-byte, including their hypothesis, program,
expected_effect, and failure_risk. Revise only candidate IDs that are not in
accepted_candidate_ids. Return all four slots in the canonical order.

Operation payload:

{{OPERATION_PAYLOAD_JSON}}
```

### D.2 Independent Reviewer Prompt (exact template)

```text
You are the independent Official Codex reviewer for a frozen pre-measurement
representation-candidate batch. Return only JSON matching the supplied output
schema.

Review only the frozen aggregate-safe context and candidate payload below. You
have no proposer transcript and no measured outcomes. Preserve every candidate
ID. Check falsifiability, role fit, duplication, protected-boundary safety, arm
compatibility, deterministic interpretability, and publication interpretability.
Accept only candidates that satisfy every check. Required changes must be
specific and must not alter the frozen evaluator, metrics, A1 promotion, model
weights, protected split, or diagnostic non-advancement. Do not expose hidden
reasoning.

previously_accepted_candidate_ids were accepted in an earlier independent
review and are required to be byte-identical in this round. Recheck them, but
do not request stylistic changes or reinterpret their scientific semantics.
Reject a previously accepted candidate only for a concrete newly observed
safety, determinism, duplication, or contract defect.

Operation payload:

{{OPERATION_PAYLOAD_JSON}}
```

**Why this matters:** these templates make candidate generation auditable and
falsifiable while preventing the language model from accessing the held-out
evaluation signal or freely changing the retrieval runtime. Sources: [P14]-[P16].

## Appendix E - A2 Closeout Update Template

Slide 13 is now receipt-bound to the valid A2 closeout/evaluation/audit receipt
set. Future revisions must not be filled from remote `result.json` files,
liveness logs, or memory.

```text
A2 closeout authority: <PASS receipt ID and SHA-256>
Coverage: <exact measured and dormant accounting under 52 / 40 / 12 contract>
Per-arm winner receipts: <three primary winner IDs and SHA-256 values>
Diagnostic records: <two ARM-01/02 no-winner tie IDs and SHA-256 values>
Primary metric: <validated aggregate OUT Recall@100 values>
Secondary metrics: <validated aggregate nDCG values>
Operational outcomes: <latency, throughput, cost, index size, RAM, VRAM>
Reserve decision: <admitted/dormant receipt-bound accounting>
Result-integrity audit: <PASS audit ID and SHA-256>
Safe return and provider teardown: <PASS receipt IDs>
Claim boundary: REP-DEV only; no Selection/Final/legal claim.
```

The post-closeout visual source must be the receipt-bound A2 publication figure
manifest in `outputs/figures/armindex/a2-goal004/`, not a manually drawn chart.

## Sources

### Project controls and evidence

- **[P1]** [ArmIndex Research Plan V02](../../research/ARMINDEX_RESEARCH_PLAN_V02.md): narrative, frozen stages, representation grammar, and research questions.
- **[P2]** [Current campaign plan](../../../PLAN.md): campaign state and phase routing.
- **[P3]** [DAPFAM source contract](../../../control/assets/dapfam-p1-source.v1.json): revision, counts, fields, domain labels, and split totals.
- **[P4]** [Deterministic common-program compiler](../../../src/myis_research/armindex/scientific_common_programs_v11.py): exact P00-P04 semantics.
- **[P5]** `control/armindex/a1.2/rep-harness-split-decision.v1.json`: canonical protected split decision; present counts/hashes only.
- **[P6]** [A1 publication-impact preregistration](../../research/A1_2_PUBLICATION_IMPACT_PREREGISTRATION_V13.md): development/selection/final claim boundaries.
- **[P7]** [A0-A2 advisor progress report](../../progress_report/ARMINDEX_A0_A1_A2_ADVISOR_PROGRESS_2026-08-16.md): A0 closeout and A1 synthesis.
- **[P8]** [A1 cell EDA CSV](../../../outputs/tables/armindex/a12-v16-20260811-r15.cell-eda.v16.csv) and linked A1 figures: valid terminal REP-DEV aggregate evidence.
- **[P9]** [A1 model source locks](../../research/A1_2_MODEL_SOURCE_LOCKS.md): model identity, revision, license, pooling, and deployment conditions.
- **[P10]** [Frozen dense adapter contract](../../../src/myis_research/armindex/a1_2_contract.py): exact ARM-02 to ARM-05 templates.
- **[P11]** [A2 Goal 004](../../goal/A2_PER_ARM_AUTOINDEX_goal_004.md): candidate universe, reserve policy, safe return, and closeout conditions.
- **[P12]** `control/runbooks/A2_PER_ARM_AUTOINDEX_EXECUTION_V2.md`: A2 lifecycle, recovery, and execution controls.
- **[P13]** [A3 Extended Goal 003](../../goal/A3_TRANSFER_COMPLEMENTARITY_AND_HARNESSOPT_goal_003.md): three-primary A3 gates, transfer, fixed unions, HarnessOpt, and budget.
- **[P14]** [A2 Official Codex bridge](../../../control/armindex/a2/official-codex-bridge.v1.json): prompt/model/schema binding.
- **[P15]** [A2 representation proposer prompt](../../../prompts/armindex/official-codex/representation-propose.v1.md).
- **[P16]** [A2 representation reviewer prompt](../../../prompts/armindex/official-codex/representation-review.v1.md).
- **[P17]** [A2 Goal 004 closeout projection](../../../control/armindex/a2/a2-goal004-closeout-projection.v1.json): canonical aggregate closeout projection and A3 routing.
- **[P18]** Owner-local A2 execution closeout and independent integrity audit: receipt-bound measured evidence; disclose only aggregate-safe values and hashes.

### External literature and official model documentation

- **[R1]** Ayaou, I., Cavallucci, D., and Chibane, H. *DAPFAM: A Domain-Aware Family-level Dataset to Benchmark Cross-Domain Patent Retrieval* (2025), [arXiv:2506.22141](https://arxiv.org/abs/2506.22141). Use for benchmark design and citation-label limitation, not legal conclusions.
- **[R2]** *GEPA: Reflective Prompt Evolution Can Outperform Reinforcement Learning*, [arXiv:2507.19457](https://arxiv.org/abs/2507.19457). Used only as methodological lineage here; verify its PDF before quoting numerical comparisons.
- **[R3]** O'Nuallain et al. *AutoIndex: Learning Representation Programs for Retrieval*, [arXiv:2607.18603](https://arxiv.org/abs/2607.18603). Motivation for constrained representation optimization.
- **[R4]** [BAAI/bge-m3 model card](https://huggingface.co/BAAI/bge-m3).
- **[R5]** [datalyes/patembed-large model card](https://huggingface.co/datalyes/patembed-large).
- **[R6]** [Snowflake Arctic Embed M v2.0 model card](https://huggingface.co/Snowflake/snowflake-arctic-embed-m-v2.0).
- **[R7]** [Qwen3-Embedding-0.6B model card](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B).

## Final Pre-Presentation Check

- Keep the main deck to Slides 1-15; move exact templates, 25-cell table, and full A2 prompts to backup.
- Use F08/F09 only with a visible `REP-DEV development evidence` label.
- Keep Slide 13 aligned to the receipt-bound A2 closeout projection. Preserve ARM-03 numerical tie, ARM-04 strict improvement, ARM-05 no-strict-improvement, and ARM-01/02 diagnostic-tie qualifiers.
- Do not display raw DAPFAM text, IDs, qrels, per-query outcomes, provider output, or generated A2 candidate results.
- Preserve the `ARM-03 research/non-commercial` qualifier whenever licensing is mentioned.
- State that A3 is pending a hash-bound Train-250 package and fresh provider admission; do not imply that the idle A2 instance is reusable.
