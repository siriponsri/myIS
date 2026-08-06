# A1.2 Owner-Local CPU Preflight

## Purpose

This document records the implementation and outcome of the reversible CPU-only
preflight that must pass before any A1.2 GPU reservation or measured retrieval.
The versioned A1.2 execution contract remains immutable and launch-locked.

## Validator

`src/myis_research/armindex/a1_2_preflight.py` is invoked with:

```text
python -m myis_research.armindex.a1_2_cli preflight --repository-root . --receipt outputs/audits/armindex/a1.2-owner-local-preflight-20260806.json
```

With an external read-only Owner staging root, it validates every dense-arm
`SHA256SUMS` entry and critical commitment, Snowflake remote-code byte hashes,
the measured Qwen maximum input length, dense adapter parity, storage, live
provider quote/instance metadata, and the external termination/TTL receipt.
Only sanitized metadata is accepted. The validator never contacts a provider,
reads access material, copies model bytes into Git, or opens protected benchmark
payloads.

## Current Receipt

The executed receipt is
`outputs/audits/armindex/a1.2-owner-local-preflight-20260806.json`. Its status
is `blocked_owner_input`: the canonical contract bindings pass, but all ten
Owner evidence groups are absent from the current workspace. The receipt keeps
`launch_ready=false`, `execution_contract_adopted=false`, `gpu_reserved=false`,
`measured_execution=false`, `protected_data_accessed=false`, and all scientific
and charged-resource counters at zero. This is engineering preflight evidence,
not retrieval-quality or scientific performance evidence.

## MLflow Projection

`outputs/audits/armindex/a1.2-owner-local-preflight-mlflow-safe.json` is the
scanner-safe projection. `scripts/register_a12_preflight_mlflow.py` mirrors only
that projection and writes a registration record that binds the canonical
receipt by SHA-256. Model bytes, protected payloads, provider payloads, and
access material is never an MLflow artifact.

## Owner Inputs Required

The Owner must provide an external read-only staging root containing complete
manifests for `ARM-02` through `ARM-05`; Snowflake remote-code byte hashes;
the measured Qwen maximum length; adapter parity and storage checks; a live
quote and provider instance identity; and a sanitized termination/TTL receipt.
After rerunning the CPU preflight successfully, the Owner must explicitly adopt
the unchanged execution contract and budget before any GPU capacity is reserved.

## Additive Four-GPU Revision

The blocked CPU receipt remains preserved as earlier engineering evidence. The
latest preparation state is the additive `a1.2-local-vast-4x3090-v2` revision,
which validates local synthetic four-worker orchestration and keeps the v1
contract byte-identical and unadopted. Its live Owner action is documented in
`docs/operations/A1_2_VAST_4X3090_OWNER_RUNBOOK.md`. The planning rate is USD
0.60 per hour for the complete four-RTX3090 instance, with an estimated 2-4
instance-hours (USD 1.20-2.40) plus 2-4 local hours. Passing that live preflight
still leaves scientific launch and adoption closed.
