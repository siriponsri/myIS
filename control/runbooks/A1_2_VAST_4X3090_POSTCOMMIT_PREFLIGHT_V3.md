# A1.2 Vast 4xRTX3090 Post-Commit Preflight Correction v3

## Purpose

This additive correction preserves the immutable v2 preparation receipt and
fixes one preflight defect discovered only after the first clean commit. The v2
validator regenerated its expected input from the current `HEAD`, although the
v2 input correctly retained the commit and tree where preparation began. A
post-commit `HEAD` therefore caused false drift even when every v2 file hash
matched its receipt.

Revision `a1.2-local-vast-4x3090-postcommit-v3` validates immutable v2 bytes
through the v2 receipt instead. The clean current commit and tree are captured
when the Owner builds the frozen bundle and are then compared during remote
verification. This separates preparation provenance from live bundle identity.

## Boundary

- v1 and v2 files remain byte-identical historical evidence.
- `launch_allowed=false` and `adopted_for_execution=false` remain mandatory.
- No paid worker contact, GPU reservation, model download, measured retrieval,
  optimization, Selection, Final, paid API, or weight change is authorized.
- All scientific and resource counters remain zero.

## Planning Price and Hard Stops

The Owner planning rate is USD 0.60 per hour for the complete four-RTX3090
instance, not per GPU. Reserve 2-4 instance-hours for the live preflight, for
an estimated raw worker cost of USD 1.20-2.40, plus 2-4 local coordination
hours. This estimate is planning evidence only. The Owner must bind the live
provider quote and identity before upload. The unchanged hard stops are USD 18
for the common screen, USD 23 for A1, and USD 100 for the campaign; a quote or
projected charge that does not fit must stop as `BLOCKED_BUDGET`.

## Acceptance

The v3 validator must run from a clean, committed Research worktree, validate
the v2 receipt and every v3 binding, and return the current commit and tree.
The bundle builder must embed those same identities and a resolved OCI image
digest. The live coordinator must verify them before starting synthetic remote
workers. A mismatch stops the preflight.

## Owner Command

Use `docs/operations/A1_2_VAST_4X3090_OWNER_RUNBOOK_V3.md`. It gives the exact
command substitutions for the preserved v2 beginner runbook. No secret or
protected value is written to Git.
