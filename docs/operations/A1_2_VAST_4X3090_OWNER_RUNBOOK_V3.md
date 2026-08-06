# A1.2 Vast 4xRTX3090 Owner Runbook v3

This is the additive post-commit correction for
`docs/operations/A1_2_VAST_4X3090_OWNER_RUNBOOK.md`. Follow every safety rule,
hardware requirement, variable declaration, upload, verify, watchdog, start,
status, collect, teardown, destroy, and destroy-verification command in that
preserved v2 runbook. Replace only the two commands below.

Planning price: USD 0.60 per hour for the complete four-RTX3090 instance. The
expected live-preflight window is 2-4 instance-hours (USD 1.20-2.40 raw worker
cost), plus 2-4 local hours. Record the live quote before upload. Stop as
`BLOCKED_BUDGET` if it does not fit the unchanged USD 18 common-screen, USD 23
A1, and USD 100 campaign hard stops.

## 1. Validate the Clean Pushed Revision

From PowerShell in `01_Research`, after pulling the pushed `main` commit:

```powershell
git status --short
uv run --no-sync python -m myis_research.armindex.a1_2_vast_postcommit validate --repository-root .
uv run --no-sync pytest tests/test_armindex_a1_2_vast_postcommit.py tests/test_armindex_a1_2_vast.py -q -p no:cacheprovider
```

`git status --short` must be empty. The validator must return
`status=prepared_postcommit_launch_locked`, the current Git commit and tree,
`launch_allowed=false`, and `adopted_for_execution=false`.

## 2. Build the Frozen Bundle

After building the digest-bound image exactly as documented in the v2 runbook,
replace its `build-frozen-bundle` command with:

```powershell
$GitCommit = (git rev-parse HEAD).Trim()
$GitTree = (git rev-parse 'HEAD^{tree}').Trim()
$BundleArchive = Join-Path $OwnerTransferRoot 'a1.2-frozen-bundle-v3.tar.gz'
uv run --no-sync python -m myis_research.armindex.a1_2_vast_postcommit build-frozen-bundle --repository-root . --output $BundleArchive --image-digest $ImageDigest
```

Continue with sections 3 through 5 of the v2 runbook. Pass `$GitCommit`,
`$GitTree`, and `$ImageDigest` to the unchanged coordinator verification
command. Run only synthetic preflight workers, collect only the allowlisted
archive, then destroy and verify the Vast instance from the local machine.

Passing the preflight does not adopt the revision or authorize scientific
execution. Stop and return the sanitized receipts to the local repository.
