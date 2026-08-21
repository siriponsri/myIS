# A5/A6 Instance-Rotation Handoff

Status: `PAUSED_AFTER_A4_INSTANCE_ROTATION`

## Completed

- A4 Selection-125 closeout remains the canonical predecessor: four profiles
  completed `125/125`, deterministic, zero recorded failures, one Selection
  exposure, and zero Final exposures.
- Aggregate-safe A5 provenance is staged in Owner Store:
  `armindex/a5/provenance/a5-finalist-provenance-manifest-20260822.json`.
- The pointer-only A5 bundle was rebuilt against the final pushed `main` as
  `a5-pointer-bundle-v6-20260822.json`.
- The opaque Final-872 input receipt is staged at
  `armindex/a5/final-872-input/receipt.json` with `payload_materialized=false`.
- Safe-return artifacts from Vast `47790578` are recorded under
  `armindex/handoff/vast-47790578-20260822/`.
- No A5 Final-872 or A6 full-corpus execution was started.

## Provider closeout

The instance identity was verified as `47790578` / `fb2ac0d6cc8e`. Four RTX
3090 GPUs were idle, approximately 130 GiB disk was available, and no A4/A5/A6
worker remained after the only proven orphan log-reader shell was reaped.
Protected payload, qrels, membership, query files, rankings, per-query
outcomes, credentials, and model payloads were not exported.

## Resume protocol

After Owner has destroyed the old instance and updates `vast-ssh.md`, resume this
same goal and goal index. Read the new `vast-ssh.md`, verify fresh provider
identity, quote, TTL, budget, runtime, disk, and GPU health, then create a
fresh isolated A5 root. Do not reuse old PIDs, caches, workers, quotes,
partial outputs, or provider admission. Open Final only through the automatic
D2 receipt after the provenance audit is valid. Start A6 only after a complete
`PASS_A5_FINAL_CONFIRMATION` and a single frozen winner. Keep `D3_SUBMIT_RELEASE`
closed.
