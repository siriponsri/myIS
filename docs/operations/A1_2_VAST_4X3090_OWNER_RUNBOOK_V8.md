# A1.2 Validation-Complete Bundle Repair v8

This additive repair preserves v1-v7. The v7 verifier stopped before GPU work
because the frozen code bundle omitted a historical v1 receipt that the
repository validator reads. v8 changes only the bundle packaging closure and
uses a fresh `/opt/myis/a1.2-v8` root on the same unchanged instance.

The new bundle includes the exact repository-safe files read by the preserved
v1, v2, v3, and v5 validators. A historical Dockerfile may be present only
because the immutable v2 receipt binds its hash. It is not executed. The active
path still has no custom image build, Docker-in-Docker, model download, Jupyter,
measured retrieval, optimization, Selection, Final, paid API, or weight change.

## Required local state

- Research `main` is clean and pushed.
- The v8 bundle was built by the v8 module from that exact commit and tree.
- The v7 root remains preserved as failed-attempt evidence.
- The v7 model, wheelhouse, job, and supplement trees remain checksum-valid.
- `launch_allowed=false` and `adopted_for_execution=false`.

## Owner-local commands

Keep SSH values only in the Owner shell. Do not write them to Git.

```powershell
$Coordinator = 'scripts/a1_2_vast/Invoke-A12VastDirectBaseCoordinatorV8.ps1'
$OwnerRoot = Join-Path (Resolve-Path '..') '04_Owner_Stores\a1.2-vast-20260806'
$Bundle = Join-Path $OwnerRoot 'transfer\a1.2-direct-base-code-bundle-v8.tar.gz'
$BundleSha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $Bundle).Hash.ToLowerInvariant()
$GitCommit = (git rev-parse HEAD).Trim()
$GitTree = (git rev-parse 'HEAD^{tree}').Trim()
$Common = @('-HostName',$VastHost,'-Port',$VastPort,'-UserName',$VastUser,`
  '-KeyPath',$SshKey,'-RemoteRoot','/opt/myis/a1.2-v8',`
  '-SourceRemoteRoot','/opt/myis/a1.2-v7')

powershell -NoProfile -File $Coordinator -Action stage-repair @Common `
  -BundlePath $Bundle -ExpectedGitCommit $GitCommit -ExpectedGitTree $GitTree `
  -ExpectedBundleSha256 $BundleSha256 -DryRun
powershell -NoProfile -File $Coordinator -Action verify @Common `
  -ExpectedGitCommit $GitCommit -ExpectedGitTree $GitTree `
  -ExpectedManifestDigest 'sha256:2428b92ebbaeceba5572b98c18c8a94e43162bead6e88588ad54471147c58a20' `
  -ExpectedBundleSha256 $BundleSha256 -DryRun
```

Repeat both commands without `-DryRun`. Verification must pass the bundle
manifest self-hash, exact Git identity, validation-lineage hashes, model and
wheelhouse SHA256SUMS, offline dependency installation, runtime anchors, and
four-GPU hardware identity before synthetic workers start.

```powershell
powershell -NoProfile -File $Coordinator -Action start @Common
powershell -NoProfile -File $Coordinator -Action status @Common
powershell -NoProfile -File $Coordinator -Action collect @Common `
  -CollectPath (Join-Path $OwnerRoot 'return')
powershell -NoProfile -File $Coordinator -Action teardown @Common
```

Only synthetic preflight is allowed. After safe local collection, apply the
conditional continuation policy. Continue to a separately authorized PLAN
goal only if every policy condition passes; otherwise destroy the provider
instance and verify absence.
