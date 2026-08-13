# A2 IM 005-001: canonical readiness closure

- Session mode: `IM`
- Phase/Task: `A2_PER_ARM_AUTOINDEX / A2.1 FROZEN_FIVE_ARM_EXECUTION`
- Source audit: `docs/audit/A2_PER_ARM_AUTOINDEX_audit_005.md`
- Canonical repair revision: `32ee1a954abcf8d21702597732811b7224e77d5e`
- Routing: `READY_FOR_AP_FRESH_INSTANCE_STAGING`

## Summary

Closed the two canonical readiness inconsistencies from audit 005 without
contacting or provisioning a provider. The A2 execution bundle closure now
requires both the historical v1 and current v2 readiness envelopes, together
with append-only execution-ledger schemas v1-v3. Focused regressions assert exact
v1/v2 inclusion and reject drift in either required envelope.

The current v2 contract and envelope now state
`READY_FOR_AP_FRESH_INSTANCE_STAGING_MEASUREMENT_LOCKED`. Historical ledger entry
`A2EXEC-EV0004` remains unchanged; additive successor `A2EXEC-EV0005` records the
post-IM readiness state under schema v3. The read model, goal, PLAN, HANDOFF and
generated projections now agree that CPU-local implementation is complete, AP
fresh-instance admission and isolated staging are next, and measured execution
remains false.

Entry preflight retains A1 `REUSE_ELIGIBLE` as lineage but separately reports the
current A2 disposition as `FRESH_INSTANCE_REQUIRED`, with
`reuse_existing_instance_permitted=false`.

## Changed authority and closure surface

- current A2 readiness contract and v2 envelope status
- additive execution-ledger entry/schema v3
- immutable execution-bundle closure and drift regressions
- A2 entry preflight disposition fields
- shared read model, report records, PLAN, HANDOFF and A2 goal
- generated Obsidian, MLflow-safe, report and provenance projections

Frozen candidate bytes, candidate count and roles, metrics/tie policy, reserve
predicate, USD 35 A2 forward hard stop, 40-hour admission floor, protected-data
boundary and measured authority were not changed.

## Focused validation

- A2 candidate/contracts/readiness/preflight/executor suite: `74 passed`
- read-model and Obsidian report contract suite: `41 passed`
- earlier focused readiness/read-model subset: `58 passed`
- Ruff on changed Python/test surface: `PASS`
- A2 entry preflight: `PASS_A2_ENTRY_PREFLIGHT`; A2 disposition
  `FRESH_INSTANCE_REQUIRED`; reuse `false`; execution authorized `false`
- synthetic operational dry-run: `PASS_A2_SYNTHETIC_OPERATIONAL_DRY_RUN`, 52/52,
  provider contacted `false`, measured A2 started `false`, protected payload `false`
- `myis-report sync` and `myis-report check`: `PASS`, drift `false`
- `myis-assets validate --mode quick`: `PASS`
- `git diff --check`: `PASS`

One initial combined validation command exceeded its wrapper timeout before a
summary was returned. The affected validations were rerun separately and passed
with the results above.

## Final pushed-HEAD bundle and deployment package

After this handoff is committed and pushed, the clean final `main == origin/main`
revision is used to rebuild and validate the execution bundle and metadata-only
deployment package under:

`../04_Owner_Stores/armindex/a2/a2-im-audit005-final-head-20260813/`

The exact final Git commit/tree, bundle/package hashes, manifest hash and receipt
self-hashes are authoritative in these Owner-local files:

- `execution-bundle.receipt.v1.json`
- `deployment-package.receipt.v1.json`

These final dynamic hashes are intentionally not copied back into Git because
doing so would create a commit/bundle hash cycle. AP must validate both receipts
and their paired archives before provider admission.

## Boundaries and next action

IM did not contact/provision Vast, stage remotely, download models, use GPU or
paid resources, access protected data, create measured authority, evaluate a
candidate, or start measured A2.

AP next reads this handoff, validates the final Owner-local pushed-HEAD bundle and
deployment receipts, obtains fresh aggregate-safe provider evidence, and performs
fresh-instance admission plus isolated staging only. Measured A2 remains closed
pending a separate readiness decision and explicit measured LO goal.
