---
title: "A5 frozen final confirmation handoff"
phase_id: A5_FINAL_CONFIRMATION
task_id: A5.1
status: BLOCKED_PROVENANCE_AND_D2
lifecycle: BLOCKED
evidence_class: prepared_final_confirmation_handoff
scientific_authority: false
execution_permitted: false
provider_instance_id: 47790578
required_owner_decision: D2_OPEN_FINAL
conditional_owner_preauthorization: D2_OPEN_FINAL_ON_A4_AUTOMATIC_PASS
automatic_continuation_allowed: true
continuation_mode: CONDITIONAL_AUTO_CONTINUE_MINIMAL_TRANSITIONS
routine_owner_interaction: false
next_phase_handoff_mode: IMMEDIATE_AFTER_PASS_A5
final_query_count: 872
protected_payloads_allowed: false
previous_goal: docs/goal/A4_PRODUCTION_TRANSFER_AND_SELECTION_goal_001.md
next_goal: docs/goal/A6_FULL_DAPFAM_MATERIALIZATION_AND_SCALABILITY_goal_001.md
last_material_update: 2026-08-20
next_authorized_action: WAIT_FOR_CANONICAL_PROVENANCE_MANIFEST_AND_MANUAL_OR_CONDITIONAL_D2
selection_handoff_contract_uri: docs/operations/A4_SELECTION_125_OWNER_HANDOFF_20260820.md
a5_pointer_bundle_schema: myis.armindex-a4-a5-pointer-bundle.v2
publication_priority: TIER_1_REVIEWER_DEFENSIBLE_CONFIRMATION
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

The publication target is tier 1: Final-872 must provide complete two-system
coverage, paired uncertainty, independent integrity review, and a frozen
winner binding that A6 can consume without interpretation drift.

The final split contains exactly 872 queries under the campaign contract. A5
must not change the frozen comparison set, representation program, model
adapter, evaluator, metric, output depth, tie policy, or runtime semantics
after A4 Selection. Its confirmatory comparison is exactly the preregistered
strongest static/common-program comparator and one research champion. The
separate commercial champion is reported from Selection unless it is identical
to one of those two systems; it cannot expand the Final comparison family.

## Required A4 predecessor

Do not proceed until the A4 goal has a canonical closeout with:

- complete FAST/BALANCED/DEEP profile receipts and legal-transfer isolation;
- one valid Selection receipt at most, with finalist/program hashes frozen;
- a frozen two-system Final registry that resolves the preregistered strongest
  comparator and exactly one research champion from the A4 Selection registry;
- `selection_accesses` equal to 0 or 1 and `final_accesses` equal to 0 before
  D2;
- result-integrity audit, safe-return receipt, provider disposition, and
  aggregate-safe projections;
- an A5 bundle manifest whose hashes resolve to clean pushed code and the A4
  closeout receipts.
- the validated Owner-local Selection-125 handoff at
  `docs/operations/A4_SELECTION_125_OWNER_HANDOFF_20260820.md`, including
  paired OUT-vector and evaluator-handoff commitments;
- If continuity is requested, a conditional D2 receipt must bind all of the
  above plus the A4 automatic PASS record, A5 bundle self-hash, exact final
  split commitment, and `owner_conditional_approval: true`.

## A5 bundle contract

Preparation is represented by the hash-only Owner Store bundle at
`04_Owner_Stores/armindex/data-bundle/<bundle-id>/`. The `final-872/sealed/`
marker is `SEALED_PRE_D2`/`PENDING_A5_D2`; it is not Final access and does not
create a finalist or winner. A5 may consume only a validated Selection-125
handoff and must keep the preparation counters at zero until D2 admission.

The bundle is full in provenance and interfaces, but pointer-only for protected
data. Store the repository-safe portion under the campaign evidence/control
conventions and the protected handoff under
`<MYIS_ROOT>/04_Owner_Stores/armindex/a5/<attempt-id>/`.
Its validated schema is `myis.armindex-a4-a5-pointer-bundle.v2`; a v1 bundle is
not sufficient for conditional D2.

While A4 is running, the local preparation artifact is
`control/armindex/a5/a5-pending-a4-selection-template.v1.json`. It is explicitly
`PENDING_A4_SELECTION`, has `execution_permitted: false`, keeps both Selection
and Final counters at zero, and contains no provisional finalist or Final
pointer. It is a bundle interface template only; the PASS pointer bundle is
created only after A4 closeout and validated Selection evidence.

Required bundle members:

1. clean code/runtime bundle, Git commit/tree, dependency and image identity;
2. frozen finalist/program/prompt/representation/model/license/runtime hashes
   and A4 Selection receipt;
3. final evaluator contract, metric contract, split commitment hash, and
   expected count `872`;
4. Owner-local evaluator handoff receipt and opaque evaluator/final-input
   pointers, plus ephemeral token-map hash;
5. safe-export allowlist, provider admission template, watchdog/checkpoint
   schema, resume marker, and attempt-scoped ledger template;
6. complete SHA-256 manifest and bundle self-hash;
7. an explicit claim boundary stating that no Final result exists before the
   A5 measured closeout.

The bundle must also bind the Final registry, the A4-protected A5 budget reserve,
and the aggregate-only statistical plan: paired deltas, 10,000 paired bootstrap
resamples, 95% confidence intervals, rank-biserial effect, win/tie/loss, and
the preregistered correction rule. It cannot add a Final system because it had
an attractive Selection outcome.

The bundle must set `protected_payload_included: false`. Raw qrels, split
membership, query IDs, rankings, per-query outcomes, credentials, raw provider
payloads, model weights, and absolute private paths remain outside Git, chat,
projections, and remote staging. A5 may materialize them only inside the
Owner-local evaluator path after a valid D2 receipt and only through the active protected-data
contract.

## Work status

| Step | Status | Completion evidence |
|---|---|---|
| A4 closeout and Selection receipt verified | PASS | A4 coverage, safe-return, legal-isolation, and result-integrity receipts |
| A5 pointer-only bundle manifest built | FIX_REQUIRED | Structural bundle validation passes; provenance audit `control/armindex/a5/a5-provenance-audit-20260821.json` unresolved |
| D2_OPEN_FINAL recorded by Owner or conditional auto-pass receipt | BLOCKED | D2 cannot open Final until provenance audit passes |
| Fresh provider admission and final stage | BLOCKED | observation, quote, TTL, adoption |
| Final-872 measured confirmation | BLOCKED | complete final coverage receipt |
| Safe return and independent audit | BLOCKED | final safe-return/audit receipts |
| A5 closeout and A6 frozen-winner handoff | BLOCKED | terminal report and projections |

## Minimal continuation policy

After a valid conditional D2 receipt, this goal advances through fresh A5
admission, Final-872, safe return, audit, and the A6 winner handoff without
routine Owner prompts or additional micro-gates. Fix-forward and compatible
checkpoint recovery remain internal engineering actions. The orchestrator
must stop only for a real scientific, protected-data, budget/TTL, provider
identity, evidence-integrity, or Owner-only boundary.

On a valid `PASS_A5_FINAL_CONFIRMATION`, hand off exactly one frozen winner to
A6 immediately. A5 failure or ambiguity closes with evidence and never starts
A6; it must not be repaired by selecting a replacement system.

## Execution flow after D2

1. Validate the A4 closeout, bundle self-hash, finalist freeze, clean Git tree,
   canonical finalist prompt/model/representation provenance, protected
   Final-872 pointer receipt, and the exact D2 decision receipt (manual or
   conditional auto-pass). If any binding differs, stop.
2. Create a new A5 attempt ID and isolated root named
   `/opt/myis/a5-goal001-<UTC>` on instance `47790578`; do not reuse A4
   workers, roots, PIDs, caches, quotes, budget admissions, or partial outputs.
3. Obtain fresh provider identity, all-fee quote, TTL, budget admission,
   runtime verification, and protected-evaluator handoff. Do not infer current
   authority from the A4 quote or historical instance receipts.
4. Materialize the protected final inputs only inside the Owner-local evaluator
   boundary. Export only aggregate-safe metrics, counts, hashes, receipts, and
   safe pointers.
5. Run exactly one frozen final-872 evaluation for each member of the
   two-system Final registry, with durable checkpoints and attempt-scoped
   recovery. Never combine incompatible partial attempts or relaunch a unit
   with a durable valid result.
6. Validate complete coverage, metric/evaluator identity, protected boundary,
   paired-statistics identity, safe return, worker teardown, and provider
   disposition. Generate the independent result-integrity audit and the
   aggregate-safe final comparison/operational table and frozen-winner
   configuration receipt needed by A6.
7. Update projections and create
   `docs/long_run/A5_FINAL_CONFIRMATION_lo_001_001.md`. Hand off exactly one
   frozen winner configuration to A6. Keep `D3_SUBMIT_RELEASE` closed; A6 may
   only materialize that configuration over the full corpus and cannot reopen
   Selection or Final, tune any component, or alter the A5 winner.

## Validation commands

Before a valid D2 receipt, validate the pointer-only bundle and its receipt hashes without
opening the Final split:

```text
rtk pytest -q tests/test_a4_evaluator_selection.py tests/test_a4_selection_runner.py tests/test_a5_pending_handoff_validator.py tests/test_a6_pending_materialization_validator.py tests/test_a6_materialization.py tests/test_a6_preparation_bundle.py
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
duplicate Final access, an expanded or altered two-system Final registry,
incomplete 872 coverage, incompatible partial outputs, or any attempt to
submit release without `D3_SUBMIT_RELEASE`.

## Terminal states

Before a valid manual or conditional D2 receipt this goal remains
`BLOCKED_OWNER_D2`. After that receipt it may terminate as
`PASS_A5_FINAL_CONFIRMATION`, `STOP_FAIL_CLOSED_WITH_EVIDENCE`, or
`BLOCKED_OWNER_ACTION`. A successful A5 result is confirmatory evidence only;
post-confirmatory full-corpus materialization proceeds only through A6's
separate admission, while publication/release remains governed by
`D3_SUBMIT_RELEASE` and A7.
