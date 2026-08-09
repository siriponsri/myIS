# A1.2 Scientific Execution Adoption Inputs V12-R3

## Scope

V12-R3 is an additive local-only finalizer. It preserves V11, V12, V13, and
every earlier receipt. It validates external aggregate-safe evidence and emits
one immutable repository-safe receipt. It never contacts a provider, opens an
instance, admits a quote, adopts execution, launches, measures retrieval, or
opens Selection or Final.

## Required External Evidence

Before finalization, the Owner-local store must contain these separate regular
files outside Git: the R3 code bundle, its R3 self-hashed receipt, the protected
compiler receipt, the exact matching 25/25 binding set, and the watchdog dry-run
receipt. The compiler receipt supplies all seven linked commitments: handoff,
transfer manifest, corpus, query, split, evaluator, and ephemeral-token map.

The current R2 bundle is preserved historical evidence. Do not reinterpret it
as an R3 bundle. Build R3 only after its source commit is pushed and the
worktree is clean:

```powershell
uv run --no-sync python -m myis_research.armindex.a1_2_scientific_execution_adoption_inputs_v12_r3 build-bundle `
  --repository-root . `
  --output <OWNER_LOCAL_R3_BUNDLE> `
  --receipt-output <OWNER_LOCAL_R3_BUNDLE_RECEIPT>
```

Run the Owner-local protected compiler separately. It must produce a complete
binding set and its aggregate-safe receipt before continuing. Then finalize:

```powershell
uv run --no-sync python -m myis_research.armindex.a1_2_scientific_execution_adoption_inputs_v12_r3 finalize `
  --repository-root . `
  --bundle <OWNER_LOCAL_R3_BUNDLE> `
  --bundle-receipt <OWNER_LOCAL_R3_BUNDLE_RECEIPT> `
  --owner-receipt <OWNER_LOCAL_COMPILER_RECEIPT> `
  --binding-set <OWNER_LOCAL_25_BINDING_SET> `
  --watchdog-receipt <OWNER_LOCAL_WATCHDOG_RECEIPT>
```

The command checks bytes, self-hashes, archive closure, static V11 bindings,
all nine Owner receipt fields, and equality of the seven shared commitments.
It writes only aggregate hashes and counts to the canonical receipt. Provider
identity, all-fee quote, live budget admission, and live provider receipt remain
`PENDING_LIVE_PROVIDER`; all execution authorization and measured counters stay
false or zero.
