# IS1 Research V0.1 Owner Gates

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
| G2 Track C Development | OUT-positive/power audit, proposed split, qrels-blind view schema, route/final budgets, protected workspace design | open candidate-exposure development/selection |
| G3 Track C Freeze | valid ablations, selected policy, failure table, exact pool and protocol hashes | freeze Gate C method, split commitments, and candidate pool |
| G4 Track R Development | G3 pool hash, R0 headroom, reranker/evidence budget, negative controls, PDF/source permissions | open ranking/evidence development on the identical pool |
| G5 Optional HarnessOpt | A0-A3 preregistration, calibration report, matched model/provider/effort/budget/repeats, patch protections | open optional S optimizer work |
| G6 External Confirmation | frozen Git/config/prompt/skill/model/environment/pool, one primary baseline per gate, aggregate schema, external evaluator receipt | authorize the Owner-run one-command confirmation request exactly once |
| G7 External Transfer | external corpus/license/privacy/protocol comparability and budget | run a separately scoped transfer study |
| G8 Publication | aggregate confirmation or clearly labeled descriptive evidence, claim-evidence audit, all repeats, limitations, artifact inventory | build/submit the named publication package |

Gate C and Gate R claims are independent. G4 requires a G3 pool, but a negative
Gate C confirmation does not erase a positive Gate R comparison on that frozen
pool, and vice versa. Track S is optional and never blocks C/R reporting.

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

Only adaptation and selection qrels may be exposed to an approved optimizer.
Network re-download is disabled during measured optimization.

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
