---
title: "A4 long-run production transfer, one-shot Selection, and A5 bundle preparation"
phase_id: A4_PRODUCTION_TRANSFER_AND_SELECTION
task_id: A4.1
status: CLOSED_WITH_EVIDENCE_SELECTION_HANDOFF_BLOCKED
lifecycle: CLOSED
evidence_class: measured_development_and_selection_preparation
scientific_authority: false
execution_permitted: false
provider_instance_id: 47790578
a4_auto_pass_continuation: true
continuation_mode: CONDITIONAL_AUTO_CONTINUE_MINIMAL_TRANSITIONS
routine_owner_interaction: false
missing_handoff_policy: BLOCKED_OWNER_INPUT_NO_GPU_HOLD
conditional_owner_decisions: [D1_START_CAMPAIGN, D2_OPEN_FINAL]
a3_readiness_binding_uri: control/armindex/a4/a4-readiness-binding-20260819.json
a3_readiness_binding_sha256: 4fb8b8f8d6d80941b0c76116d13c4cfd5199dbcd0d17e59152f0088c54c4f7fd
selection_access_limit: 1
final_accesses_allowed: 0
selection_accesses: 0
final_accesses: 0
protected_payloads_allowed: false
previous_goal: docs/goal/A3_TRANSFER_COMPLEMENTARITY_AND_HARNESSOPT_goal_003.md
next_goal: docs/goal/A5_FINAL_CONFIRMATION_goal_001.md
last_material_update: 2026-08-20
next_authorized_action: OWNER_ACTION_SUPPLY_HASH_BOUND_SELECTION_125_HANDOFF
closeout_attempt_id: a4-goal001-20260819T180000Z-a4x12
closeout_audit_sha256: 08b83b848023c52967329b769d7b230cf7009290664e95ddd340d569bb0157b5
selection_handoff_blocker_sha256: 32e5a634b40226a9af2f766fb0f2949a539d3c869968d10324056f25ac839822
selection_handoff_contract_uri: docs/operations/A4_SELECTION_125_OWNER_HANDOFF_20260820.md
selection_handoff_status: BLOCKED_OWNER_INPUT
publication_priority: TIER_1_REVIEWER_DEFENSIBLE_EVIDENCE
---

# Goal 001: A4 production transfer and Selection

## Objective and publication value

Run the frozen A4 production-transfer study on the existing Vast instance,
measure the `FAST`, `BALANCED`, and `DEEP` profiles, evaluate the isolated legal
structured-retrieval transfer, and expose Selection at most once. Preserve
negative, flat, unsupported, and boundary results as publication evidence. The
goal also prepares a complete hash/pointer-only A5 handoff without opening the
Final split.

The publication-facing design has two deliberately separate outputs: a
license-segregated research reference that may include `ARM-03`, and a
commercial-capable serving frontier built only from permitted commercial arms.
This makes a useful research result publishable even if it cannot be deployed,
while preventing a research-only model from being presented as a production
profile. The A4 Selection analysis then distinguishes the research and
commercial champions without retrofitting either after exposure.

The goal does not optimize for a positive result. A4 scientific authority is
created only by valid measured receipts and an independent result-integrity
audit; this goal document is not a numeric source of truth. Publication impact
is tier 1: Selection-125 must preserve paired uncertainty and W/T/L evidence,
and every downstream A5/A6 claim must remain independently auditable.

## Starting state

The canonical A3 closeout is bound by
`control/armindex/a4/a4-readiness-binding-20260819.json`. It records the passing
A3 result-integrity audit, aggregate-safe return, three primary winner program
hashes, nine transfer operations, five fixed controls, and completed HarnessOpt
boundary evaluation. Its claim boundary remains
`contract_only_a4_readiness_no_production_measurement_no_selection_no_final`.

The existing instance is `47790578` and is authorized by `vast-ssh.md` for
routine technical work, autonomous recovery, and project push. A direct SSH
observation on 2026-08-19 identified four RTX 3090 GPUs, Python 3.11, 190 GB
free disk, and historical A2/A3 roots. Historical roots, PIDs, watchdogs,
checkpoints, and receipts are not reusable A4 lineage. Any stale process must
be observed, classified, and reaped only after its identity is proven orphaned.
The Owner handoff contract is
`docs/operations/A4_SELECTION_125_OWNER_HANDOFF_20260820.md`; no Selection
payload may be synthesized from HDEV-100.

## Work status

| Step | Status | Completion evidence |
|---|---|---|
| Canonical A3/A4 integrity and contract validation | COMPLETE | A3 readiness binding and A4 closeout receipts |
| Fresh provider admission and isolated A4 attempt | COMPLETE | A4 admission and attempt `a4-goal001-20260819T180000Z-a4x12` |
| A4 runtime/profile stage and smoke checks | COMPLETE | runtime, watchdog, and profile receipts |
| FAST/BALANCED/DEEP measured execution | COMPLETE | complete profile coverage and aggregate receipts |
| Legal transfer isolation and unsupported-map evidence | COMPLETE | isolated unsupported transfer receipt |
| One-shot Selection-125 owner handoff | BLOCKED | blocker receipt `32e5a634...` and handoff contract |
| One-shot Selection exposure | BLOCKED | preflight counter and Selection receipt; maximum one |
| A5 v2 hash/pointer-only bundle | BLOCKED | real handoff, finalist hashes, safe-export and Git closure |
| Safe return, audit, projections, and closeout | COMPLETE | A4 audit/safe-return plus recorded Selection blocker |

## Frozen scientific and safety invariants

- Keep the A3-bound primary scope and winner program hashes unchanged:
  `ARM-03`, `ARM-04`, and `ARM-05`; retain `ARM-01` and `ARM-02` only as
  diagnostic context where the A4 contract allows it.
- Use the A4 contract at
  `control/armindex/a4/a4-readiness-contract.v1.json` as the interface for
  profile completeness, commercial licensing, Pareto dimensions, and legal
  transfer isolation.
- Measure the frozen production configurations only on the protected
  `HARNESS-DEV` commitment of 100 Train-250 queries. A4 may not mutate a
  representation, harness, adapter, cache policy, or profile after this
  measurement starts.
- Produce exactly `FAST`, `BALANCED`, and `DEEP` commercial profile records.
  Every named profile must contain only commercial-capable arms; the commercial
  fixed union is `ARM-04` plus `ARM-05`. A license-segregated `ARM-03`
  research-reference comparator may be measured under the same frozen
  evaluator, but it is not a fourth profile and never enters a commercial
  frontier or deployment claim.
- Preserve the frozen primary metric `OUT Recall@100`, secondary OUT nDCG
  metrics, and operational latency, throughput, cost, index-size, RAM, and VRAM
  definitions. No post-hoc metric, tie, depth, license, or evaluator change is
  permitted.
- Freeze the Selection registry before Selection access: at most four distinct
  slots in the order prescribed by the research plan: strongest static/common
  baseline, strongest single-arm AutoIndex champion, research HarnessOpt
  champion if promoted, and commercial production champion if distinct. Empty
  or duplicate slots remain empty; no profile is added after the registry hash.
- Selection analyses must report the predeclared lexicographic decision,
  10,000 paired bootstrap resamples, 95% confidence intervals, paired
  win/tie/loss counts, and the correction rule for the small preregistered
  comparison family. These are aggregate-safe evaluator outputs, never
  per-query projections.
- Legal transfer is diagnostic and isolated. It must not feed back into the
  patent campaign, access protected data, or increment Selection or Final.
- The current Owner instruction authorizes this A4 measured run and one
  Selection exposure. Record that authorization in the attempt admission; do
  not create a new routine micro-gate. The one-shot preflight counter is a
  readiness record, not a second Selection access.
- Treat that instruction as the Owner's `D1_START_CAMPAIGN` continuation for
  A4. Bind its receipt to the fresh admission and this goal revision without
  mutating or claiming that a historical D1 record covers the new phase.
- The Owner has additionally pre-authorized conditional continuity: if and only
  if the complete A4 result, safe-return, independent integrity audit, and
  pointer-only A5 bundle all pass their automatic checks, the orchestrator may
  emit a hash-bound `D2_OPEN_FINAL` decision receipt and continue directly to
  A5 on a fresh attempt. This receipt is the recorded Owner decision; it must
  not be emitted for a partial, flat-but-incomplete, failed, or unaudited A4.
- `final_accesses` remains zero until that receipt exists. `D3_SUBMIT_RELEASE`
  remains Owner-only and is never exercised by A4/A5.
- Protected qrels, split membership, raw query/family IDs, per-query outcomes,
  credentials, model payloads, and raw provider payloads remain Owner-local.
  Repository, chat, projections, and the A5 bundle receive only hashes, counts,
  safe IDs, receipts, and opaque pointers.

## Minimal continuation policy

This goal runs as one autonomous continuation. After a canonical receipt and
its independent checks pass, the orchestrator advances to the next numbered
step without another routine Owner prompt or a new micro-gate. Ordinary SSH,
package, timeout, worker, checkpoint, cache, and deterministic staging faults
are fix-forward/resume work inside the same attempt lineage.

The only pre-Selection Owner-input stop is the missing or invalid real
Selection-125 handoff. When that handoff is absent, record
`BLOCKED_OWNER_INPUT`, release any GPU hold, and emit the exact Owner Store
path/hash action. Never wait indefinitely, infer vectors, or use HDEV-100 as a
substitute. Once the Owner handoff is present and validates, resume this goal
lineage and consume Selection at most once.

## Provider, budget, and TTL authority

- Use instance `47790578` only. Additional instance creation is forbidden; the
  instance must not be destroyed by the agent.
- Connect direct first and use the proxy endpoint only as fallback. Do not print
  keys, inherited environments, or provider payloads.
- Before any spend or remote stage, obtain a fresh authenticated provider
  observation, all-fee quote no older than 900 seconds, runtime/GPU identity,
  available disk/RAM, process state, and a 48-hour target TTL. Require at least
  24 hours remaining at admission.
- Compute the whole-workload estimate from the current campaign headroom and
  accrued spend. The historical post-A3 headroom estimate is
  USD `79.31170133333334052`; it is a reference only and must be revalidated.
  If the current ceiling, accrued spend, quote, or next-action estimate is
  unknown, use `UNKNOWN_DO_NOT_SPEND`. Never infer authority from `vast-ssh.md`
  hourly text or historical receipts.
- The A4 admission must reserve a fresh quote-backed amount sufficient for the
  single A5 Final-872 confirmation and its safe return before discretionary A4
  expansion. A4 may close with complete evidence without that reserve, but it
  cannot emit conditional D2 or claim automatic A5 continuity.
- Stop before the live admission if the quote or projected A4 workload exceeds
  the verified remaining campaign/goal ceiling, TTL floor, or provider identity.

## Execution flow

1. **Bind integrity.** Read `PLAN.md`, this goal, the A4 readiness contract and
   binding, the A3 closeout goal, and the current campaign record. Verify all
   referenced hashes, the A3 closeout state, the exact three-primary scope, and
   that Selection/Final counters are still zero.
2. **Inspect and isolate the instance.** Connect direct, verify hostname,
   identity, runtime, GPUs, disk, RAM, and Git/project location. Inventory
   `/opt/myis` roots and running processes. Preserve historical evidence. Reap
   only proven orphan processes; fail closed on ambiguous ownership. Generate a
   fresh attempt ID and a non-existing attempt root such as
   `/opt/myis/a4-goal001-<timestamp>`.
3. **Admit the workload.** Record the fresh provider observation, quote, TTL,
   budget projection, Owner intent, and protected-data boundary. Do not stage or
   spend until the whole-workload admission passes.
4. **Build and validate the bundle.** Package only clean pushed code, frozen
   controls, runtime bindings, model/license snapshots, A3 winner hashes,
   HARNESS-DEV commitment, A4 profile contracts, the four-slot Selection
   registry policy, legal-transfer maps, evaluator interfaces, and safe export
   rules. Recompute the bundle and file hashes after staging. Create a durable
   append-only ledger, attempt checkpoint, watchdog, and stop marker.
5. **Run launch checks.** Exercise transport, cancellation, heartbeat,
   checkpoint/resume, worker reaping, protected-field scan, and safe-return dry
   checks. Require an independent launch-integrity review before measured work.
6. **Measure A4.** Run the three complete commercial profiles over the frozen
   HARNESS-DEV input under the frozen evaluator. Measure the eligible
   research-reference comparator separately, with its license label intact.
   Record profile coverage, non-dominated frontier status, latency/cost/resource
   aggregates, unsupported mappings, and failures. A partial profile is not a
   result and cannot be combined with another attempt.
7. **Run legal transfer diagnostics.** Run the minimum frozen legal mini
   diagnostic first; run the full legal benchmark only after the mini diagnostic
   is valid and the A5 reserve remains intact. Emit explicit supported, mixed,
   unsupported, or stopped-with-evidence states. Do not return raw legal inputs
   or feed the diagnostic back into ArmIndex.
8. **Freeze the Selection registry and consume Selection.** After all A4
   development checks pass, freeze the distinct at-most-four finalist registry
   and its comparator relationships, then validate the owner-local
   `docs/operations/A4_SELECTION_125_OWNER_HANDOFF_20260820.md` contract before
   consuming the preflight counter once. Perform at most one Selection exposure
   using exactly 125 OUT paired vectors, the frozen lexicographic rule, 10,000
   bootstrap resamples, 95% confidence intervals, rank-biserial effect, and
   W/T/L. Record the research and commercial champion designations, Selection
   receipt, and finalist hashes. If the handoff hash, vector count, evaluator
   handoff, preflight counter, license check, Pareto frontier, profile
   completeness, legal isolation, protected boundary, or registry closure
   fails, do not open Selection.
9. **Prepare A5 handoff.** Build the A5 bundle described in
   `docs/goal/A5_FINAL_CONFIRMATION_goal_001.md` using the v2 pointer-bundle
   contract. Bind finalist program/prompt/representation/model/license/runtime
   hashes, evaluator handoff pointer, Final-872 commitment, safe-export
   manifest, and clean pushed Git commit/tree. Keep protected inputs as
   Owner-local opaque pointers and hashes. Do not materialize or copy raw final
   payloads to the repository, chat, projections, or the remote staging root.
10. **Return and audit.** Stop workers at a safe boundary, validate the
    allowlisted aggregate-safe return, verify worker teardown, and write an
    independent result-integrity audit. Failed attempts remain separate and are
    never mixed with the successful attempt.
11. **Automatic continuity decision.** After all A4 acceptance criteria pass,
    write an append-only conditional D2 receipt binding the A4 result audit,
    safe-return receipt, A5 bundle self-hash, clean Git commit/tree, and exact
    protected split commitment. The receipt must state `selection_accesses` as
    0 or 1, `final_accesses` as 0 before launch, and `owner_conditional_approval`
    as true. If any binding is missing, preserve A4 evidence and stop without
    opening Final.
12. **Close out / continue.** Update the canonical evidence/read-model/report projections
    only from validated receipts, create
    `docs/long_run/A4_PRODUCTION_TRANSFER_AND_SELECTION_lo_001_001.md`, run
    focused tests and `git diff --check`, and commit/push intended changes. If
    the conditional D2 receipt was emitted, continue immediately into the A5
    goal on a new isolated root and fresh admission; otherwise record
    `OWNER_ACTION_DESTROY` unless an explicitly authorized non-A5 action
    justifies `KEEP_GPU`.

## Required artifacts

Store canonical aggregate-safe records under the existing campaign/evidence and
control conventions, with Owner-local protected material under
`<MYIS_ROOT>/04_Owner_Stores/armindex/a4/<attempt-id>/`:

- fresh provider observation, all-fee quote, budget/TTL admission, and attempt
  identity;
- clean execution bundle manifest/receipt, runtime and model/license bindings,
  stage/adoption receipts, and launch-integrity review;
- per-profile FAST/BALANCED/DEEP manifests and aggregate result receipts;
- a separately labeled research-reference receipt, commercial Pareto frontier
  receipt, and a frozen at-most-four Selection registry with comparator roles;
- legal transfer receipt with explicit unsupported mappings;
- durable ledger/checkpoints, watchdog/heartbeat/reaping receipts, and safe
  return archive/receipt;
- one-shot Selection preflight counter and Selection receipt, with
  `selection_accesses` exactly `0` or `1` and `final_accesses` exactly `0`;
- A5 bundle manifest, evaluator handoff receipt, final-split commitment hash,
  opaque pointer, and SHA-256 manifest;
- result-integrity audit, figure/claim manifest if generated, projections, and
  the long-run handoff.

The figure/claim manifest must allow reconstruction of aggregate-safe
publication tables and figures: quality-latency-cost frontier, profile resource
table, research-versus-commercial decision table, Selection paired-effect
summary, and legal-transfer boundary summary. It must distinguish measured,
unsupported, and unmeasured states rather than impute missing results.

No artifact may contain raw qrels, membership, query IDs, rankings, per-query
outcomes, credentials, or provider payloads.

## Validation commands

Run these focused checks from the repository root before launch and again at
closeout:

```text
rtk pytest -q tests/test_a4_readiness.py
rtk git diff --check
```

Also run the repository's JSON/schema validators for every generated A4/A5
receipt and verify each recorded SHA-256 against its canonical file. The remote
launch review must include transport, watchdog, checkpoint/resume, reaping, and
safe-return smoke evidence; a passing local test alone does not authorize
measurement.

## Recovery and hard stops

Fix forward ordinary SSH, package, path, timeout, worker, OOM, cache,
checkpoint, and deterministic staging failures while preserving attempt
lineage. Use a new engineering hypothesis after repeated failures; never
blindly retry the same failed command.

Hard stop and preserve state on:

- A3/A4 hash or scientific-binding drift, candidate/representation/evaluator
  mutation, unsupported license use, or incomplete profile coverage;
- unknown or over-cap budget, stale quote, insufficient TTL, provider identity
  drift, ambiguous remote-root ownership, or unverified worker liveness;
- protected-data exposure or an attempt to copy protected bytes outside the
  Owner-local boundary;
- malformed/already-consumed Selection counter, second Selection exposure,
  any Final access before the hash-bound conditional D2 receipt, or any request
  to bypass `D2_OPEN_FINAL`;
- an unfrozen or altered Selection registry, a research-only arm in a
  commercial profile, or a conditional-D2 decision without a protected A5
  budget reserve;
- incompatible partial outputs, irrecoverable provenance ambiguity, or a
  possible protected leak.

## Acceptance and terminal states

Success requires complete A4 profile/transfer coverage, a clear research versus
commercial claim boundary, at most one valid Selection receipt, zero Final
access before the conditional D2 receipt, safe return, independent result
audit, hash-closed A5 pointer bundle, and synchronized projections. A flat or
negative result is a valid success if evidence is complete and claim-limited,
but it never triggers D2 when coverage, audit completeness, or the A5 reserve
is missing.

Terminal states are `PASS_A4_SELECTION_AND_A5_HANDOFF`,
`CLOSED_WITH_EVIDENCE_SELECTION_HANDOFF_BLOCKED`,
`STOP_FAIL_CLOSED_WITH_EVIDENCE`, or `BLOCKED_OWNER_ACTION`. The current
terminal state is the evidence-preserving Selection-handoff blocker recorded in
the A4 closeout; a future continuation must use a new attempt and must not
reuse this measured root. A blocked state must preserve the same attempt and
goal lineage for resume.

## Next action

After A4 closeout, hand off to
`docs/goal/A5_FINAL_CONFIRMATION_goal_001.md`. The current handoff is blocked
until an Owner-local, hash-bound Selection-125 paired-vector/evaluator handoff
is independently validated. A5 then remains blocked until a manual
`D2_OPEN_FINAL` or this goal's hash-bound conditional D2 receipt exists.
