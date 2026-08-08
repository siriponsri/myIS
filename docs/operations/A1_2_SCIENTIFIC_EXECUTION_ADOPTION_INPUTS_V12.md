# A1.2 Scientific Execution Adoption Inputs v12

## Purpose

This runbook governs additive, Owner-local preparation of the inputs required
to review the unchanged A1.2 scientific execution request v11 for a later
adoption decision. V11 and every v1-v10 predecessor remain immutable.

This work is local CPU preparation only. It does not authorize provider
contact, GPU reservation, measured retrieval, optimization, Selection, Final,
paid APIs, model download, or any model, precision, adapter, program,
evaluator, or protected-split change.

## Required outputs

The v12 package must bind:

1. the exact unchanged v11 request and receipt;
2. a clean pushed execution commit, tree, and frozen bundle hash;
3. aggregate-safe hashes and counts from Owner-local protected handoff and
   transfer receipts;
4. exactly 25 arm-by-program compilation bindings with zero coverage gaps,
   omissions, truncations, and unresolved over-length inputs;
5. a whole-workload budget-admission model;
6. a non-operative Owner-local watchdog/provider-destroy dry-run;
7. a publication-impact preregistration that keeps OUT Recall@100 primary;
8. a deterministic post-return instance disposition policy; and
9. an exact live-provider binding template whose values remain
   `PENDING_LIVE_PROVIDER` until a later authorized provider goal.

## Owner-local protected compilation boundary

The repository may contain only schemas, hashes, counts, status values, and
safe pointers. Corpus/query text, qrels, membership, query identifiers,
per-query outcomes, the opaque-token identity map, evaluator payloads,
credentials, model bytes, and personal paths remain outside Git.

The protected compiler must run locally from an Owner-supplied protected root.
It emits only an aggregate-safe receipt. Missing protected inputs are reported
as pending; they must never be replaced with fixture or invented values.

## Provider boundary

No provider may be contacted during v12 preparation. The destroyed v10
instance is not reusable. Fresh provider identity, all-fee quote, four GPU
UUIDs, and live runtime observations remain `PENDING_LIVE_PROVIDER`.

The provider should be opened only after every local and protected binding has
validated. This prevents paid idle time while contracts or compilation inputs
are incomplete.

### Exact Owner request point and instance plan

Do **not** open an instance while the v12 compiled-binding receipt reports
fewer than 25 validated bindings or any Owner-local handoff/transfer receipt is
missing. The agent requests a live instance only after the canonical v12 local
receipt reports `ready_for_live_adoption_goal=true`.

The later request is for one SSH-only Vast instance with exactly four NVIDIA
GeForce RTX 3090 GPUs (approximately 24 GiB VRAM each), at least 16 vCPUs,
64 GiB RAM, and 250 GiB free disk. It launches
`pytorch/pytorch:2.6.0-cuda11.8-cudnn9-runtime` directly on `linux/amd64`, with
no Jupyter, Docker-in-Docker, runtime model download, or network fallback.

Plan for 2-4 instance hours and enforce a six-hour Owner-local TTL. At the
planning rate of USD 0.60 per four-GPU instance-hour, raw compute is USD
1.20-2.40 and the six-hour raw-compute ceiling is USD 3.60. These figures are
planning values only. A fresh quote no older than 900 seconds must include
storage, network, platform, tax, surcharge, billing granularity, and minimum
billing. The projected whole workload must remain within USD 18 for the common
screen, USD 23 for A1, and USD 100 for the campaign, or admission stops as
`BLOCKED_BUDGET`.

## Instance disposition after a future measured run

After local safe-return validation, the local evaluator must classify the live
instance before the Owner acts:

- `REUSE_ELIGIBLE`: every frozen revision/runtime/model/program hash is
  unchanged, workers are clean, protected scans pass, budget and TTL cover an
  already-authorized compatible next PLAN workload, and the provider destroy
  path remains immediately available.
- `DESTROY_REQUIRED`: any safety failure, drift, unknown state, insufficient
  budget or TTL, protected-data concern, missing next-goal authorization, or
  scientific boundary requiring fresh provider admission is present.

`REUSE_ELIGIBLE` reports `Owner continue next goal on PLAN`. It does not itself
authorize that goal. `DESTROY_REQUIRED` reports `Owner destroy instance`.
Neither result invokes a provider action automatically.

The decision is made only after all return artifacts have been collected and
validated locally. Reuse is considered for an already-authorized compatible
next PLAN workload, normally A2, only when hashes/runtime are unchanged,
workers are clean, safety scans pass, budget and TTL remain sufficient, and
the provider destroy path is still immediately available. Otherwise the
report must say `DESTROY_REQUIRED` and the Owner destroys the instance before
the local goal resumes.

## Publication boundary

A1.2 is a candidate-exposure and representation-screening study on REP-DEV.
OUT Recall@100 is the primary development outcome. OUT nDCG@100 and OUT
nDCG@10 are required secondary ranking outcomes. The analysis preregisters
program effects, retriever effects, their interaction, unique relevant-family
contribution, overlap/complementarity, and latency/resource/cost trade-offs.

The maximum of the 25 cells is not, by itself, a promotion rule. A1.2 remains
development and diagnostic evidence until later frozen Selection and Final
confirmation gates are separately authorized and completed.

## Checkpoints

1. Validate v11 and record its exact hashes.
2. Materialize and test v12 schemas, policies, and local-only tooling.
3. Build the frozen execution bundle from a clean pushed commit.
4. Run the Owner-local protected compiler and validate all 25 bindings.
5. Confirm zero truncation and zero unresolved over-length inputs.
6. Run watchdog/destroy-command dry-run without provider action.
7. Emit the canonical v12 receipt before projections.
8. Run rigor, safety, report, MLflow, Brain, Dashboard, and session validation.
9. Commit and push only after every local requirement is proven.

The bundle command must be run only after the reusable bundle builder is
committed, pushed, and the worktree is clean. Both outputs stay in the external
Owner root:

```powershell
$OwnerRoot = Join-Path (Resolve-Path '..') '04_Owner_Stores\a1.2-vast-20260806'
uv run --no-sync python -m myis_research.armindex.a1_2_scientific_execution_adoption_inputs_v12 build-bundle `
  --repository-root . `
  --output (Join-Path $OwnerRoot 'transfer\a1.2-scientific-execution-bundle-v12-r2.tar.gz') `
  --receipt-output (Join-Path $OwnerRoot 'receipts\A1_2_EXECUTION_BUNDLE_V12_R2.json')
```

The earlier `a1.2-scientific-execution-code-bundle-v12.tar.gz` is preserved as
failed historical preparation evidence. It is not an adoption input because it
omitted required A1.2 result schemas and the v11 Owner-local evaluator handoff
contract. Do not upload or use it for v12 execution.

The v12 bundle freezes its exact tracked-path set by SHA-256 and refuses any
new, removed, or renamed selected path. Its required external receipt is
published atomically with the archive. Remote verification binds the exact v11
request and receipt bytes through the v12 static hash check; it intentionally
does not replay the historical v1-v10 provider lineage validator on Vast.

## Current launch gate

`launch_allowed=false` and `adopted_for_execution=false` remain mandatory.
Live-provider fields remain pending and do not block completion of reusable
local tooling, but they do block any claim of live adoption or GPU readiness.
The immediate Owner input is the protected A1.2 store binding through
`MYIS_STORE`; it is not an SSH endpoint or Vast reservation.
