# myIS Research 1.0 Local Operations

Run commands from the Research repository root. `AGENTS.md`, `PLAN.md`, and
`OWNER_GATES.md` remain authoritative.

## Reusable asset preflight

Use the Research registry before creating or recomputing an artifact:

```powershell
uv run --no-sync myis-assets validate --mode quick
uv run --no-sync myis-assets query --task <TASK_ID>
uv run --no-sync myis-assets query --asset-id <ASSET_ID> --json
uv run --no-sync myis-assets map --check
```

Quick validation checks registry structure, source existence, byte anchors,
manifest presence, and registered-path Git drift without reading protected
payloads. Full validation hashes source files and manifest closures, and is
fail-closed before protected content:

```powershell
uv run --no-sync myis-assets validate --mode full --asset-id <ASSET_ID> `
  --approval-record <OWNER_GATE_DECISION.json>
```

An unrelated App HEAD advance is a warning. A changed registered path, byte
anchor, source SHA-256, or manifest SHA-256 is a drift failure. Do not edit App
assets in place or use the registry as Gate approval.

## Clean locked environment

Python 3.11 and `pyproject.toml + uv.lock` are canonical. Select only the groups
and extras required by the task and record them in measured manifests.

```powershell
uv sync --locked --extra tracking --extra dashboard --extra test --extra notebook
uv run --no-sync python 05_code/scripts/capture_environment.py
```

Replay uses the exact recorded groups/extras. Hashed requirements may be
exported for interoperability but cannot replace `uv.lock`.

## Required offline checks

```powershell
git status --short
git rev-parse HEAD
git branch --show-current
uv run --no-sync python 05_code/scripts/validate_restructure.py
uv run --no-sync python 05_code/scripts/validate_integrity.py
uv run --no-sync python -m unittest discover -s 05_code/tests -v
git diff --check
```

A test failure caused by a missing locked dependency is an environment failure;
do not edit the test to bypass it.

## BATCH_2A canonicality procedure

For `BATCH_2A_ARTIFACT_VALIDATION.json`, `BATCH_2A_CSV_VALIDATION.json`, and
`BATCH_2A_INGESTION_CANDIDATES.csv`:

1. compare worktree bytes, Git index/blob bytes, and manifest expected SHA-256;
2. identify the producer, source input, timestamp, encoding/line-ending policy,
   and any historical validation record;
3. parse the records semantically and validate counts, keys, references, and
   backlinks independently;
4. determine whether current bytes reproduce from the documented producer, or
   whether the manifest expectation points to a known canonical historical blob;
5. record the decision and evidence hashes through G0;
6. never replace an expected hash merely to make the validator pass.

## Standard run preparation

1. Identify Phase/Task, track, stage, primary metric, comparator, budget, and Gate.
2. Verify `myIS Research` / `myis-research`, protocol `1.0`, Track C/S version
   `0.1`, and the exact approval record.
3. Validate corpus/split/qrels/family/evaluator/protected-surface commitments.
4. Confirm only adaptation/selection labels are reachable and disable network
   re-download during measured optimization.
5. Create a manifest v3 `RunSpec` with exact environment/provider/repeat fields.
6. Run preflight and deterministic fixture/dry-run tests before scientific data.
7. Stop before any unapproved API/GPU/Vast/vLLM/PageIndex/external action.

## Current F1/G1 preparation boundary

Current verified readiness is `F0 = closed`, `G0 = approved`,
`F1 = waiting_gate`, and `G1 = pending`. Preparation may create or validate
non-executable drafts and fail-closed adapter scaffolding. Only the dedicated
Owner-local preparation command may read the declared corpus/query/qrels files,
and only to validate/hash them and produce sealed membership plus safe
aggregates. No agent-facing raw data, confirmation surface, measured evaluation,
paid API, or GPU resource is authorized.

`myis-harness reproduce dapfam` is not a scientific execution path at this
state. Until a future valid G1 authorization and frozen RunSpec are supplied,
it must fail closed as unavailable or `waiting_gate` before any protected or
scientific access. Help, dry-run, and schema-only validation do not authorize
reproduction and cannot create measured manifests or scientific metrics.

Run the complete preparation workflow from the repository root without editing
YAML or moving the source data:

```powershell
& ".\05_code\scripts\Start-F1G1Preparation.ps1"
```

The command discovers the approved in-place DAPFAM source, validates exact byte
anchors, computes full SHA-256 hashes, checks query/qrels/corpus alignment,
creates the deterministic `250/125/872` split, seals raw IDs outside Git, writes
an append-only safe batch, validates redaction, mirrors one zero-metric
preparation run, and executes the safe review notebook. Absolute source paths
stay only in external `config/owner-paths.json`; Dashboard and MLflow receive no
membership or payload.

Use the read-only validator independently:

```powershell
uv run --no-sync python 05_code/scripts/validate_f1_g1_preparation.py
```

`--describe-schema` reports field names and aggregate identifier counts only and
writes nothing. A failed or corrected semantic proposal is retained and a new
append-only proposal supersedes it through `safe/projections/current.json`.

## Scientific phase commands

Commands below are target interfaces until their adapters are implemented and
validated. Do not infer availability from documentation. The DAPFAM command is
currently a non-executable F1/G1 scaffold: it can validate its checked-in draft
only when explicitly requested, always returns `WAITING_GATE`, and never opens
research data, qrels, a provider, GPU, MLflow, or a run-artifact directory.

```text
myis-harness doctor
myis-harness reproduce dapfam --manifest 03_experiments/templates/f1-dapfam-runspec-draft.yaml --dry-run
myis-harness audit shared-split --manifest PATH
myis-harness audit c-margin --manifest PATH
myis-harness run dev --track C --arm C0 --manifest PATH
myis-harness search --track C --arm C1 --manifest PATH
myis-harness select --track C --arm C1 --manifest PATH
myis-harness freeze c1-harness --manifest PATH
myis-harness diagnostic c-ranking --manifest PATH
myis-harness audit s-margin --manifest PATH
myis-harness optimize --track S --arm A2 --manifest PATH
myis-harness optimize --track S --arm A2L --manifest PATH
myis-harness optimize --track S --arm A3 --manifest PATH
myis-confirmation emit-request --request-id ID --git-commit COMMIT `
  --submission-hash C=SHA256 --config-hash C=SHA256 `
  --protocol-hash analysis=SHA256 --output REQUEST.json
myis-confirmation validate-aggregate --request REQUEST.json --aggregate AGGREGATE.json
myis-harness report owner --manifest PATH
```

The external Owner-run confirmation evaluator is intentionally not a repository
command. The repo only emits/validates hash-only/aggregate-only packages.

## Dashboard startup and security

Use the singleton Owner Console launcher after the locked extras are installed.
It reuses a healthy myIS Dashboard on ports 8765-8770 and never installs
dependencies automatically. Bind exactly to loopback; remote hosts are invalid.

```powershell
uv sync --locked --extra dashboard --extra tracking --extra notebook --extra test
& 06_frontend/start_owner_console.ps1 -NoBrowser
```

Open `http://127.0.0.1:8765`. The same-origin Owner console reads the canonical
plan, process, flow, harness-rule, tool, gate, and artifact projections. Evidence
completion is operational evidence only; authorization remains a separate Owner
Gate state.

The Owner view is Thai-first and opens on Today/Owner Inbox. Data and
Presentation show registry-derived DAPFAM metadata, in-place lineage, and an
explicit no-results guardrail without live fetches. The execution path renders
directly from `PLAN.md` as `Phase -> Task`. Each Task shows its purpose, inputs, outputs,
tests, acceptance criteria, Gate, budget/stop rule, rollback, risk, evidence,
dependencies, and Linear issue/status. The Gate handbook explains in plain
language what approval opens and what remains locked. PLAN is canonical;
Dashboard, Linear, and MLflow are validated projections and cannot open a Gate.

Use the validated session index instead of rereading every historical capsule:

```powershell
uv run --no-sync myis-sessions validate-all
uv run --no-sync myis-sessions latest-valid --task F1.1 --gate G1
```

Every implementation closeout includes a Gate request state, Owner actions,
and next resources. This request is a report only; approval still requires the
existing preview-confirm decision flow and immutable Gate record.

The interactive Flow computes completion only from validated canonical Task
evidence, uses Linear only as a work-tracking signal, and keeps Gate approval as
a separate status. It provides Phase jump controls, human-readable filters, and
automatic refresh every 60 seconds while the page is visible. A Linear `Done`
without canonical evidence is shown as `Verify evidence`, never `Complete`.

Before a decision write, inspect the preview, evidence hashes, Git commit,
authoritative OS actor ID, and prior-record hash, then explicitly confirm. The
browser never supplies authoritative actor identity. Do not add CORS/CDN or
remote binding. A future remote deployment requires a new authenticated identity
architecture and Owner decision.

An `approved` preview must select at least one verified evidence package from
`00_governance/config/evidence_catalog.yaml`. The backend verifies its path,
SHA-256, Gate, Phase, and Task compatibility; free-form evidence hashes cannot
authorize an approval. Rejection or deferral may still be recorded without an
evidence package. Existing immutable decisions remain readable even when they
predate the catalog.

## PDF viewer operation

Default to metadata/hash display. Stream a PDF only when its exact path and
SHA-256 are in the Owner-approved allowlist and license/privacy approval is
recorded. The viewer writes one ignored local receipt before access and returns
no protected evaluation artifacts.

On a lost/corrupt local receipt ledger:

1. stop PDF access and preserve the damaged root read-only;
2. verify ACLs, receipt hashes, links, and the last Git-anchored chain head;
3. record the unrecoverable range and cause through an Owner decision;
4. create a new local ledger root with a genesis record referencing the last
   trustworthy head and incident decision;
5. never fabricate missing receipts or call the chain tamper-proof.

## MLflow operation and recovery

Set `MYIS_MLFLOW_STORE` to the approved persistent root outside Git. Bootstrap
logs no artifacts and no scientific metrics. Catalog/scientific projection uses
explicit validated/redacted files only.

For the current F0 closeout, bootstrap is limited to the approved external
runtime root, `database/mlflow.db`, `artifacts/`, and a connectivity record
showing `scientific_run=false`, `dataset_access=none`, `artifact_count=0`, and
`scientific_metric_count=0`. Do not run governance-document replay or mirroring
as part of this bootstrap; that requires separate Owner approval after review.

Validate the important-document catalog without writing to MLflow:

```powershell
uv run --no-sync python 05_code/scripts/sync_governance_documents.py --dry-run
```

After the source commit is clean, mirror the allowlisted governance documents:

```powershell
uv run --no-sync python 05_code/scripts/sync_governance_documents.py
```

Each document run records its canonical SHA-256 plus the validated PLAN, Phase,
Task, Gate, Linear issue, Dashboard content, and MLflow experiment bindings.
This is an additive, rebuildable mirror; the documents and decisions in Git
remain authoritative.

Use the Git Bash launcher for browser access. It opens MLflow through the pinned
read-only WSGI guard; it never starts the standard writable server directly.

```powershell
& "C:\Program Files\Git\bin\bash.exe" "06_frontend/mlflow/mlflow.sh" doctor
& "C:\Program Files\Git\bin\bash.exe" "06_frontend/mlflow/mlflow.sh" start
```

Open `http://127.0.0.1:5000`. `start` runs in the foreground and stops with
Ctrl+C. The launcher rejects WSL, remote binding, unknown MLflow route maps,
write-capable database URIs, occupied ports, and version drift.

For non-developer Owner operation, open `06_frontend/` in Windows Explorer and
double-click `START_OWNER_CONSOLE.cmd`. It starts both loopback services and
opens their browser tabs without installing or synchronizing dependencies.
Double-click `STOP_OWNER_CONSOLE.cmd` to stop the two services.

If MLflow is unavailable, the canonical run remains valid and an immutable
`sync_deferred` receipt is written. Recovery:

1. validate canonical Git/run artifacts and hashes;
2. quarantine the corrupt MLflow store without changing canonical files;
3. generate a `rebuild_plan` from explicit allowlisted artifacts;
4. replay idempotent mirror specs through the serialized writer;
5. compare mirror receipts and canonical hashes; never auto-repair source files.

## Run output and authority

Every scientific run contains applicable prompt/skill/flow/config, runtime and
progress JSONL, candidate/evidence/per-query rows, metrics/statistics/result,
validation/environment, immutable manifest, and receipts. Logs are diagnostic;
validated metrics/statistics are numeric artifacts; the manifest is the
paper-facing index; MLflow/Brain are mirrors/pointers.

## Failure handling

Classify source/parser, identity/family, split/leakage, query grounding,
exposure, fusion/ranking, evidence, evaluator, provider/model, budget/resource,
or incomplete/tampered bundle. Stop before retry when the class is unknown.
Resume only from a checkpoint whose input/config hashes match. Never report only
successful repeats, tune from confirmation aggregates, or use a stronger claim
than the Gate classification permits.

## CPU/GPU sprint closeout

Use CPU-local work for fixture replay, code, manifests, dependency and dry-run
checks. When a GPU Sprint is authorized, record the instance, wall cap, cost
formula, egress scope, SSH request, and no-fallback rule in the session capsule.
Pull only allowlisted aggregate/hash artifacts, validate locally, stop remote
processes, and then pause with:

> บันทึกข้อมูลครบทุกอย่างแล้ว เสนอ Owner destroy Vast Instance ทันที หลังจากนั้น ให้ Owner พิมพ์ “ดำเนินการต่อ” เพื่อทำงานต่อบน local project ครับ

Do not run another command until the Owner confirms destruction and types
`ดำเนินการต่อ`.

Before `git commit` or `git push`, update `HANDOFF.md`, relevant docs, generated
Obsidian notes, and the Brain pointer. Validate all projections and the serial
Brain writer first; a failed Brain update blocks commit/push.
