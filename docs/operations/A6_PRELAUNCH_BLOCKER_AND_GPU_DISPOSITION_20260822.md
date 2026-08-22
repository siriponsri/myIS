# A6 Prelaunch Blocker and GPU Disposition

Date: 2026-08-22
Phase: `A6_FULL_DAPFAM_MATERIALIZATION_AND_SCALABILITY`
Evidence class: operational prelaunch / no measured A6 result

## Verified State

- A5 is terminal and valid: `PASS_A5_FINAL_CONFIRMATION`.
- The frozen A5 research champion is `ARM-03`, model `datalyes/patembed-large`.
- A5 Final-872 aggregate-safe result: Recall@100 `0.442476` versus the static comparator `0.331097`, delta `+0.111379`.
- The A6 source snapshot is Owner-Store-only: `45,336` documents and `45,336` families, source SHA-256 `a0588cbc7a0aa70c0e5880073d3b696450eb4d0e3752229e69a1661f6d69e74c`.
- No A6 corpus upload, model upload, remote root, worker, canary, full run, or A6 metric was created.
- Vast instance `48367896` was verified as `2 x RTX 3090`; both GPUs were idle at the last observation, disk had approximately `111 GiB` free, and no A6 worker was present.

## Engineering Readiness

The A6 harness is committed at `0ec3eaae` and pushed to `origin/main`. Focused validation passed:

```text
35 tests passed
ruff check passed
git diff --check passed
```

The harness now binds the staged ARM-03 semantic manifest, enforces offline model loading, checks installed runtime package versions, bounds passage batches, merges latency histograms across shards, writes an Owner-Store index manifest, and reaps child workers on failure.

## Launch Blockers

1. The A6 contract requires a separate A6 budget ceiling and fresh all-fee budget admission. No canonical A6-specific ceiling is present. Historical campaign ceilings and A5/A4 reservations are not valid A6 spending authority.
2. Before launch, the admission package must provide and validate the staged source-snapshot receipt, model manifest, runtime/package receipt, semantic manifest, fresh remote-root receipt, fresh quote, health receipts, and safe-export manifest.
3. Independent audit still requires the canary/full attempt lineage to use distinct identities or a formally valid isolated-root lineage.
4. Source provenance, model identity, and runtime package versions must be checked against the canonical A5/A1 manifests and locks rather than only self-attested local receipts.

These are fail-closed launch conditions. No scientific result is inferred from the absence of a run.

## GPU Disposition

### Recommended disposition now

`DESTROY_REQUIRED` after Owner confirms the dashboard action. There is no active or recoverable A6 workload, no pending remote artifact requiring the instance, and A7 publication/release is local and remains `D3_SUBMIT_RELEASE`-gated. Do not keep the instance merely for a possible future A6.

### Remaining GPU work

- A6: one future GPU phase remains only if the Owner supplies a separate A6 ceiling and a fresh admission is created. It must run the frozen ARM-03 representation over the full DAPFAM corpus and then be independently audited.
- A7: no GPU phase is required by the current plan; publication/release is local and D3-gated.
- A0-A5: GPU work is complete for the current campaign state.

## Owner Action Required

Choose one terminal route:

1. Destroy instance `48367896` now and resume A6 later with a new/fresh instance, a canonical A6 budget ceiling, and a fresh control amendment that binds the new provider instance; or
2. Provide a canonical A6 ceiling, then create fresh A6 admission and lineage receipts before any paid staging or execution.

Until route 2 is complete, A6 remains `UNKNOWN_DO_NOT_SPEND`; no A6 metric, throughput, cost, or scalability claim may be reported.
