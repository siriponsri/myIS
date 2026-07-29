# myIS Research 1.0 Owner Gates

Owner Gates authorize a named scope, evidence set, budget, and action. Silence,
an agent recommendation, an earlier approval, or a dashboard preview is not
approval.

## Canonical decision record

Every Git-tracked governance decision is one immutable JSON record under
`00_governance/approvals/`, written only by the typed loopback decision API after
preview and explicit confirmation. It records:

```text
decision_id, gate_id, status, rationale, timestamp, actor,
display_label (optional/non-authoritative), evidence_manifest_hashes, git_commit, prior_record_hash,
supersedes_decision_id (when correcting an earlier decision)
```

The backend Windows/OS account is authoritative. Never trust an actor supplied
by the browser. A correction is a new superseding record; no decision is edited
or overwritten. Owner Gate decisions are the only canonical governance records
in Git.

## Gate table

| Gate | Required evidence | Owner decision |
|---|---|---|
| G0 Integrity/Migration | repo/overlay conflict map, integrity diagnosis, locked environment, tests, rollback, exact cleanup candidates | approve active documentation/contracts and any separately named archive/delete action |
| G1 Reproduction | corpus/query/qrels/family/evaluator commitments, field protocol, published targets, compute budget | run BM25/dense/Hybrid RRF reproduction |
| G2 Shared split and C development | shared membership commitment, C firewall, OUT-positive/power audit, C-MARGIN/C-SOEI audit, qrels-blind view schema, route/final budgets | open Track C C0/C1 development and selection |
| G3 Track C freeze | valid C0/C1 ablations, selected C1 policy, failure table, exact frozen-pool/protocol hashes, C ranking-diagnostic specification | freeze C0/C1 and hand over the frozen C1 harness to Track S |
| G4 Track S provider and baseline lock | G3 frozen-harness receipt, A0/A1 preregistration, provider/model preflight, S firewall, S-MARGIN audit, budget/retry plan | open required matched-budget A2/A2L/A3 optimization arms |
| G5 Track S freeze | all A2/A2L/A3 three-seed finalists, matched budget/model/provider evidence, optimization lineage, one frozen artifact per arm | submit nine seed-finalists once and freeze Track S arms |
| G6 Joint confirmation | frozen Git/config/prompt/skill/model/environment/pool, Track C and S aggregate schemas, one sealed joint test, external evaluator receipt | authorize the Owner-run one-command joint confirmation request exactly once |
| G7 External transfer | frozen PatenTEB `retrieval_OUT` compatibility, license/privacy evidence, no-retuning protocol and run-specific budget | run separately scoped C1 transfer without blocking Q or publication |
| G8 Publication | aggregate confirmation or clearly labeled descriptive evidence, claim-evidence audit, all repeats, limitations, artifact inventory, independent review | build or submit the named Track C and/or Track S publication package |

For G1, the Dashboard may present one validated external `OwnerValueBatchV1`
as a single hash/count-only evidence package. The batch remains a proposal while
`gate_status=pending` and `authorization=NOT_AUTHORIZED`. Approval still requires
an explicit immutable G1 decision binding the exact proposal/evidence hash,
clean Git commit, frozen RunSpec, compute/provider/time/cost budget, reproduction
scope, and any paid GPU/API or data-egress permission. Preparing or viewing the
batch is never approval.

The active graph is `Track C -> frozen C1 harness -> Track S`. Track C contains
a frozen-pool ranking/headroom diagnostic only; it is not an independent ranking/evidence lane
or a separately confirmable gate. Track S is required after a valid C1 harness.
Deferred evidence/ranking transfer work remains separately gated and cannot
change a frozen C1 or S result.

## Protected surfaces

Agents, optimizers, dashboard, Brain, MCP, MLflow, and report generators cannot
access or mutate:

- confirmation qrels, membership, IDs, protected payloads, or per-query outcomes;
- frozen split/query-ID hashes and qrels snapshots;
- evaluator, metric, and statistics implementation after freeze;
- corpus membership, parser semantics, family mapping, and ground truth;
- baseline result artifacts and frozen candidate pools;
- approval/budget/redaction/protection/manifest-validation code during measured
  optimization;
- immutable provenance, decisions, manifests, receipts, and result artifacts.

Only Track C adaptation/selection qrels may be exposed to its approved optimizer.
Track S optimizers receive only the separately authorized S surface. Shared query
membership uses seed `42` and the committed 250/125/872 partition; evaluators,
budgets, manifests, artifacts, and firewalls remain track-specific. Network
re-download is disabled during measured optimization.

## Confirmation boundary

Confirmation is executed outside the agent workspace by the Owner. The repo
emits only submission/config/protocol hashes. The returned package contains only
exact n, point estimates, paired deltas, 95% paired-bootstrap CIs, rank-biserial
effects, W/L/T, comparison-family metadata, and input/output hashes.

MDE is design sensitivity, not a pass threshold. Positive point delta is an
observed improvement; CI lower > 0 supports superiority; a positive delta with a
CI crossing zero is a higher measured score with uncertain superiority.

## Paid, provider, and external actions

Approval must name provider, requested model, endpoint class, effort, budget,
data leaving the machine, and fallback policy. No silent model/provider fallback
is permitted. Third-party providers are development-only by default. Paid API,
GPU, Vast.ai, vLLM, PageIndex model calls, cloud storage, MCP writes, and external
datasets require the applicable gate.

## Dashboard and PDF decisions

The dashboard is read-only for experiment artifacts and loopback-only. The only
canonical write is the typed decision endpoint. PDF access receipts are a second
narrow local-only write surface: one ignored, append-only, hash-chained JSON
receipt per access. The local receipt chain is tamper-evident, not tamper-proof.
Only a periodic chain-head digest and receipt range may be anchored through a new
Owner Gate record. PDF content requires an exact path/hash allowlist plus
license/privacy approval.

## Destructive and publication actions

Every delete requires a separate YES/NO approval naming exact files/directories,
even when an obsolete document has a replacement and backlink. Archive/move must
also name scope and preserve provenance. Commit, push, PR, merge, and publication
require explicit instructions; one action does not imply another.

Never call DAPFAM output a novelty/FTO opinion. Never claim significant
outperformance when the CI crosses zero. Never call a full-1,247-query
qrels-informed result unseen confirmation.

## Stop conditions

Stop and append a failure/decision record on split/qrels/family leakage, actor or
provider identity drift, unapproved fallback, batch-order drift beyond declared
tolerance, pool hash mismatch, absent ranking headroom, budget/retry exhaustion,
protected-data return, remote dashboard binding, path/ACL escape, corrupt ledger,
or unresolved validation/hash failure.
