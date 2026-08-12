---
schema_version: myis.research.implementation-handoff.v1
phase: A2_PER_ARM_AUTOINDEX
task: A2.1_FROZEN_FIVE_ARM_EXECUTION
session_mode: IM
source_audit: docs/audit/A2_PER_ARM_AUTOINDEX_audit_002.md
revision: 4a2ba332c596ae2d256d8c6897276cb5207ec336
status: IMPLEMENTED_VALIDATED_TTL_EXTENSION_REQUIRED
---

# IM Handoff 002-001

## Implementation summary

- Replaced caller-controlled admission hashes with a versioned, self-hashed,
  aggregate-safe provider observation and URI/file-hash source bindings.
- Admission derives remaining TTL from fresh `ttl_deadline_utc`, enforces the
  900-second freshness limit, and fails below 40 hours.
- Added mandatory pinned-SSH live probing before remote mutation: provider,
  runtime, GPU UUID/topology/processes, model/data, bundle, root and TTL identity.
- Stage/adoption receipts bind provider observation and live-probe receipt bytes.
- Frozen 52-candidate semantics and all protected/measured locks remain unchanged.

## Changed surface

A2 readiness/executor source, provider/live-probe/stage/adoption schemas, focused
tests, deterministic artifact provenance projections, `PLAN.md`, `HANDOFF.md`,
and this handoff.

## Checks

- Focused A2 suite: `44 passed`.
- Ruff and changed-schema parse: PASS.
- Entry preflight: `PASS_A2_ENTRY_PREFLIGHT`, `a2_execution_authorized=false`.
- Synthetic dry-run: PASS; 52 candidates, five winners,
  `provider_contacted=false`, `measured_a2_started=false`.
- Report/provenance drift and `git diff --check`: PASS.

## Staging state

No provider login/logout, API call, remote stage, GPU work, model download,
protected-data access, candidate evaluation or measured A2 execution occurred.
AP's last aggregate-safe evidence had about 3.38 hours remaining, below the
mandatory 40-hour threshold. No admission/adoption/live evidence was fabricated.

## Clean pushed bundle

- Pushed implementation revision: `4a2ba332c596ae2d256d8c6897276cb5207ec336`
- Git tree: `beeaa90ff662f5712bd6cde944eb67b4c25b6148`
- Owner-local path: `../04_Owner_Stores/armindex/a2/a2-im-audit002-20260812/`
- Bundle SHA-256: `73d7668237ac9fa26cecc2b520bced63f21a338f928151cd30bf2d5b4bf49515`
- Receipt SHA-256: `8202676c7e251eaa9de6ad8c40f26d5fe3bba75add0d04d8bbb50aeb753d90f3`
- Receipt status: `PASS_CLEAN_HASH_BOUND_A2_BUNDLE`; clean worktree and
  `main == origin/main` were verified by the bundle builder.

## Routing

`NEEDS_OWNER_TTL_EXTENSION`
