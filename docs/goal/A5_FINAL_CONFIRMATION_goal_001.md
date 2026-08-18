---
title: "A5 frozen final confirmation handoff"
phase_id: A5_FINAL_CONFIRMATION
task_id: A5.1
status: BLOCKED_OWNER_D2
lifecycle: BLOCKED
evidence_class: prepared_final_confirmation_handoff
scientific_authority: false
execution_permitted: false
provider_instance_id: 47790578
required_owner_decision: D2_OPEN_FINAL
conditional_owner_preauthorization: D2_OPEN_FINAL_ON_A4_AUTOMATIC_PASS
automatic_continuation_allowed: true
final_query_count: 872
protected_payloads_allowed: false
previous_goal: docs/goal/A4_PRODUCTION_TRANSFER_AND_SELECTION_goal_001.md
next_goal: A6_PUBLICATION_AND_RELEASE
last_material_update: 2026-08-19
next_authorized_action: WAIT_FOR_MANUAL_OR_CONDITIONAL_D2_AND_VALIDATE_A4_HANDOFF
---

# Goal 001: A5 final confirmation

## Objective and boundary

Run one frozen confirmation over the final split only after `D2_OPEN_FINAL` is
recorded by the Owner or by the Owner's explicit conditional pre-authorization
receipt emitted after an automatic A4 PASS. This document is an executable
handoff specification,
not permission to open Final. It may be used for aggregate-safe bundle
validation and recovery planning while blocked, but it must not start a provider
workload or inspect protected Final membership.

The final split contains exactly 872 queries under the campaign contract. A5
must not change the finalist, representation program, model adapter, evaluator,
metric, output depth, tie policy, or runtime semantics after A4 Selection.

## Required A4 predecessor

Do not proceed until the A4 goal has a canonical closeout with:

- complete FAST/BALANCED/DEEP profile receipts and legal-transfer isolation;
- one valid Selection receipt at most, with finalist/program hashes frozen;
- `selection_accesses` equal to 0 or 1 and `final_accesses` equal to 0 before
  D2;
- result-integrity audit, safe-return receipt, provider disposition, and
  aggregate-safe projections;
- an A5 bundle manifest whose hashes resolve to clean pushed code and the A4
  closeout receipts.
- If continuity is requested, a conditional D2 receipt must bind all of the
  above plus the A4 automatic PASS record, A5 bundle self-hash, exact final
  split commitment, and `owner_conditional_approval: true`.

## A5 bundle contract

The bundle is full in provenance and interfaces, but pointer-only for protected
data. Store the repository-safe portion under the campaign evidence/control
conventions and the protected handoff under
`<MYIS_ROOT>/04_Owner_Stores/armindex/a5/<attempt-id>/`.

Required bundle members:

1. clean code/runtime bundle, Git commit/tree, dependency and image identity;
2. frozen finalist/program/model/license hashes and A4 Selection receipt;
3. final evaluator contract, metric contract, split commitment hash, and
   expected count `872`;
4. Owner-local evaluator handoff receipt, opaque final-input pointer, and
   ephemeral token-map hash;
5. safe-export allowlist, provider admission template, watchdog/checkpoint
   schema, resume marker, and attempt-scoped ledger template;
6. complete SHA-256 manifest and bundle self-hash;
7. an explicit claim boundary stating that no Final result exists before the
   A5 measured closeout.

The bundle must set `protected_payload_included: false`. Raw qrels, split
membership, query IDs, rankings, per-query outcomes, credentials, raw provider
payloads, model weights, and absolute private paths remain outside Git, chat,
projections, and remote staging. A5 may materialize them only inside the
Owner-local evaluator path after a valid D2 receipt and only through the active protected-data
contract.

## Work status

| Step | Status | Completion evidence |
|---|---|---|
| A4 closeout and Selection receipt verified | BLOCKED | A4 result/audit hashes |
| A5 pointer-only bundle manifest built | PENDING | bundle and self-hash |
| D2_OPEN_FINAL recorded by Owner or conditional auto-pass receipt | BLOCKED | decision receipt |
| Fresh provider admission and final stage | BLOCKED | observation, quote, TTL, adoption |
| Final-872 measured confirmation | BLOCKED | complete final coverage receipt |
| Safe return and independent audit | BLOCKED | final safe-return/audit receipts |
| A5 closeout and A6 handoff | BLOCKED | terminal report and projections |

## Execution flow after D2

1. Validate the A4 closeout, bundle self-hash, finalist freeze, clean Git tree,
   and the exact D2 decision receipt (manual or conditional auto-pass). If any
   binding differs, stop.
2. Create a new A5 attempt ID and isolated root on instance `47790578`; do not
   reuse A4 workers, roots, PIDs, caches, or partial outputs.
3. Obtain fresh provider identity, all-fee quote, TTL, budget admission,
   runtime verification, and protected-evaluator handoff. Do not infer current
   authority from the A4 quote or historical instance receipts.
4. Materialize the protected final inputs only inside the Owner-local evaluator
   boundary. Export only aggregate-safe metrics, counts, hashes, receipts, and
   safe pointers.
5. Run exactly one frozen final-872 evaluation with durable checkpoints and
   attempt-scoped recovery. Never combine incompatible partial attempts or
   relaunch a unit with a durable valid result.
6. Validate complete coverage, metric/evaluator identity, protected boundary,
   safe return, worker teardown, and provider disposition. Generate the
   independent result-integrity audit.
7. Update projections and create
   `docs/long_run/A5_FINAL_CONFIRMATION_lo_001_001.md`. Keep `D3_SUBMIT_RELEASE`
   closed; A6 publication/release cannot start from this goal.

## Validation commands

Before a valid D2 receipt, validate the pointer-only bundle and its receipt hashes without
opening the Final split:

```text
rtk pytest -q tests/test_a4_readiness.py
rtk git diff --check
```

After a valid D2 receipt, add the repository's schema/evidence validators for the final
authority, evaluator handoff, complete-coverage receipt, safe-return receipt,
and result-integrity audit. A5 is not complete until all 872 final units are
accounted for and the aggregate-safe return is independently hash-validated.

## Hard stops

Stop before any Final access if D2 is absent, malformed, stale, or inconsistent
with the campaign. A conditional receipt is valid only when A4 automatic PASS
is complete and independently audited; it cannot be created from a partial or
unaudited result. Also stop on finalist or evaluator drift, protected-data
leak, unknown/over-cap budget, insufficient TTL, provider identity drift,
duplicate Final access, incomplete 872 coverage, incompatible partial outputs,
or any attempt to submit release without `D3_SUBMIT_RELEASE`.

## Terminal states

Before a valid manual or conditional D2 receipt this goal remains
`BLOCKED_OWNER_D2`. After that receipt it may terminate as
`PASS_A5_FINAL_CONFIRMATION`, `STOP_FAIL_CLOSED_WITH_EVIDENCE`, or
`BLOCKED_OWNER_ACTION`. A successful A5 result is confirmatory evidence only;
publication/release remains governed by `D3_SUBMIT_RELEASE` and A6.
