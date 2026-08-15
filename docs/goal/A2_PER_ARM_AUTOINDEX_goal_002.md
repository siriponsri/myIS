---
title: "A2 provenance-v2 measured five-arm AutoIndex execution"
phase_id: A2_PER_ARM_AUTOINDEX
task_id: A2.1
status: READY_FOR_MEASURED_EXECUTION
lifecycle: READY
evidence_class: measured_execution_authority
scientific_authority: true
measured_a2_authorized: true
measurement_authority_uri: control/armindex/a2/measured-authority/a2-im-audit008-provenance-v2.authority.v2.json
claim_boundary: "This goal authorizes only the frozen A2 five-arm measured retrieval execution. It does not authorize candidate generation or mutation, candidate evaluation, REP-DEV measurement, A3, Selection, Final, D2, or D3."
last_material_update: 2026-08-15
next_authorized_action: LO_EXECUTE_FROZEN_A2_WITH_FRESH_ADMISSION_AND_SAFE_RETURN
---

# A2 provenance-v2 measured five-arm AutoIndex execution

## Authority and frozen scope

Use the separate tracked authority at
`control/armindex/a2/measured-authority/a2-im-audit008-provenance-v2.authority.v2.json`
and the successor execution adoption receipt under the Owner-local root
`armindex/a2/a2-ap-audit009-provenance-v2-20260815/`. The authority is bound to
attempt `a2-im-audit008-provenance-v2`, bundle commit
`665cdcc76c4619a0a60419978179e1ab6b6d7cf6`, tree
`caf451410a2b1dda1c8b4d51a03f324186ff915b`, the frozen candidate manifest,
freeze receipt, lock, and execution-adoption receipt.

The immutable universe is exactly 40 matched candidates plus 12 dormant
conditional-reserve candidates. `ARM-01` and `ARM-02` are diagnostic and
non-advancing. Only `ARM-03`, `ARM-05`, and `ARM-04` may advance under the
frozen strict-improvement and tie-rejection rules. Do not generate, replace,
edit, re-score, or reinterpret candidates.

## Fresh preflight and admission

Before any worker launch, use the successor Owner-local assets and obtain a
fresh authenticated provider observation/admission for Vast instance
`47700074`. The quote must be no older than the contract freshness window,
cover the full Owner-approved 84-hour total TTL and every fee component, and
remain at or below the USD 50 Task/Run hard stop. The canonical TTL deadline is
`2026-08-17T22:35:12.980077Z`; the initial admission must prove at least 40
hours remaining. Stop on unknown fees, stale quote, identity drift, or any
non-zero GPU/A2 process count. The A2 Phase ceiling remains USD 150.

Revalidate the successor attempt ID, bundle SHA, bundle receipt SHA, Git commit
and tree, remote root, Owner-local manifest, remote input manifest, false
measurement-authority commitment, adoption receipt, watchdog, runtime/model/data
hashes, provider binding, and authority v2 as one equality chain. The bundle
commit must be an ancestor of clean pushed `main`, and every path in the
execution-bundle closure must be byte-unchanged between the bundle commit and
the authority HEAD. Do not upload model bytes, download data, log in/out, rotate
credentials, destroy, or reprovision the instance during execution.

## Measured execution sequence

Invoke the repository-owned production command with the successor adoption,
authority v2, `remote-transport-config.json`, `input-manifest.json`, the frozen
command argv, an Owner-local output directory, and an append-only lifecycle
ledger. Use remote-only transport. The CUDA-bound engine must not run on local
Windows. The staged remote root is
`/opt/myis/a2-im-audit008-provenance-v2`.

Execute the 40 matched candidates first. Persist a durable aggregate-safe
receipt, process identity, heartbeat, cancellation state, and checkpoint for
each candidate. Resume only from the ledger and never relaunch a candidate
with a durable result. Preserve the exact frozen order and stop at the matched
barrier with `MATCHED_COMPLETE_RESERVE_ADMISSION_REQUIRED`.

At the matched barrier, obtain a fresh reserve-budget admission from the same
provider and source artifacts. Require the deterministic unfinished-work TTL
floor `53848` seconds plus the unchanged USD 50 Task/Run hard stop. Do not
reuse the initial 40-hour floor as the reserve floor. Activate a reserve arm
only when the frozen predicate passes; otherwise write the required dormant
receipt.

This goal runs frozen retrieval only and emits aggregate-safe candidate and
lifecycle evidence. Candidate evaluation and REP-DEV measurement are outside
this LO goal and remain closed by the authority. A later AP/LO step may consume
protected qrels and membership only if a separate canonical authority opens
that surface. Git, MLflow, Obsidian, Brain, Paper, chat, remote provider logs,
and safe-return archives receive aggregate-safe results, hashes, counts, safe
IDs, and pointers only.

## Recovery, safe return, and artifacts

On interruption, use the durable supervisor PID/start identity, heartbeat,
cancellation, reaping, and recovery checkpoints. Fail closed on stale
identity, duplicate lock, missing result, hash drift, or ambiguous worker
liveness. Preserve the remote attempt root until safe-return validation passes.

Before closeout, produce and hash-bind at least:

- append-only lifecycle ledger and terminal checkpoint;
- exact candidate coverage, matched-barrier, reserve-admission,
  decision/continuation, and aggregate result receipts;
- safe-return archive and safe-return receipt with protected payload excluded;
- winner/advancement receipts and provider closeout evidence;
- `docs/long_run/A2_PER_ARM_AUTOINDEX_lo_002_001.md` with measured status,
  aggregate-safe metrics, recovery used, artifact hashes, and provider
  disposition.

Refresh the validated read model and Obsidian/MLflow projections after
closeout. Do not copy raw qrels, membership, query IDs, rankings, per-query
outcomes, credentials, or raw provider payloads into projections.

Do not destroy the provider from the executor. At closeout, report
`OWNER_ACTION_DESTROY` if no immediate authorized reuse remains and give the
Owner the exact dashboard action; otherwise report a concrete `KEEP_GPU`
condition.

## Hard stops

Stop before launch or at any checkpoint on bundle/authority/adoption/attempt
drift, a non-ancestor bundle commit, execution-closure drift, stale or partial
quote, TTL below the applicable floor, price above USD 50, Phase spending above
USD 150, GPU/runtime/model/data drift, protected output, candidate mutation,
exact tie, incomplete coverage, duplicate worker, stale heartbeat, or any
request to open candidate evaluation, REP-DEV measurement, A3, HARNESS-DEV,
Selection, Final, D2, or D3.

This goal is an execution instruction only. It does not authorize redesign,
fallback model/provider changes, or interpretation beyond canonical aggregate
evidence.
