# A1.2 Synthetic Live Preflight v9 Owner Runbook

This runbook is only for the A1.2 synthetic execution-lifecycle preflight on
the already-open four-RTX3090 Vast instance. It does not authorize measured
retrieval, optimization, Selection, Final, paid APIs, or model changes.

Revision v9 is additive. Preserve `/opt/myis/a1.2-v6`, `a1.2-v7`, and
`a1.2-v8` as failed-attempt evidence. v9 uses a fresh
`/opt/myis/a1.2-v9` root and reuses only checksum-validated staged artifacts.

## 1. Owner inputs

Open PowerShell in the repository root. Fill only the five values below. Do
not paste the private-key contents, Hugging Face tokens, or Vast credentials
into a command, receipt, Git file, or chat.

```powershell
$VastHost = '<VAST_SSH_HOST>'
$VastPort = <VAST_SSH_PORT>
$VastUser = 'root'
$SshKey = '<LOCAL_PRIVATE_KEY_PATH>'
$AttemptId = 'a12-v9-20260807-01'
```

The attempt ID must use lowercase letters, digits, dots, underscores, or
hyphens. A failed or completed attempt ID is never reused.

## 2. Frozen local values

Run these commands after the v9 commit is clean and pushed:

```powershell
$OwnerRoot = Resolve-Path '..\04_Owner_Stores\a1.2-vast-20260806'
$Coordinator = 'scripts/a1_2_vast/Invoke-A12VastDirectBaseCoordinatorV9.ps1'
$Bundle = Join-Path $OwnerRoot 'transfer\a1.2-direct-base-code-bundle-v9.tar.gz'
$Return = Join-Path $OwnerRoot 'return'
$Head = (git rev-parse HEAD).Trim()
$Tree = (git show -s --format=%T HEAD).Trim()
$BundleSha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $Bundle).Hash.ToLowerInvariant()
$ReceiptRoot = Join-Path $OwnerRoot 'receipts'
$Common = @(
  '-HostName', $VastHost, '-Port', $VastPort, '-UserName', $VastUser,
  '-KeyPath', $SshKey, '-RemoteRoot', '/opt/myis/a1.2-v9',
  '-SourceRemoteRoot', '/opt/myis/a1.2-v7',
  '-ExpectedGitCommit', $Head, '-ExpectedGitTree', $Tree,
  '-ExpectedBundleSha256', $BundleSha256
)
```

The source root is v7 because it contains the validated models, base
wheelhouse, jobs, and supplement wheelhouse. v8 never completed staging.

Before continuing, confirm the live total-instance quote fits all remaining
hard stops: USD 18 common screen, USD 23 A1, and USD 100 campaign. Stop with
`BLOCKED_BUDGET` if it does not fit.

## 3. Stage the fresh root

```powershell
& $Coordinator -Action stage-repair @Common -BundlePath $Bundle `
  -ReceiptPath (Join-Path $ReceiptRoot 'LIVE_V9_STAGE.json')
```

This uploads only the frozen code bundle. It copies the existing staged model,
wheelhouse, supplement, and job bytes on the same instance, then verifies the
archive hash and safe member types before extraction.

## 4. Verify before GPU work

```powershell
& $Coordinator -Action verify @Common `
  -ReceiptPath (Join-Path $ReceiptRoot 'LIVE_V9_VERIFY.json')
```

Verification must write
`/opt/myis/a1.2-v9/output/preflight/verification-pass.v9.json`. If verification
fails, stop. Preserve the root and logs. Do not run `start`.

## 5. Start synthetic preflight

The start command is intentionally synchronous. Keep its PowerShell terminal
open. The remote launcher traps exit, interrupt, and termination signals and
terminates/reaps its verified child processes.

```powershell
& $Coordinator -Action start @Common -AttemptId $AttemptId `
  -ReceiptPath (Join-Path $ReceiptRoot 'LIVE_V9_START.json')
```

Only synthetic adapter parity, ARM-05 adapter-level maximum-length probing,
and synthetic four-worker checkpoint/resume checks run. Each arm is fixed to
one `CUDA_VISIBLE_DEVICES` slot.

From a second PowerShell terminal, recreate the variables in sections 1-2 and
check status no more often than needed:

```powershell
& $Coordinator -Action status @Common -AttemptId $AttemptId
```

Valid lifecycle states are `RUNNING`, `FAILED`, and `COMPLETE`. Stale
heartbeats or a changed PID/start-time identity report `FAILED`, never PASS.

## 6. Verify guest teardown

The synchronous launcher reaps every child and writes the immutable teardown
receipt before it returns `COMPLETE`. Re-run the idempotent verification below
before collection. It checks the same attempt and does not destroy the provider
instance:

```powershell
& $Coordinator -Action teardown @Common -AttemptId $AttemptId `
  -ReceiptPath (Join-Path $ReceiptRoot 'LIVE_V9_TEARDOWN.json')
```

## 7. Collect and verify locally

Collect only after status is `COMPLETE`:

```powershell
& $Coordinator -Action collect @Common -AttemptId $AttemptId `
  -CollectPath $Return -ReceiptPath (Join-Path $ReceiptRoot 'LIVE_V9_COLLECT.json')
```

Collection requires the same-attempt PASS summary and marker. It compares the
remote and local archive SHA-256, rejects unsafe archive members, and validates
every member hash against the included manifest. Retrying collection is safe
only when the existing local archive has the identical hash. The archive must
include the same-attempt `teardown.json`; collection fails closed without it.

## 8. Decide instance disposition

After local collection validates, destroy the Vast instance by default. The
instance may remain open only when the Owner continuation policy still passes:
same instance identity, unchanged frozen hashes, quote/budget headroom,
working TTL/destroy path, protected-data boundary, and a separately authorized
next PLAN goal. In that case report `Owner continue next goal on PLAN` instead
of requesting destruction.

`launch_allowed=false` and `adopted_for_execution=false` remain unchanged
through this runbook. They refer to scientific execution, not this bounded
synthetic engineering preflight.
