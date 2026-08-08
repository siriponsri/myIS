# A1.2 Publication-Impact Preregistration V12

## Status and authority

This additive publication-analysis contract is local-only preparation. It binds
the unchanged A1.2 scientific execution request v11 and its receipt by file and
self SHA-256, while preserving every v1-v11 artifact unchanged. It does not
adopt execution, contact a provider, authorize a launch, open Selection or
Final, or establish a retrieval-quality or publication result.

## Objective

The contract makes future ArmIndex claims interpretable at publication review:
it separates candidate exposure from ranking quality, distinguishes development
from confirmation, and requires fair comparisons for representation effects,
cross-arm complementarity, and operational performance.

## Outcome hierarchy

The sole primary outcome is family-level OUT Recall@100, macro-aggregated over
eligible OUT queries under the frozen evaluator, family mapping, cutoff, and
stable tie policy. OUT nDCG@100 and OUT nDCG@10 are ordered secondary ranking
outcomes. Neither oracle-pool nDCG nor oracle-pool Recall is a deployed result.

The future protected evaluator receipt must record the missing/unjudged-query
policy before measurement. Repository projections contain only aggregate-safe
estimates, hashes, counts, effect sizes, confidence intervals, comparison-family
metadata, and claim boundaries.

## Development and confirmation

REP-DEV supports the common screen and representation development. HARNESS-DEV
supports transfer, complementarity, and harness development after the relevant
representation programs freeze. Selection-125 may be used exactly once to
select frozen finalists; it is not a confirmatory test. Final-872 is the sole
confirmatory evaluation and may run only after `D2_OPEN_FINAL` with every
finalist frozen before its exposure.

No post-Selection or post-Final program, arm, adapter, evaluator, split,
threshold, depth, fusion, or operational mutation is permitted.

## Confirmatory comparison and statistics

The future primary comparison is the frozen HarnessOpt champion against the
frozen strongest valid single-arm champion on the identical family-level
protocol. The protected confirmation analysis uses eligible OUT queries as the
paired unit and performs exactly 10,000 paired bootstrap resamples with a seed
bound in the frozen confirmation analysis receipt.

Each safe aggregate claim receipt reports point estimates, paired delta, a
two-sided 95% paired-bootstrap confidence interval, win/tie/loss, rank-biserial
effect, and comparison-family ID. Superiority requires the primary interval's
lower bound to exceed zero. A positive point estimate whose interval crosses
zero is reported as uncertain superiority. Holm correction applies only to a
small preregistered additional confirmatory family; all other analysis is
labelled exploratory.

## Exposure and complementarity

Single-arm and multi-arm comparisons must use the same total candidate-depth
budget. The future receipt binds per-arm depth, union construction, deduplication,
fusion, family aggregation, pool hash, and all-arm latency and cost. Oracle
metrics are frozen-pool diagnostics only.

Complementarity requires the eligible OUT-query denominator, unique relevant
family-query-pair numerator, a defined pairwise relevant-pair overlap, an
equal-depth union versus best-single comparison, and incremental latency/cost.
A non-best arm may be retained only through its preregistered gate, never from
model-name diversity or a favourable post-hoc cell.

## Representation interaction and operational reporting

Representation effects are reported through a program-by-arm matrix containing
within-arm and cross-arm transfer deltas, rank order, rank-reversal indicators,
paired effects/confidence intervals, and truncation/cost context. Any conclusion
is limited to the five frozen arms, five programs, DAPFAM protocol, and frozen
budget; it cannot claim universal causal behaviour.

Operational claims require a frozen cold/warm procedure, repetition count,
execution order, discard policy, hardware/runtime identity, resource sampling
cadence, and failure/timeout/OOM denominator. Ranking replay proves ranking
determinism; it is not evidence of latency variance.

## Candidate integrity

The candidate universe and budget must freeze before measurement, and every
development decision must be replayable from a ledger. Promotion must follow a
frozen lexicographic rule. Max-cell promotion is forbidden. Research and
commercial-capable champion tracks remain distinct.

## Next action

Retain `launch_allowed=false`, `adopted_for_execution=false`, and all counters
at zero. The next authorized work remains the unchanged v11 Owner-local
adoption-input preparation; this v12 layer is a prerequisite for future
publication-grade claim analysis, not a substitute for that adoption process.
