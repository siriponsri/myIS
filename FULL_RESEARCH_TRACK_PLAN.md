# myIS Research 1.0 Scientific Protocol

Status: `PREREGISTERED_CONTRACT_EXECUTION_GATED`
Track versions: C `0.1`, S `0.1`

## Research graph and claims

The active path is `Track C -> frozen C1 harness -> Track S`, followed by one
sealed joint test and two independently governed papers. There is no active
independent ranking/evidence lane. Frozen-pool ranking is a Track C diagnostic; claim/passage
evidence is qualitative appendix material or a separately gated deferred transfer.

DAPFAM evaluates family-level retrieval relevance. It cannot establish patent
novelty, infringement, freedom to operate, validity, or any legal conclusion.

Track C asks whether mechanism-grounded multi-route candidate recovery benefits
from a bounded metric-tuned policy. Its primary comparison is C1-C0 on OUT
Recall@100. Track S asks whether typed HarnessOpt improves over full SkillOpt
under matched resources. Its primary comparison is A3-A2 on the untouched test.

## Shared membership, separate experiments

The two tracks commit to seed `42` and query counts `250/125/872`. A protected
Owner process freezes exact IDs, qrels snapshot, strata, membership hashes, and
actual OUT-positive counts. Values `181/91/633` are planning estimates only.

Sharing membership does not share experimental state. C and S have distinct
evaluators, optimizer workspaces, budgets, manifests, artifact roots, protection
checks, and result packages. Confirmation membership, qrels, payloads, and
per-query outcomes remain outside this repository. The repository exchanges only
hash-only requests and schema-validated aggregate packages.

## Track C controls

The primary protocol-matched controls are:

| ID | Locked recipe |
|---|---|
| B0 | `Llama-Embed-Nemotron-8B` TAC dense top-400, revision `aa3b43a495a9b280d1bdb716da37c54bb495d630` |
| B1 | Same encoder plus BM25 min-max fusion, weights `0.7/0.3` |
| B2 | Naive TAC/Abstract/Claim1 reciprocal-rank fusion |

Pure BM25 and `patembed-base` are secondary controls. Published DAPFAM values
are reproduction references only. The primary comparator is resolved from one
preregistered protocol-matched local baseline manifest before any C arm result.

## C0 zero-tuned arm

C0 has exactly six atomic routes: TAC BM25, TAC dense, independent-claim BM25,
independent-claim dense, grounded-mechanism BM25, and grounded-mechanism dense.
The quotas are `100/100/50/50/50/50`, raw family budget is `400`, RRF uses
`k=60`, and the final family list is top-100. Query terms must map to source spans;
ungrounded additions are quarantined. Family deduplication and tie-breaking are
deterministic and retain every route/view/publication rank and score.

## C1 metric-tuned arm

C1 starts from C0 and may edit only route enablement, quotas, fusion choice,
RRF parameter, and pool/rerank depths while retaining the raw budget of 400.
Prompts, query views, encoder identity/revision, and reranker instructions are
frozen. At most 100 valid configurations may be evaluated on `C_TRAIN`.
Exactly five Pareto finalists are hashed and submitted to `C_SELECTION` once.
Candidates are accepted only on strictly greater preregistered primary selection
score; ties reject.

Before C1, the baseline-only C-MARGIN audit chooses `delta_IN` and `delta_ALL`
from `{0,0.0025,0.005}` with `delta_ALL <= delta_IN`. The Owner also signs the
C smallest effect of interest. Both are interpretive, not hard observed-result
gates, and remain `TBD_BLOCKING` until signed.

## Track C evaluation

- Primary: C1-C0 paired OUT Recall@100.
- Additional Holm family: C0-B1 and C1-B1.
- Descriptive: C0 over all 1,247 queries only after all arms freeze.
- Diagnostic: identical pool hash, no-rerank order, frozen reranker,
  oracle/reachable nDCG, promotions/demotions, and failure layer.

The diagnostic cannot add/remove candidates, tune a ranker, or create an
independent scientific gate. A negative C1-C0 result remains publishable.

## Track S starting state and provider

All optimized arms descend from the same frozen A1 and consume the same frozen
C1 harness. The target is `qwen/qwen3-30b-a3b-instruct-2507`, non-thinking,
through the provisional OpenRouter CoreWeave BF16 endpoint. Routing, fallback,
and unsupported parameter dropping are forbidden.

The preflight checks resolved model/provider identity, seeds, tools, strict
schema behavior, context capacity, latency/errors, and repeated-fixture
stability. An identical retry is allowed once only for a transport error. A hard
failure stops execution and requires a new Owner decision. The endpoint remains
`COREWEAVE_FINAL_FREEZE_TBD_BLOCKING` until the preflight passes.

## Track S arms and budgets

- A0: frozen baseline.
- A1: frozen human seed skill and common start.
- A2: SkillOpt `v0.2.0`, commit
  `51d0a4d96e88558c84dee637f98e24e3fb2d1547`, frozen harness.
- A2L: required adapted SkillOpt-Lite, source commit
  `4cb4eeef1f95375a9179737ab94cf5e64b9647c6`, frozen harness.
- A3: optimized skill plus the declared typed harness allowlist.

A2, A2L, and A3 execute in parallel from the same A1 with seeds `11,23,47`, cap
`160 rollouts/seed` and `480/arm`, USD 20 per arm, USD 30 shared services, USD 90
target and USD 100 hard stop. Model, provider, effort, data, evaluator, tools,
initial state, retry policy, and stopping rules match. A2L-P (`400/seed`) and
broad HarnessOpt A3X are future exploratory variants and cannot replace an arm.

An independent baseline-only three-seed S-MARGIN audit must resolve
`S_MARGIN_VALUES_TBD_BLOCKING` before arm execution. Nine seed-finalists are
submitted once; one artifact per arm is frozen without test feedback.

## Track S evaluation

- Primary, no multiplicity correction: A3-A2 paired OUT Recall@100.
- Preregistered Holm family: A1-A0, A2-A1, A2L-A1, A3-A1, A2L-A2.
- Exploratory only: A3-A2L.

Every comparison reports exact n, point estimates, paired delta, deterministic
10,000-resample paired-bootstrap 95% CI, rank-biserial effect, W/L/T, input/output
hashes, cost, latency, tokens, provider identity, fallback state, and all repeats.
Delta above zero is observed improvement; CI lower above zero strengthens the
superiority claim but is not a hard gate.

## Transfer and publication

CT applies frozen artifacts to PatenTEB `retrieval_OUT` without retuning. It is
blocked until license/field compatibility and a run-specific G7 budget resolve
`CT_BUDGET_LICENSE_TBD_BLOCKING`; it does not block joint evaluation or papers.

Track C and Track S each have separate G8 publication records. The workflow is
research -> write -> integrity audit -> independent review -> revision -> final
integrity -> IEEE assembly. Results-dependent drafts state `Results: n/a` and
`wating for results` until validated aggregates exist. Null, boundary, and failed
outcomes remain in the record; no figures or result claims are fabricated.

## Stop conditions

Stop on missing approval, identity/hash drift, protected-data exposure, budget
ceiling, invalid provider resolution, fallback, inconsistent split/evaluator,
mutable frozen artifact, repeated selection access, missing headroom, or an
unclassified failure. Retain negative and invalid attempts with correct labels.
