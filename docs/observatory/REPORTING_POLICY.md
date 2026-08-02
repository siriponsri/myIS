# Research Reporting Policy

This is the canonical reporting contract for repository-safe research
projections. Git-tracked control records, validated manifests, receipts,
registries, and the shared read model remain authoritative; Markdown is a
rebuildable explanation of those records.

## Lifecycle

Create a Phase and Task report at start, update it after each material state
change, meaningful run, failure/recovery, or decision, and finalize it or mark
it blocked at close. Generated reports are deterministic and are never edited
by hand. Owner notes are separate and are preserved by sync.

Allowed report lifecycle values are `planned`, `active`, `blocked`,
`completed`, and `superseded`. `evidence_class` and `scientific_authority`
must describe the evidence actually present. A fixture is engineering evidence
only and can never be promoted to measured evidence.

## Required Phase and Task structure

Every Phase and Task report contains these sections, in this order:

1. `Objective`
2. `Starting State`
3. `Inputs and Frozen Bindings`
4. `Work Performed`
5. `Artifacts Produced`
6. `Metrics`
7. `Result`
8. `Interpretation`
9. `Supported Claims`
10. `Unsupported Claims`
11. `Failures and Recovery`
12. `Governance and Safety`
13. `Decision`
14. `Next Action`
15. `Evidence Links`

The report distinguishes output, result, interpretation, decision, and next
action. It uses aggregate-safe references only, explains the purpose of each
important artifact, and links to canonical sources instead of copying values
into a second source of truth. Reports use evidence-led prose without first-
person authorial claims.

## Machine record

`schemas/phase-task-report.v1.json` defines `myis.phase-task-report.v1`.
Each record includes the phase/task identity, lifecycle and evidence boundary,
read-model revision, Git commit, objective, starting state, frozen bindings,
work summary, artifact and metric references, result/interpretation/claims,
failure and governance fields, decision, one next authorized action, evidence
links, validation status, and a self SHA-256. JSON and Markdown are generated
from the same record.

## Safety and contradiction guards

Generated content must not contain qrels, split membership, query IDs,
rankings, per-query outcomes, credentials, secrets, absolute personal paths,
or raw provider payloads. If the canonical fixture is `passed`, no projection
may say it is unexecuted or merely available. If Official Round 3 is accepted,
no projection may say review is pending or required. While P2 measured counters
are zero, no projection may say measured P2 started, Owner-local preflight ran,
real selection opened, or the final split opened. Real and synthetic counters
are always labeled separately.

## Future measured-run integration

The runner integration checklist is in
`docs/observatory/MEASURED_PREFLIGHT_INTEGRATION.md`. It is a prerequisite for
Owner-local measured preflight, not evidence that runtime integration has been
validated. This reporting closeout never opens a measured request or selection.
