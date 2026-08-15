---
title: "A2 one-session exact-root recovery, measured AutoIndex, and publication closeout"
phase_id: A2_PER_ARM_AUTOINDEX
task_id: A2.1
status: READY_FOR_LO_ONE_SESSION
lifecycle: ACTIVE
evidence_class: measured_execution_and_publication_closeout
scientific_authority: false
measured_a2_authorized: false
candidate_count: 52
matched_candidate_count: 40
conditional_reserve_candidate_count: 12
previous_goal: docs/goal/A2_PER_ARM_AUTOINDEX_goal_003.md
previous_attempt: a2-ap-audit011-v3-full-a2
provider_instance_id: 47782993_or_fresh_fallback
previous_remote_root: /opt/myis/a2-ap-audit011-v3-full-a2
last_material_update: 2026-08-15
next_authorized_action: LO_EXECUTE_GOAL_004
---

# Goal 004: one-session A2 closeout

## Objective and publication value

Run the complete A2 path in one orchestrated LO session: recover or replace
the stopped pre-authority environment, bind fresh provider and v3 authority
facts, execute the frozen 52-candidate per-arm AutoIndex workload, return
aggregate-safe evidence, and prepare publication figures only after measured
closeout. The goal maximizes publication value through complete candidate
coverage, deterministic provenance, recovery evidence, negative/boundary
findings, and reviewer-readable figures. It must not optimize for a positive
result.

Goal 003 is closed lineage. Do not resume it, reuse its attempt ID, or treat
its pre-stage observation as measured evidence. Goal 004 must create a new
attempt ID, new ledger, new receipts, and a new v3 authority even when the
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
2. **Recover the provider/root under Owner authority.** Obtain a fresh
   authenticated observation for instance `47782993` and prove process-zero
   state, runtime/model/data identity, all-fee quote, 84-hour total TTL, at
   least 40 hours remaining at admission, and a whole-workload quote at or
   below USD 50. Inspect only aggregate-safe metadata for
   `/opt/myis/a2-ap-audit011-v3-full-a2`: it must be a non-symlink directory,
   have no active worker, and have no evidence of an active owner. Record the
   observation and Owner authorization. Then clear only that exact root and
   record the path, metadata, pre-clear hash/manifest, and post-clear proof.
   Do not inspect or copy protected contents. If any check is ambiguous, do
   not clear the root: use the Owner-approved destroy fallback and provision a
   replacement instance/root, then bind it under the new attempt.
3. **Stage and adopt.** Build fresh provider binding, admission, input,
   transport, stage, watchdog, lifecycle, and execution-adoption receipts.
   Revalidate all hashes against the clean pushed bundle. Run transport,
   cancellation, reaping, checkpoint, recovery, and safe-return dry checks
   before measured launch. Issue v3 authority only after the new equality
   chain passes; it must bind the new attempt, provider instance, adoption
   receipt, Owner-local commitments, and frozen candidate hashes.
4. **Measure all frozen candidates.** Run the 40 matched candidates in frozen
   order with durable per-candidate checkpoints and process identities. At
   the matched barrier, obtain the fresh reserve admission using the
   deterministic unfinished-work TTL floor of `53848` seconds and the USD 50
   hard stop. Run the 12 conditional reserve candidates only when the frozen
   predicate passes; otherwise emit the required dormant reserve receipt.
   Complete the Owner-local aggregate evaluation and REP-DEV measurement only
   under the new v3 authority. Never relaunch a candidate with a durable
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
adoption receipts, v3 authority, candidate coverage and reserve receipts,
aggregate result/evaluation receipts, safe-return archive/receipt, provider
closeout evidence, evidence audit, figure manifest, and the LO handoff. Every
artifact must be SHA-256 bound where its schema requires it and must pass the
task-specific validators, focused tests, `git diff --check`, report sync/check,
and figure render/visual QA when figures are created.

## Hard stops and closeout

Stop before measured launch on identity/hash drift, missing fresh provider
evidence, unknown fee, quote above USD 50, TTL below the applicable floor,
nonzero pre-existing workers, ambiguous exact-root ownership, protected-data
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
