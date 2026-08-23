---
title: "A6 post-confirmatory full-DAPFAM materialization and scalability"
phase_id: A6_FULL_DAPFAM_MATERIALIZATION_AND_SCALABILITY
task_id: A6.1
status: PASS_A6_FULL_DAPFAM_MATERIALIZATION
lifecycle: CLOSED
evidence_class: post_confirmatory_operational_scalability
scientific_authority: true
execution_permitted: true
required_predecessor_terminal_state: PASS_A5_FINAL_CONFIRMATION
required_owner_decision: NONE_ROUTINE_ENGINEERING; A6_CEILING_USD_20_BOUND
d3_required: false
protected_payloads_allowed: false
full_corpus_owner_local_only: true
provider_instance_id: 48367896
provider_instance_status: ACTIVE_VERIFIED_A6_INSTANCE
fresh_provider_instance_required: false
previous_goal: docs/goal/A5_FINAL_CONFIRMATION_goal_001.md
next_goal: docs/goal/A7_SEVEN_LAYER_RETRIEVAL_DIAGNOSIS_goal_001.md
last_material_update: 2026-08-23
next_authorized_action: PREPARE_A7_SEVEN_LAYER_DIAGNOSIS_FROM_HASH_BOUND_A6_HANDOFF
a6_winner_binding_schema: myis.armindex-a6-a5-winner-binding.v1
a6_attempt_admission_schema: myis.armindex-a6-attempt-admission.v1
continuation_mode: CONTINUE_AFTER_PASS_A5_WITH_FRESH_ADMISSION
routine_owner_interaction: false
publication_priority: TIER_1_REVIEWER_DEFENSIBLE_FULL_CORPUS_EVALUATION_AND_FROZEN_POOL
---

# Goal 001: A6 full-DAPFAM materialization and scalability

## Objective and publication value

Run exactly one configuration frozen by the valid A5 closeout across full
DAPFAM. A6 creates the deterministic ARM-03 Top-200 family pool for the
committed 1,247 queries, safe-returns the complete claim-bearing pool to Owner
Store, and evaluates it locally with the Owner-local qrels and population view.

The required metric package is Recall@10/20/50/100/200 and nDCG@10/100,
reported separately for ALL, IN, and OUT. It also records document/family/
chunk/representation counts, p50/p95/p99 latency, throughput, RAM/VRAM,
index size, cost, determinism, checkpoints, and failure taxonomy.

This is post-confirmatory and non-adaptive: the full-corpus metrics characterize
the frozen configuration and create an immutable candidate universe for A7/A8.
They cannot choose a new winner, reopen Selection/Final, tune any component,
or create an external-generalization or paired-baseline superiority claim.

## Starting state and frozen authority

The pre-A5 Owner Store bundle recorded the canonical DAPFAM source manifest and
full-corpus inventory (`45,336` rows) by hash/pointer only. That preparation
was superseded by the hash-bound `full09` attempt after
`PASS_A5_FINAL_CONFIRMATION`; it did not select a winner or expose qrels on the
provider. The completed A6 evidence is now authoritative for the frozen pool,
while all protected evaluation payloads remain Owner-local.

The A6-A8 phase amendment is the authority for this routing change:
`control/armindex/a6/a6-a8-phase-amendment.v3.json`. The executable A6
interface is `control/armindex/a6/a6-frozen-pool-execution-contract.v2.json`.
The numeric phase ceiling is USD 20 in
`control/budgets/armindex-a6-frozen-pool.v1.json`.

A6 is admitted only after the valid A5 terminal closeout supplies one explicit
materialization target and a fresh A6 admission binds the long run. That target
must be selected and frozen by A5, not by A6. It must bind all of the
following exact A5-derived hashes:

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
- qrels, split membership, protected identifiers, or per-query evaluation
  outcomes on the provider; these may be read only in Owner Store after safe
  return to calculate the specified aggregate metrics;
- export of rankings, per-query outcomes, qrels, membership, raw IDs, or model
  and provider payloads outside Owner Store;
- a new winner, a comparative full-corpus superiority claim, or feedback from
  the metrics into A4/A5 decisions.

## Work status (updated 2026-08-23)

| Step | Status | Completion evidence |
|---|---|---|
| A5 terminal/audit/safe-return bindings validated | PASS | hash-verified predecessor receipt set |
| One materialization target frozen by A5 | PASS | ARM-03 frozen winner binding |
| Numeric A6 budget authority | COMPLETE | USD 20 phase ceiling and stop-at-ceiling control |
| Fresh provider, TTL, runtime, and health admission | PASS | fresh admission, runtime, health, and isolated-root receipts |
| Full corpus/query input and safe-export manifest frozen | PASS | exact source/query hashes and protected-field scan |
| Isolated ARM-03 full-corpus materialization | PASS | `a6-goal001-20260823T052423Z-full09`; `45,336/45,336` coverage, worker teardown, and safe-return manifest |
| Top-200 pool generation and deep-ranking export | PASS | full09 completion marker, 1,247 x 200 pool, and matching SHA-256 manifest |
| Owner-local ALL/IN/OUT evaluation | PASS | Owner-local receipt with 1,247 queries, 49,869 relation rows, and aggregate-only curves |
| Aggregate-safe EDA and independent integrity audit | PASS | `control/armindex/a6/a6-result-integrity-audit-20260823.json`; independent hash, coverage, teardown, and claim-boundary checks passed |
| Provider disposition | OWNER_CONFIRMED_INSTANCE_DESTROYED | `control/armindex/a6/a6-provider-disposition-20260823.json`; Owner confirmed Vast instance `48367896` destroyed after safe return and teardown |
| A7/A8 immutable handoff prepared | PASS | `control/armindex/a6/a6-frozen-pool-authority-20260823.json` and `control/armindex/a6/a6-a7-handoff-20260823.json` |

## Minimal continuation policy

A6 is the immediate post-A5 continuation, not a new exploratory branch. The
fresh USD 20 admission and isolated `full09` root are the active authority.
Same-instance reuse remains operational only: provider identity, quote, budget,
TTL, health, runtime, and attempt root are bound to this attempt.

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
   return plan. Instance `48367896` may be reused only after explicit Owner A6
   approval and this fresh A6 admission passes. Do not use an A4/A5 quote, root,
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
opens D3 automatically. A7 can begin only after a valid hash-bound A6 frozen
diagnostic bundle and independent integrity audit. A8 remains gated by
`D3_SUBMIT_RELEASE` and the validated aggregate-safe evidence set from A0
through A7.
