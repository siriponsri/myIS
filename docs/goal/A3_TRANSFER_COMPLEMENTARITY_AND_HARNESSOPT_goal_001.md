# A3.1 Train-250 Headroom Diagnostic Preparation

## Objective

Prepare, but do not execute, a post-A2 aggregate-only authority for one
non-adaptive held-out HDEV-100 winner-versus-frozen-A1-incumbent Recall@100 OUT
diagnostic. A separate Train-250 comparison is descriptive only and cannot be
described as held-out evidence.

## Current Canonical State

`authority_state` is strictly `PENDING_A2_CLOSEOUT`. This goal is a disjoint
preparation surface while A2 remains independently active. It creates no A2
evidence and does not alter A2 execution, candidate, authority, or closeout
artifacts.

## Required Runtime Bindings

The preparation may validate only a runtime-supplied, self-hashed aggregate
envelope containing all of the following:

1. A valid PASS A2 closeout receipt with all five arms, verified safe return,
   and no Selection or Final access.
2. Exactly five frozen winner program SHA-256 values, one for each active arm,
   each bound to a valid PASS aggregate-only `Train-250` receipt emitted only
   by the separate post-A2 Owner-local fixed diagnostic, not by an A2 train
   evaluation receipt.
3. One valid, frozen PASS A1 incumbent aggregate receipt with compatible
   Recall@100 OUT aggregates and incumbent program hashes for all five arms.

Synthetic, missing, incomplete, non-PASS, non-authoritative, unhashed,
duplicate, incompatible, non-Train-250, Selection, Final, or protected payloads
must fail closed. Inputs and outputs remain aggregate-only. No HDEV-100 input
may enter this repository and no HDEV-100 evaluation may run until the valid A2
closeout binding is complete.

## Scientific and Safety Invariants

- The primary reviewer-facing diagnostic is the same-scope held-out HDEV-100
  comparison between each frozen A2 winner and its frozen A1 incumbent. It is
  non-adaptive and produces no promotion or selection decision.
- Train-250 deltas are secondary descriptive context only, never held-out
  evidence.
- Before valid A2 closeout, no candidate mutation, retrieval, REP-DEV,
  HDEV-100, Selection, Final, provider contact, remote execution, or spend is
  permitted. This repository never contains a protected-data or retrieval
  runner.
- Protected membership, qrels, query identifiers, rankings, per-query outcomes,
  credentials, and raw payloads are forbidden.
- A2 is a runtime input boundary only. This preparation must not inspect,
  create, edit, or infer measured A2 artifacts.
- The output binds only receipt hashes, winner program hashes, and aggregate
  metric values; it cannot replace A2 closeout authority.

## Execution Flow After A2 Closeout

1. Supply the closed A2 aggregate-safe closeout and five aggregate-safe winner
   receipt projections through the A3.1 input schema.
2. Supply the frozen A1 incumbent aggregate receipt projection.
3. Validate all schema, self-hash, arm-completeness, scope, authority, and
   protected-boundary invariants, then emit the one non-adaptive HDEV-100
   authorization.
4. An Owner-local protected evaluator, outside this repository surface, may
   return only five bound aggregate receipts. Each receipt must bind the fixed
   evaluator, split decision, membership and qrels commitments, model/runtime,
   frozen tuple, and winner-selection lineage.
5. Validate those receipts and build the primary held-out HDEV-100 delta report.
   Train-250 remains a separate descriptive-only report.

## Terminal States

- `PENDING_A2_CLOSEOUT`: expected until a valid A2 closeout binding exists.
- `POST_A2_CLOSEOUT_HDEV100_AUTHORIZED`: all closed A2 and frozen A1 bindings
  are valid; this is not a repository execution permission.
- `PRIMARY_HDEV_DIAGNOSTIC`: valid same-scope held-out aggregate comparison
  report produced after the five HDEV-100 aggregate receipts return.
- `DESCRIPTIVE_ONLY`: valid Train-250 context report produced after runtime
  validation.
- `REJECTED_INPUT`: validation fails closed with no partial report.

No terminal state opens A3 transfer work, HarnessOpt, Selection, Final, or any
spend authority.
