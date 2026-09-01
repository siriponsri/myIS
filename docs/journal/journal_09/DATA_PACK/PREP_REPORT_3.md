source: docs/journal/JOURNAL_ARC_UPDATE.md; docs/journal/DATA_PACK/I1_bound_by_pool_depth.csv; docs/journal/DATA_PACK/I2_section_exposure.csv; docs/journal/DATA_PACK/F_case_studies.md; docs/journal/DATA_PACK/A_domain_exposure.csv; docs/journal/DATA_PACK/B2_depth_curve_extended.csv

# Journal Data-Prep Report, Round 3

All work in this round is post-hoc and local. No retrieval, indexing,
embedding, reranking, model execution, provider spend, or frozen-artifact
mutation was performed. The purpose of this round was to close the four
reviewer-facing gaps identified in `JOURNAL_ARC_UPDATE.md` before drafting the
journal narrative.

## Deliverables

| Item | Status | Output |
|---|---|---|
| I1. Apples-to-apples pool-depth bound | PASS | `DATA_PACK/I1_bound_by_pool_depth.csv` |
| I2. IPC-section exposure roll-up | PASS | `DATA_PACK/I2_section_exposure.csv` |
| I3. Zero-at-Top-1000 case studies | PASS | `DATA_PACK/F_case_studies.md` |
| I4. Domain-code validation | PASS | Rule recorded below and applied to I2 |

## I1: perfect-ordering bound at Recall@100

For each judged query and pool depth `k`, the oracle numerator is the number of
distinct relevant families found in the pool, capped at 100. The reported
quantity is the mean of that per-query recall, so it is directly comparable to
the observed Recall@100. The observed baseline is `0.188450`.

| pool depth | oracle Recall@100 | gain over observed |
|---:|---:|---:|
| 200 | 0.260167 | 0.071717 |
| 300 | 0.317703 | 0.129253 |
| 500 | 0.409842 | 0.221392 |
| 1000 | 0.529463 | 0.341013 |

Sanity check: the 200-row value is `0.260166940` before six-decimal display
rounding, reproducing the existing Rule 0 perfect-ordering bound `0.260167`.
The table makes the comparison valid: every row is Recall@100, while only the
available candidate pool changes.

## I2: IPC-section exposure

The existing 3-character table remains available as a descriptive appendix;
its 128 bins have small per-bin sample sizes (median 8 queries, no bin with 20
queries). It is therefore not used for ranked domain claims. The section-level
roll-up is the primary domain view:

| section | queries | incidences | absent rate | macro Recall@100 | bound |
|---|---:|---:|---:|---:|---:|
| A | 102 | 491 | 0.762 | 0.202696 | 0.255644 |
| B | 290 | 1,930 | 0.818 | 0.166662 | 0.234908 |
| C | 127 | 667 | 0.726 | 0.205912 | 0.290190 |
| D | 60 | 396 | 0.712 | 0.261816 | 0.333502 |
| E | 63 | 357 | 0.770 | 0.269600 | 0.368152 |
| F | 133 | 777 | 0.802 | 0.214407 | 0.286643 |
| G | 98 | 435 | 0.747 | 0.122455 | 0.191243 |
| H | 31 | 120 | 0.925 | 0.063833 | 0.128349 |

The roll-up contains 904 valid A--H queries and 5,173 strict cross-domain
incidences. The excluded `O60` record is one query with 20 incidences and is
not silently folded into any IPC section. The stable conclusion is uniformity:
every valid section loses 71.2%--92.5% of relevant families by Top-200.

## I3: failure cases

The old cases were replaced. Exactly two cases are now retained, both sampled
from the 219 queries with no relevant family in Top-1000. The cases preserve
opaque IDs, public title/abstract snippets, domains, relation status, relevant
counts, and the explicit statement `none in Top-1000`. They are intended to
make the exposure ceiling concrete without turning a descriptive example into
a semantic or causal claim.

## I4: IPC code validation rule

`G60` is a valid IPC 3-character class under section `G`; it must be mapped to
section `G` and must not be labelled as an invalid section. The observed `O60`
value comes from raw code `O60G/40`. Because `O` is outside the valid IPC
sections A--H used for the roll-up, it is marked `EXCLUDED_NON_IPC_SECTION` for
I2 and excluded from the section totals. It may remain in the 3-character
appendix only with that exclusion label. This rule corrects the earlier
wording: `O60` is excluded from the section analysis, while `G60` is retained
as a valid class inside section G.

## Rule 0 regression check

PASS. The prior canonical totals remain unchanged: 905 judged queries, 5,193
strict cross-domain relevant incidences, 796 found in ranks 1--100, 332 found
only in ranks 101--200, 4,065 absent from Top-200, Final-872 totals 619/158/95,
observed Recall@100 `0.188450`, and Top-200 perfect-ordering bound `0.260167`.
The I2 A--H roll-up intentionally excludes the single non-A--H `O60` record,
which is why its totals are 904 queries and 5,173 incidences.

## Evidence and boundary

All numeric values are deterministic projections from the retained A6
deep-ranking artifact and canonical relation field `domain_rel`. Public DAPFAM
Parquet supplies query/family IPC labels and text snippets. Protected qrels,
raw query membership, and per-query outcome payloads remain Owner-local and are
not copied into Git. No fixture or synthetic record is represented as measured
evidence.

## Closeout

The four post-hoc fixes are complete and suitable for journal drafting. The
central narrative can now compare pool depth and ordering on the same metric,
use IPC sections rather than underpowered 3-character rankings, illustrate the
zero-exposure tail with two clean cases, and state the classification parsing
rule without claiming that valid `G60` IPC classes are invalid.
