# A4 Readiness Contract

This is an additive, contract-only scaffold for `A4_PRODUCTION_TRANSFER_AND_SELECTION`.
It does not start A4 measurement, open Selection or Final, inspect protected
membership or qrels, or instantiate a production candidate from speculative
results.

The handoff is fail-closed until the A3 closeout receipt, three winner program
hashes, transfer/complementarity/HarnessOpt aggregate receipts, and safe-return
receipt are present. The current A3 preparation manifest is therefore reported
as `pending_a3_closeout`, not as A4 scientific authority.

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
