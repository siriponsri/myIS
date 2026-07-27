# Archive cutover — 2026-07-27

Owner approval: YES, current session.

Safety checks completed before mutation:

- All nine Research legacy shells contained zero entries.
- `Projects/myIS/App` contained zero entries.
- No external process command or executable referenced
  `Tools/experience-brain-is1-runtime` at cutover.
- Source and target paths resolved inside the My_Research workspace and target
  directories did not already exist.

Actions:

| Source | Destination/action |
|---|---|
| `Projects/` | `99_Archive/00_myIS/navigation-shells/legacy-Projects-shell-20260727/` |
| `Tools/experience-brain-is1-runtime/` | `99_Archive/00_myIS/experience-brain-is1/runtime-20260727/` |
| Empty Research shells: `artifacts`, `config`, `docs`, `mlartifacts`, `mlruns`, `research`, `runtime`, `templates`, `tracks` | Removed after zero-entry check |
| Empty root `Tools/` shell | Removed after runtime archival |

No App PDF, Brain note, scientific result, held-out data, or historical
provenance record was deleted.
