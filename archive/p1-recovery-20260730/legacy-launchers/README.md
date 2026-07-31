# Retired standalone launchers

These files preserve the exact standalone Owner launcher sources that were
kept during unified Dashboard acceptance. They were retired from active
`projections/` only after Windows health-token, malformed-port,
concurrent-launch, duplicate-process, unknown-owner, failure rollback, and
browser-after-health checks passed.

They are historical rollback material, not supported runtime entry points.
Their original active paths and SHA-256 values are:

- `projections/open-dashboard.cmd`: `ac660d485ba23c1d0e31b6735a5e63cd223da6d5bec02431dbb4eea102228c53`
- `projections/open-mlflow.cmd`: `594374515359e1cd8b5e79b3d568a6347a7e22ff71aa89a20e14ef3966577949`
- `projections/open-obsidian-report.cmd`: `4ed90c80dc28d038de7d986557f3e859e1891b8d55b2d85f0e635b3f136e626f`

Use Git history and the acceptance receipt for reviewed rollback. Do not run
these archived files directly.
