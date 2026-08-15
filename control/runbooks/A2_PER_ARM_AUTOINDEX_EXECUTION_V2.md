# A2 Per-arm AutoIndex Execution: USD 60 Successor

## Scope

This additive successor governs only fresh all-fee admission and staging
readiness. It preserves the frozen 52-candidate universe, all historical v1/v2
controls and receipts, and the measurement lock. ARM-01 retrieval runs on the
fresh Vast instance CPU in the same attempt as the GPU arms and remains
diagnostic/non-advancing; ARM-02 remains diagnostic/non-advancing. The existing
Owner-local boundary applies only to aggregate-safe evaluation after remote
retrieval returns its approved artifacts.

## Non-negotiable bindings

- Budget profile: `control/budgets/a2-execution-readiness-v2.json`.
- Readiness contract: `control/armindex/a2/execution-readiness-contract.v3.json`.
- Envelope: `control/execution-envelope-a2-readiness-v3.yaml`.
- Forward all-fee hard stop: USD 60, inclusive, for the entire frozen workload.
- Target TTL: 84 hours. Initial admission floor: 40 hours. The deterministic
  matched reserve checkpoint floor remains 53848 seconds.
- Historical USD 35, USD 45, and USD 50 artifacts remain read-only and must
  never be rewritten or used as the fresh admission receipt.

## Admission sequence

1. Verify the frozen manifest, freeze receipt, and lock hashes; stop on drift
   or any non-zero protected, candidate-evaluation, or measured counter.
2. Bind a runtime-supplied fresh Vast instance using aggregate-safe runtime,
   model-lockset, data-handoff, SSH-host-key, and management-authority sources.
3. Require a fresh all-fee quote covering compute, storage, network,
   platform/other fee, tax/surcharge, 84-hour TTL, and all 52 candidates. The
   quote must be no older than 900 seconds and total no more than USD 60.
4. Require at least 40 hours remaining at admission. At the matched reserve
   checkpoint, require the unchanged 53848-second floor.
5. Emit only `a2-provider-admission-receipt.v3.json` under a new attempt ID.
   The receipt binds the USD 60 budget profile and v3 readiness-contract hashes.
6. Stage only after fresh admission and the separately required adoption path.
   No candidate evaluation, protected data, or measured A2 execution is
   authorized by this runbook.

## Fail-closed conditions

Stop before staging on a missing fee component, stale quote, total above USD
60, TTL below the applicable floor, historical-instance reuse, hash drift,
provider destruction, or any protected-data boundary breach. Preserve the
failed attempt evidence and create a new receipt chain only after a clean
recovery.
