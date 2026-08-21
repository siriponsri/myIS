---
phase_id: A4_PRODUCTION_TRANSFER_AND_SELECTION
task_id: A4.1
attempt_id: a4-goal001-20260821T071350Z-sel01
status: ACTIVE_MEASURED_EXECUTION
evidence_class: live_execution_checkpoint
selection_accesses: 0
final_accesses: 0
protected_payload_included: false
---

# A4 Selection-125 live checkpoint

This aggregate-safe checkpoint records the fresh A4 Selection-125 execution
currently running on authorized Vast instance `47790578`. It is not a result
report and must not be used as Selection or Final evidence until the workers,
safe-return, evaluator handoff, and independent integrity audit pass.

## Fresh attempt binding

- Attempt: `a4-goal001-20260821T071350Z-sel01`
- Remote root: `/opt/myis/a4-goal001-20260821T071350Z-sel01`
- Seed root: `/opt/myis/a4-goal001-20260819T180000Z-a4x12` (immutable retrieval
  assets only)
- Selection scope: `125` queries; canonical OUT evaluator denominator remains
  `90` eligible units
- Parent split hash:
  `33a1818ff3c00775d43951182fdf769255c8ebfc591de183df4fbfdd3b039dc6`
- Selection and Final counters remain `0/0`.

## Active profiles

The fresh root launched exactly four isolated, tagged workers:

| Profile | Scope | State at checkpoint |
|---|---|---|
| `FAST` | commercial-capable | CPU/model/index work active; no completion receipt yet |
| `BALANCED` | commercial-capable | CPU/model/index work active; no completion receipt yet |
| `DEEP` | commercial-capable | CPU/model/index work active; no completion receipt yet |
| `ARM-03_RESEARCH_REFERENCE` | research-only | CPU/GPU model/index work active; no completion receipt yet |

No `ranking-package.json` is treated as valid until its hash-bound request,
scope, coverage, and completion receipt validate. The immutable `x02` outputs
are excluded and cannot be mixed into this attempt.

## Parallel readiness work

Local A5 pending handoff validation passed with execution disabled, Final-872
bound to `872`, and counters `0/0`. Local A6 pending materialization validation
passed with execution disabled and the full DAPFAM corpus remaining
pointer-only. These are readiness artifacts, not measured A5/A6 evidence.

The focused A4/A5/A6 contract suite passed (`37` tests). Brain handoff notes
were updated with the fresh admission/stage and active-worker lineage.

## Next sequential gates

1. Complete all four fresh A4 packages and verify coverage/hash receipts.
2. Safe-return packages and run the Owner-local paired evaluator (`125` scope,
   `90` OUT metric units).
3. Freeze and consume Selection-125 exactly once; audit A4 and prepare A5.
4. Run A5 Final-872 only after a valid Selection handoff and conditional D2.
5. Run A6 full DAPFAM only after `PASS_A5_FINAL_CONFIRMATION` and one frozen
   winner.

No claim of a winner, Selection superiority, Final-872 performance, A6
scalability, or publication result is supported by this live checkpoint.
