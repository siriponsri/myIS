# A1.2 Common Multi-Arm Screening Contract Scaffold

## Identity

- Campaign: `armindex-multiretriever-v2`
- Phase: `A1_BASELINES_AND_MULTI_ARM_SCREENING`
- Task: `A1.2`
- Scaffold revision: `a1.2-common-multi-arm-screen-v1`
- Evidence class: `engineering_contract_scaffold`
- Scientific authority: `false`

## Objective

Prepare and validate the complete offline execution-contract scaffold required
before any A1.2 GPU reservation or measured retrieval. Freeze the ARM-01 CPU
adapter, the public source revisions for ARM-02 through ARM-05, a hash-bound
budget profile, execution envelope, launch checklist, and two-layer shutdown
plan. This runbook closes the scaffold goal only; it does not close the
scientific common-screen task.

## Starting State

- A1.1 synthetic adapter validation is complete and receipt-bound.
- ARM-01 completed a synthetic repository-local Okapi fixture path on CPU.
- ARM-02 through ARM-05 remain declared and fail closed.
- ArmIndex measured, candidate, Selection, Final, GPU, paid-API, model-download,
  and provider-switch counters are zero.
- The A1.2 GPU/time/budget proposal is planning evidence and does not authorize
  execution.

## Authorized Work

1. Add and lock `bm25s==0.3.10` for the future ARM-01 measured adapter.
2. Validate ARM-01 rank parity against the existing Okapi reference using only
   synthetic local inputs and CPU.
3. Freeze public repository revisions and public critical-artifact commitments
   for the four dense models without downloading model payloads.
4. Materialize and validate the versioned A1.2 envelope, budget, model locks,
   lockset, launch checklist, shutdown plan, execution contract, receipt, and
   append-only hash-chained ledger.
5. Update canonical plans, source-of-truth records, code, tests, Brain pointers,
   and projections.
6. Generate detailed English reports for every registered Phase and Task using
   the canonical fifteen-section report contract.
7. Audit generated reports for archival. Archive only a report that is
   explicitly superseded, unreferenced by the generated manifest and artifact
   graph, checksum-validated, and retained with a supersession pointer. Preserve
   current historical SCOPE/P1/P2 evidence-lineage reports.

## Prohibited Work

- Do not access Owner-local DAPFAM payloads, qrels, membership, query IDs,
  rankings, or per-query outcomes from the agent workspace.
- Do not reserve or use a GPU.
- Do not run measured retrieval or dense embedding inference.
- Do not download model, tokenizer, configuration, or remote-code payloads.
- Do not use paid APIs, switch providers, or touch credentials.
- Do not open Selection or Final.
- Do not claim scientific A1.2 completion from scaffold or synthetic evidence.

## ARM-01 CPU Contract

- package: `bm25s==0.3.10`
- wheel SHA-256:
  `d271d4e1ad7ffdacb224f41bc54aba55159438ecf06439ffe929f088efa96858`
- scorer: Lucene BM25, `k1=1.2`, `b=0.75`
- backend / CSC backend: NumPy / NumPy
- tokenizer: Unicode NFKC, casefold, `(?u)\b\w+\b`, no stopwords, no
  stemming, unique query terms
- output: zero-score rows removed; stable document-ID lexical tie-break
- resource boundary: local CPU only and exactly USD `0` GPU budget

The `bm25s` Lucene score differs from the repository Okapi reference by the
constant factor `k1 + 1`; acceptance therefore requires exact rank parity, not
score equality.

## Dense Source Locks

The scaffold freezes public source revisions and critical LFS commitments for:

- `BAAI/bge-m3` at `5617a9f61b028005a4858fdac845db406aefb181`;
- `datalyes/patembed-large` at
  `2d5c0f92a3e5dc3d5415c08e612c57543c0e03ad`;
- `Snowflake/snowflake-arctic-embed-m-v2.0` at
  `95c2741480856aa9666782eb4afe11959938017f`;
- `Qwen/Qwen3-Embedding-0.6B` at
  `97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3`.

Every dense lock remains
`metadata_frozen_owner_artifacts_pending`. The Owner-local runner must provide a
complete `SHA256SUMS` manifest for all runtime files and byte-level SHA-256
commitments for Snowflake remote code. Git object IDs do not replace local
runtime-file hashes.

## Resource Proposal

- ARM-01: local CPU, no Vast instance, USD `0` GPU budget.
- Dense arms: one Owner-managed 24 GiB GPU used sequentially.
- Suitable classes: RTX 4090 24 GB, RTX 3090 24 GB, L4 24 GB, or A10 24 GB.
- A100 or H100: not required.
- Host minimum: 8 vCPU, 32 GiB RAM; 64 GiB RAM recommended.
- Local SSD minimum: 200 GiB.
- GPU reservation estimate: 8-16 hours.
- End-to-end estimate including local validation: 10-20 hours.
- Raw GPU estimate: USD 2.40-12.80, subject to a live quote.
- Hard stops: USD 5 pilot, USD 18 common screen, USD 23 A1, USD 100 campaign.

## Shutdown Contract

The in-instance guard stops work, flushes aggregate-safe artifacts, writes a
terminal receipt, emits a shutdown request, and powers off. A separate
Owner-local watcher holding provider credentials must invoke provider instance
termination, verify destruction, and write a sanitized receipt. Guest poweroff
alone is not proof that Vast or another provider stopped billing. Launch remains
locked until the termination/TTL integration passes a dry run.

## Required Owner Inputs Before Launch

- A read-only protected root exposed only to the Owner-local runner.
- Pre-staged dense artifacts and complete `SHA256SUMS` manifests.
- Frozen Snowflake remote-code byte hashes and passing adapter parity tests.
- A frozen Qwen measured maximum input length.
- Provider account credit and credentials kept outside the agent workspace.
- A live quote, capacity, and provider instance identifier bound into preflight.
- A validated external termination watcher, TTL, artifact return target, and
  storage-capacity check.
- Explicit adoption of the unchanged execution contract and budget profile.

## Acceptance Checks

- Focused ARM-01 parity, contract, CLI, tamper, and budget tests pass.
- All five lock files and the lockset validate deterministically.
- Launch remains false and all real/resource counters remain zero.
- The report schema/content validator and two sync/check cycles pass.
- Every registered Phase and Task has one detailed English generated report.
- The archive audit emits an explicit disposition; no referenced report moves.
- Protected-path, unsafe-path, artifact-graph, checksum, session, Dashboard/API,
  MLflow doctor, assets, layout, Brain literature, tests, Ruff, and whitespace
  checks pass before commit and push.

## Closeout State

The scaffold may close as
`a1_2_contract_scaffold_complete_launch_locked`. The next automatic action is
an Owner-local artifact-manifest and external-termination dry-run preflight on
CPU. GPU reservation remains prohibited until every checklist item passes and
the unchanged contract is explicitly adopted.
