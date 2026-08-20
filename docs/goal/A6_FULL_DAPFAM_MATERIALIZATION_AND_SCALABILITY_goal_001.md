---
title: "A6 post-confirmatory full-DAPFAM materialization and scalability"
phase_id: A6_FULL_DAPFAM_MATERIALIZATION_AND_SCALABILITY
task_id: A6.1
status: BLOCKED_A5_CLOSEOUT
lifecycle: BLOCKED
evidence_class: post_confirmatory_operational_scalability
scientific_authority: false
execution_permitted: false
required_predecessor_terminal_state: PASS_A5_FINAL_CONFIRMATION
required_owner_decision: none
d3_required: false
protected_payloads_allowed: false
full_corpus_owner_local_only: true
provider_instance_id: 47790578
previous_goal: docs/goal/A5_FINAL_CONFIRMATION_goal_001.md
next_goal: docs/goal/A7_PUBLICATION_AND_RELEASE_goal_001.md
last_material_update: 2026-08-19
next_authorized_action: WAIT_FOR_VALID_A5_CLOSEOUT_AND_FROZEN_MATERIALIZATION_TARGET
a6_winner_binding_schema: myis.armindex-a6-a5-winner-binding.v1
a6_attempt_admission_schema: myis.armindex-a6-attempt-admission.v1
continuation_mode: CONTINUE_AFTER_PASS_A5_WITH_FRESH_ADMISSION
routine_owner_interaction: false
publication_priority: TIER_1_REVIEWER_DEFENSIBLE_SCALABILITY
---

# Goal 001: A6 full-DAPFAM materialization and scalability

## Objective and publication value

Materialize exactly one configuration frozen by the valid A5 closeout across
the approved complete DAPFAM corpus. A6 produces reproducible operational
evidence that the confirmed configuration can be rendered, embedded or indexed
as applicable, checkpointed, recovered, and safely returned at corpus scale.

The publication target is tier 1 operational evidence: complete coverage,
determinism, resource/cost/latency accounting, recovery lineage, failure
taxonomy, independent audit, and figures/tables that never overclaim quality.

This is deliberately post-confirmatory. Its publication contribution is
deployment and scalability evidence: source coverage, family/document/chunk/
representation counts, resource use, cost, throughput, latency, index size,
determinism, and a transparent failure taxonomy. It is not another
retrieval-quality experiment, an external-generalization study, or an
opportunity to improve the system after observing A5.

## Starting state and frozen authority

The pre-A5 Owner Store bundle records the canonical DAPFAM source manifest and
full-corpus inventory (`45,336` rows) by hash/pointer only. Its A6 marker is
`SOURCE_HASHED`/`PENDING_A5_FROZEN_WINNER`; preparation does not materialize the
corpus, select a winner, open qrels, or authorize execution. A6 remains
`execution_permitted: false` until `PASS_A5_FINAL_CONFIRMATION` and a fresh
admission/root are available.

The A6/A7 phase amendment is the authority for this routing change:
`control/armindex/a6/a6-a7-phase-amendment.v1.json`. The executable A6
interface is
`control/armindex/a6/a6-full-dapfam-execution-contract.v1.json`.

A6 remains blocked until a valid A5 terminal closeout supplies one explicit
materialization target. That target must be selected and frozen by A5, not by
A6. It must bind all of the following exact A5-derived hashes:

1. representation program;
2. prompt or encoder prefix;
3. model adapter and license snapshot;
4. chunking policy;
5. retrieval and index configuration;
6. runtime lock and code revision;
7. A5 result-integrity audit, safe-return, and final registry receipts.

If A5 does not create one unambiguous, hash-closed target, A6 closes
fail-closed with the reason and preserves A5 evidence. It never resolves a
tie or selects a replacement configuration.

The checked-in preparation interface is
`control/armindex/a6/a6-pending-a5-closeout-template.v1.json`. It has no winner,
corpus hash, Owner Store path, or execution permission. It can be validated
locally while A4/A5 run, but cannot be turned into an A6 attempt without the
complete A5 binding and a new A6 admission. The post-A5 code validators require
`myis.armindex-a6-a5-winner-binding.v1` and
`myis.armindex-a6-attempt-admission.v1`; these bind exactly one winner and
forbid stale runtime reuse.

## Non-adaptive scientific boundary

The following actions are forbidden in A6:

- changing the A5 winner or selecting a different profile;
- prompt, representation, chunking, index, retrieval, or model tuning;
- model training, adapters, distillation, or weight changes;
- accessing, reopening, rerunning, or incrementing Selection or Final;
- access to qrels, split membership, protected query identities, rankings, or
  per-query outcomes;
- reporting retrieval quality, generalization, or full-corpus superiority over
  a baseline from this single-configuration materialization.

A6 may report only that the frozen configuration was or was not materialized
at the specified corpus scale under the recorded operational conditions. A
full-corpus comparison claim requires a distinct preregistered paired study;
it is outside this goal.

## Work status

| Step | Status | Completion evidence |
|---|---|---|
| A5 terminal/audit/safe-return bindings validated | BLOCKED | hash-verified predecessor receipt set |
| One materialization target frozen by A5 | BLOCKED | target registry and exact configuration hashes |
| Fresh A6 budget, provider, TTL, and health admission | BLOCKED | A6-specific admission receipt and fresh-attempt validator |
| Owner-local full-corpus source and safe-export manifest frozen | BLOCKED | source hash and protected-boundary scan |
| Isolated materialization run completed or bounded failure closed | BLOCKED | coverage/checkpoint/failure receipts |
| Aggregate-safe EDA, figures, and independent integrity audit | BLOCKED | validated metric and audit package |
| A7 publication handoff prepared | BLOCKED | aggregate-safe A6 closeout bundle |

## Minimal continuation policy

A6 is the immediate post-A5 continuation, not a new exploratory branch. After
the validated A5 frozen-winner binding is available, admit one fresh A6 root
and continue without a routine Owner prompt or extra gate. Same-instance reuse
is operational only: provider identity, quote, budget, TTL, health, runtime,
and attempt root must all be fresh.

Fix-forward is limited to operational recovery inside the isolated A6 attempt.
Stop only for winner/configuration drift, source ambiguity, protected-data
exposure, unknown budget/TTL, provider/process identity ambiguity,
incompatible partial outputs, or failed integrity/safe-export checks. A6 never
reopens Selection or Final and never changes the A5 winner.

## Execution flow

1. **Verify predecessor integrity.** Validate the A5 terminal state, A5
   result-integrity audit, safe return, exactly one frozen materialization
   target, and all target component hashes. Verify that Selection and Final
   counters are historical facts only and that A6 has no operation capable of
   changing either.
2. **Admit the A6 workload.** Create a new A6 attempt ID and an isolated
   Owner Store root at
   `<MYIS_ROOT>/04_Owner_Stores/armindex/a6/<attempt-id>/` and a remote root
   `/opt/myis/a6-goal001-<UTC>`. Obtain a fresh
   provider identity, all-fee quote, whole-workload budget admission, TTL,
   runtime/GPU/CPU/disk/RAM health receipt, watchdog, checkpoint, and safe
   return plan. Instance `47790578` may be retained and reused only after A5
   closes and this fresh A6 admission passes. Do not use an A4/A5 quote, root,
   worker, cache, PID, partial output, or budget admission as A6 authority.
3. **Freeze source and execution inputs.** Materialize the approved full
   DAPFAM source only inside the Owner Store. Freeze its source hash, the A5
   target registry, code/runtime/configuration hashes, output schema, resource
   sampling interval, retry policy, failure taxonomy, and aggregate-safe
   export allowlist. Run a protected-field scan before staging.
4. **Run the frozen materialization.** Execute the frozen representation and
   index procedure with attempt-scoped checkpoints. Capture coverage by
   documents, families, chunks, and representations; p50/p95/p99 latency;
   throughput; peak RAM/VRAM; index size; cost; determinism hashes; failures;
   and recovery lineage. Recover engineering faults only through compatible
   checkpoints. Never merge incompatible partial output.
5. **Safe return.** Keep raw corpus, document/family IDs, intermediate
   representations, index shards, model payloads, and provider payloads in
   the Owner Store. Return only allowlisted aggregate metrics, counts, hashes,
   manifests, receipts, figures, and failure taxonomy to the repository.
6. **Audit and close.** Run an independent A6 result-integrity audit that
   verifies frozen A5 binding, source/configuration hashes, coverage accounting,
   safe return, worker teardown, resource/cost receipt, determinism evidence,
   and claim boundary. Produce aggregate-safe EDA CSVs and figures. Update
   projections, commit/push the resulting safe artifacts, and prepare the A7
   evidence pointer set. `D3_SUBMIT_RELEASE` remains closed.

## Required artifacts

Owner Store only:

- frozen full-corpus source and input inventory;
- raw representation/index outputs and checkpoint lineage;
- attempt-scoped worker logs, resource samples, provider evidence, and
  protected failure details;
- A5 target materialization inputs and opaque source pointers.

Repository-safe outputs:

- A6 admission, source/configuration, safe-return, teardown, and integrity
  audit receipts;
- aggregate coverage/resource/cost/determinism/failure CSVs;
- aggregate-safe scalability and failure figures with figure-claim manifests;
- hash-only A7 handoff manifest and a claim-boundary statement.

All aggregate-safe outputs must be provenance-hash bound and scanned for
protected fields before Git, Paper, Brain, Obsidian, MLflow, Dashboard, or
chat receives them.

## Recovery and hard stops

Permitted fix-forward actions are operational only: batch size, concurrency,
timeouts, retry policy, checkpoint interval, process supervision, upload
chunking, cache location inside the isolated A6 root, or restart from a
compatible checkpoint. Record every material recovery event.

Stop before processing on A5 configuration/hash drift, missing or ambiguous
A5 materialization target, corpus source/hash ambiguity, an unverified budget
or quote, insufficient TTL, provider/process identity ambiguity, a protected
data leak, an attempt to tune/reselect/reopen evaluation, incompatible partial
outputs, or a failed protected-field scan. Preserve evidence and close with a
bounded operational finding; do not substitute another target.

## Validation and terminal states

Before launch, validate the amendment, A6 execution contract, target binding,
budget admission, source manifest, and export allowlist. After execution,
validate complete accounting, determinism, safe return, teardown, and the
independent result-integrity audit. Also run the focused A5/A6 contract suite
and `rtk git diff --check` before closeout:

```text
rtk pytest -q tests/test_a5_pending_handoff_validator.py tests/test_a6_pending_materialization_validator.py tests/test_a6_materialization.py tests/test_a6_preparation_bundle.py
```

Terminal states are `PASS_A6_FULL_DAPFAM_MATERIALIZATION`,
`STOP_A6_WITH_OPERATIONAL_EVIDENCE`, or `BLOCKED_OWNER_ACTION`. A6 never
opens D3 automatically. A7 can begin only after `D3_SUBMIT_RELEASE` and the
validated aggregate-safe evidence set from A0 through A6.
