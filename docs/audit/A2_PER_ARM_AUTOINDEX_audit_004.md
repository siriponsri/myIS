# A2 AP Audit 004: fresh-instance deployment readiness

- Session mode: `AP`
- Phase/Task: `A2_PER_ARM_AUTOINDEX / A2.1 FROZEN_FIVE_ARM_EXECUTION`
- Reviewed revision: `cfec58eda2544433b88fb6c96d47ec5cd76ff4d9`
- Source IM handoff: `docs/implementation/A2_PER_ARM_AUTOINDEX_im_003_001.md`
- Owner route: destroy instance `47411176`, provision a fresh Vast instance, then replace `vast-ssh.md`
- Routing: `NEEDS_IM`
- Date: `2026-08-12`

## Objective

Prepare the CPU-local code, controls, bundle, and reusable deployment assets so a later
AP/LO session can admit and stage A2 on a newly provisioned Vast instance without
reusing stale provider identity or downloading frozen assets again.

## Evidence inspected

- A1 r15 terminal receipt and remote-retention audit
- live authenticated Vast observation and pinned SSH process/root inspection
- final IM 003 bundle receipt and isolated bundle validator
- A2 provider observation/admission/live-probe schemas and operational executor
- local Owner stores for four frozen model roots, Linux wheelhouse, A1 safe return,
  A1 handoffs, and the frozen A1 execution bundle
- focused A2 tests, Ruff, and A2 entry preflight

## Findings that matter

1. **The old instance disposition is `DESTROY_REQUIRED`.** A1 r15 is terminal `25/25 PASS` with
   safe-return SHA-256 `cdbfa4f...3522f3`. Live inspection found zero A1 workers,
   zero A2 workers, zero GPU compute processes, and no A2 measured root. Local
   model and wheelhouse manifests match the remote bytes, so no further pull is
   required before the Owner destroys instance `47411176`. The entry preflight's
   `REUSE_ELIGIBLE` field is inherited A1 disposition; it does not override the
   Owner's fresh-instance route or establish A2 admission/readiness.
2. **The current A2 provider contract cannot admit a new instance.** Instance
   `47411176` is fixed in the readiness contract, provider observation/admission
   schemas, live-probe schema, validator, and current goal wording. A fresh
   instance must be bound through an additive current contract revision or a
   validated provider-instance binding; do not mutate historical receipts.
3. **The current bundle is not the final new-instance bundle.** Bundle
   `a4279056...63e563` is valid for commit `cfec58e`, but it predates three bounded
   staging-path repairs found during AP dry staging: immutable receipt reuse for
   stage-plan/adoption validation, post-probe validation time, and bounded remote
   clock skew. Rebuild only after these repairs and the new-instance binding pass.
4. **Reusable deployment assets are available locally.** Model manifests validate
   `12/12` files for each ARM-02..05; the Linux wheelhouse validates `14/14`
   declared files. The A1 safe-return archive, baseline/journal/closeout handoffs,
   and frozen A1 execution bundle are also local and hash-matched. No model download
   or protected-data pull is needed.
5. **A deployment package and Owner-local measured-input manifest still need a
   concrete builder/validator.** The code/control bundle intentionally excludes
   model bytes and protected inputs. IM must create a hash-only deployment manifest
   over the existing Owner-local assets and a new-instance stage path. Protected
   corpus/query/qrels/membership bytes remain Owner-local and must not enter Git.
6. **Publication claims remain pre-measurement only.** Current evidence supports
   reproducibility, freeze integrity, provider lifecycle, and launch-readiness
   claims. It does not support A2 effectiveness, latency, cost, winner, or
   superiority claims. Those must resolve to future validated measured receipts
   and safe return, never to this audit, logs, fixtures, or provider state.
7. **The generated A2 report source is operationally stale.** Report sync/check
   passes one shared revision, but the A2 phase/task projection still says the
   production adapter and matched-first reserve lifecycle are pending. IM 003
   already completed that surface. IM must repair the canonical report-record
   mapping so generated A2 status follows the current new-instance rebind route.
   Until then, the generated report remains `scientific_authority=false` and must
   not be used as launch status or publication evidence for A2 completion.

## Implementation work requested

1. Preserve historical A2 readiness artifacts and add the smallest current revision
   that binds a runtime-supplied, freshly observed Vast instance ID while retaining
   4x RTX 3090, 24 GiB each, runtime/model/data/GPU/SSH checks, 48h target, >=40h
   admission floor, and USD 35 forward hard stop.
2. Retain and finish the AP staging repairs currently visible in the worktree; add
   focused regressions for original immutable bundle receipt reuse and bounded
   remote clock skew.
3. Add a CPU-local deployment-package builder/validator using existing assets under
   `04_Owner_Stores/a1.2-vast-20260806` and
   `04_Owner_Stores/armindex-a2/a1-baseline-safe-return`. Bind four model manifests,
   Linux wheelhouse `SHA256SUMS`, A1 handoffs, runtime identity, frozen code bundle,
   and the new A2 code/control bundle. Do not copy protected payloads into the
   deployment package.
4. Provide exact fresh-instance commands for admission, identity upload, asset
   transfer, isolated stage, watchdog verification, resume, safe return, and closeout.
   Stage must remain separate from measured `execute`.
5. Build a clean pushed-HEAD A2 bundle plus an Owner-local deployment receipt after
   all changes. The bundle/receipt must not bind the destroyed instance.
6. Update `PLAN.md`, `HANDOFF.md`, runbook and goal wording consistently. Do not
   create measured authority or an LO-ready goal until a fresh instance has passed
   provider admission and isolated staging.
7. Repair the A2 report-record/projection source so generated A2 phase/task reports
   no longer claim the production adapter is pending and instead report the current
   `NEEDS_IM_NEW_INSTANCE_REBIND_MEASUREMENT_LOCKED` route. Regenerate and validate
   projections only after the canonical source is corrected.

## Scientific and protected boundaries

- Do not change the 52 candidate bytes, freeze manifest/receipt/lock, metrics, tie
  policy, matched-first reserve predicate, or ARM-01/02 non-advancement.
- Do not access or export REP-DEV membership, qrels, query IDs, per-query outcomes,
  HARNESS-DEV, Selection, or Final.
- Do not contact or provision a provider, edit Owner credentials, download models,
  or start measured A2 in IM.
- Preserve A1 r15 and all historical provider receipts as immutable evidence.

## Smallest useful validation

```powershell
uv run --no-sync pytest -q tests/test_armindex_a2_execution_readiness.py tests/test_armindex_a2_operational_executor.py tests/test_armindex_a2_measured_adapter.py tests/test_armindex_a2_owner_local_engine.py tests/test_armindex_a2_program_runtime.py
uv run --no-sync ruff check <changed A2 source and tests>
uv run --no-sync python -m myis_research.armindex.a2_entry_preflight_v16 --repository-root .
uv run --no-sync python -m myis_research.armindex.a2_operational_executor --repository-root . --attempt-id a2-im-audit004-dryrun --dry-run
uv run --no-sync myis-assets validate --mode quick
git diff --check
```

## Expected IM output

Write `docs/implementation/A2_PER_ARM_AUTOINDEX_im_004_001.md` with the final
revision, changed controls/schemas/code, local deployment asset receipt, focused
checks, clean bundle path/hash, exact new-instance staging commands, remaining
limits, and route `READY_FOR_AP_FRESH_INSTANCE_STAGING` only when no CPU-local
launch blocker remains.
