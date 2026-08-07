# A1.2 Scientific Execution and Adoption Request v11

## Authority and status

- Phase: `A1_BASELINES_AND_MULTI_ARM_SCREENING`
- Task: `A1.2`
- Campaign: `armindex-multiretriever-v2`
- Standing authorization: `D1_START_CAMPAIGN`
- Revision: `a1.2-scientific-execution-adoption-request-v11`
- Preparation mode: local CPU only
- Status: request preparation only, not adopted
- Scientific authority: `false`
- `launch_allowed=false`
- `adopted_for_execution=false`

This additive revision prepares the exact request that a later goal may review
and adopt. It does not contact a provider, open protected evaluator payloads,
start retrieval, optimize a representation or harness, access Selection or
Final, use a paid API, or change model weights.

## Required additive artifacts

The deterministic v11 materializer creates and validates:

1. the unchanged v1-v10 lineage index;
2. a measured common-screen budget request;
3. an Owner-local protected evaluator handoff contract;
4. five immutable workload manifests and their set manifest;
5. fail-closed stop conditions;
6. a fresh-provider admission plan;
7. the scientific execution and adoption request;
8. a preparation receipt that keeps execution locked.

The independent pre-adoption review rejected the first draft because it named
programs without executable hashes, assigned all 250 training queries to
REP-DEV, and lacked an authorized scientific transfer/result path. The repaired
v11 package additionally binds an additive scientific-transfer contract, the
five executable common-program specifications and compiler source manifest,
and an aggregate-safe result receipt schema. The failed draft and recovery stay
visible in the append-only preparation ledger.

Historical v1-v10 contracts, receipts, failures, and run artifacts remain
immutable. The v9 synthetic result is adapter and lifecycle evidence only. It
is not retrieval-quality evidence or proof that the full measured workload fits.

## Protected evaluator handoff

The Owner-local protected store retains qrels, split membership, query IDs,
evaluator payloads, per-query outcomes, credentials, provider access material,
and the local mapping between ephemeral work IDs and protected identities.
The repository binds only safe schemas, hashes, counts, and pointers. A future
execution may send only frozen corpus/query text with run-scoped opaque work
tokens and must return candidate family identifiers keyed by those tokens to
the protected Owner-local return root. Evaluation and aggregate publication
metrics are produced locally after safe return validation.

The v11 request binds the handoff protocol, not the still-unopened protected
payload. Adoption requires a separate Owner-local handoff receipt whose safe
hash commitments match the unchanged v11 protocol. Missing or mismatched
handoff evidence blocks before provider contact.

REP-DEV is fixed at 150 queries. The remaining 100 Train-250 queries remain
reserved for HARNESS-DEV and cannot enter A1.2 representation screening. Exact
membership remains Owner-local; Git receives only counts and commitments.

## Scientific transfer and safe return

The v5 topology and v6 synthetic safe-export allowlist remain unchanged. The
additive v11 transfer contract creates the future scientific path for frozen
corpus and REP-DEV query text keyed only by run-scoped opaque tokens. It also
requires structured independent-claim markers without original identifiers.
Qrels, membership, original IDs, the token map, evaluator, credentials, and
canonical writers remain local.

Every uploaded byte must appear in a hash/size/path-bound remote-stage manifest.
Symlinks, traversal, special files, undeclared artifacts, and all network
fallback fail closed. Safe return permits only Top-100 opaque results and
bounded lifecycle/resource/failure receipts. It forbids logs, model bytes,
embeddings, caches, tensor checkpoints, raw inputs, environment dumps, and raw
provider payloads. Remote cleanup is recorded only after local return
validation and is never represented as secure deletion or provider destruction.

## Frozen common programs

The compiler in
`src/myis_research/armindex/scientific_common_programs_v11.py` is isolated from
the historical fixture compiler. It freezes exact byte semantics:

- `P00-TAC-DOC`: one ordered family TAC document;
- `P01-TA-DOC`: one ordered family title/abstract document;
- `P02-CLAIM1`: the first structured independent claim, with no regex fallback;
- `P03-PASSAGE`: complete 384-token logical passages with 64-token overlap and
  no omitted final passage;
- `P04-SECTION-MULTIVIEW`: title/abstract/claims views fused with RRF `k=60`,
  depth 100 per view, and lexical opaque-family-token ties.

The logical workload remains 25 program-arm results. P04 has three physical
view paths, so the frozen physical accounting is 35 program-view paths. A
future adoption receipt must bind all 25 per-arm compiled manifests, tokenizer
and adapter hashes, effective input limits, coverage, storage, and zero silent
truncation or over-length inputs.

## Workload topology

- `ARM-01`: local CPU, frozen `bm25s` adapter, no GPU budget.
- `ARM-02`: remote GPU 0.
- `ARM-03`: remote GPU 1, research/non-commercial result boundary retained.
- `ARM-04`: remote GPU 2 with frozen Snowflake custom-code hashes.
- `ARM-05`: remote GPU 3 with the v9 32,768-token cap limited to the exact
  frozen single-GPU FP16 batch-one scope.

The ARM-05 job now enforces those scope fields in machine-readable form:
FP16, batch size one, maximum 32,768 input tokens, and the exact v9 result
receipt hash. It permits no OOM mutation because batch size is already one.

The dense manifests run concurrently, one arm per RTX 3090. They freeze the
model lock, adapter behavior, common program set, top-k, output contract,
heartbeat, checkpoint, resume, and safe return requirements. Actual protected
input bundle hashes and the clean pushed execution commit/tree are bound only
in a later adoption receipt; placeholders cannot authorize launch.

## Budget request

The common-screen hard stop remains USD 18, the A1 hard stop USD 23, and the
campaign hard stop USD 100. Planning assumes one four-RTX3090 instance for
2-4 hours, with a six-hour Owner-local TTL ceiling. A fresh live quote and the
remaining authoritative budget must admit the entire TTL-bounded workload.
No default price, stale v9 quote, partial-arm admission, or inferred remaining
balance is allowed.

The fresh quote receipt must also state billing granularity, minimum billable
time, storage, network, platform/other fees, tax or surcharge, and the computed
worst-case six-hour total. Any unknown billable component or a total that does
not fit every remaining hard stop produces `BLOCKED_BUDGET`.

## Required result evidence

All 25 program-arm outputs must validate; 24/25 is a failed incomplete screen
and cannot promote an arm. Owner-local evaluation emits one aggregate-safe
receipt per program-arm with Recall@100/OUT, nDCG@100/OUT, nDCG@10/OUT, unique
relevant contribution, latency/throughput, RAM/VRAM, index and return size,
determinism replay, retries/OOM recovery, and failure categories. Per-query
rankings/outcomes and any identifier remain protected. Canonical receipt write
precedes MLflow, Brain, Obsidian, Dashboard, and Paper projection.

## Fresh provider admission

The destroyed v9 instance cannot be reused. A later adoption goal must verify
a fresh provider identity and quote, direct official PyTorch image manifest,
linux/amd64, Python 3.11, PyTorch 2.6.0+cu118, CUDA 11.8, four distinct RTX
3090 UUIDs, CPU/RAM/disk minimums, frozen code/model/wheelhouse hashes,
Owner-local TTL watchdog, provider destroy path, protected-boundary scan, and
return capacity. Provider credentials remain Owner-local and never enter Git.

## Stop conditions

Stop before launch on missing adoption, dirty or unpushed source identity,
lineage/hash mismatch, protected handoff mismatch, missing artifacts, stale or
over-budget quote, provider/runtime/GPU mismatch, unsafe remote paths, or an
unavailable watchdog/destroy path.

Stop all workers and preserve safe receipts on heartbeat expiry, worker exit,
OOM outside the permitted batch-size-only recovery, non-finite embeddings,
dimension/count/identity mismatch, checkpoint failure, disk pressure, budget
or TTL exhaustion, protected/credential detection, or safe-export failure.
No partial result can be promoted as a completed common screen.

## Owner review boundary

This preparation closes only when all v11 files validate, an independent rigor
review finds no blocking issue, generated projections agree, and all counters
remain zero. The exact next action is a separate Owner-authorized adoption goal
that binds the unchanged v11 hashes, a clean pushed execution commit/tree, the
Owner-local protected handoff and transfer receipts, 25 compiled program-arm
bindings, fresh provider quote/identity with all billable components, and the
remaining budget. Until then, no provider may be opened.
