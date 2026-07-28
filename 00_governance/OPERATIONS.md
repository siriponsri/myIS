# Research Operations

Use this page for routine repository work. The governing authority remains
`AGENTS.md` and `OWNER_GATES.md`.

## Read-only checks

From the Research repository root:

```powershell
python 05_code/scripts/validate_restructure.py
$env:PYTHONPATH = "05_code/src"
python -m unittest discover -s 05_code/tests -v
git status --short
```

Render and verify Mermaid diagrams:

```powershell
python "C:\Users\Siripon Sri\.codex\skills\mermaid-task-mapper\scripts\render_mermaid_blocks.py" README.md --output-dir 04_outputs/diagrams --theme neutral
python "C:\Users\Siripon Sri\.codex\skills\mermaid-task-mapper\scripts\render_mermaid_blocks.py" PLAN.md --output-dir 04_outputs/diagrams --theme neutral
```

## Before research execution

1. Record the Owner-approved track, questions, budget, sources, and protected
   split boundary.
2. Verify corpus/split hashes and whether the requested scope is offline,
   development or prospective confirmation.
3. Create path candidates when the active gate requires a method choice.
4. Freeze evaluator, module pool, model roles and budget across benchmark arms.
5. Create an immutable run specification and execute preflight/dry-run first.
6. Stop before paid/API/GPU/Vast work, confirmation access or publication.

## Stores and workspaces

Persistent MLflow data belongs under the workspace-level
`01_Stores/00_myIS/mlflow/` boundary. HyperResearch source staging and tool
pilots are disposable workspace data. Do not place datasets, credentials, or
research results inside third-party tool repositories.

The run contract requires prompt, flow, progress, result, metrics, runtime
JSONL, per-query rows, validation report, immutable manifest and append-only
MLflow receipts. See `OBSERVABILITY_AND_RUN_LOGGING.md`.

Run the deterministic demo in the pinned MLflow environment:

```powershell
$workspace = (Resolve-Path ..\..\..).Path
$python = Join-Path $workspace "02_Tools\01_environments\mlflow\Scripts\python.exe"
$env:PYTHONPATH = (Resolve-Path "05_code\src").Path
& $python -m myis_research.harness.cli doctor --research-root . --mlflow-root (Join-Path $workspace "01_Stores\00_myIS\mlflow")
& $python 03_experiments\V01_brain_drive_agent_demo\V01_brain_drive_agent_demo.py
```

## Change control

Do not delete, commit, push, publish, stop a process, access held-out data, or
start a paid/API/GPU/Vast operation unless the corresponding Owner approval is
explicit. Archive moves preserve provenance but still require clearly stated
scope.
