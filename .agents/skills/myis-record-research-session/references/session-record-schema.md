# Session capsule schema

Use JSON with this minimum shape:

```json
{
  "schema_version": "myis.research-session.v1",
  "session_id": "20260727T120000Z-<short-hash>",
  "run_id": null,
  "goal_id": null,
  "started_at_utc": null,
  "ended_at_utc": "2026-07-27T12:00:00Z",
  "scope": "Concise completed scope",
  "provenance": "agent-observed",
  "owner_approvals": [
    {
      "gate": "R0",
      "source": "verbatim pointer to the Owner approval",
      "scope": "what the approval permits"
    }
  ],
  "repository": {
    "path": ".",
    "revision": "<git-sha>",
    "dirty_paths": []
  },
  "events": [
    {
      "event_id": "EV0001",
      "sequence": 1,
      "type": "decision",
      "provenance": "owner",
      "summary": "Concise fact",
      "evidence_refs": [
        {
          "path": "relative/path",
          "sha256": "<64 hex characters>",
          "locator": "JSON field, row key, or line"
        }
      ]
    }
  ],
  "run_artifacts": {
    "prompt": null,
    "flow": null,
    "progress": null,
    "result": null,
    "metrics": null,
    "runtime": null,
    "per_query_metrics": null,
    "validation_report": null,
    "manifest": null,
    "mlflow_receipts": []
  },
  "open_threads": [],
  "integrity": {
    "all_refs_exist": true,
    "all_hashes_match": true,
    "contains_protected_payload": false,
    "contains_secrets": false
  }
}
```

## Binding rules

- Bind a claim to an experiment and an exact evidence locator.
- Bind a decision to the Owner approval or evidence that motivated it.
- Bind a heuristic to a source path and symbol or line locator.
- Bind a dead end to its observed failure and reusable lesson.
- Keep `agent-proposed` items in `open_threads` until explicitly confirmed or rejected.
- Use `null` for unavailable values; never substitute a guessed value as fact.

The capsule may summarize metrics but cannot supersede `metrics.json`, per-query artifacts, or a validated canonical-results manifest.
