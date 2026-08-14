# A2 AP Audit 006: fresh staging passed, measured remote launch path incomplete

- Session mode: `AP`
- Phase/Task: `A2_PER_ARM_AUTOINDEX / A2.1 FROZEN_FIVE_ARM_EXECUTION`
- Source IM handoff: `docs/implementation/A2_PER_ARM_AUTOINDEX_im_005_001.md`
- Reviewed staging repair revision: `daf124ace981e070d012cca6d8c0feaed607d41a`
- Routing: `NEEDS_IM`
- Date: `2026-08-14`

## AP decision

Canonical readiness closure, final pushed-HEAD bundle/deployment receipts, fresh
Vast admission, complete asset transfer, and isolated staging all pass. The
terminal operational state is `EXTERNAL_EXECUTION_REQUESTED_NOT_LAUNCHED`.
No A2 candidate, REP-DEV measurement, measured retrieval, Selection, Final, or
GPU scientific worker was started.

Measured LO is not ready yet. The canonical `execute` command starts the A2
production adapter as a subprocess on the machine running the orchestrator, but
the four CUDA devices and staged models exist only on the remote Vast instance.
There is no tracked remote measured-launch transport, no remote Git provenance
surface that can validate the tracked measurement authority, and no real
Owner-local measured input manifest. Starting LO now would fail closed or risk
executing on the wrong host. This is launch-critical implementation work, not a
scientific-design change.

The reserve checkpoint has a second launch-critical defect. Initial provider
admission correctly requires at least `40` hours remaining, but `reserve-admit`
reuses the same 40-hour floor after all 40 matched candidates finish. The frozen
budget profile projects a matched dense critical path of about `17.92` hours and
a worst-case full critical path of about `26.87` hours. Its explicit six-hour
reserve implies a checkpoint floor of about `14.95` hours for the remaining
conditional-reserve work, not another 40 hours. Under the current implementation,
the matched barrier cannot pass even when the full workload remains inside the
USD 35 quote. This is an execution-budget lifecycle defect; the initial 40-hour
admission floor and USD 35 hard stop must remain unchanged.

## Pushed-HEAD bundle and deployment closure

- Git commit and `origin/main`: `daf124ace981e070d012cca6d8c0feaed607d41a`
- Git tree: `4b355ddaf7ccdbda5696080b007e5cdbfd7bf1fe`
- Execution bundle SHA-256:
  `2ba3793e775734f0620850bec088222124d5cf9ed8d972285512bad58ce3d7e2`
- Execution bundle receipt self-hash:
  `88d92abb313d27857cb309e08369602b36634ca093c9980088bb8cf9a7c47b8c`
- Deployment package SHA-256:
  `5462b86dfe908fb0d2c8159d4838a9e4170c186c3a57785f1ebc05460b15ec66`
- Deployment package receipt self-hash:
  `a2a129676a9aa06e5a3541daee34f82cc6730b6687c156aa598fe7fe08daa602`
- Owner-local root:
  `../04_Owner_Stores/armindex/a2/a2-ap-audit006-pushed-head-20260814/`

The deployment package is hash-only metadata. It contains no model bytes,
wheel bytes, protected payload, or scientific authority. All four model roots,
the Linux wheelhouse, A1 handoffs/safe return/runtime identity, frozen A1 bundle,
and A2 bundle were re-probed and passed.

## Provider admission and isolated staging

- Vast instance: `47700074`, status `RUNNING`, verified
- Topology: four `RTX 3090`, `24,576 MiB` VRAM each
- All-fee 48-hour quote: USD `27.939255`
- A2 forward hard stop: USD `35`
- Provider TTL deadline: `2026-08-16T10:35:12.980077Z`
- Fresh admission remaining TTL: `152,989` seconds
- Provider instance binding SHA-256:
  `9e39b2f252af6810064dbd8d4b4020d78824d4cd7f2c784d6adaad1173764d96`
- Provider admission receipt SHA-256:
  `96b057a9140f90eb3501ab40b844bc4c4c186b037457bc52c0f8dcf37805636c`
- Remote root: `/opt/myis/a2-im-audit005-final`
- Live-probe receipt SHA-256:
  `2a5338a8edf60b25ac780abb54f3410ce387705a91c3d5268b499b81954c4071`
- Remote-stage receipt SHA-256:
  `b6e690226b572e350686201315d561f9215626500f0e80e59c50abf22efa50bb`
- Execution-adoption receipt SHA-256:
  `a4342274785503652b1a9a899fd27fa24ab0c39bac6ad25c4b2f03d038bb8bbe`
- Genesis checkpoint SHA-256:
  `1c9f1cd93e53dbc946eaea0663ded1ac077b8eb381d629bcc2e21d56689a9004`
- Watchdog deadline: `2026-08-16T09:35:00Z`
- Owner-local evidence root:
  `../04_Owner_Stores/armindex/a2/a2-ap-audit006-fresh-stage-20260814/`

The stage receipt proves a fresh root, staged-bundle hash equality, live
watchdog heartbeat, zero GPU compute processes, zero A2 workers, no A1-root
mutation, and `measured_a2_started=false`.

## Upload and ARM-02 transfer note

The remote incoming tree contains the hash-validated ARM-02 through ARM-05
model roots, Linux wheelhouse, frozen A1 bundle, A1 handoffs/safe return,
runtime identity, and the current A2 bundle/deployment receipts. No model must
be re-uploaded for the next IM session.

ARM-02 took longer because its local model tree is about `2.293 GB`, dominated
by one `2.271 GB` `pytorch_model.bin`. ARM-03/04/05 are approximately
`1.380/1.239/1.207 GB`; ARM-02 is therefore about `1.66-1.90x` larger and its
first transfer required resumable recovery. ARM-02 is now complete and its full
`SHA256SUMS` validation passes.

## Repairs completed during AP

Canonical stage initially failed before remote-root creation because
`pgrep -f 'myis_research.armindex.a2_'` matched its own remote shell command.
The minimal repair uses the self-excluding pattern
`pgrep -f '[m]yis_research.armindex.a2_'` and adds a regression assertion.
Focused executor tests passed (`31 passed`) and the repair was pushed as
`daf124ace981e070d012cca6d8c0feaed607d41a`.

A subsequent live probe failed closed because the supplied remote identity
paths omitted the existing `identity/` directory. Re-running with the actual
hash-validated paths passed without code change. The failed probes created no
execution root and started no worker.

## IM work required before measured LO

1. Implement one canonical remote measured-execution transport for the existing
   Vast instance and staged asset tree. The orchestrator must never silently run
   the CUDA-bound production engine on local Windows.
2. Preserve the frozen 52-candidate membership, matched-first barrier,
   ARM-01/02 non-advancement, evaluator semantics, exact ties, budget/TTL rules,
   checkpoint/recovery, and aggregate-only receipt contract.
3. Materialize and validate a real Owner-local measured input manifest from the
   existing A1 v16/runtime/model/data/evaluator bindings. Keep credentials and
   protected payloads outside Git, projections, chat, and raw provider logs.
4. Provide clean pushed-HEAD measurement-authority provenance on the execution
   host, or add a narrowly scoped hash-bound remote provenance mechanism that
   preserves the current authority contract. Do not weaken provenance checks.
5. Reuse instance `47700074`, `/opt/myis/a2-im-audit005-final`, and the existing
   uploaded model/wheel/A1 assets. Upload only small changed code/control files.
6. Exercise remote preflight and a non-measured/synthetic transport check only.
   Do not evaluate a frozen candidate or access REP-DEV for measurement in IM.
7. Write `docs/implementation/A2_PER_ARM_AUTOINDEX_im_006_001.md`, run focused
   tests/Ruff/preflight/dry-run plus `git diff --check`, and commit/push.
8. Separate initial admission from reserve-checkpoint admission. Keep the fresh
   initial floor at `40` hours. At the matched barrier, derive the minimum
   remaining TTL deterministically from the frozen runtime projection for the
   unfinished reserve critical path plus the existing six-hour reserve (about
   `14.95` hours with current canonical inputs). Keep the USD `35` whole-workload
   hard stop, fresh source re-probe, and all fee components unchanged. Add tests
   proving that 40-hour initial admission remains mandatory, a sufficient
   checkpoint TTL passes, and an insufficient checkpoint TTL fails closed.

Because this changes the measured launch transport and authority provenance,
IM must return to AP for a short launch-readiness review before LO.

## AP closeout validation

- Focused A2 candidate-freeze/contracts/readiness/preflight/executor/read-model
  suite: `99 passed`
- Ruff on the changed Python and test surface: `PASS`
- A2 entry preflight: `PASS_A2_ENTRY_PREFLIGHT`; current disposition
  `STAGED_FRESH_INSTANCE`; reuse permitted; execution and candidate evaluation
  unauthorized
- Synthetic operational dry-run: `PASS_A2_SYNTHETIC_OPERATIONAL_DRY_RUN`,
  `52/52`; provider contacted `false`, measured A2 started `false`, protected
  payload included `false`
- Canonical YAML/JSON parsing, quick asset validation, and `git diff --check`:
  `PASS`
- Safe live provider observation at `2026-08-14T17:24:12Z`: instance running,
  all-fee rate USD `0.575817794/hour`, accrued approximately USD `3.925135`,
  remaining TTL approximately `41.183351` hours, GPU utilization `0%`, and
  two additional idle hours approximately USD `1.151636`
- Immediate remote recheck: watchdog identity alive with heartbeat age `2.307`
  seconds, GPU compute processes `0`, A2 processes `0`

The first combined focused pytest invocation exceeded its wrapper timeout before
returning a result. The identical test set was rerun with a longer wrapper and
completed at `99 passed`; this was an observation-wrapper timeout, not a test
failure. Obsidian and MLflow projections remain pending because a full report
sync would create unrelated timestamp/source-revision churn across 285 files.

## Boundaries and compute disposition

The live GPU should be kept only for the immediate IM repair because the full
asset upload and isolated staging are complete. The current provider rate is
approximately USD `0.575818/hour` including storage. If IM cannot produce a
validated launch path promptly, AP must reassess TTL/budget and destroy or
replace the instance rather than leave it idle.

Measured A2 remains closed. No measurement authority or LO-ready measured goal
was created in this audit.
