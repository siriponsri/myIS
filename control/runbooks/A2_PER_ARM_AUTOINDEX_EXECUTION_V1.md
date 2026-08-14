# A2 Per-arm AutoIndex Execution

## Scope

This runbook creates readiness evidence, an isolated staging root, and only
then permits the separately governed A2 runner to begin. It never generates or
mutates a candidate. The immutable A2 input is 40 matched candidates plus 12
dormant conditional-reserve candidates. ARM-01 and ARM-02 remain diagnostic
and non-advancing.

## Checkpoints

1. Verify the candidate manifest, freeze receipt, and lock byte hashes. Stop on
   any mismatch or any non-zero protected, candidate-evaluation, or measured
   counter.
2. Build a clean hash-bound execution bundle. The bundle may contain only
   allowlisted code, controls, schemas, hashes, and aggregate-safe pointers.
3. Collect fresh provider identity, 4x RTX 3090 runtime/model/data hashes,
   all-fee quote, whole-workload budget, management authority, and SSH evidence
   for a runtime-supplied fresh Vast instance. Bind the observation with
   `a2-provider-instance-binding.v1.json`; never reuse the destroyed historical
   instance or relax a v1 receipt. Vast CLI is preferred; `OwnerDashboardSsh`
   is valid only with pinned SSH evidence and
   `OWNER_MANUAL_DASHBOARD_DESTROY_READY`.
4. Require a forward all-fee hard stop no greater than USD 35 and at least
   40 hours remaining from a fresh absolute TTL deadline. The Owner-approved
   total instance TTL is 60 hours. Reject unknown fees or a partial-arm quote.
5. Create `/opt/myis/a2-<attempt-id>` only after provider admission passes,
   stage the immutable bundle, and install a new TTL/watchdog receipt. Never
   mutate or reuse an A1 remote root.
6. Launch with `control/armindex/a2/measured-command-argv.v1.json` and the
   hash-bound Owner-local input manifest. Execute and durably receipt exactly
   the 40 matched candidates first. Resume never reruns a durable receipt.
7. At the matched barrier, stop with
   `MATCHED_COMPLETE_RESERVE_ADMISSION_REQUIRED` until a fresh admission still
   proves at least the deterministic reserve floor
   `ceil(worst_case_dense_parallel_critical_path_seconds - matched_dense_parallel_critical_path_seconds + owner_ttl_reserve_seconds) = 53848s`
   and the unchanged USD 35 hard stop. The initial admission floor remains 40h
   and is not reused for reserve admission.
8. Derive the three primary-arm decisions from the frozen batch order,
   Owner-local A1 v16 incumbents, strict primary improvement, and the actual
   four frozen reserve axes. Persist one decision and one continuation receipt.
   Each reserve arm is then either four active results or four dormant receipts.
9. Evaluation measures the frozen REP-DEV view and emits aggregate-only receipts;
   query IDs, qrels, membership, rankings, and per-query outcomes remain Owner-local.
   Winner selection rejects exact ties and cannot advance ARM-01 or ARM-02.
10. Safe return validates archive hashes and excludes protected payloads. Do not
   destroy the provider instance.

## Fresh-instance staging commands

Use `control/armindex/a2/execution-readiness-contract.v2.json` and
`control/execution-envelope-a2-readiness-v2.yaml` for the current route. These
commands are for a future AP/LO staging session; IM does not run them. All paths
below are Owner-local unless explicitly remote.

```powershell
$attempt = "a2-<fresh-attempt>"
$owner = "<owner-local-a2-root>"
$source = "$owner/provider-evidence"
$stage = "$owner/stage"

# Before provider contact, build and validate the metadata-only deployment package
# from the final pushed-HEAD A2 bundle and existing Owner-local assets.
uv run --no-sync python -m myis_research.armindex.a2_operational_executor --repository-root . --attempt-id $attempt deployment-package --output "$owner/deployment-package.tar.gz" --receipt-output "$owner/deployment-package.receipt.v1.json" --arm-02-model-root "<owner-store>/a1.2-vast-20260806/models/ARM-02" --arm-03-model-root "<owner-store>/a1.2-vast-20260806/models/ARM-03" --arm-04-model-root "<owner-store>/a1.2-vast-20260806/models/ARM-04" --arm-05-model-root "<owner-store>/a1.2-vast-20260806/models/ARM-05" --wheelhouse-root "<owner-store>/a1.2-vast-20260806/build-context/runtime/wheelhouse" --a1-baseline-root "<owner-store>/armindex-a2/a1-baseline-safe-return/a12-v16-20260811-r15" --a1-journal-root "<owner-store>/a1.2-v16-20260809/runs/a12-v16-20260811-r15/journal-eda-r15/a12-v16-20260811-r15" --a1-closeout-root "<owner-store>/a1.2-v16-20260809/runs/a12-v16-20260811-r15/provider-closeout-r15/remote-closeout-mirror/a12-v16-20260811-r15" --runtime-identity "<owner-store>/a1.2-v16-20260809/runs/a12-v16-20260811-r15/admission/receipts/ssh-runtime.receipt.v16.json" --frozen-a1-bundle "<owner-store>/a1.2-v16-20260809/transfer/a1.2-engineering-execution-bundle-v16-frozen-69a056f7.tar.gz" --frozen-a1-bundle-receipt "<owner-store>/a1.2-v16-20260809/receipts/a1.2-engineering-execution-bundle-v16-frozen-69a056f7.json" --a2-bundle "$owner/execution-bundle.tar.gz" --a2-bundle-receipt "$owner/execution-bundle.receipt.v1.json"

uv run --no-sync python -m myis_research.armindex.a2_operational_executor --repository-root . --attempt-id $attempt deployment-validate --package "$owner/deployment-package.tar.gz" --receipt "$owner/deployment-package.receipt.v1.json"

uv run --no-sync python -m myis_research.armindex.a2_operational_executor --repository-root . --attempt-id $attempt bind-instance --provider-observation "$source/provider-observation.v2.json" --runtime-source "$source/runtime.json" --model-lockset-source "$source/model-lockset.json" --data-handoff-source "$source/data-handoff.json" --ssh-host-key-source "$source/ssh-host-key.txt" --management-authority-source "$source/management-authority.json" --output "$stage/provider-instance-binding.v1.json"

uv run --no-sync python -m myis_research.armindex.a2_operational_executor --repository-root . --attempt-id $attempt admit --provider-observation "$source/provider-observation.v2.json" --runtime-source "$source/runtime.json" --model-lockset-source "$source/model-lockset.json" --data-handoff-source "$source/data-handoff.json" --ssh-host-key-source "$source/ssh-host-key.txt" --management-authority-source "$source/management-authority.json" --provider-instance-binding "$stage/provider-instance-binding.v1.json" --output "$stage/provider-admission.v2.json"

# Transfer the exact local asset roots and artifacts bound by the deployment
# manifest: four model roots, wheelhouse, A1 baseline/journal/closeout handoffs,
# safe-return archive, runtime receipt, frozen A1 bundle, and A2 bundle. Use a
# manifest-aware rsync/scp wrapper that verifies every declared hash remotely;
# never download models or transfer protected corpus/query/qrels/membership data.
rsync -a --files-from "$owner/deployment-transfer-files.txt" "<owner-store>/" "<target>:/opt/myis/$attempt-incoming/assets/"
scp -F "$owner/ssh-config" "$source/instance-id.txt" "$source/runtime.json" "$source/model-lockset.json" "$source/data-handoff.json" "$owner/execution-bundle.tar.gz" "$owner/deployment-package.tar.gz" "$owner/deployment-package.receipt.v1.json" "<target>:/opt/myis/$attempt-incoming/"

uv run --no-sync python -m myis_research.armindex.a2_operational_executor --repository-root . --attempt-id $attempt stage --provider-admission-receipt "$stage/provider-admission.v2.json" --provider-instance-binding "$stage/provider-instance-binding.v1.json" --bundle-receipt "$owner/execution-bundle.receipt.v1.json" --bundle "$owner/execution-bundle.tar.gz" --remote-root "/opt/myis/$attempt" --watchdog-deadline-utc "<absolute-watchdog-deadline-before-provider-deadline>" --owner-connection "$owner/connection.json" --provider-observation "$source/provider-observation.v2.json" --runtime-source "$source/runtime.json" --model-lockset-source "$source/model-lockset.json" --data-handoff-source "$source/data-handoff.json" --ssh-host-key-source "$source/ssh-host-key.txt" --management-authority-source "$source/management-authority.json" --remote-instance-id-path "/opt/myis/$attempt-incoming/instance-id.txt" --remote-runtime-path "/opt/myis/$attempt-incoming/runtime.json" --remote-model-lockset-path "/opt/myis/$attempt-incoming/model-lockset.json" --remote-data-handoff-path "/opt/myis/$attempt-incoming/data-handoff.json" --output-directory "$stage"

# Stage verifies zero GPU compute/A2 processes, identity hashes, the immutable
# bundle, and watchdog PID/start-time/heartbeat. Stop here; it does not execute A2.
```

After a separately authorized measured session, use the same attempt-bound
receipts for recovery and closeout:

```powershell
uv run --no-sync python -m myis_research.armindex.a2_operational_executor --repository-root . --attempt-id $attempt resume --ledger "$owner/lifecycle.jsonl"
uv run --no-sync python -m myis_research.armindex.a2_operational_executor --repository-root . --attempt-id $attempt safe-return --archive "$owner/safe-return.tar.gz" --remote-root "/opt/myis/$attempt" --output "$owner/safe-return.receipt.v1.json"
uv run --no-sync python -m myis_research.armindex.a2_operational_executor --repository-root . --attempt-id $attempt closeout --coverage "$owner/exact-coverage.receipt.json" --winner-receipts "$owner/winner-receipt-hashes.json" --safe-return-receipt "$owner/safe-return.receipt.v1.json" --terminal-checkpoint-sha256 "<terminal-checkpoint-sha256>" --output "$owner/execution-closeout.receipt.v1.json"
```

## Measured Commands

The Owner-local manifest must validate against
`schemas/armindex/a2-owner-local-measured-input.v1.json`, bind the A1 v16
runtime/model/data/evaluator artifacts, protected corpus/query/qrels/membership
files by Owner-local relative path and SHA-256, the four staged dense-model
directories, the engine source hash, and the A1 incumbent candidate, program
hash, and aggregate primary metric for ARM-03, ARM-05, and ARM-04. The tracked
command contract invokes the repository-owned production engine; fixture or
caller-selected engine commands fail closed.

```powershell
uv run --no-sync python -m myis_research.armindex.a2_operational_executor --repository-root . --attempt-id <attempt> execute --execution-adoption-receipt <owner-local-adoption.json> --measurement-authority <tracked-authority.json> --command-argv-json control/armindex/a2/measured-command-argv.v1.json --owner-root <owner-local-root> --owner-input-manifest <owner-local-root/input.json> --output-directory <owner-local-output> --checkpoint-ledger <owner-local-ledger.jsonl>
```

The first call ends at the matched barrier. After AP/LO creates the fresh
reserve-budget admission from a new provider observation and its exact source
artifacts, rerun the same command with
`--reserve-budget-admission <owner-local-reserve-admission.json>`. The fresh v2
path also supplies `--provider-instance-binding <owner-local-binding.json>` to
`reserve-admit`. Attempt,
adoption, authority, freeze, matched receipt-set, decision, and continuation
identities must remain unchanged.

```powershell
uv run --no-sync python -m myis_research.armindex.a2_operational_executor --repository-root . --attempt-id <attempt> reserve-admit --execution-adoption-receipt <owner-local-adoption.json> --measurement-authority <tracked-authority.json> --provider-observation <fresh-provider-observation.json> --runtime-source <runtime-source-artifact> --model-lockset-source <model-lockset-source-artifact> --data-handoff-source <data-handoff-source-artifact> --ssh-host-key-source <ssh-host-key-source-artifact> --management-authority-source <management-authority-source-artifact> --output <owner-local-reserve-admission.json>
```

## Hard Stops

Stop before staging or execution on a hash mismatch, stale quote, price above
USD 35, TTL below 40 hours remaining, missing management authority, unexpected GPU
identity, model/data/runtime hash drift, candidate mutation, protected output,
or any request for A3, HARNESS-DEV, Selection, or Final access.

## Ledger

Append exactly one record for each material transition to
`control/armindex/a2/execution-ledger.v1.jsonl`. The ledger is append-only;
each record binds its predecessor hash, attempt ID, freeze bindings, status,
and aggregate-safe evidence hashes.
