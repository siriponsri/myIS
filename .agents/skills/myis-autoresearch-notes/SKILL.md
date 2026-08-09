---
name: myis-autoresearch-notes
description: Build and maintain Thai-first, beginner-readable research notes and implementation handoffs from safe repository metadata. Use after CPU/GPU sprints, protocol repairs, dashboard work, or before commit/push when the Owner needs a clear status, evidence, Gate request, and next-action summary.
---

# Research Notes Workflow

Use this skill when a myIS session needs a durable explanation of what the
agent did, what is blocked, what the evidence means, and what the Owner must
decide. It is a projection workflow: Git, validated manifests, and immutable
Gate records remain authoritative.

## Workflow

1. Read `PLAN.md`, the active task files, the latest valid session capsule, and
   `HANDOFF.md`.
2. Run `myis-assets validate --mode quick` and the task-specific asset query.
3. Separate fixture, development, descriptive, and confirmation evidence.
   Never place qrels, protected IDs, membership, per-query outcomes, or
   credentials in a note.
4. Write or regenerate a generated note under `obsidian_report/` with a YAML
   frontmatter contract and a Thai-first body. Explain difficult English terms
   in plain Thai on first use.
5. Close every implementation session with Phase, Task, Gate, status, checks,
   changed files, untouched protected surfaces, Owner actions, requested
   Owner decisions, and next-phase resources.
6. Validate the catalog, Dashboard response, session capsule, and `HANDOFF.md`
   before commit/push. If Brain cannot be updated through its serial-writer
   lease, stop before commit/push.

## Note contract

Generated notes must use `myis.obsidian-note.v2`, contain only allowlisted source
paths, stay below 512 KiB, and expose pathless `obsidian://` links. Use the
repository report and asset validators (there is no separate
`myis_research.notes` module in this project):

```powershell
uv run --no-sync myis-report build --repository-root .
uv run --no-sync myis-report check --repository-root .
uv run --no-sync myis-assets validate --mode quick
```

See [note-contract.md](references/note-contract.md) for the field meanings and
the Owner-readable closeout template.

## GPU handoff rule

After a GPU Sprint, pull and validate all allowlisted artifacts locally, stop
remote processes, record local metrics/MLflow-safe artifacts and manifests,
then classify the live instance from verified same-attempt evidence before the
Owner acts:

- `REUSE_ELIGIBLE` only when safe return passed, frozen identities are
  unchanged, workers and protected scans are clean, the tested provider
  destroy path remains available, budget and TTL are sufficient, and an
  already-authorized compatible next PLAN workload exists. Report
  `Owner continue next goal on PLAN`; this does not authorize that goal.
- `DESTROY_REQUIRED` for drift, unknown state, safety or protected-data
  concern, budget or TTL pressure, missing next-goal authorization, or a
  scientific boundary requiring fresh provider admission. Report
  `Owner destroy instance` and wait for Owner confirmation before local
  continuation that depends on provider closeout.

Never retain an idle instance without an explicit evidence-backed disposition,
and never let a reuse decision broaden scientific or execution authority.
