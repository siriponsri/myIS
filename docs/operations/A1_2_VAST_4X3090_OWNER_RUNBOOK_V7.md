# A1.2 Same-Instance Repair Preflight v7

This is a repair of the launch-locked v6 preflight only. It keeps every v1-v6
file and receipt unchanged. It does not authorize measured retrieval,
optimization, Selection, Final, paid APIs, model downloads, or weight changes.

## What changed

Two live failures are preserved as engineering evidence:

1. The initial v6 wheelhouse did not include `pydantic`, which the repository
   runtime needs.
2. A supplement repair wrote `__pycache__` into the frozen code tree.

v7 uses a fresh `/opt/myis/a1.2-v7` root on the same already-verified instance.
It reuses the staged v6 models, wheelhouse, jobs, and supplement only after
their SHA256SUMS validation. It uploads only the new frozen v7 code bundle.
Every remote Python command has `PYTHONDONTWRITEBYTECODE=1`.

## Before connecting

Keep the instance identity, four GPU UUIDs, quote, image/runtime locks, and
owner TTL/watchdog evidence valid. Stop and destroy by default if any check is
missing, the instance has changed, the quote exceeds a hard stop, or the
protected-data boundary cannot be proved. The continuation policy does not
authorize launch or adoption.

Prepare only the v7 frozen code bundle under the Owner-local transfer area.
Do not upload qrels, membership, query identifiers, protected evaluator data,
credentials, private keys, provider payloads, models, wheels, jobs, or the
supplement again.

## Owner commands

Use the Owner-local SSH variables from the v6 procedure. Do not save them in
this repository.

```powershell
$Coordinator = 'scripts/a1_2_vast/Invoke-A12VastDirectBaseCoordinatorV7.ps1'
$OwnerRoot = Join-Path (Resolve-Path '..') '04_Owner_Stores\a1.2-vast-20260806'
$V7Bundle = Join-Path $OwnerRoot 'transfer\a1.2-direct-base-code-bundle-v7.tar.gz'
$BundleSha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $V7Bundle).Hash.ToLowerInvariant()
$GitCommit = (git rev-parse HEAD).Trim()
$GitTree = (git rev-parse 'HEAD^{tree}').Trim()
$Common = @('-HostName',$VastHost,'-Port',$VastPort,'-UserName',$VastUser,'-KeyPath',$SshKey,`
  '-RemoteRoot','/opt/myis/a1.2-v7','-SourceRemoteRoot','/opt/myis/a1.2-v6')

powershell -NoProfile -File $Coordinator -Action stage-repair @Common `
  -BundlePath $V7Bundle -ExpectedGitCommit $GitCommit -ExpectedGitTree $GitTree `
  -ExpectedBundleSha256 $BundleSha256 -DryRun
powershell -NoProfile -File $Coordinator -Action verify @Common `
  -ExpectedGitCommit $GitCommit -ExpectedGitTree $GitTree `
  -ExpectedManifestDigest 'sha256:2428b92ebbaeceba5572b98c18c8a94e43162bead6e88588ad54471147c58a20' `
  -ExpectedBundleSha256 $BundleSha256 -DryRun
```

After both dry-runs pass, repeat only `stage-repair` and `verify` without
`-DryRun`. The verifier must confirm the supplement checksum and runtime
dependencies, the supplement exact tree and safe receipt, the v6 staged
SHA256SUMS, the fresh frozen code tree, and the absence of `__pycache__` before
and after validation.

Run only the synthetic preflight after verification passes:

```powershell
powershell -NoProfile -File $Coordinator -Action start @Common
powershell -NoProfile -File $Coordinator -Action status @Common
powershell -NoProfile -File $Coordinator -Action collect @Common `
  -CollectPath (Join-Path $OwnerRoot 'return')
powershell -NoProfile -File $Coordinator -Action teardown @Common
```

The four actions retain v6 synthetic-only behavior. A PASS still leaves
`launch_allowed=false` and `adopted_for_execution=false`.

## Closeout

Run guest teardown, collect only the v6 safe-export allowlisted aggregate-safe
artifacts, validate them locally, then destroy the provider instance and verify
it is absent by default. When every condition in
`owner-instance-continuation-policy.v1.json` passes and the next PLAN goal is
separately authorized, report `Owner continue next goal on PLAN` instead of a
destroy request. Retention never grants scientific execution.
