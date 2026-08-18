---
title: "A3 Extended three-primary transfer, complementarity, and HarnessOpt"
phase_id: A3_TRANSFER_COMPLEMENTARITY_AND_HARNESSOPT
task_id: A3.1_A3.2
status: CLOSED
lifecycle: CLOSED
evidence_class: measured_development_and_publication_preparation
scientific_authority: true
execution_permitted: false
previous_goal: docs/goal/A3_TRANSFER_COMPLEMENTARITY_AND_HARNESSOPT_goal_002.md
amendment_uri: control/armindex/a2/a2-goal004-three-primary-amendment.v1.json
preparation_authority_uri: control/armindex/a3/a3-three-primary-preparation-authority.v1.json
preparation_manifest_uri: control/armindex/a3/a3-three-primary-preparation-manifest.v1.json
budget_extension_uri: control/budgets/armindex-budget-extension-a3-three-primary.v1.json
a3_attempt_id: a3-goal003-20260818-028
result_integrity_audit_sha256: 3fbc601111b204d3d4829aab63cda2e4368f2b76fd08315c14f4c21abf820644
safe_return_receipt_sha256: 48cb4c51680ec3e59a876dad9b3feaa0593c39585bf27ae4eaf1d50e950453dc
harnessopt_evaluation_sha256: 547ed212febe8c70f6675ca9851e652d391940598fbfb39ec41394c8c453007a
a4_readiness_binding_sha256: 4fb8b8f8d6d80941b0c76116d13c4cfd5199dbcd0d17e59152f0088c54c4f7fd
---

# Goal 003: Extended A3 after amended A2 closeout

## Objective

Measure whether the three receipt-bound A2 primary winners transfer across
compatible retrievers, whether fixed equal-depth unions contribute additional
candidate exposure, and whether a deterministic label-free HarnessOpt policy
improves the quality-latency-cost frontier. The goal retains useful no-gain and
boundary results; it does not optimize for a positive outcome.

## Authoritative Predecessor

A2 attempt `a2-goal004-20260816-005` is closed by an Owner-approved,
evidence-preserving amendment. Its aggregate accounting is `52 = 44 measured
+ 8 dormant conditional reserves`, with zero failure markers. ARM-01 and
ARM-02 have exact three-way primary-score ties and are receipt-bound diagnostic
no-winner outcomes. ARM-03, ARM-05, and ARM-04 have unique A2 winner receipts.

The amended closeout receipt is `e4bc663d7ee09282c334f25945ede247a50b81742a690c214e0f2aa9ffb81d1d`;
the independent integrity audit is `7d31b80d4dab6897f3110ee629ddf8f9d12fd5f0522b0d8ccd175ba892986642`.
Safe return and worker reap are validated. A2 accrued whole-workload cost is
USD `54.52666666666665948`, below its frozen USD `60` cap.

ARM-05 is retained as a unique A2 primary winner but is explicitly labeled
`NO_STRICT_IMPROVEMENT` relative to its frozen A1 incumbent. It is eligible for
the approved A3 transfer/complementarity test but cannot support an A2
improvement claim. ARM-01/02 cannot enter any A3 optimization input.

## Scientific Invariants

- Candidate/program bytes, representation semantics, model adapters, indexes,
  evaluator, data, metrics, output depth, and A2 receipt bindings remain frozen.
- A3 scope is exactly ARM-03, ARM-04, and ARM-05. The complete matrix has
  three self-winner reuse cells and at most six compatible cross-arm transfer
  cells; unsupported cells remain explicit and cannot be substituted.
- ARM-01/02 remain A2 diagnostic no-winner evidence only. No lexical, latency,
  cost, or secondary-metric post-hoc tie break is permitted.
- Complementarity uses preregistered equal-depth fixed-union controls before
  adaptive HarnessOpt measurement; the commercial-only fixed union is ARM-04
  plus ARM-05.
- Extended HarnessOpt permits at most three complete batches, each with exactly
  four frozen roles: quality exploit, cost/latency ablation, routing hypothesis,
  and diversity profile. Partial batches never produce a measured conclusion.
- Adaptive work is limited to Train-250. HDEV-100 is aggregate-only and
  non-adaptive. Selection and Final remain closed.

## Budget And Provider Authority

The A3 whole-workload hard stop is USD `35`; the campaign ceiling is USD `180`.
The estimated remaining campaign headroom after recorded A1, actual A2, and a
full USD 35 A3 reservation is USD `79.31170133333334052`. A3 must obtain a
fresh all-fee quote and provider identity no older than 900 seconds, a 48-hour
target TTL, and a whole-workload admission that uses actual accrued A2 cost.

The current Vast instance may be reused only after this fresh admission. A new
instance is forbidden. Pre-admission provider contact, remote execution,
spend, candidate mutation, Selection, and Final are forbidden.

## Execution Flow

1. Validate the amended A2 closeout, v2 integrity audit, safe return, worker
   reap, three winner receipts, two diagnostic no-winner records, and frozen
   A1 incumbent evidence.
2. Validate the three-primary A3 bundle, then issue the post-A2 budget
   admission from a fresh quote and live provider identity.
3. Build the receipt-bound runtime package and validate the 3x3 transfer
   matrix before remote measurement. Keep unsupported cells explicit.
4. Measure compatible transfer cells and equal-depth complementarity controls.
5. Run one to three complete HarnessOpt batches only while the hard stop, TTL,
   label-free boundary, and batch-completeness rule remain satisfied.
6. Safe-return and independently audit the result. Produce receipt-bound
   aggregate figures, EDA, and claim-limited presentation/report updates.
7. Keep the instance only while a named, immediately authorized A3 workload
   remains. Otherwise request Owner destruction.

## Closeout

Stage `a3-goal003-20260818-028` completed all 14 authorized operations. The
aggregate-only Owner-local evaluation, HarnessOpt boundary evaluation, and
independent result-integrity audit all passed. The closeout produced no
Selection or Final access and no protected payload projection. A4 is prepared
as a contract-only readiness handoff; a separate Owner-authorized A4 goal is
required before production measurement.

## Hard Stops

Stop before measurement on an A2 receipt mismatch, missing primary-winner or
diagnostic-exclusion proof, stale/over-cap quote, insufficient TTL, provider
identity drift, protected-output surface, representation/model/evaluator
mutation, incomplete batch, budget projection above USD `35`, Selection access,
or Final access. A2 outputs are never reinterpreted to repair A3 admission.
