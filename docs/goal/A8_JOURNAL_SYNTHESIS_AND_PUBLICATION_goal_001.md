---
title: "A8 journal synthesis and publication"
phase_id: A8_JOURNAL_SYNTHESIS_AND_PUBLICATION
task_id: A8.1
status: PASS_A8_JOURNAL_PACKAGE
evidence_class: publication_synthesis
scientific_authority: true
claim_boundary: "synthesize validated A0-A7 evidence; do not create a new retrieval claim"
owner_gate_decision: "D3_SUBMIT_RELEASE_APPROVED_AUTOMATIC_AFTER_A7_PASS"
---

# Goal 001: A8 Journal Synthesis and Publication

## Objective

Convert the validated A0-A7 ArmIndex evidence into a journal-strength
manuscript and submission package. This phase follows `inbox/UPDATE_PLAN.md`.
It is a writing, literature, figure, table, and reproducibility phase, not a
new retrieval or reranking experiment.

## Preconditions

- A6 frozen full-DAPFAM diagnostic bundle and safe-return audit are complete.
- A7 seven-layer diagnosis and comparison framework is complete.
- Every quantitative claim is bound to a canonical receipt, manifest, or
  aggregate-safe result.
- The Owner approved automatic `D3_SUBMIT_RELEASE` immediately after A7 PASS.

## Closeout evidence

The anonymous V01 package is staged at
`03_Paper/01_ArmIndex/paper_01/`, with rules, manuscript source, references,
aggregate-safe figures/tables, claim-to-evidence matrix, and release manifest.
The package is ready for the Owner's venue submission workflow; this session
did not upload or submit to an external venue.

| Output | Evidence |
|---|---|
| Claim-to-evidence matrix | `03_Paper/01_ArmIndex/paper_01/provenance/claim_to_evidence.csv` |
| Manuscript source | `03_Paper/01_ArmIndex/paper_01/manuscript/paper_v01.tex` |
| Rules and workspace template | `03_Paper/01_ArmIndex/paper_01/RULES_AND_TEMPLATE.md` |
| Release manifest | `03_Paper/01_ArmIndex/paper_01/provenance/release-manifest.json` |
| A7 integrity | `control/armindex/a7/a7-result-integrity-audit-20260823.json` |

No protected payload, new retrieval experiment, reranker, or winner change was
performed.

## Execution

1. Freeze the claim-to-evidence matrix and separate development,
   confirmatory, operational, diagnostic, and external-comparison evidence.
2. Audit primary sources and protocol comparability for related work.
3. Produce publication figures, tables, manuscript source, references, and
   reviewer-simulation responses from validated evidence only.
4. Run number, citation, license, protected-data, and double-blind checks.
5. Prepare a release manifest and request `D3_SUBMIT_RELEASE` only after all
   checks pass.

## Protected-data and claim boundary

Protected qrels, membership, IDs, rankings, per-query outcomes, credentials,
model payloads, and provider payloads remain in Owner Store. Git and Paper
receive only aggregate-safe projections, figures, tables, hashes, and pointers.
No new retrieval model, reranker, pool expansion, winner change, or post-hoc
tuning is allowed.

## Terminal states

- `PASS_A8_JOURNAL_PACKAGE`
- `STOP_A8_WITH_EVIDENCE`
- `BLOCKED_OWNER_D3`
