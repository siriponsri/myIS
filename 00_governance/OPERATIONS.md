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
2. Verify U041 status explicitly.
3. Create three path candidates from `00_governance/templates/`.
4. Stop for one Owner Top-1 selection.
5. Create an immutable experiment manifest and run Gates 0-3 in order.
6. Stop again before protected held-out access or publication.

## Stores and workspaces

Persistent MLflow data belongs under the workspace-level
`01_Stores/00_myIS/mlflow/` boundary. HyperResearch source staging and tool
pilots are disposable workspace data. Do not place datasets, credentials, or
research results inside third-party tool repositories.

The offline contract requires `prompt.json`, `flow.json`, `progress.jsonl`,
`result.json`, and `metrics.json` for every agent run, including failed runs.
Install the `tracking` extra to mirror these artifacts and numeric metrics into
the shared local MLflow SQLite/artifact store; the file ledger remains the
offline and failure-safe source of audit evidence.
Run the deterministic demo without external dependencies:

```powershell
python 03_experiments/V01_brain_drive_agent_demo/V01_brain_drive_agent_demo.py
jupyter-nbconvert --to notebook --execute 03_experiments/V01_brain_drive_agent_demo/V01_brain_drive_agent_demo.ipynb --output executed.ipynb
```

## Change control

Do not delete, commit, push, publish, stop a process, access held-out data, or
start a paid/API/GPU/Vast operation unless the corresponding Owner approval is
explicit. Archive moves preserve provenance but still require clearly stated
scope.
