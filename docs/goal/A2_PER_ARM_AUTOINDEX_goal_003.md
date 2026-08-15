---
title: "A2 v3 successor fresh-admission and staging preparation"
phase_id: A2_PER_ARM_AUTOINDEX
task_id: A2.1
status: STOP_PREAUTHORITY_UNSAFE_REMOTE_ROOT
lifecycle: CLOSED
evidence_class: operational_preauthority_preparation
scientific_authority: false
measured_a2_authorized: false
last_material_update: 2026-08-15
next_authorized_action: LO_EXECUTE_A2_PER_ARM_AUTOINDEX_GOAL_004
---

# A2 v3 successor fresh-admission and staging preparation

## Purpose and boundary

This goal prepares only the missing, time-sensitive Owner-local facts needed
for AP to issue a separate v3 measured-execution authority. It authorizes a
fresh authenticated provider observation, instance binding, admission, isolated
stage, and non-measured transport/lifecycle validation for attempt
`a2-ap-audit011-v3-full-a2`.

It is not a measurement authority. Do not invoke `execute`, start candidate
retrieval, open qrels, membership, or the Owner-local evaluator, or emit a
candidate-result, reserve, winner, or closeout receipt. Candidate generation,
mutation, A3, Selection, Final, D2, and D3 remain closed.

Goal 002, authority v2, their adoption, provider evidence, and remote root are
immutable failed-prelaunch lineage. Do not reuse their bundle, admission,
transport, provider identity, connection material, or remote root.

## Frozen pre-provider bindings

The clean pushed successor bundle is at the Owner-local path
`../04_Owner_Stores/armindex/a2/a2-ap-audit011-v3-preauthority-20260815/`.
Its receipt is `execution-bundle.receipt.v1.json` with:

- attempt ID `a2-ap-audit011-v3-full-a2`;
- bundle SHA-256 `a5006482f92e8ea535744cd5e44f665e3582d19d91f4d626406d08b89f0fd81c`;
- receipt SHA-256 `3222119cbf2307c74633739470506e9aa5e465c71cef41b1a6afa0782b9e6ac5`;
- Git commit `aecd01a34dd46a636a1a88c082e9e2582aadf8cb` and tree
  `2144b32afe9a8a8ddced56c60327910e8be040d0`.

The future remote root is exactly `/opt/myis/a2-ap-audit011-v3-full-a2`.
Use an empty, isolated root; never rename, overwrite, or clear an existing
root. The static commitment is
`control/armindex/a2/measurement-authority-commitment.v2.json`, file SHA-256
`0fd6bccd7619b4c855a15de9c5ef5493f46aee5a31282f4b6009e36079b72b39`.

## Required sequence

1. Verify clean `main == origin/main`, the bundle receipt/self-hash, bundle
   Git commit/tree, frozen candidate bindings, and v3 closure. Stop on any
   drift. Do not rebuild the bundle in this goal.
2. Create a new Owner-local subdirectory for fresh provider evidence and a new
   append-only lifecycle ledger under the successor root. Do not copy stale
   provider observations, admissions, transport configurations, or connection
   material from the v2 attempt.
3. Obtain one fresh authenticated provider observation for an available
   eligible instance. It must prove the required runtime/model/data bindings,
   process-zero state, all-fee quote, and a total 84-hour TTL that leaves at
   least 40 hours at initial admission. The whole-workload quote must be at or
   below USD 50 and remain within the USD 150 Phase ceiling. Stop on unknown
   fees, stale quote, identity drift, an unavailable instance, or nonzero GPU/
   A2 process counts.
4. Build and validate a new provider-instance binding and provider-admission
   receipt for this attempt. Produce the new Owner-local input manifest and
   remote retrieval input with the frozen candidate universe and protected
   paths remaining Owner-local. Build the v3 remote transport configuration
   only after its fresh instance ID, bundle, manifest, and request hashes are
   known.
5. Run only the runbook's non-measured deployment/stage, transport-check,
   interruption/cancellation/reaping, recovery, and safe-return validation.
   Stage the new isolated remote root and produce a new execution-adoption
   receipt. The remote transport must contain no qrels, membership, evaluator,
   query IDs, rankings, per-query outcomes, credentials, or raw provider
   payloads.
6. Record an aggregate-safe pre-authority result in
   `docs/long_run/A2_PER_ARM_AUTOINDEX_lo_003_001.md`: status, attempt/root,
   bundle/admission/adoption/transport hashes, validation results, recovery
   used, and the GPU disposition. Do not report scientific metrics.

## AP return checkpoint

Stop after the pre-authority closeout. Preserve the remote root and instance
only while AP promptly validates the equality chain and either issues v3
authority plus a measured Goal 004 or declares the evidence failed. Do not
run `execute` before that separate AP authority exists.

AP can issue v3 only if the new authority truthfully binds the fresh provider
instance ID; new adoption receipt SHA-256; Owner-local manifest self/file
hashes; evaluator, qrels, membership, token-map, runtime, model-lockset,
data-handoff, and transport-request commitments; exact frozen candidate
bindings; and the bundle commit/tree above. The authority must keep the
evaluation Owner-local and aggregate-safe, with A3/Selection/Final closed.
## Recovery and hard stops

Use the durable process identity, heartbeat, cancellation, reaping, and ledger
rules in the A2 runbook. Stop before staging on a duplicate lock or unsafe
remote root; after staging, preserve the root until the required safe-return
validation passes. Do not destroy the instance from the executor. At closeout,
report `KEEP_GPU` only until the AP return checkpoint; otherwise report the
applicable destroy disposition with aggregate-safe evidence.
