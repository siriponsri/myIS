# Observability and Run Logging Rules

These rules apply to every Research experiment, agent trial, benchmark arm and
notebook demo. `PLAN.md`, `AGENTS.md` and Owner gates still control whether a
run is allowed.

## Authority order

1. Console output is a live human view only.
2. `runtime.jsonl` is append-only diagnostic event truth.
3. `progress.jsonl` is the milestone projection of runtime events.
4. `metrics.json` and `per_query_metrics.jsonl` are numeric truth.
5. MLflow is a searchable mirror of parameters, metrics, artifacts and lineage.
6. A validated immutable `manifest.json` is the paper-facing run index.

Paper tables and reports must read validated manifests and metric artifacts.
They must not scrape stdout, JSONL text, chat summaries or the MLflow UI.

## Required artifacts

```text
prompt.json
flow.json
progress.jsonl
result.json
metrics.json
runtime.jsonl
per_query_metrics.jsonl
validation_report.json
manifest.json
receipts/mlflow-*.json
```

`manifest.json` is written atomically after all canonical run artifacts and is
never overwritten. Later MLflow retries create append-only receipts.

## structlog

Pin `structlog==26.1.0`. Emit each application event once. A shared
`ProcessorFormatter` sends the redacted event dictionary to console and
`runtime.jsonl`; milestone events are additionally projected to
`progress.jsonl` with the same `event_id`.

Every event requires:

```text
schema_version, event_id, timestamp_utc, monotonic_ns, sequence,
level, event, run_id, goal_id, phase, component, status
```

Use dotted event names. Do not log a second hand-written copy for another sink.

## Redaction

Recursively redact token, API key, authorization, cookie, password, secret,
private key and SSH key fields. Do not log full environments, credentials, raw
confidential source text, confirmation query identities or unfiltered command
arguments. Sanitize exception messages before logging.

## MLflow

- Params: immutable dataset, split, seed, model, evaluator, config and budgets.
- Tags: goal, run, trial, arm, phase, git SHA, hashes, approval and manifest SHA.
- Metrics: explicit numeric calls with step where applicable.
- Artifacts: sanitized run bundle and licensed data only.
- Traces: reserve trace/span IDs; payload capture remains disabled until a
  privacy gate explicitly opens it.

SQLite MLflow uses a serialized writer. If sync fails, finalize the local bundle
and write a `sync_deferred` receipt. Retry must be idempotent.

## Failure behavior

- Exception or interrupt: flush logs, preserve partial metrics, finalize a
  failed/interrupted manifest, then re-raise.
- Process or power crash: report incomplete runs that lack a manifest; never
  infer success.
- Disk-full or canonical-write failure: fail closed.
- Tampered artifact, truncated JSONL or split mismatch: invalidate the bundle.
- Rerun: create a new run ID; never overwrite an old bundle.

## Retention

Development logs become review-eligible after 180 days and failed logs after
365 days. Promoted, confirmation and paper runs remain retained until the Owner
approves archiving. A retention job may report eligible items but may not delete
them automatically.
