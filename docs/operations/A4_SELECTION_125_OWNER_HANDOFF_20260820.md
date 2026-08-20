---
title: "Owner handoff contract for the one-shot Selection-125 exposure"
phase_id: A4_PRODUCTION_TRANSFER_AND_SELECTION
task_id: A4.1
status: BLOCKED_OWNER_INPUT
lifecycle: BLOCKED
evidence_class: owner_local_selection_handoff_contract
scientific_authority: false
execution_permitted: false
provider_instance_id: 47790578
selection_query_count: 125
selection_access_limit: 1
selection_accesses: 0
final_accesses: 0
protected_payloads_allowed: false
blocker_receipt_sha256: 32e5a634b40226a9af2f766fb0f2949a539d3c869968d10324056f25ac839822
next_authorized_action: OWNER_SUPPLY_AND_VALIDATE_REAL_SELECTION_125_HANDOFF
---

# Owner Handoff: Selection-125

This is the only approved input contract for clearing the A4 Selection
handoff blocker. It is a pointer/hash contract, not a Selection result and not
permission to open Final. The target publication route is tier 1: preserve the
predeclared comparison, complete paired uncertainty evidence, independent
auditability, and a clean A5-to-A6 provenance chain.

## Current canonical state

- A4 closeout attempt: `a4-goal001-20260819T180000Z-a4x12`.
- A4 result-integrity audit: `08b83b848023c52967329b769d7b230cf7009290664e95ddd340d569bb0157b5`.
- A4 Selection handoff blocker: `32e5a634b40226a9af2f766fb0f2949a539d3c869968d10324056f25ac839822`.
- `selection_accesses=0` and `final_accesses=0` remain authoritative.
- No vector, finalist decision, Final result, or winner may be inferred from
  HDEV-100 output.

## Owner Store input contract

Place the protected handoff under:

```text
<MYIS_ROOT>/04_Owner_Stores/armindex/a4/selection-125/<handoff-id>/
```

The repository may receive only the aggregate-safe manifest, SHA-256 values,
counts, receipts, and opaque relative pointers. The paired vectors,
evaluator handoff, qrels, split membership, raw query/family IDs, rankings,
and per-query outcomes remain in the Owner Store.

The aggregate-safe manifest must contain exactly these input commitments:

| Field | Required value or rule |
|---|---|
| `selection_input_sha256` | SHA-256 of the canonical input body excluding this field |
| `paired_out_vectors_sha256` | SHA-256 of canonical comparison IDs/system hashes/three metric vectors |
| `evaluator_handoff_sha256` | SHA-256 of the protected evaluator handoff receipt |
| `selection_query_count` | Exactly `125` |
| `selection_population` | Exactly `OUT` |
| `comparison_family_id` | Frozen preregistered family identifier |
| `bootstrap_seed` | Non-negative integer recorded before exposure |
| `comparisons` | Non-empty frozen finalist comparisons; no protected keys |

Each comparison must contain distinct left/right system SHA-256 values and
exactly these metric vector names: `recall_at_100`, `ndcg_at_100`, and
`ndcg_at_10`. Every left/right vector must contain exactly 125 finite values in
`[0, 1]`. Do not create vectors from HDEV-100, fixtures, guessed rankings, or
post-hoc finalist choices.

The frozen pre-Selection registry must be self-hashed, have status
`FROZEN_BEFORE_SELECTION`, contain distinct candidates only, and bind each
candidate to its source receipt. It may contain up to four preregistered
roles. It is not the Final registry.

## One-shot procedure

1. Validate the manifest, registry, evaluator handoff hash, vector hash,
   protected-field scan, counters, and A4 receipts without opening Final.
2. Invoke the owner-local Selection runner exactly once. Its write-once output
   must contain aggregate statistics only: paired deltas, 10,000 bootstrap
   resamples, 95% confidence intervals, rank-biserial effect, and W/T/L.
3. Freeze the Final registry from the Selection receipt with exactly two
   distinct systems: `static_common_baseline` and `research_champion`.
4. Build and validate the A5 v2 pointer bundle. It must bind all finalist
   program/prompt/representation/model/license/runtime hashes, A4 audit and
   safe-return receipts, Final-872 commitment, evaluator handoff pointer,
   safe-export manifest, clean pushed Git commit/tree, and A5 reserve.
5. Emit conditional `D2_OPEN_FINAL` only when every A4 automatic PASS
   predicate is true and the bundle is independently audited. Otherwise keep
   A5 blocked; a manual Owner D2 remains valid and separate.

## Vast reuse and fresh attempts

Instance `47790578` is the only authorized instance. Reusing the instance does
not reuse an attempt. After valid D2, create a new A5 root named
`/opt/myis/a5-goal001-<UTC>` with fresh provider identity, quote, TTL, budget,
runtime/GPU/disk health, and checkpoints. After a valid A5 closeout, create a
separate `/opt/myis/a6-goal001-<UTC>` root with another fresh admission. Never
reuse A4 roots, PIDs, workers, caches, checkpoints, partial outputs, quotes, or
budget receipts.

Before the Owner handoff exists, only code-check staging is allowed. The
non-measured staging root is `/opt/myis/a5-codecheck-<UTC>/current`; it must
contain no protected input, worker, PID, or scientific output.

## Tier-1 evidence and hard stops

The tier-1 evidence set is the hash-closed Selection receipt, exactly-two-system
A5 Final-872 coverage and independent audit, and the A6 aggregate scalability
and failure package. A6 may claim only frozen-winner materialization and
operational scalability; it cannot claim full-corpus superiority or reopen
Selection/Final. Stop on missing or drifted hashes, protected-field exposure,
duplicate access, stale authority, unknown budget/TTL, incomplete coverage, or
incompatible partial output.

Owner action: place the real hash-bound handoff at the Owner Store path above
and return its manifest path plus aggregate-safe manifest hash. Do not paste
vectors, qrels, query IDs, credentials, or raw evaluator payloads into Git,
chat, or the repository.

## Validation

```text
rtk pytest -q tests/test_a4_evaluator_selection.py tests/test_a4_selection_runner.py tests/test_a5_pending_handoff_validator.py tests/test_a6_pending_materialization_validator.py tests/test_a6_materialization.py tests/test_a6_preparation_bundle.py
rtk git diff --check
```

Until those checks pass against the real Owner-local handoff, this document
remains `BLOCKED_OWNER_INPUT`; it does not authorize Selection, D2, Final, A5,
or A6 execution.
