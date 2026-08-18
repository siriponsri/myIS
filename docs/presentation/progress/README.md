# ArmIndex Current Progress Deck

This folder contains a short, advisor-facing update for the current ArmIndex
state on 19 August 2026. It is intentionally separate from the full advisor
talk under `docs/presentation/`.

## Contents

- `progress_A3_current.md`: slide copy, presenter notes, source pointers, and
  claim boundaries.
- `build_progress_A3_current.mjs`: reproducible PowerPoint source.
- `ArmIndex_Progress_A0_A3_2026-08-18.pptx`: editable six-slide deck.
- `ArmIndex_Progress_A0_A3_2026-08-18.inspect.ndjson`: object and speaker-note
  inspection record.
- `QC.md`: focused content and layout review.

## Rebuild

From the repository root, use the local Artifact Tool workspace:

```powershell
$skill = 'C:\Users\Siripon Sri\.codex\plugins\cache\openai-primary-runtime\presentations\26.802.11031\skills\presentations'
$build = 'docs\presentation\progress\.build'
node "$skill\container_tools\setup_artifact_tool_workspace.mjs" --workspace $build
Copy-Item docs\presentation\progress\build_progress_A3_current.mjs "$build\build_progress_A3_current.mjs" -Force
$env:PROGRESS_ROOT = (Resolve-Path docs\presentation\progress).Path
node "$build\build_progress_A3_current.mjs"
```

The slide deck uses summary A1/A2 figures only. It contains no protected
records, relevance judgments, split membership, rankings, or per-query output.
