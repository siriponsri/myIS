---
title: "A4 long-run production transfer, one-shot Selection, and A5 bundle preparation"
phase_id: A4_PRODUCTION_TRANSFER_AND_SELECTION
task_id: A4.1
status: READY_FOR_LONG_RUN
lifecycle: ACTIVE
evidence_class: measured_development_and_selection_preparation
scientific_authority: false
execution_permitted: true
provider_instance_id: 47790578
a4_auto_pass_continuation: true
conditional_owner_decisions: [D1_START_CAMPAIGN, D2_OPEN_FINAL]
a3_readiness_binding_uri: control/armindex/a4/a4-readiness-binding-20260819.json
a3_readiness_binding_sha256: 4fb8b8f8d6d80941b0c76116d13c4cfd5199dbcd0d17e59152f0088c54c4f7fd
selection_access_limit: 1
final_accesses_allowed: 0
protected_payloads_allowed: false
previous_goal: docs/goal/A3_TRANSFER_COMPLEMENTARITY_AND_HARNESSOPT_goal_003.md
next_goal: docs/goal/A5_FINAL_CONFIRMATION_goal_001.md
last_material_update: 2026-08-19
next_authorized_action: START_A4_LONG_RUN_WITH_FRESH_ADMISSION_AND_ISOLATED_ATTEMPT_ROOT
---

# Goal 001: A4 production transfer and Selection

## Objective and publication value

Run the frozen A4 production-transfer study on the existing Vast instance,
measure the `FAST`, `BALANCED`, and `DEEP` profiles, evaluate the isolated legal
structured-retrieval transfer, and expose Selection at most once. Preserve
negative, flat, unsupported, and boundary results as publication evidence. The
goal also prepares a complete hash/pointer-only A5 handoff without opening the
Final split.

The goal does not optimize for a positive result. A4 scientific authority is
created only by valid measured receipts and an independent result-integrity
audit; this goal document is not a numeric source of truth.

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

## Work status

| Step | Status | Completion evidence |
|---|---|---|
| Canonical A3/A4 integrity and contract validation | PENDING | validator output and input hash record |
| Fresh provider admission and isolated A4 attempt | PENDING | provider observation, quote, admission, root proof |
| A4 runtime/profile stage and smoke checks | PENDING | stage, runtime, watchdog, and dry-run receipts |
| FAST/BALANCED/DEEP measured execution | PENDING | complete profile coverage and aggregate receipts |
| Legal transfer isolation and unsupported-map evidence | PENDING | transfer receipt with zero protected access |
| One-shot Selection exposure | PENDING | preflight counter and Selection receipt; maximum one |
| A5 hash/pointer-only bundle | PENDING | bundle manifest, evaluator handoff, SHA-256 closure |
| Safe return, audit, projections, and closeout | PENDING | safe-return receipt, result audit, LO handoff |

## Frozen scientific and safety invariants

- Keep the A3-bound primary scope and winner program hashes unchanged:
  `ARM-03`, `ARM-04`, and `ARM-05`; retain `ARM-01` and `ARM-02` only as
  diagnostic context where the A4 contract allows it.
- Use the A4 contract at
  `control/armindex/a4/a4-readiness-contract.v1.json` as the interface for
  profile completeness, commercial licensing, Pareto dimensions, and legal
  transfer isolation.
- Produce exactly `FAST`, `BALANCED`, and `DEEP` profile records. Commercial
  profiles may not include `ARM-03`; the commercial fixed union is `ARM-04` plus
  `ARM-05`.
- Preserve the frozen primary metric `OUT Recall@100`, secondary OUT nDCG
  metrics, and operational latency, throughput, cost, index-size, RAM, and VRAM
  definitions. No post-hoc metric, tie, depth, license, or evaluator change is
  permitted.
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
   controls, runtime bindings, model/license snapshots, A3 winner hashes, A4
   profile contracts, legal-transfer maps, evaluator interfaces, and safe
   export rules. Recompute the bundle and file hashes after staging. Create a
   durable append-only ledger, attempt checkpoint, watchdog, and stop marker.
5. **Run launch checks.** Exercise transport, cancellation, heartbeat,
   checkpoint/resume, worker reaping, protected-field scan, and safe-return dry
   checks. Require an independent launch-integrity review before measured work.
6. **Measure A4.** Run the three complete profiles over the authorized
   development input under the frozen evaluator. Record profile coverage,
   latency/cost/resource aggregates, unsupported mappings, and failures. A
   partial profile is not a result and cannot be combined with another attempt.
7. **Run legal transfer diagnostics.** Evaluate only the isolated legal
   structured-retrieval mapping. Emit explicit supported, mixed, unsupported,
   or stopped-with-evidence states. Do not return raw legal inputs or feed the
   diagnostic back into ArmIndex.
8. **Consume the one-shot preflight and Selection.** After all aggregate-safe
   A4 checks pass, atomically consume the owner-local preflight counter once.
   Perform at most one Selection exposure using the frozen lexicographic rule.
   Record the Selection receipt and finalist hashes. If the preflight counter,
   license check, Pareto frontier, profile completeness, legal isolation, or
   protected boundary fails, do not open Selection.
9. **Prepare A5 handoff.** Build the A5 bundle described in
   `docs/goal/A5_FINAL_CONFIRMATION_goal_001.md`. Keep protected inputs as
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
- legal transfer receipt with explicit unsupported mappings;
- durable ledger/checkpoints, watchdog/heartbeat/reaping receipts, and safe
  return archive/receipt;
- one-shot Selection preflight counter and Selection receipt, with
  `selection_accesses` exactly `0` or `1` and `final_accesses` exactly `0`;
- A5 bundle manifest, evaluator handoff receipt, final-split commitment hash,
  opaque pointer, and SHA-256 manifest;
- result-integrity audit, figure/claim manifest if generated, projections, and
  the long-run handoff.

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
- incompatible partial outputs, irrecoverable provenance ambiguity, or a
  possible protected leak.

## Acceptance and terminal states

Success requires complete A4 profile/transfer coverage, at most one valid
Selection receipt, zero Final access before the conditional D2 receipt, safe
return, independent result audit, hash-closed A5 pointer bundle, and
synchronized projections. A flat or negative result is a valid success if
evidence is complete and claim-limited, but it never triggers D2 when coverage
or audit completeness is missing.

Terminal states are `PASS_A4_SELECTION_AND_A5_HANDOFF`,
`STOP_FAIL_CLOSED_WITH_EVIDENCE`, or `BLOCKED_OWNER_ACTION`. A blocked state
must preserve the same attempt and goal lineage for resume.

## Next action

After A4 closeout, hand off to
`docs/goal/A5_FINAL_CONFIRMATION_goal_001.md`. A5 remains blocked until a
manual `D2_OPEN_FINAL` or this goal's hash-bound conditional D2 receipt exists.
