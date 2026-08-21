---
phase_id: A4_PRODUCTION_TRANSFER_AND_SELECTION
task_id: A4.1
attempt_id: a4-goal001-20260821T071350Z-sel01
status: PASS_A4_SELECTION_CLOSEOUT
evidence_class: live_execution_checkpoint
selection_accesses: 1
final_accesses: 0
protected_payload_included: false
---

# A4 Selection-125 closeout checkpoint

This aggregate-safe checkpoint records the fresh A4 Selection-125 execution
completed on authorized Vast instance `47790578`. This checkpoint is an
aggregate-safe pointer to the measured closeout; the canonical coverage,
safe-return, legal-isolation, and result-integrity receipts are authoritative.

## Fresh attempt binding

- Attempt: `a4-goal001-20260821T071350Z-sel01`
- Remote root: `/opt/myis/a4-goal001-20260821T071350Z-sel01`
- Seed root: `/opt/myis/a4-goal001-20260819T180000Z-a4x12` (immutable retrieval
  assets only)
- Selection scope: `125` queries; canonical OUT evaluator denominator remains
  `90` eligible units
- Parent split hash:
  `33a1818ff3c00775d43951182fdf769255c8ebfc591de183df4fbfdd3b039dc6`
- Selection and Final counters are `1/0`.

## Measured profiles

The fresh root launched exactly four isolated, tagged workers:

| Profile | Scope | State at checkpoint |
|---|---|---|
| `FAST` | commercial-capable | `125/125`, deterministic, zero recorded failures |
| `BALANCED` | commercial-capable | `125/125`, deterministic, zero recorded failures |
| `DEEP` | commercial-capable | `125/125`, deterministic, zero recorded failures |
| `ARM-03_RESEARCH_REFERENCE` | research-only | `125/125`, deterministic, zero recorded failures |

No `ranking-package.json` is treated as valid until its hash-bound request,
scope, coverage, and completion receipt validate. The immutable `x02` outputs
are excluded and cannot be mixed into this attempt.

## Parallel readiness work

Local A5 pending-template validation passed with execution disabled, Final-872
bound to `872`, and its unopened template counters `0/0`. The measured A4
Selection counter is `1` and Final remains `0`. Local A6 pending materialization validation
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

Selection has been consumed exactly once (`selection_accesses=1`) over the
aggregate OUT evaluator population (`90` eligible units); `final_accesses=0`.
The A4 result-integrity audit and safe-return receipts pass. Final-872 and A6
remain unopened; A5 is currently held by the independent provenance audit in
`control/armindex/a5/a5-provenance-audit-20260821.json`.
