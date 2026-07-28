# myIS Research Track S v0.1 HarnessOpt contract

## Identity and prerequisite

This contract applies to `myIS Research` (`myis-research`), protocol `1.0`,
Track S `0.1`, after the G3-approved frozen Track C1 harness. It neither creates
an independent ranking track nor permits Track C changes.

## Arms and invariants

| Arm | Editable surface |
|---|---|
| A0 | frozen C1 control |
| A1 | frozen human seed skill |
| A2 | SkillOpt skill text from frozen A1 |
| A2L | SkillOpt-Lite skill text from frozen A1 |
| A3 | typed HarnessOpt fields from frozen A1 |

A2, A2L, and A3 use the same target/provider/parameters, A1 state, authorized
data access, evaluator/statistics, tools, seeds `11/23/47`, 160-rollout cap per
seed, selection rule, and stop ceilings. A2 uses SkillOpt v0.2.0 commit
`51d0a4d96e88558c84dee637f98e24e3fb2d1547`; A2L uses adapted SkillOpt-Lite
commit `4cb4eeef1f95375a9179737ab94cf5e64b9647c6`. Each optimized arm has USD 20;
shared services have USD 30; USD 100 is a project hard stop.

## Provider, firewall, and patch rule

The target is `qwen/qwen3-30b-a3b-instruct-2507`, non-thinking, through
provisional OpenRouter CoreWeave BF16. Reject fallback, routing, parameter
dropping, and non-transport retries. Preflight must verify identity, seed,
tools, strict schema, context, latency/errors, and repeated-fixture stability.

Only A3 may change typed route enablement, quotas/depths within the frozen
budget, deterministic fusion, pool/rerank depths, and validated context/control
fields. Reject any edit to query views, prompts, encoder, reranker instructions,
corpus, qrels, split membership, family mapping, evaluator/statistics, model,
provider, budget, confirmation, or protected historical artifact. Reject
undeclared tools, executable code, protected path access, and network
re-download during measured optimization.

The shared commitment is 250/125/872 at seed 42. Track S has its own evaluator,
optimizer, budget, manifests, artifacts, and firewall. Joint-test membership,
qrels, outcomes, and protected per-query payloads never enter the workspace.

## Selection, artifacts, and confirmation

Preregister one primary selection score per arm. Accept only
`candidate_score > incumbent_score`; reject exact ties and lower scores. Preserve
all valid, rejected, and invalid attempts. The immutable bundle includes run
spec, prompt/skill/config, provider events, validation records, cost/progress
lineage, final artifact, environment, manifest, and allowlisted MLflow receipt.
Write the manifest last and never overwrite it.

After SF, the Owner-run external evaluator performs one joint test. The repo
emits only a hash-only request and accepts only a schema-valid aggregate package.
The primary A3-A2 paired OUT Recall@100 comparison has no multiplicity
correction. Holm applies only to A1-A0, A2-A1, A2L-A1, A3-A1, and A2L-A2;
A3-A2L is exploratory.
