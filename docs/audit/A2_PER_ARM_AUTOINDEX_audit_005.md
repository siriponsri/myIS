# A2 AP Audit 005: canonical readiness and budget review

- Session mode: `AP`
- Phase/Task: `A2_PER_ARM_AUTOINDEX / A2.1 FROZEN_FIVE_ARM_EXECUTION`
- Reviewed revision: `1537e50e164e646aaa1f8fe2933a58596fe3e43a`
- Source IM handoff: `docs/implementation/A2_PER_ARM_AUTOINDEX_im_004_001.md`
- Provider contact/provisioning: not performed
- Routing: `NEEDS_IM`
- Date: `2026-08-13`

## Decision

A2 is structurally sound at the frozen-design and CPU-local deployment-package
layers, but it is not ready for fresh Vast admission or staging. Measured A2 remains
closed. The highest-value next action is one bounded IM repair of the current
readiness closure and status chain before any paid provider action.

## Evidence inspected

- `PLAN.md`, `control/source-of-truth.yaml`, and the A2 implementation handoffs
- current campaign, A2 candidate freeze receipt, readiness contract/envelopes,
  budget profiles, goal, runbook, and append-only execution ledger
- Owner-local final execution-bundle and deployment-package receipts from IM 004
- current Git revision and the commit delta after the bundle receipt
- focused candidate-freeze/execution-contract/readiness tests, Ruff, entry
  preflight, deployment-package validation, and canonical status output

No provider CLI/API/dashboard/SSH contact, provisioning, remote staging, GPU work,
candidate evaluation, REP-DEV measurement, or protected-data access occurred.

## Findings

### Major: current v2 envelope is absent from the immutable execution bundle

`control/source-of-truth.yaml` and `docs/goal/A2_goal.md` identify
`control/execution-envelope-a2-readiness-v2.yaml` as current supporting authority
for the runtime-supplied fresh-instance path. The bundle closure in
`src/myis_research/armindex/a2_execution_readiness.py` includes the current v2
contract but only the historical v1 envelope. The validated Owner-local bundle
therefore omits the current envelope while claiming the minimum immutable
code/control closure.

Why this matters: remote admission/staging could consume v2 schemas and contract
bytes without carrying the current envelope that authorizes only provider admission
and staging while keeping measured work locked. This weakens independent replay and
creates an avoidable authority ambiguity at the paid-execution boundary.

Required repair: add the v2 envelope to the required bundle closure, retain v1 as
historical compatibility, add a focused regression that fails when either required
envelope is absent or drifted, and rebuild the execution bundle and deployment
package from clean pushed HEAD.

### Major: current authoritative status still says the completed rebind needs IM

The current authority `control/armindex/a2/execution-readiness-contract.v2.json`,
the v2 envelope, and ledger entry `A2EXEC-EV0004` report
`NEEDS_IM_NEW_INSTANCE_REBIND_MEASUREMENT_LOCKED`, although IM 004 states that the
runtime-supplied rebind, staging repairs, and CPU-local package are complete. `PLAN.md`
and the generated status instead route to AP fresh-instance staging.

Why this matters: the source-of-truth authority and Owner-facing plan disagree on
the next executable state. AP must not resolve that conflict by contacting a paid
provider. The canonical chain must first express one consistent post-IM state.

Required repair: make the smallest additive/current status correction so the
contract, envelope, ledger successor, goal/read model, and projections agree that
CPU-local implementation is complete, fresh admission/staging is the later AP
action, and measured execution remains false. Preserve all historical records.

### Minor: A1 reuse lineage remains easy to misread as A2 lifecycle evidence

The entry preflight passes but reports `provider_disposition_status=REUSE_ELIGIBLE`
and `reuse_existing_instance_permitted=true` from A1 lineage. The current A2 route
requires a fresh runtime-supplied instance and explicitly rejects historical instance
`47411176`.

Required repair: retain the A1 lineage fields but add an explicit current A2
disposition such as `FRESH_INSTANCE_REQUIRED`, with reuse false, so automation and
Owner-facing projections cannot mistake A1 retention evidence for A2 admission.

## Budget assessment

- Campaign hard stop: USD `150`.
- Recorded A1 charge: USD `11.161632`.
- Remaining campaign ceiling: USD `138.838368`.
- A2 Phase/Task forward hard stop: USD `35`.
- A2 preparation spent/accrued: USD `0`.
- Fresh all-fee quote: absent; estimated next paid cost is `UNKNOWN`.
- Budget status: `UNKNOWN_DO_NOT_SPEND` until a fresh quote covers compute,
  storage, network, platform/other fees, taxes/surcharges, at least 40 hours, and
  all 52 candidates, with no unknown component.

The numerical ceilings are coherent and A2 fits inside the remaining campaign cap,
but no paid action is presently admissible because the fresh quote and provider
admission receipt do not exist.

## GPU and Vast lifecycle

Canonical provider admission evidence for a live A2 instance is absent. The latest
verified record for instance `47411176` predates the Owner fresh-instance route; the
repository records the decision to destroy/reject it but does not contain a current
authenticated provider-absence receipt. Planning did not contact the provider.

GPU decision is therefore `UNKNOWN`, instance `NONE`, hourly rate and accrued GPU
cost `UNKNOWN`. Do not keep, stage, provision, or spend against any instance during
the IM repair. Resolve provider state only in a later AP staging session after the
canonical repair, using fresh aggregate-safe provider evidence under the runbook.

## Publication impact

The frozen 52-candidate design, production adapter, matched-first reserve lifecycle,
and metadata-only deployment package materially strengthen reproducibility. They do
not yet support effectiveness, latency, cost, winner, or superiority claims. Closing
the two readiness inconsistencies before provider use has the highest expected
publication value per unit effort because it protects provenance at the boundary
where future measured evidence will be created, while costing no GPU spend.

## Validation observed

- Focused A2 structural suite: `28 passed`.
- Ruff on the focused readiness surface: `PASS`.
- A2 entry preflight: `PASS_A2_ENTRY_PREFLIGHT`; A2 execution authorized `false`.
- Owner-local deployment package validation: `PASS`.
- Bundle SHA-256 and deployment-package SHA-256 match their receipts.
- Git worktree clean; `HEAD == origin/main` at review time.

These checks do not waive the authority-closure and status-coherence findings.

## IM work requested

1. Add `control/execution-envelope-a2-readiness-v2.yaml` to the A2 execution-bundle
   closure and test exact v1/v2 inclusion and drift rejection.
2. Reconcile the current post-IM readiness status across the v2 contract, v2
   envelope, append-only successor ledger entry, goal/read model, and projections.
3. Add an explicit current A2 fresh-instance disposition to preflight/status output
   while retaining A1 `REUSE_ELIGIBLE` only as lineage.
4. Rebuild and validate the clean pushed-HEAD execution bundle and deployment package.
5. Do not contact/provision Vast, stage remotely, create measured authority, access
   protected data, or start candidate evaluation/measured A2.

## Expected IM output

Write `docs/implementation/A2_PER_ARM_AUTOINDEX_im_005_001.md` with the exact
revision, changed authority/closure surface, focused checks, final Owner-local bundle
and package receipt paths/hashes, and route back to AP for fresh provider admission
and isolated staging only.

