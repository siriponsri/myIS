# myIS Research Handoff

## Session scope

This session completed bounded implementation and documentation work only. No
qrels evaluation, protected membership access, paid API, GPU/Vast connection,
confirmation request, publication, or scientific metric run occurred.

## Current status

- Program: `myIS Research` / machine `myis-research` / protocol `1.0`.
- Active flow: `Track C -> frozen C1 harness -> Track S`.
- `F0 = closed`, `G0 = approved`.
- `F1/F1.1 = waiting_gate`, `G1 = pending`; CPU Sprint preparation is complete
  for the current bounded scope.
- Track S protocol repair is documented and fixture-tested; S0/S1 remain
  blocked until engine provenance, CoreWeave preflight, and Owner S-MARGIN
  values are resolved. No Track S experiment ran.
- `Data_Review.ipynb` is closed as metadata-only F1/G1 preparation. Empty
  outputs are intentional privacy behavior, not missing scientific results.

## Implemented in this session

- F1 CPU contracts: model artifact/source manifest, runtime map, cloud-transfer
  policy, synthetic-only baseline replay, and fail-closed validation.
- Track S contracts: A2/A2L/A3 engine provenance, A3 typed C1 overlay, signed
  S-MARGIN acceptance, deterministic finalist selection (`11 -> 23 -> 47`),
  matched realized campaigns, and descriptive mechanism counters.
- Dashboard: session-protected Notes API, Thai-first note reader, pathless
  Obsidian links, and interactive flow graph/presentation hooks.
- Obsidian projection: generated status, F1.1 CPU Sprint, and Track S protocol
  notes under `07_obsidian_note/generated/` plus a reusable notes skill.
- Governance: CPU/GPU Sprint lifecycle, Vast SSH request and destroy-stop
  rule, mandatory Gate report after each implementation session, and mandatory
  docs/HANDOFF/Obsidian/Brain refresh before commit/push.

## Blockers and Owner decisions

- `G1`: Owner must approve the exact corpus/query/qrels/family/evaluator
  commitments, model artifact/hash, compute option, provider, wall-time,
  hard cost ceiling, data-egress scope, and no-fallback policy.
- `S_ENGINE_PROVENANCE_TBD_BLOCKING`: verify that the pinned A2 and A2L
  references resolve to the recorded upstream trees/parents and that executable
  sources are available before S0/S1.
- `S_MARGIN_VALUES_TBD_BLOCKING`: Owner chooses signed `m_ALL` and `m_IN` only
  after the baseline-only audit; the optimizer cannot choose them.
- `COREWEAVE_FINAL_FREEZE_TBD_BLOCKING`: CoreWeave preflight and exact target
  provider identity remain unapproved.
- `CT_BUDGET_LICENSE_TBD_BLOCKING`: PatenTEB transfer remains deferred.

Recommended compute choices, in order: Owner-controlled GPU with the locked
Nemotron artifact already cached; explicitly approved cloud GPU for preparation
or measured work after G1; or defer. Local CPU is suitable for fixtures and
contracts, not the 8B encoder.

## Owner closeout

**Owner must do:** review this handoff and the generated notes; decide whether
to prepare a G1 package; choose compute/time/cost/egress policy; and, separately,
resolve Track S provenance and margins. Silence is not approval.

**Next Gate request:** `G1`, status `draft`/`pending`; this is a report only and
does not open the Gate.

**Next-phase resources:** CPU local workspace for dry runs; if G1 is approved,
an Owner-controlled or approved cloud GPU with at least 48 GiB VRAM, 16 vCPU,
64 GiB RAM, 150 GiB SSD, named wall/cost limits, and an explicitly approved
network/egress scope. Vast SSH host/user/port/key authorization must be supplied
again in that session.

After any authorized GPU Sprint, the agent will pull and validate allowlisted
artifacts, stop remote processes, and pause with the required destroy-instance
message until the Owner confirms destruction and types `ดำเนินการต่อ`.

## Protected surfaces untouched

Confirmation qrels, membership, IDs, per-query outcomes, protected payloads,
App datasets/models/indexes, paid providers, GPU instances, external
publication, immutable approvals, and historical session capsules were not
modified or accessed for scientific use.

## Projection checkpoint

Before commit/push, regenerate `07_obsidian_note/generated/`, validate the
session capsule index and asset map, update the Brain pointer using its
serial-writer lease, and refresh the PLAN hash in Linear/MLflow projection
catalogs. A failed Brain update blocks commit/push.

This system is decision support for retrieval research, not legal advice.

Final implementation capsule: `04_outputs/audits/research-sessions/20260729T161500Z-implementation-closeout-final.json`.
Verification at closeout: full test suite `179 passed`, 56 subtests passed;
restructure, integrity, literature, reusable-asset, and session validation all
passed. One Starlette/httpx deprecation warning remains environment-level.
