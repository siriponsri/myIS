# A1.2 Instance Disposition v12

This additive Owner policy decides whether a future, still-live A1.2 instance
may remain available after a successfully collected safe return. It preserves
all v1-v11 contracts and receipts. It is not a provider command, execution
adoption, or permission to start scientific work.

## Current state

The current canonical state is `NO_LIVE_INSTANCE` and `PENDING_LIVE_PROVIDER`.
The v10 instance was destroyed and cannot be reused. Do not run an evaluation
for that historical instance.

## Future local-only evaluation

Prepare one aggregate-safe JSON evidence file outside Git. It must include:

- locally validated archive, member manifest, collection, and teardown hashes;
- preflight and current sanitized instance-identity/frozen-binding hashes;
- an all-fee quote no older than 900 seconds, projected cost for all hard stops,
  remaining TTL, and a safety margin;
- a protected-boundary scan receipt;
- an Owner-local watchdog/destroy dry-run receipt; and
- an explicit Owner-authorized next PLAN goal whose execution adoption remains
  false.

Run only this local command:

```powershell
uv run --no-sync python -m myis_research.armindex.a1_2_instance_disposition_v12 evaluate --repository-root . --evidence <SAFE_LOCAL_EVIDENCE_JSON> --receipt-id a1.2-instance-disposition-<attempt>-v12
```

The evaluator never opens SSH, calls a provider API or CLI, destroys an
instance, or writes a canonical receipt. It emits `REUSE_ELIGIBLE` only when
every predicate passes. Missing, stale, malformed, or changed evidence emits
`DESTROY_REQUIRED` with sorted reason codes.

`REUSE_ELIGIBLE` means only: report `Owner continue next goal on PLAN`. It
does not change `launch_allowed=false` or `adopted_for_execution=false`.
`DESTROY_REQUIRED` means only: report `Owner destroy instance`; provider
destruction remains an explicit Owner action followed by a separate closeout
receipt. Guest poweroff never proves provider destruction.

## Destroy dry run

The dry-run proof must state `mode=owner_local_dry_run`,
`provider_action_performed=false`, `destroy_command_validated=true`,
`ttl_trigger_simulated=true`, and
`guest_poweroff_is_provider_destruction=false`. It validates the local
watchdog path only. It must not invoke a provider destruction command.
