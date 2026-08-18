# A4 Readiness Contract

This is an additive, contract-only scaffold for `A4_PRODUCTION_TRANSFER_AND_SELECTION`.
It does not start A4 measurement, open Selection or Final, inspect protected
membership or qrels, or instantiate a production candidate from speculative
results.

The A3 closeout is now bound by
`control/armindex/a4/a4-readiness-binding-20260819.json` (`binding_sha256`
`4fb8b8f8d6d80941b0c76116d13c4cfd5199dbcd0d17e59152f0088c54c4f7fd`). The
binding references the passing A3 result-integrity audit, aggregate safe return,
flat HarnessOpt evaluation, and frozen runtime bindings. It is a readiness
handoff only: `measured_execution`, `selection_permitted`, and
`final_permitted` remain false.

The handoff is fail-closed unless the A3 closeout binding, three winner program
hashes, transfer/complementarity/HarnessOpt aggregate receipts, and safe-return
receipt are present. The A4 binding is therefore `contract_only_ready`, not A4
scientific authority.

The scaffold validates:

- the frozen three-primary A3 scope and nine-cell transfer matrix;
- explicit model/license snapshots, with `ARM-03` excluded from commercial
  profiles and `ARM-04 + ARM-05` retained as the commercial fixed union;
- a deterministic non-dominated quality/latency/cost frontier;
- complete `FAST`, `BALANCED`, and `DEEP` profile manifests with contract-only
  status and zero Selection/Final counters;
- legal structured-retrieval transfer isolation and explicit unsupported maps;
- an atomic owner-local one-shot Selection preflight counter.

The one-shot counter records only that aggregate-safe preflight checks passed.
It is not Selection access and cannot be reused after consumption. Any missing,
false, malformed, or already-consumed state raises `A4ReadinessError`.
