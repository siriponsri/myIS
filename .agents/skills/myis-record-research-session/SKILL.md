---
name: myis-record-research-session
description: Record a completed myIS research or implementation session as an auditable provenance capsule linked to immutable run artifacts and MLflow receipts. Use after a task or run has finished when decisions, experiments, failures, pivots, claims, prompts, flows, results, metrics, or open threads must be captured without changing scientific evidence.
---

# Record a myIS Research Session

Run this skill only as a post-task epilogue or as the pre-manifest finalization step of an active run. Never interrupt execution to maintain a second live memory system.

## Preserve authority

- Treat `AGENTS.md`, `00_governance/OWNER_GATES.md`, and `PLAN.md` as governing authority.
- Treat validated canonical-results manifests and per-query artifacts as numeric truth. Treat MLflow as a searchable mirror and Brain notes as human-readable pointers.
- Never infer a metric, approval, result, or user decision from silence.
- Never open a protected split, start an experiment, or rerun a command while recording.
- Never modify an existing `manifest.json`. If a run has no manifest yet, finish the capsule and validation before the harness writes the manifest atomically and last.
- Preserve historical names inside evidence citations. Use current paths for new navigation links.

## Collect source evidence

Read only what is required from the completed task:

1. The user request, explicit approvals, and final scope.
2. Repository status, revision, changed-file list, and verification output.
3. The run bundle, if one exists: `prompt.json`, `flow.json`, `progress.jsonl`, `result.json`, `metrics.json`, `runtime.jsonl`, `per_query_metrics.jsonl`, `validation_report.json`, `manifest.json`, and MLflow receipts.
4. Existing session capsules for ID collision checks only.

Do not copy secrets, environment values, raw private document text, or protected query content into the capsule.

## Classify events

Record only research-significant events:

- `decision`: the Owner selected or rejected an alternative.
- `experiment`: an execution produced an artifact or measurement.
- `dead_end`: evidence invalidated or blocked an approach.
- `pivot`: evidence caused a material direction change.
- `claim`: a falsifiable statement was created or changed.
- `heuristic`: a reusable implementation insight with a code reference.
- `action`: a concrete file, command, or validation action occurred.
- `observation`: relevant information that cannot yet be promoted.

Skip routine reads, formatting, and unexecuted speculation unless they affect an open thread.

Assign one provenance value to each event:

- `owner`: explicitly stated or approved by the Owner.
- `agent-observed`: directly supported by a file, command output, or run artifact.
- `agent-proposed`: suggested or inferred but not Owner-confirmed.
- `owner-revised`: an earlier agent proposal corrected by the Owner.

Default to `agent-proposed` when uncertain. Never upgrade provenance automatically.

## Write the capsule

Read [references/session-record-schema.md](references/session-record-schema.md) and follow its schema.

Choose the target without overwriting existing evidence:

- During an active run before finalization: write `research_session.json` in that run bundle, then let normal validation and manifest finalization continue.
- For a finalized run: write an external review capsule under `04_outputs/audits/research-sessions/<run_id>-<session_id>.json` and point to the immutable run.
- For non-run work: write `04_outputs/audits/research-sessions/<session_id>.json`.

Use UTC timestamps and collision-resistant IDs. Link artifacts by repository-relative path plus SHA-256. Store a brief paraphrase of prompts or decisions only when necessary; otherwise link the canonical artifact.

For every quantitative statement, include the exact artifact and JSON field or row key that supports it. Mark missing bindings as open obligations instead of inventing values.

## Validate and mirror

1. Re-read the capsule and verify all required fields.
2. Verify every referenced path and SHA-256.
3. Verify event sequence order and provenance values.
4. Verify the capsule does not contain credentials, protected payloads, or unapproved metrics.
5. If an approved MLflow run exists, mirror the capsule as an artifact and record the resulting append-only receipt. Do not make MLflow the only copy.
6. Report counts for decisions, experiments, claims, failures, and open threads in one concise summary.

Do not alter Git state, publish, or write to the Brain as part of this skill.

## Upstream attribution

This project-specific workflow adapts the event taxonomy and conservative provenance principles from Orchestra Research's `ara-research-manager`. The pinned source and adaptation record are in `00_governance/config/tools.lock.yaml`; the upstream MIT notice is preserved in `LICENSE.upstream`.
