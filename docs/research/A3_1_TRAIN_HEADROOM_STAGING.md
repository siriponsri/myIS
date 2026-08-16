# A3.1 Train-Headroom Staging

The checked-in A3.1 bundle is a hash-only preparation surface for ARM-01
through ARM-05. Its manifest is `PENDING_A2_CLOSEOUT` and intentionally contains
no winner, receipt, query, ranking, membership, qrels, provider, or runtime
payload.

The bundle may be admitted only after a valid A2 closeout, five winner-selection
receipt hashes, and the frozen A1 incumbent aggregate receipt are supplied at
runtime. Owner-local fixed diagnostic outputs must return aggregate-only hashes
and metrics bound to the fixed evaluator, split, membership/qrels commitments,
model/runtime, and frozen tuple. No staging step starts measurement, accesses
protected data, contacts a provider, mutates A2, opens Selection/Final, or
spends.
