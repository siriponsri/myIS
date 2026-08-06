# A1.2 Vast 4xRTX3090 Owner Runbook v5

This additive revision uses the verified official image directly on Vast:
`pytorch/pytorch:2.6.0-cuda11.8-cudnn9-runtime@sha256:2428b92ebbaeceba5572b98c18c8a94e43162bead6e88588ad54471147c58a20` on `linux/amd64`.
It preserves the v1-v3 contracts and receipts. Do not run the old image-build
steps from v2/v3 for this revision.

The four-RTX3090 planning rate remains USD 0.60 per instance-hour, with a
2-4-hour preflight estimate (USD 1.20-2.40). The live quote must fit USD 18
common-screen, USD 23 A1, and USD 100 campaign hard stops. Otherwise stop
`BLOCKED_BUDGET`. No paid instance is opened by this local preparation.

## 1. Validate local revision

```powershell
git status --short
uv run --no-sync python -m myis_research.armindex.a1_2_runtime_minimal_direct_base validate --repository-root .
uv run --no-sync pytest tests/test_armindex_a1_2_runtime_minimal_direct_base.py -q -p no:cacheprovider
```

The status must remain direct-base prepared and show `launch_allowed=false`,
`adopted_for_execution=false`, measured runs zero, and charged USD zero.

## 2. Stage locally, outside Git

```powershell
$OwnerRoot = Join-Path (Resolve-Path '..') '04_Owner_Stores\a1.2-vast-20260806'
$ModelRoot = Join-Path $OwnerRoot 'models'
uv run --no-sync --with 'huggingface-hub==0.30.2' python -m myis_research.armindex.a1_2_runtime_minimal stage --repository-root . --arm ARM-02 --model-directory (Join-Path $ModelRoot 'ARM-02')
uv run --no-sync --with 'huggingface-hub==0.30.2' python -m myis_research.armindex.a1_2_runtime_minimal stage --repository-root . --arm ARM-03 --model-directory (Join-Path $ModelRoot 'ARM-03')
uv run --no-sync --with 'huggingface-hub==0.30.2' python -m myis_research.armindex.a1_2_runtime_minimal stage --repository-root . --arm ARM-04 --model-directory (Join-Path $ModelRoot 'ARM-04')
uv run --no-sync --with 'huggingface-hub==0.30.2' python -m myis_research.armindex.a1_2_runtime_minimal stage --repository-root . --arm ARM-05 --model-directory (Join-Path $ModelRoot 'ARM-05')
```

These are Owner-local public-artifact downloads at the exact locked revisions.
They use `allow_patterns` and one worker and resume the existing local cache.
The remote image must never download a model. CPU dense model loading is
intentionally skipped; only hashes, metadata, and static tokenizer checks are
allowed locally. CUDA parity, Qwen measured length, and VRAM feasibility stay
pending live Vast preflight.

Prepare a Linux x86_64 wheelhouse in the pinned image or an equivalent Linux
container. The wheelhouse must contain `SHA256SUMS`; no PyPI access is allowed
after upload. Do not build an image, save an image, upload an image, load an
image, use Docker-in-Docker, or start Jupyter.

## 3. Build the frozen code bundle

```powershell
$Bundle = Join-Path $OwnerRoot 'transfer\a1.2-direct-base-code-bundle-v5.tar.gz'
uv run --no-sync python -m myis_research.armindex.a1_2_runtime_minimal build-code-bundle --repository-root . --output $Bundle
```

The bundle contains code and manifests only, never model bytes or protected
data. Safe job manifests are copied to `$OwnerRoot\transfer\jobs`.

## 4. Owner-local SSH coordinator

Set the SSH values in the current PowerShell session only; never write secrets
to Git or a report. The provider must first show one disposable instance with
four distinct RTX 3090 GPUs and a live quote within the hard stops.

```powershell
$Coordinator = 'scripts/a1_2_vast/Invoke-A12VastDirectBaseCoordinator.ps1'
$Common = @('-HostName',$VastHost,'-Port',$VastPort,'-UserName',$VastUser,'-KeyPath',$SshKey,'-RemoteRoot','/opt/myis/a1.2-v5')
powershell -NoProfile -File $Coordinator -Action upload @Common -BundlePath $Bundle -WheelhousePath (Join-Path $OwnerRoot 'build-context\runtime\wheelhouse') -ModelRoot $ModelRoot -JobManifestRoot (Join-Path $OwnerRoot 'transfer\jobs') -DryRun
powershell -NoProfile -File $Coordinator -Action verify @Common -ExpectedGitCommit $GitCommit -ExpectedGitTree $GitTree -ExpectedManifestDigest 'sha256:2428b92ebbaeceba5572b98c18c8a94e43162bead6e88588ad54471147c58a20' -DryRun
```

After reviewing the dry-run receipt, run upload and verify against the SSH
worker. The bootstrap checks the direct image identity, `linux/amd64`, Python,
PyTorch/CUDA, four GPU UUIDs, CPU/RAM/disk, wheel and model hashes, Snowflake
remote-code OIDs, and forbidden-path absence. It creates a venv with
`--system-site-packages` and installs additional packages with `--no-index`.

## 5. Synthetic preflight and termination

Start only the four synthetic workers after every live checklist item passes.
Dense adapter parity, Qwen maximum length, VRAM feasibility, heartbeat/resume,
live quote, and provider destroy/TTL remain pending checks. Guest `poweroff`
is not provider destruction. Use the local watchdog, collect only allowlisted
aggregate receipts, then destroy and verify the provider instance before
resuming work on CPU.

Measured retrieval, REP-DEV, HARNESS-DEV, Selection, Final, paid API calls, and
weight changes remain forbidden. This revision is not adopted for execution.
