# A2 LO 004-001: measured AutoIndex terminal closeout

- Session mode: `LO`
- Phase / task: `A2_PER_ARM_AUTOINDEX / A2.1`
- Source goal: `docs/goal/A2_PER_ARM_AUTOINDEX_goal_004.md`
- Attempt: `a2-goal004-20260816-005`
- Terminal status: `PASS_A2_EXECUTION_CLOSEOUT`
- Integrity status: `PASS_A2_RESULT_INTEGRITY`
- Provider disposition: `OWNER_ACTION_DESTROY`

## Outcome

The complete frozen A2 universe is accounted for as `52 = 44 measured + 8
dormant conditional-reserve candidates`, with zero candidate failures. The
aggregate-safe return passed and no remote workers remained. Total charged
workload cost was USD `54.52666666666665948`, within the USD 60 hard stop.

The result is development evidence only. It supports the audited A2 measured
comparison and bounded A3 preparation, but does not support Selection, Final,
legal, causal, or production-superiority claims.

## Primary outcomes

| Arm | Retained representation | OUT Recall@100 | A1 comparison | A3 disposition |
| --- | --- | ---: | --- | --- |
| ARM-01 | diagnostic top tie | 0.23467 | three-way tie, no winner | excluded diagnostic |
| ARM-02 | diagnostic top tie | 0.29000 | three-way tie, no winner | excluded diagnostic |
| ARM-03 | `matched-b2-orthogonal` | 0.42300 | numerical tie at presentation precision | primary transfer input |
| ARM-04 | `matched-b1-orthogonal` | 0.35867 | strict improvement from 0.35267 | primary transfer input |
| ARM-05 | `matched-b1-matched-ablation` | 0.37367 | no strict improvement from 0.38000 | primary transfer input |

ARM-03, ARM-04, and ARM-05 are retained only under the Owner-approved
three-primary amendment. ARM-01 and ARM-02 remain bounded negative diagnostic
evidence rather than hidden failures.

## Evidence chain

| Evidence | Status | Record SHA-256 |
| --- | --- | --- |
| measured execution closeout | PASS | `e4bc663d7ee09282c334f25945ede247a50b81742a690c214e0f2aa9ffb81d1d` |
| result-integrity audit | PASS | `7d31b80d4dab6897f3110ee629ddf8f9d12fd5f0522b0d8ccd175ba892986642` |
| aggregate-safe return | PASS | `659982aea768c6d4c057a75c6a50b04026d7c48875d604e06b1563a1b2b09484` |
| closeout projection | PASS | `80ce52d3edcac62298b3b3ed96d685fe98d9bc8cd1e1f870147a2c742f40027a` |

The receipt files remain in the Owner Store. The repository projection retains
only allowlisted aggregate metrics, hashes, safe IDs, and `owner-store://`
pointers. It validates the closeout file SHA-256, integrity-audit file SHA-256,
safe-return file SHA-256, and each corresponding record hash before generating
any downstream artifact.

## Recovery and safe return

The attempt preserves the incompatible earlier runtime attempt as non-combinable
failure lineage. The terminal attempt used durable candidate checkpoints,
recovery provenance, matched-first reserve handling, and a separate dormant
receipt repair. The repair changed only receipt provenance bindings and did not
alter frozen candidates, measured metrics, evaluator behavior, or aggregate
results. No incompatible partial output was combined.

Safe return includes 57 allowlisted aggregate artifacts. The protected scan
passed, and worker reaping completed before the closeout receipt was issued.

## Publication artifacts

The following figure families are rendered from the validated projection in
`outputs/figures/armindex/a2-goal004/`, each as PNG, SVG, and PDF:

1. candidate coverage and recovery completeness;
2. five-arm aggregate OUT metrics;
3. quality-latency-cost frontier;
4. matched-first reserve decision path;
5. appendix provenance and audit map.

The figure manifest is
`outputs/figures/armindex/a2-goal004/a2-goal004-figure-manifest.v1.json`.
Figures label ARM-01/02 as diagnostics and preserve the ARM-03 tie and ARM-05
non-improvement qualifications.

## A3 and provider disposition

A3 Extended must use only ARM-03, ARM-04, and ARM-05. It is not launchable
until a fresh Owner-authorized, hash-bound Train-250 query, corpus, and
evaluator package is available; the A1 REP-DEV package is not a substitute.
There is no already-authorized executable workload for the idle instance, so
the evidence-based disposition is `OWNER_ACTION_DESTROY`. Do not destroy it
automatically and do not retain it solely for a possible future A3 run.

## Post-measurement audit prompt

```text
Act as the independent post-measurement publication auditor. Read
docs/long_run/A2_PER_ARM_AUTOINDEX_lo_004_001.md,
control/armindex/a2/a2-goal004-closeout-projection.v1.json, and the A2 figure
manifest. Verify aggregate-safe hash bindings, complete 52-candidate
accounting, claim boundaries, figure labels, and the three-primary A3 route.
Classify every finding as PASS, FIX_FORWARD, REPLAN_INTERNAL, or HARD_STOP.
Do not open A3, Selection, or Final.
```
