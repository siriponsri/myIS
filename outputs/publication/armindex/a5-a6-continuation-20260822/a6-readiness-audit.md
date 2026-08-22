# A6 Readiness Audit

Audit date: 2026-08-22  
Evidence class: aggregate-safe readiness review  
Scope: `A6_FULL_DAPFAM_MATERIALIZATION_AND_SCALABILITY`

## Determination

`A6_NOT_ADMISSIBLE_YET`.

The canonical A6 contract requires a terminal `PASS_A5_FINAL_CONFIRMATION`
and exactly one hash-closed A5 winner. Current artifacts show A5 input
preparation/materialization and a live Final attempt lineage, but do not
constitute an A5 closeout, result-integrity audit, safe-return receipt, or
frozen winner configuration. A6 metrics and quality claims therefore remain
pending and must not be inferred.

## Verified readiness inputs

- The canonical DAPFAM source declares `45,336` corpus rows at revision
  `a59a74ce31384165065af1823a83c6f94ccafd48` (`control/assets/dapfam-p1-source.v1.json`).
- The A5 opaque materialization manifest records the same `45,336` corpus
  count and a corpus hash, but it is an A5 input/transport artifact, not an
  A6 admission or result.
- The A6 contract and phase amendment prohibit tuning, winner changes,
  Selection/Final reopening, qrels or membership access, rankings, and
  per-query outcome export.
- No A6 attempt root, A6 admission receipt, materialization checkpoint, or
  A6 result artifact is present under `04_Owner_Stores/armindex/a6/`.

## Required before A6 launch

1. A5 terminal state `PASS_A5_FINAL_CONFIRMATION`.
2. A5 result-integrity audit, safe-return receipt, final registry, and
   aggregate-safe closeout, all hash-validated.
3. Exactly one frozen winner binding covering representation, prompt/prefix,
   model adapter, chunking, retrieval/index configuration, runtime lock, and
   code revision.
4. Fresh A6 attempt ID/root and fresh provider identity, quote, budget, TTL,
   runtime, CPU/GPU/RAM/disk health, watchdog, and safe-return evidence.
5. A6 source/configuration hashes and protected-field scan bound to the
   `45,336`-row corpus inventory.

## Contract discrepancy to resolve at admission

The checked-in A6 contract/template still names provider instance `47790578`,
which is a destroyed predecessor. The next A6 admission must bind the actual
live instance used after A5, with fresh provider evidence; the stale ID must
not be treated as current authority.

## Claim boundary

This note contains no A5 metrics and no A6 metrics. It supports only the
readiness determination above. A6 can report operational scalability for one
frozen winner after a valid admission; it cannot support a new quality,
generalization, or comparative full-corpus claim.
