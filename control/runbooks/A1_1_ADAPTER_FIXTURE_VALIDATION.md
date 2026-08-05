# A1.1 Adapter Fixture Validation

## Authority

- Phase: `A1_BASELINES_AND_MULTI_ARM_SCREENING`
- Task: `A1.1`
- Campaign: `control/campaigns/armindex-multiretriever-v2.yaml`
- Budget: `control/budgets/armindex-migration-v2.yaml`
- Standing authorization: `D1_START_CAMPAIGN`
- Evidence class: `engineering_fixture`
- Scientific authority: `false`

## Objective

Close A1.1 with a deterministic, offline adapter scaffold for all five declared
arms and a complete ARM-01 BM25 compile-index-search-evaluate path on CPU. The
run uses synthetic patent-family fixtures only. It establishes interface,
lineage, safety, and resource-planning readiness; it does not establish
scientific baseline parity or measured retrieval quality.

## Frozen Boundary

- CPU only, zero charged cost, and no network model download.
- No protected REP-DEV corpus or evaluator payload, qrels, membership, query
  IDs, rankings, per-query outcomes, credentials, or raw provider payloads.
- No App sparse-index payload access. Registry metadata and safe pointers only.
- ARM-01 uses the repository-local deterministic Okapi BM25 fixture backend.
  It remains distinct from the future version-locked `bm25s` measured adapter.
- ARM-02 through ARM-05 remain metadata-only and fail closed before model or
  network access.
- No measured retrieval, GPU, paid API, provider switch, A1.2 execution,
  Selection, or Final.
- The A1.2 GPU specification, elapsed-time estimate, and budget are a proposal,
  not an adopted execution contract or launch authorization.

## Falsifiable Engineering Hypothesis

The existing representation compiler and family-preserving ARM-01 interface
can execute a complete synthetic BM25 path deterministically on CPU while all
dense adapters fail closed and every protected/measured counter remains zero.

## Execution Steps

1. Validate the reusable-asset registry and query only assets allowed for A1.1.
2. Freeze five-arm fixture capability declarations and resource assumptions.
3. Compile a synthetic patent-family representation in forward and reversed
   source order and require byte-identical commitments.
4. Build the ARM-01 CPU index, execute the synthetic query workload, aggregate
   at family level, and validate aggregate fixture metrics.
5. Record compile, index-build, and search-workload latency, throughput, Python
   allocation, and deterministic storage commitments as host observations.
6. Prove ARM-02 through ARM-05 cannot execute without resolved offline model
   locks and pre-staged artifacts.
7. Persist write-once manifest and receipt artifacts under
   `outputs/fixtures/armindex/a1.1/adapter-cpu-v1/`.
8. Emit a task receipt and a non-authorizing A1.2 GPU/time/budget proposal.
9. Update canonical controls, PLAN, HANDOFF, reports, projections, Brain, and
   the research-session capsule from validated aggregate-safe evidence.
10. Generate detailed English reports for every registered Phase and Task from
    one validated read-model object using the canonical fifteen-section
    contract. Keep reports at active paths unless they are verified
    `superseded`, unreferenced, and safe to move to the generated archive.

## Acceptance

- ARM-01 completes compile, index, search, family aggregation, and synthetic
  aggregate evaluation on CPU.
- The five-arm registry is complete; four dense arms fail closed before model
  or network access.
- Forward/reversed input and repeated/hash-seed runs produce stable manifest
  commitments, excluding explicitly host-observed runtime fields.
- Manifest and receipt are canonical JSON, self-hashed, mutually bound,
  write-once, and aggregate-safe.
- CPU observations are labeled engineering fixture evidence and cannot support
  production-capacity or retrieval-quality claims.
- The A1.2 proposal identifies assumptions, a single-GPU planning class,
  estimated elapsed-time range, and charged-USD ceilings from the approved
  scientific plan without launching or reserving compute.
- Measured, candidate, Selection, and Final counters remain zero.
- A1.2 remains closed until a separate versioned execution contract and budget
  profile bind exact model artifacts, protected roots, provider availability,
  pre-run estimates, and automatic shutdown.
- Focused tests and every mandatory repository check pass before commit/push.
- Every Phase and Task has one detailed English generated Obsidian report with
  the fifteen required sections, matching machine record, current lifecycle,
  evidence boundary, and next authorized action.
- Any archive move is exact, hash-audited, dependency-safe, and preserves the
  managed note and supersession pointer. Historical evidence that remains in
  the artifact graph is retained at its expected path.

## A1.2 Resource Proposal

- Planning class: one 24 GiB GPU; preferred RTX 4090, RTX 3090, L4, or A10.
  A100 or H100 capacity is not required for the proposed sequential screen.
- Host: at least 8 vCPU, 32 GiB RAM, and 200 GiB local SSD; 64 GiB RAM is
  recommended. BF16 is preferred with FP16 fallback.
- Estimate: 8-16 GPU reservation hours plus 2-4 local collection/validation
  hours, for 10-20 hours end to end. Confidence remains low until the protected
  unit count and an Owner-local throughput pilot are available.
- Cost assumption: USD 0.30-0.80 per GPU-hour, USD 2.40-12.80 raw compute,
  USD 5 model-parity/pilot hard stop, USD 18 common-screen hard stop, USD 23 A1
  hard stop, and USD 100 campaign hard stop.
- The proposal is non-authorizing. A1.2 requires a separate versioned execution
  contract, hash-bound budget profile, frozen pre-staged model/tokenizer and
  remote-code hashes, live quote, protected-root availability, pre-run estimate,
  and automatic shutdown/artifact-return plan before any GPU reservation.

## Ledger

Append material starts, runs, failures, recoveries, and closeout events to
`control/armindex/a1.1-adapter-fixture-validation-ledger.v1.jsonl`. Every entry
binds the previous entry hash; existing lines are immutable.
