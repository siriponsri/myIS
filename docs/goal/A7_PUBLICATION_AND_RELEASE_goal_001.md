---
title: "A7 publication and release"
phase_id: A7_PUBLICATION_AND_RELEASE
task_id: A7.1
status: BLOCKED_OWNER_D3
lifecycle: BLOCKED
evidence_class: publication_and_release
scientific_authority: false
execution_permitted: false
required_owner_decision: D3_SUBMIT_RELEASE
protected_payloads_allowed: false
previous_goal: docs/goal/A6_FULL_DAPFAM_MATERIALIZATION_AND_SCALABILITY_goal_001.md
last_material_update: 2026-08-19
next_authorized_action: WAIT_FOR_D3_SUBMIT_RELEASE_AND_VALIDATED_A0_A6_EVIDENCE
---

# Goal 001: A7 publication and release

## Objective and boundary

Create the manuscript, reproducibility package, figures, tables, release
bundle, and public claims only after `D3_SUBMIT_RELEASE` is recorded. A7 uses
validated aggregate-safe evidence from A0 through A6 and never treats a
projection, slide, draft, Brain note, or unverified summary as scientific
authority.

A7 reports A6 only as post-confirmatory operational scalability evidence. It
must not convert A6 coverage, throughput, or cost findings into claims of
retrieval-quality superiority, external generalization, legal validity, or
commercial superiority without separately valid evidence.

## Required predecessor evidence

- canonical A0-A5 measured/audited receipts and claim boundaries;
- A6 aggregate-safe closeout, audit, figures, data tables, and source hashes,
  or an explicit bounded A6 failure/unsupported closeout;
- a complete provenance graph from every publication number to a canonical
  receipt or approved aggregate-safe table;
- a fresh `D3_SUBMIT_RELEASE` receipt binding the exact manuscript/release
  revision and allowed claim scope.

## Work status

| Step | Status | Completion evidence |
|---|---|---|
| A0-A6 evidence registry and claim boundaries verified | BLOCKED | publication evidence manifest |
| D3_SUBMIT_RELEASE recorded | BLOCKED | Owner decision receipt |
| Manuscript, tables, figures, and reproducibility package assembled | BLOCKED | hash-closed release candidate |
| Independent claim/citation/protected-data audit passed | BLOCKED | release audit receipt |
| Publication/release projections and Git closeout complete | BLOCKED | pushed release commit and safe artifacts |

## Execution flow

1. Validate D3, the A0-A6 evidence manifest, claim boundaries, and protected
   data scan before drafting publication-facing results.
2. Build all tables and figures from validated aggregate-safe source artifacts;
   retain numeric provenance and figure-claim manifests.
3. Assemble the manuscript and reproducibility bundle with frozen code/config
   hashes, license notices, methods, negative outcomes, failure analysis, and
   limitations.
4. Run independent citation, claim, layout, reproducibility, license, and
   protected-data audits. Repair only presentation or provenance defects;
   never alter measured evidence.
5. Commit/push clean release artifacts, update projections, and record the
   release disposition. Raw corpus, qrels, memberships, raw IDs, rankings,
   per-query outcomes, credentials, provider payloads, and model payloads are
   never included.

## Terminal states

`PASS_A7_PUBLICATION_AND_RELEASE`, `STOP_A7_WITH_EVIDENCE`, or
`BLOCKED_OWNER_ACTION`. No new scientific measurement, candidate selection,
or Final access is authorized by A7.
