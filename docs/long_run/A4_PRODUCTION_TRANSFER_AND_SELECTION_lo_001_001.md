---
phase_id: A4_PRODUCTION_TRANSFER_AND_SELECTION
task_id: A4.1
attempt_id: a4-goal001-20260819T180000Z-a4x12
status: CLOSED_WITH_EVIDENCE_SELECTION_HANDOFF_BLOCKED
evidence_class: measured_development_and_selection_preparation
selection_accesses: 0
final_accesses: 0
protected_payload_included: false
---

# A4 Production Transfer and Selection: Long-Run Closeout

## Scope

This closeout records the completed A4 production-transfer measurements on
Vast instance `47790578`. It is an aggregate-safe projection derived from the
Owner Store receipts. It does not open Selection or Final and is not a source
of protected query, membership, qrels, ranking, or per-query evidence.

## Measured coverage

All four authorized HDEV measurements completed `100/100` units with zero
reported failures and deterministic replay markers. The three commercial
profiles remain separate from the research-only ARM-03 reference.

| System | License scope | OUT Recall@100 | OUT nDCG@100 | OUT nDCG@10 | p50 ms | p95 ms | p99 ms | QPS | Cost USD |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| FAST | commercial-capable | 0.3458333 | 0.2927644 | 0.2493370 | 487.24 | 1524.23 | 1571.27 | 0.02831 | 0.633451 |
| BALANCED | commercial-capable | 0.3826389 | 0.3287772 | 0.2784424 | 732.51 | 1771.50 | 2348.53 | 0.01134 | 1.581839 |
| DEEP | commercial-capable | 0.3826389 | 0.3287772 | 0.2784424 | 314.43 | 1637.75 | 1817.28 | 0.01518 | 1.181535 |
| ARM-03 research reference | research-only | 0.4631944 | 0.3729340 | 0.3057749 | 327.71 | 1742.99 | 1899.35 | 0.01452 | 1.234891 |

The commercial non-dominated frontier receipt identifies FAST and DEEP. The
ARM-03 reference is reported as research evidence only and is excluded from
the commercial frontier and any production claim.

## Legal transfer boundary

The LegalBench mini transfer is `UNSUPPORTED` because the required frozen
LegalBench-RAG mini dataset, evaluator schema, and legal runtime artifact are
absent from the authorized evidence stores. Full legal transfer was not run.
The diagnostic is isolated, has no patent retuning feedback, and records zero
Selection and Final accesses. This is a bounded unsupported result, not a
quality failure and not legal advice.

## Integrity and safe return

- Remote ARM-03 completion receipt: `18dd5657b4b3ae81401d8de0944bec83fb39e0baf9f21425a22201a71f0f0550`.
- Remote ARM-03 ranking package: `8f10925ff0bb0156b4341b3b3667de208314a88ddddbcc25c592b4020ef4e4b5`.
- Owner-local ARM-03 aggregate receipt: `53620ad3d2ec9637b684871384cb8b7462a52e37b63bc5547fdf0ade83de4157`.
- Research safe-return receipt: `8a882b79234d75d72b9304053960dd322fe56e0486159b423a7753406afcb665`.
- Complete A4 coverage receipt: `8e1e2e6a2e1a00a93ced7219f488ed9ebbc9bbfee8f79bb1f6796a7dabcb4653`.
- Independent aggregate result-integrity audit: `08b83b848023c52967329b769d7b230cf7009290664e95ddd340d569bb0157b5`.
- Selection handoff blocker receipt: `32e5a634b40226a9af2f766fb0f2949a539d3c869968d10324056f25ac839822`.
- Remote workers are gone; all four GPUs were observed idle and approximately
  142 GiB disk remained after safe return.

## Selection and A5 status

Selection was deliberately not opened. A repository/Owner Store search found
no hash-bound Selection-125 paired-vector handoff, frozen finalist registry,
or protected Selection evaluator receipt. Constructing vectors from the
HDEV-100 rankings or inventing finalist roles would change the scientific unit,
so the correct state is fail-closed:

- `selection_accesses=0` and `final_accesses=0` remain authoritative.
- No Selection receipt, finalist decision, or production winner exists.
- Conditional `D2_OPEN_FINAL` was not emitted.
- A5 remains a pointer-only pending template with
  `execution_permitted=false`; the latest remote pending bundle is isolated at
  `/opt/myis/a5-pending-a4-selection-20260820T112000Z` and contains no
  protected payload.

The next valid continuation requires an Owner-local, hash-bound Selection-125
paired-vector/evaluator handoff. After that handoff is independently checked,
the one-shot Selection can be consumed exactly once, the two-system A5 Final
registry can be frozen, and only then can the conditional D2 path be evaluated.

## Reproducibility commands

```text
rtk uv run --no-sync pytest -q tests/test_a4_evaluator_selection.py tests/test_a5_pending_handoff_validator.py tests/test_a4_selection_runner.py
rtk uv run --no-sync ruff check scripts/evaluate_a4_hdev_owner_local.py scripts/validate_a4_owner_closeout.py src/myis_research/armindex/a4_selection_runner.py
rtk uv run --no-sync python scripts/validate_a4_owner_closeout.py --root <MYIS_ROOT>/04_Owner_Stores/armindex/a4/a4-goal001-20260819T180000Z-a4x12 --output <MYIS_ROOT>/04_Owner_Stores/armindex/a4/a4-goal001-20260819T180000Z-a4x12/hdev-evaluations/A4_RESULT_INTEGRITY_AUDIT.json
rtk uv run --no-sync python scripts/validate_a5_pending_handoff.py --template control/armindex/a5/a5-pending-a4-selection-template.v1.json
```

## Claim boundary

The evidence supports complete A4 development/profile transfer coverage,
commercial frontier diagnostics, a separately labeled research reference,
explicit unsupported legal-transfer evidence, and reproducible protected-data
controls. It does not support Selection superiority, a production winner,
Final-872 performance, generalization, legal novelty, or an A5/A6 result.
