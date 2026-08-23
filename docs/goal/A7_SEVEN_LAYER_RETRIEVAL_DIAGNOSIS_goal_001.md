---
title: "A7 seven-layer retrieval diagnosis and comparison"
phase_id: A7_SEVEN_LAYER_RETRIEVAL_DIAGNOSIS
task_id: A7.1
status: PASS_A7_SEVEN_LAYER_DIAGNOSIS
lifecycle: CLOSED
evidence_class: post_confirmatory_diagnostic
scientific_authority: true
execution_permitted: false
previous_goal: docs/goal/A6_FULL_DAPFAM_MATERIALIZATION_AND_SCALABILITY_goal_001.md
next_goal: docs/goal/A8_JOURNAL_SYNTHESIS_AND_PUBLICATION_goal_001.md
---

# Goal 001: Seven-layer retrieval diagnosis

## Objective

Use the immutable A6 frozen diagnostic bundle to explain, validate, and bound
the A5-confirmed retrieval result. A7 is CPU-first and does not reopen model or
representation selection. The only optional GPU work is the preregistered
fixed-reference reproduction in A7-L3R.

## Execution status

| Work item | Status | Evidence |
|---|---|---|
| Hash-bound predecessor verification | COMPLETE | `control/armindex/a6/a6-a7-handoff-20260823.json` |
| Owner CPU-first admission | COMPLETE | `control/armindex/a7/a7-owner-approval-admission-20260823.json` |
| L1-L3 and L4-L7 diagnostics | COMPLETE | `a7-goal001-20260823T093525Z-cpu02` aggregate-safe output |
| L3R fixed-reference reproduction | NOT_RUN_OPTIONAL | No fresh GPU admission after A6 instance destruction; not required for A7 validity |
| Result-integrity audit and closeout | COMPLETE | `control/armindex/a7/a7-result-integrity-audit-20260823.json` (`PASS_A7_RESULT_INTEGRITY`) |

## Scientific boundary

- Consume A6 evidence by hash only after complete full-DAPFAM coverage, safe
  return, and an independent integrity audit.
- Keep qrels, split membership, protected identifiers, rankings, and per-query
  outcomes in Owner Store; publish aggregate-safe projections only.
- Preserve the A5 winner (`ARM-03 / datalyes/patembed-large`) and the A6 pool
  depth. Do not tune prompts, representations, weights, cutoffs, or models.
- Do not reopen Selection or Final and do not introduce a reranker phase.

## Execution flow

1. Verify the A6 authority, pool, configuration, and safe-return hashes.
2. Independently replay score identity for ALL/IN/OUT and reconcile metric
   definitions, denominators, deduplication, and tie handling.
3. Audit family/relevance integrity, self-match, collision, and leakage risks.
4. Build the protocol-parity matrix; run A7-L3R only when a fresh GPU
   admission is valid and the fixed reference contract is available.
5. Attribute representation effects using frozen score summaries.
6. Produce aggregate query-rescue and candidate-exposure/error anatomy.
7. Compute oracle/retrieval-boundary aggregates from the frozen Top-200 pool.
8. Assemble a claim-to-evidence matrix and close with PASS, bounded STOP, or
   evidence-integrity hard stop.

## Required evidence

The A7 control and readiness contracts under `control/armindex/a7/` define the
required receipts and aggregate-safe allowlist. The Owner Store handoff must
bind A6 hashes and contain no protected payload.

The aggregate-safe handoff contains no protected payload. The CPU runner may
read protected diagnostic inputs only inside `04_Owner_Stores`; it must emit
only the contract allowlist.

## Recovery and terminal states

Engineering failures may be repaired forward without changing frozen inputs.
Evidence ambiguity, protected-data risk, or incompatible hashes requires a
hard stop. Terminal states are `PASS_A7_SEVEN_LAYER_DIAGNOSIS`,
`STOP_A7_WITH_EVIDENCE`, and `HARD_STOP_A7_EVIDENCE_INTEGRITY`.
