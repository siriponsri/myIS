# A1.2 Instance Disposition v13

V13 is a strictly additive hardening revision. V1-v12 remain historical
evidence. The present state is `NO_LIVE_INSTANCE` and
`PENDING_LIVE_PROVIDER`; it cannot classify the destroyed v10 instance as
reusable.

For a future live instance, V13 accepts only aggregate-safe self-hashed receipt
objects or absolute files outside the repository. It never opens SSH, contacts
a provider, invokes a CLI, destroys an instance, launches a workload, or adopts
execution.

`REUSE_ELIGIBLE` requires validated receipts for preflight identity, fresh
provider identity and all-fee quote, safe return, teardown/export, local
collection, protected scan, clean-worker proof, v12 watchdog dry run, and
immutable compatible next-goal authorization. Missing evidence or a
`fresh_provider_admission_required=true` next-goal receipt produces
`DESTROY_REQUIRED`.

The v12 watchdog receipt is only a local template/TTL proof. It must retain
`actual_provider_destroy_capability=PENDING_LIVE_PROVIDER` and
`provider_action_performed=false`; V13 does not claim live destroy capability.
