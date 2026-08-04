# ArmIndex Research Protocol

The active campaign is `armindex-multiretriever-v2`. It uses five frozen
retrieval arms and a common executable representation grammar. OUT Recall@100
is primary; OUT nDCG@100 and OUT nDCG@10 are secondary. Operational decisions
also consider latency, throughput, charged cost, index size, RAM, and VRAM.

## Scientific sequence

1. Freeze evaluator, family mapping, split commitments, model adapters, grammar, and budgets.
2. Validate all five adapters with local synthetic fixtures and no network model resolution.
3. Screen common programs and promote at most three arms through deterministic rules.
4. Run per-arm AutoIndex on the frozen representation surface.
5. Measure cross-arm transfer and same-depth complementarity.
6. Optimize a frozen deterministic harness and production profiles.
7. Freeze no more than four finalists before one Selection exposure.
8. Require `D2_OPEN_FINAL` before the frozen Final confirmation.

The complete candidate, stopping, transfer, complementarity, and HarnessOpt
rules are maintained in the [AutoIndex/HarnessOpt contract](../../control/plans/ARMINDEX_AUTOINDEX_HARNESSOPT_CONTRACT.md).

## Migration boundary

The current A0 repository migration creates infrastructure and synthetic
fixtures only. Measured ArmIndex counters remain zero. Historical P1 measured
evidence is available by pointer/hash and is not promoted to an ArmIndex result.

## Claim discipline

No development, Selection, Final, or production claim exists without a
validated manifest and receipt. Negative outcomes close with evidence rather
than being silently discarded. Patent retrieval evidence is not a legal
novelty, validity, infringement, or freedom-to-operate determination.
