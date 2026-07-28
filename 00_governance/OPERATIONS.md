# IS1 Research V0.1 Local Operations

Run commands from the Research repository root. `AGENTS.md`, `PLAN.md`, and
`OWNER_GATES.md` remain authoritative.

## Clean locked environment

Python 3.11 and `pyproject.toml + uv.lock` are canonical. Select only the groups
and extras required by the task and record them in measured manifests.

```powershell
uv sync --locked --extra tracking --extra dashboard --extra test
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
2. Verify IS1 V0.1 identity and the exact approval record.
3. Validate corpus/split/qrels/family/evaluator/protected-surface commitments.
4. Confirm only adaptation/selection labels are reachable and disable network
   re-download during measured optimization.
5. Create a manifest v3 `RunSpec` with exact environment/provider/repeat fields.
6. Run preflight and deterministic fixture/dry-run tests before scientific data.
7. Stop before any unapproved API/GPU/Vast/vLLM/PageIndex/external action.

## Scientific phase commands

Commands below are target interfaces until their adapters are implemented and
validated. Do not infer availability from documentation.

```text
myis-harness doctor
myis-harness reproduce dapfam --manifest PATH
myis-harness audit exposure --manifest PATH
myis-harness run dev --track C --manifest PATH
myis-harness compare C --manifest PATH
myis-harness freeze pool --manifest PATH
myis-harness audit ranking --manifest PATH
myis-harness run dev --track R --manifest PATH
myis-harness compare R --manifest PATH
myis-harness optimize --arm A2 --manifest PATH
myis-harness optimize --arm A3 --manifest PATH
myis-confirmation emit-request --request-id ID --git-commit COMMIT `
  --submission-hash C=SHA256 --config-hash C=SHA256 `
  --protocol-hash analysis=SHA256 --output REQUEST.json
myis-confirmation validate-aggregate --request REQUEST.json --aggregate AGGREGATE.json
myis-harness report owner --manifest PATH
```

The external Owner-run confirmation evaluator is intentionally not a repository
command. The repo only emits/validates hash-only/aggregate-only packages.

## Dashboard startup and security

Use the `myis-dashboard` entry point after the dashboard extra is installed.
Bind exactly to loopback; remote hosts are invalid.

```powershell
uv run --no-sync myis-dashboard --repository-root . --port 8765
```

Open `http://127.0.0.1:8765`. The same-origin Owner console reads the canonical
plan, process, flow, harness-rule, tool, gate, and artifact projections. Evidence
completion is operational evidence only; authorization remains a separate Owner
Gate state.

Before a decision write, inspect the preview, evidence hashes, Git commit,
authoritative OS actor ID, and prior-record hash, then explicitly confirm. The
browser never supplies authoritative actor identity. Do not add CORS/CDN or
remote binding. A future remote deployment requires a new authenticated identity
architecture and Owner decision.

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

Use the Git Bash launcher for browser access. It opens MLflow through the pinned
read-only WSGI guard; it never starts the standard writable server directly.

```powershell
& "C:\Program Files\Git\bin\bash.exe" "06_forntend/mlflow/mlflow.sh" doctor
& "C:\Program Files\Git\bin\bash.exe" "06_forntend/mlflow/mlflow.sh" start
```

Open `http://127.0.0.1:5000`. `start` runs in the foreground and stops with
Ctrl+C. The launcher rejects WSL, remote binding, unknown MLflow route maps,
write-capable database URIs, occupied ports, and version drift.

For non-developer Owner operation, open `06_forntend/` in Windows Explorer and
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
