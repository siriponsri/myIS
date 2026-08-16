---
title: "A2 one-session exact-root recovery, measured AutoIndex, and publication closeout"
phase_id: A2_PER_ARM_AUTOINDEX
task_id: A2.1
status: READY_FOR_MEASURED_EXECUTION
lifecycle: ACTIVE
evidence_class: measured_execution_and_publication_closeout
scientific_authority: true
measured_a2_authorized: true
measurement_authority_uri: control/armindex/a2/measured-authority/a2-goal004-20260816-004.authority.v4.json
candidate_count: 52
matched_candidate_count: 40
conditional_reserve_candidate_count: 12
previous_goal: docs/goal/A2_PER_ARM_AUTOINDEX_goal_003.md
previous_attempt: a2-ap-audit011-v3-full-a2
provider_instance_id: 47790578
previous_remote_root: /opt/myis/a2-ap-audit011-v3-full-a2_on_destroyed_predecessor
last_material_update: 2026-08-16
next_authorized_action: LO_EXECUTE_FROZEN_A2_V4_PARALLEL_MEASUREMENT
---

# Goal 004: one-session A2 closeout

## Objective and publication value

Run the complete A2 path in one orchestrated LO session: bind the Owner-provisioned
fresh provider environment, bind fresh provider and v4 authority
facts, execute the frozen 52-candidate per-arm AutoIndex workload, return
aggregate-safe evidence, and prepare publication figures only after measured
closeout. The goal maximizes publication value through complete candidate
coverage, deterministic provenance, recovery evidence, negative/boundary
findings, and reviewer-readable figures. It must not optimize for a positive
result.

Goal 003 is closed lineage. Do not resume it, reuse its attempt ID, or treat
its pre-stage observation as measured evidence. Goal 004 must create a new
attempt ID, new ledger, new receipts, and a new v4 authority even when the
same provider instance or the exact root is recovered.

## Frozen scientific scope

- Candidate universe: exactly 52 frozen candidates: 40 matched candidates and
  12 conditional reserve candidates.
- Arms: `ARM-01` through `ARM-05`; `ARM-01` and `ARM-02` remain diagnostic and
  non-advancing under the frozen decision rules.
- Primary development outcome: OUT Recall@100. Secondary outcomes are OUT
  nDCG@100 and OUT nDCG@10. Report latency, throughput, charged cost, index
  size, RAM, and VRAM only from validated aggregate receipts.
- Candidate generation, mutation, model changes, selection, final exposure,
  A3, D2, and D3 remain closed.
- Protected qrels, membership, query IDs, per-query outcomes, credentials,
  and raw provider payloads stay Owner-local. Projections receive only
  aggregate-safe values, hashes, counts, safe IDs, and pointers.

## One-session execution sequence

LO executes the numbered sequence without returning to the Owner for routine
engineering choices. Checkpoints are durable records, not new approval gates.

1. **Bind a new attempt.** Read `PLAN.md`, Audit 012, the A2 runbook, and the
   current budget/envelopes. Verify clean pushed code, the frozen bundle
   receipt, candidate lock, and v3 closure. Generate a new attempt ID that is
   different from `a2-ap-audit011-v3-full-a2`; create a new append-only ledger
   and checkpoint namespace.
2. **Bind the fresh provider/root under Owner authority.** Obtain a fresh
   authenticated observation for instance `47790578` and prove process-zero
   state, runtime/model/data identity, all-fee quote, 84-hour total TTL, at
   least 40 hours remaining at admission, and a whole-workload quote at or
   below USD 60. Do not reuse, inspect, or copy the predecessor exact root;
   it belongs to the destroyed predecessor lineage. Record the observation,
   Owner authorization, and isolated new-attempt root nonexistence proof.
   Stage only under `/opt/myis/<new-attempt-id>`.
3. **Stage and adopt.** Build fresh provider binding, admission, input,
   transport, stage, watchdog, lifecycle, and execution-adoption receipts.
   Revalidate all hashes against the clean pushed bundle. Run transport,
   cancellation, reaping, checkpoint, recovery, and safe-return dry checks
   before measured launch. Issue v4 authority only after the new equality
   chain passes; it must bind the new attempt, provider instance, adoption
   receipt, Owner-local commitments, and frozen candidate hashes.
4. **Measure all frozen candidates.** Run the 40 matched candidates in frozen
   order with durable per-candidate checkpoints and process identities. At
   the matched barrier, obtain the fresh reserve admission using the
   deterministic unfinished-work TTL floor of `53848` seconds and the USD 60
   hard stop. Run the 12 conditional reserve candidates only when the frozen
   predicate passes; otherwise emit the required dormant reserve receipt.
   ARM-01 retrieval runs on the bound Vast instance CPU within this same
   coordinated attempt; ARM-02 through ARM-05 use the bound GPUs. Owner-local
   work remains limited to the approved aggregate evaluation transition.
   Complete the Owner-local aggregate evaluation and REP-DEV measurement only
   under the new v4 authority. Never relaunch a candidate with a durable
   result and never mutate the frozen candidate set.
5. **Recover and return safely.** On interruption, use the runbook's
   attempt-scoped PID/start identity, heartbeat, cancellation, reaping, and
   checkpoint rules. Fail closed on drift, duplicate workers, stale identity,
   missing result, protected output, or ambiguous liveness. Pull and validate
   only the allowlisted aggregate-safe artifacts, create the safe-return
   archive/receipt, and verify provider worker teardown before closeout.
6. **Audit and prepare publication artifacts.** After measured closeout only,
   write `docs/long_run/A2_PER_ARM_AUTOINDEX_lo_004_001.md`, refresh the
   read-model, Obsidian, and MLflow projections, and run the focused evidence
   audit. Generate paper and presentation figures from validated aggregate
   receipts into `outputs/figures/armindex/a2-goal004/` and the approved Paper
   projection. Preserve SVG plus publication-size PNG/PDF where supported.
   Do not generate a scientific figure from Goal 003 stop evidence.

## Approved operational acceleration

On 2026-08-16 the Owner approved an expedited operational route for this
Goal. This changes neither the frozen scientific unit nor the required
evidence; it removes duplicated orchestration work.

- A single synthetic canary may exercise transport, worker cancellation and
  reaping, checkpoint/recovery, and safe-return validation, producing one
  hash-bound receipt that identifies each covered check.
- Hash-validated runtime, model, wheelhouse, and input assets already present
  on the bound instance may be reused. A new code bundle, fresh provider
  observation/admission, new attempt root, and new execution-adoption receipt
  remain required whenever their identities change.
- Do not run a separate formal pre-launch audit after the canary. The focused
  validator suite and launch-integrity review are the launch decision record.
- Use five disjoint workers at launch: ARM-01 on the bound instance CPU and
  ARM-02 through ARM-05 on their assigned GPUs. A single coordinator validates
  and commits durable checkpoints and receipts in frozen candidate order.

This acceleration never permits candidate or representation mutation, metric
or evaluator changes, protected-data transfer, unbound asset reuse, skipped
coverage/reserve decisions, or execution beyond the USD 60 hard stop.

## Figure and publication artifact contract

Each figure must answer one reviewer question and state its evidence-honest
takeaway in the title or caption. The minimum set after measured closeout is:

1. candidate coverage and checkpoint/recovery completeness;
2. per-arm OUT Recall@100 with secondary nDCG panels and uncertainty or
   not-computable markers;
3. quality-latency-cost frontier with explicit units and aggregate cost;
4. matched-versus-reserve decision path, including dormant/negative outcomes;
5. appendix audit figure mapping artifacts, hashes, and claim boundaries.

Use direct labels, a colorblind-safe palette, no dual axes, no unexplained
internal codes, and no visual treatment that implies a win when the receipt
does not support one. The same evidence may be adapted for slides by enlarging
labels and moving caveats to notes, but qualifiers must remain intact.

## Required artifacts and validation

The session must preserve the new attempt ledger/checkpoint, provider
observation and admission, exact-root forensic/recovery receipt, stage and
adoption receipts, v4 authority, candidate coverage and reserve receipts,
aggregate result/evaluation receipts, safe-return archive/receipt, provider
closeout evidence, evidence audit, figure manifest, and the LO handoff. Every
artifact must be SHA-256 bound where its schema requires it and must pass the
task-specific validators, focused tests, `git diff --check`, report sync/check,
and figure render/visual QA when figures are created.

## Hard stops and closeout

Stop before measured launch on identity/hash drift, missing fresh provider
evidence, unknown fee, quote above USD 60, TTL below the applicable floor,
nonzero pre-existing workers, ambiguous new-root ownership, protected-data
leak, candidate mutation, duplicate worker, stale heartbeat, incomplete
coverage, or any request to open A3/Selection/Final. If the goal stops, keep
the ledger/checkpoint and write the LO handoff with the exact stop reason and
provider disposition. On successful closeout, report `DESTROY_GPU` or
`OWNER_ACTION_DESTROY` unless a concrete, already-authorized compatible next
action justifies `KEEP_GPU`.

The terminal LO handoff is
`docs/long_run/A2_PER_ARM_AUTOINDEX_lo_004_001.md`. It must state whether
execution completed, the measured/operational evidence created, recovery used,
safe-return/provider disposition, claim boundary, figure paths, and the exact
AP prompt for post-measurement publication review.
