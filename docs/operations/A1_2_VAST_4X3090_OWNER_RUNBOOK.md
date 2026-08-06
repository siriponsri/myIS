# A1.2 Vast 4xRTX3090 Owner Runbook

This runbook opens only the Owner-local SSH/Vast preflight. It does not start
measured retrieval. Keep all access material, evaluation truth, split
membership, local evaluator files, MLflow, Brain, Obsidian, Dashboard, Git, and
OpenAI configuration on the local machine.

## 1. Before Opening Vast

From PowerShell in `01_Research`:

```powershell
uv run --no-sync python -m myis_research.armindex.a1_2_vast validate --repository-root .
uv run --no-sync pytest tests/test_armindex_a1_2_vast.py -q -p no:cacheprovider
git status --short
```

The repository must be clean and pushed. Stage the four model directories
outside Git. Each directory must contain every runtime file and one complete
`SHA256SUMS` file:

```text
<OWNER_MODEL_ROOT>/ARM-02/SHA256SUMS
<OWNER_MODEL_ROOT>/ARM-03/SHA256SUMS
<OWNER_MODEL_ROOT>/ARM-04/SHA256SUMS
<OWNER_MODEL_ROOT>/ARM-05/SHA256SUMS
```

Validate each directory locally:

```powershell
$OwnerModelRoot = '<OWNER_MODEL_ROOT>'
'ARM-02','ARM-03','ARM-04','ARM-05' | ForEach-Object {
    uv run --no-sync python -m myis_research.armindex.a1_2_vast validate-sha256s --directory (Join-Path $OwnerModelRoot $_)
}
```

Prepare an offline Python wheelhouse matching
`containers/a1_2_vast_4x3090/runtime/requirements.v2.txt`. Its
`SHA256SUMS` must list every wheel. Resolve the base image by digest; do not
build from a mutable tag alone.

```powershell
$BaseImage = 'pytorch/pytorch@sha256:<BASE_IMAGE_SHA256>'
$RuntimeImage = 'myis-a1.2-vast-runtime:v2'
$BuildContext = '<OWNER_BUILD_CONTEXT>'
docker build --build-arg BASE_IMAGE=$BaseImage -f containers/a1_2_vast_4x3090/Dockerfile -t $RuntimeImage $BuildContext
$ImageReference = $RuntimeImage
$ImageDigest = (docker image inspect --format '{{.Id}}' $RuntimeImage).Trim()
if ($ImageDigest -notmatch '^sha256:[a-f0-9]{64}$') { throw 'Built image has no immutable image ID.' }
```

Record the current quote. The planning rate supplied by the Owner is USD 0.60
per hour for the complete four-RTX3090 instance. The expected dense parallel
window is 2-4 instance-hours, or USD 1.20-2.40 raw worker cost. Do not open an
instance if the live quote cannot fit USD 18 for the common screen, USD 23 for
A1, and USD 100 for the campaign. A non-fitting quote is `BLOCKED_BUDGET`.

## 2. Open One Matching Instance

Open one disposable Vast instance with exactly four NVIDIA GeForce RTX 3090
GPUs, at least 16 vCPUs, 64 GiB RAM, and 250 GiB free disk. Enable SSH. Do not
copy any local access file, evaluation truth, split membership, or local
evaluator payload to the instance.

Set local variables without writing them to Git:

```powershell
$VastHost = '<VAST_SSH_HOST>'
$VastPort = <VAST_SSH_PORT>
$VastUser = '<VAST_SSH_USER>'
$SshKey = '<OWNER_LOCAL_SSH_KEY_PATH>'
$ProviderInstanceId = '<VAST_INSTANCE_ID>'
$RemoteRoot = '/opt/myis/a1.2-v2'
$GitCommit = (git rev-parse HEAD).Trim()
$GitTree = (git rev-parse 'HEAD^{tree}').Trim()
$OwnerTransferRoot = '<OWNER_LOCAL_TRANSFER_ROOT>'
```

Save the image and build the frozen code bundle outside the repository:

```powershell
$ImageArchive = Join-Path $OwnerTransferRoot 'a1.2-runtime-image.tar'
$BundleArchive = Join-Path $OwnerTransferRoot 'a1.2-frozen-bundle.tar.gz'
docker save --output $ImageArchive $ImageReference
uv run --no-sync python -m myis_research.armindex.a1_2_vast build-frozen-bundle --repository-root . --output $BundleArchive --image-digest $ImageDigest
```

## 3. Upload and Verify

Upload only the frozen runtime image, code bundle, and four frozen model
directories. Keep the local return directory outside Git.

```powershell
scripts/a1_2_vast/Invoke-A12VastCoordinator.ps1 -Action upload -HostName $VastHost -Port $VastPort -UserName $VastUser -KeyPath $SshKey -BundlePath $BundleArchive -ImageArchivePath $ImageArchive -ImageReference $ImageReference -RemoteRoot $RemoteRoot

scp -P $VastPort -i $SshKey -r (Join-Path $OwnerModelRoot 'ARM-02') "${VastUser}@${VastHost}:${RemoteRoot}/models/ARM-02"
scp -P $VastPort -i $SshKey -r (Join-Path $OwnerModelRoot 'ARM-03') "${VastUser}@${VastHost}:${RemoteRoot}/models/ARM-03"
scp -P $VastPort -i $SshKey -r (Join-Path $OwnerModelRoot 'ARM-04') "${VastUser}@${VastHost}:${RemoteRoot}/models/ARM-04"
scp -P $VastPort -i $SshKey -r (Join-Path $OwnerModelRoot 'ARM-05') "${VastUser}@${VastHost}:${RemoteRoot}/models/ARM-05"

scripts/a1_2_vast/Invoke-A12VastCoordinator.ps1 -Action verify -HostName $VastHost -Port $VastPort -UserName $VastUser -KeyPath $SshKey -ImageReference $ImageReference -ExpectedGitCommit $GitCommit -ExpectedGitTree $GitTree -ExpectedImageDigest $ImageDigest -RemoteRoot $RemoteRoot
```

Verification must report four distinct RTX 3090 UUIDs, compatible
CUDA/PyTorch, sufficient CPU/RAM/disk, exact commit/tree/image digest, complete
model manifests, and no forbidden remote surface. Stop on any mismatch.

## 4. Watchdog Dry Run and Synthetic Launch

Validate the local destroy command without invoking it:

```powershell
$LocalHeartbeat = Join-Path $OwnerTransferRoot 'latest-heartbeat.json'
scripts/a1_2_vast/Invoke-A12VastWatchdog.ps1 -Mode DryRun -ProviderInstanceId $ProviderInstanceId -HeartbeatPath $LocalHeartbeat -VastCliPath vastai
```

Start only the four synthetic preflight workers:

```powershell
scripts/a1_2_vast/Invoke-A12VastCoordinator.ps1 -Action start -HostName $VastHost -Port $VastPort -UserName $VastUser -KeyPath $SshKey -ImageReference $ImageReference -ExpectedImageDigest $ImageDigest -RemoteRoot $RemoteRoot
scripts/a1_2_vast/Invoke-A12VastCoordinator.ps1 -Action status -HostName $VastHost -Port $VastPort -UserName $VastUser -KeyPath $SshKey -RemoteRoot $RemoteRoot
```

The expected status is four heartbeats and four runtime receipts. This is
engineering preflight evidence only.

## 5. Collect and Destroy

Collect only the generated safe-export archive:

```powershell
$ReturnRoot = '<OWNER_LOCAL_RETURN_ROOT>'
scripts/a1_2_vast/Invoke-A12VastCoordinator.ps1 -Action collect -HostName $VastHost -Port $VastPort -UserName $VastUser -KeyPath $SshKey -CollectPath $ReturnRoot -RemoteRoot $RemoteRoot
scripts/a1_2_vast/Invoke-A12VastCoordinator.ps1 -Action teardown -HostName $VastHost -Port $VastPort -UserName $VastUser -KeyPath $SshKey -RemoteRoot $RemoteRoot
```

Guest teardown is not provider destruction. Destroy and verify the instance
from the local machine:

```powershell
vastai destroy instance $ProviderInstanceId
vastai show instance $ProviderInstanceId --raw
```

The second command must show that the instance is absent. Do not continue to
scientific execution. Return to local validation and Owner adoption of the
unchanged revision in a later authorized goal.
