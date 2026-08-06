# A1.2 Vast 4xRTX3090 Live Preflight Runbook v6

This additive live correction preserves every v1-v5 contract, receipt, and
staged model byte. Use the v5 runbook for Owner-local staging. Use this runbook
only after the v5 local stage is `PASS` and one disposable Vast SSH container
is already open with the pinned official image.

The first live identity probe established that a direct Vast container does
not expose a Docker CLI/socket and does not inherit the two offline variables
into an SSH login shell. This revision therefore injects offline variables in
every remote command and records the strongest observable identity available:
the registry-verified OCI digest and frozen bundle binding, plus exact runtime,
platform, PyTorch, CUDA, and GPU anchors. It must report that the manifest
digest was not observable inside the container when no container API exists.

## Safety gates

- Image: `pytorch/pytorch:2.6.0-cuda11.8-cudnn9-runtime`
- OCI manifest: `sha256:2428b92ebbaeceba5572b98c18c8a94e43162bead6e88588ad54471147c58a20`
- Platform: `linux/amd64`
- Mode: synthetic preflight only
- `launch_allowed=false`; `adopted_for_execution=false`
- No model/package download, measured retrieval, optimization, Selection,
  Final, paid API, or model-weight changes

The live quote must fit the USD 18 common-screen, USD 23 A1, and USD 100
campaign hard stops. At USD 0.656 per instance-hour, two to four hours cost
USD 1.312 to USD 2.624; the six-hour TTL exposure is USD 3.936.

## Dry-run

Use the external Owner root and never place SSH values or receipts in Git.

```powershell
$OwnerRoot = Join-Path (Resolve-Path '..') '04_Owner_Stores\a1.2-vast-20260806'
$Bundle = Join-Path $OwnerRoot 'transfer\a1.2-direct-base-code-bundle-v6.tar.gz'
$BundleSha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $Bundle).Hash.ToLowerInvariant()
$Coordinator = 'scripts/a1_2_vast/Invoke-A12VastDirectBaseCoordinatorV6.ps1'
$Common = @('-HostName',$VastHost,'-Port',$VastPort,'-UserName',$VastUser,'-KeyPath',$SshKey,'-RemoteRoot','/opt/myis/a1.2-v6')

powershell -NoProfile -File $Coordinator -Action upload @Common `
  -BundlePath $Bundle `
  -WheelhousePath (Join-Path $OwnerRoot 'build-context\runtime\wheelhouse') `
  -ModelRoot (Join-Path $OwnerRoot 'models') `
  -JobManifestRoot (Join-Path $OwnerRoot 'transfer\jobs') -DryRun

powershell -NoProfile -File $Coordinator -Action verify @Common `
  -ExpectedGitCommit $GitCommit -ExpectedGitTree $GitTree `
  -ExpectedManifestDigest 'sha256:2428b92ebbaeceba5572b98c18c8a94e43162bead6e88588ad54471147c58a20' `
  -ExpectedBundleSha256 $BundleSha256 -DryRun
```

## Upload and verify

Repeat the same `upload` and `verify` commands without `-DryRun`. Verification
checks the archive hash, bundle manifest self-hash, Git commit/tree, every
bundled file hash, wheelhouse and model checksums, exact model revisions,
critical artifacts, Snowflake custom-code Git OIDs, safe job manifests,
protected-path absence, offline install, dependency versions, runtime anchors,
four distinct RTX 3090 UUIDs, CPU/RAM, and staged free space.

## Synthetic GPU preflight

```powershell
powershell -NoProfile -File $Coordinator -Action start @Common
powershell -NoProfile -File $Coordinator -Action status @Common
```

The start action uses one arm per GPU, local files only. It records synthetic
formatting, pooling, normalization, output dimension, finite outputs, repeat
determinism, peak VRAM, Snowflake remote-code execution, and the maximum Qwen
candidate that completes on one RTX 3090. It then injects one bounded ARM-02
failure and requires a successful checkpoint resume before completing four
synthetic workers.

## Stop, collect, and destroy

```powershell
powershell -NoProfile -File $Coordinator -Action teardown @Common
powershell -NoProfile -File $Coordinator -Action collect @Common `
  -CollectPath (Join-Path $OwnerRoot 'return')
```

Validate the downloaded archive locally. Then the Owner must destroy the Vast
instance in the provider console and verify that the instance is absent.
Guest teardown is not provider destruction. Do not resume local canonical
work until the Owner confirms destruction.

