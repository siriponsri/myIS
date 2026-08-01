---
name: myis-run-harnessopt
description: Preflight, dry-run, execute, collect, and compare the approved myIS Research Track S v0.1 matched-budget SkillOpt, SkillOpt-Lite, and typed HarnessOpt study.
---

# Run myIS Research Track S HarnessOpt

Read `AGENTS.md`, the active `PLAN.md`, and the applicable canonical control
records. The historical `00_governance/OWNER_GATES.md` path is not active.
Track S protocol, approval, run specification, split commitments, budget,
module registry, and `references/harnessopt-contract.md` before any action.
This skill does not authorize experiments, provider calls, GPU work, or
confirmation evaluation. It is not part of the P2/R1 readiness or measured
path; do not run it for P2 and do not activate SkillOpt.

## Preserve the locked design

Track S follows frozen Track C1. It has no independent ranking phase. The shared
query-ID commitment is 250/125/872 at seed 42, but Track S keeps independent
evaluator, optimizer, firewall, budget, manifests, and artifacts. Never expose
joint-test membership, qrels, protected payloads, or per-query outcomes.

Required arms are A0, A1, A2, A2L, and A3. A2/A2L/A3 each begin at the same
frozen A1 state and use seeds 11, 23, and 47, a cap of 160 rollouts per seed,
and USD 20 per optimized arm. Shared services have USD 30; stop at USD 100
project total. A2 is SkillOpt v0.2.0 commit
`51d0a4d96e88558c84dee637f98e24e3fb2d1547`; A2L is adapted SkillOpt-Lite
commit `4cb4eeef1f95375a9179737ab94cf5e64b9647c6`. A2L-P and A3X are deferred,
exploratory variants and are not valid Track S v0.1 arms.

Use `qwen/qwen3-30b-a3b-instruct-2507` non-thinking via the provisional
OpenRouter CoreWeave BF16 endpoint. No routing, fallback, or parameter dropping
is allowed. Permit one identical retry only for a transport error. A failed
identity/schema/context/latency/repeated-fixture preflight stops for an Owner
decision under `COREWEAVE_FINAL_FREEZE_TBD_BLOCKING`.

## Execute only under the relevant gate

1. Validate `myIS Research` / `myis-research`, protocol 1.0, Track S v0.1,
   G4/G5 scope, exact Python/uv/OS/lock environment, split hashes, budget,
   provider identity, frozen A1, and fresh artifact path.
2. Dry-run fixtures proving protected-access denial, typed-patch denial, budget
   stop, event ordering, immutable manifest writing, and MLflow mirror
   isolation. Do not contact a provider during a dry run.
3. Run S0: lock A0/A1/provider and complete the separate three-seed S-MARGIN
   audit. Stop until the Owner resolves `S_MARGIN_VALUES_TBD_BLOCKING`.
4. Run A2, A2L, and A3 as required matched parallel arms from A1 with matched
   seeds, rollout caps, data access, evaluator, tool set, and stop rules. A3
   may edit only the typed allowlist in the reference contract.
5. Accept only when the preregistered primary selection score is strictly
   greater than the incumbent. Reject ties and lower scores; retain all outcomes.
6. Validate hashes, provider/fallback state, costs, repeat matching, batch-order
   invariance, and firewall integrity. Write the manifest last and immutably;
   MLflow mirrors only allowlisted validated material.
7. At SF, freeze one final artifact per arm and emit a hash-only Owner
   confirmation request. The external evaluator returns aggregate-only evidence.

Report the primary A3-A2 paired OUT Recall@100 comparison without multiplicity
correction. Apply Holm only to A1-A0, A2-A1, A2L-A1, A3-A1, and A2L-A2;
A3-A2L is exploratory. DAPFAM is retrieval relevance, not legal advice.
