# A2 IM 010-001: successor local aggregate evaluation closure

- Session mode: `IM`
- Phase/Task: `A2_PER_ARM_AUTOINDEX / A2.1 FROZEN_FIVE_ARM_EXECUTION`
- Source audit: `docs/audit/A2_PER_ARM_AUTOINDEX_audit_010.md`
- Implementation revision: `dd19996` (`Add A2 successor local evaluation authority`)
- Routing: `READY_FOR_AP`

## Outcome

IM implemented an additive successor authority path for the full frozen A2
lifecycle. Authority v3 permits only Owner-local, aggregate-safe REP-DEV
evaluation after a remote retrieval result has returned. It binds the existing
52 candidate IDs, frozen order, program hashes, freeze commitments, Owner-local
manifest, evaluator, qrels, membership, query-token map, runtime, model-lockset,
data-handoff, and exact transport request commitments.

Authority v2 and Goal 002 remain unchanged historical failed-prelaunch lineage.
The production remote path now fails before it can invoke the Owner-local
evaluator under v2. Remote retrieval still receives no qrels, membership, or
evaluator payload, and it cannot return an aggregate result that contains a
protected payload or per-query outcome.

The candidate universe, order, model/data bindings, strict-tie policy, matched
barrier, reserve predicate and floor, ARM-01/02 non-advancement, A3/Selection/
Final closure, USD 50 Task/Run hard stop, USD 150 Phase ceiling, 84-hour total
TTL, and 40-hour initial admission floor are unchanged.

No provider operation, candidate generation/mutation, measured A2 execution,
candidate evaluation, REP-DEV measurement, model download, or protected-data
exposure outside the Owner-local boundary occurred in this IM session.

## Changed Surface

- Added authority v3, commitment v2, and remote transport v3 schemas.
- Added the tracked v2 pending-AP commitment contract. It remains scientific
  authority `false` and binds a future v3 authority without reusing v2.
- Added successor authority validation and Owner-local artifact binding checks
  before qrels, membership, or token-map access.
- Updated remote execution binding so a successor must use commitment v2,
  transport v3, a fresh numeric provider identity bound in authority, and the
  exact Owner-local manifest/transport request hashes.
- Updated remote executor handoff so opaque rankings are evaluated only locally
  with v3 authority; a missing or v2 authority fails closed.
- Extended the immutable execution-bundle closure with every new schema/control.

## Focused Validation

- `tests/test_armindex_a2_operational_executor.py`: `40 passed`.
- `tests/test_armindex_a2_remote_transport.py`,
  `tests/test_armindex_a2_owner_local_engine.py`, and
  `tests/test_armindex_a2_execution_readiness.py`: `39 passed`.
- Successor commitment v2 schema and canonical self-hash: `PASS`.
- Ruff on changed implementation and tests: `PASS`.
- `myis-report check --repository-root .`: `PASS`; no projection/read-model drift.
- `git diff --check`: pending final commit check.

## AP Successor Requirements

AP must independently create a new clean pushed bundle, attempt ID, isolated
remote root, Owner-local manifest, transport configuration, adoption, authority
v3, and Goal 003. The provider quote/admission from the v2 lineage is stale and
cannot be reused. AP must not permit a remote evaluator, protected output, A3,
Selection, Final, D2, or D3.

## Limitation

This is an engineering repair, not measured scientific evidence. The new
authority and successor LO goal are intentionally absent; only AP may issue
them after reviewing the fresh bundle and current provider/budget/TTL evidence.
