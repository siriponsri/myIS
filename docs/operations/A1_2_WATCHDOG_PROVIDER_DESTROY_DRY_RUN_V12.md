# A1.2 Watchdog and Provider-Destroy Dry Run v12

This is an additive local-only dry-run contract. It checks a sanitized command
template and simulates a TTL expiry. It never calls a provider CLI/API, opens
SSH, destroys an instance, or claims that the configured provider command can
actually succeed.

The current capability is always `PENDING_LIVE_PROVIDER`. A PASS means only
that the local JSON conforms to the frozen template and that its simulated
elapsed time reaches the configured TTL. It does not prove provider access,
instance identity, destroy permission, or provider absence.

Prepare an aggregate-safe evidence object outside Git with these exact keys:

```json
{
  "target_instance_identity_sha256": "<64 lowercase hex characters>",
  "ttl_seconds": 21600,
  "heartbeat_stale_seconds": 300,
  "simulated_elapsed_seconds": 21600,
  "simulated_heartbeat_age_seconds": 0,
  "expected_trigger": "ttl_expired",
  "command_template_tokens": ["<provider_cli>", "destroy", "instance", "<provider_instance_identity_sha256>"]
}
```

Run locally:

```powershell
uv run --no-sync python -m myis_research.armindex.a1_2_watchdog_provider_destroy_dry_run_v12 evaluate --repository-root . --evidence <SAFE_LOCAL_EVIDENCE_JSON> --receipt-id a1.2-watchdog-provider-destroy-dry-run-<attempt>-v12
```

Add `--output <OWNER_LOCAL_RECEIPT_JSON>` to persist the result. The command
refuses repository output paths and will not overwrite a different existing
receipt.

The result has `provider_action_performed=false`,
`actual_provider_destroy_capability=PENDING_LIVE_PROVIDER`, and
`actual_destroy_receipt_required=true`. If a future instance must be
destroyed, that is a separate explicit Owner/provider action followed by its
own closeout receipt. Guest poweroff is never proof of provider destruction.
