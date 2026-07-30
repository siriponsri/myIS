# myIS Research Track C v0.1 CrossRoute Plan

Status: DOCUMENTATION_AND_CONTRACT_MIGRATION_ONLY

Program identity: myIS Research (myis-research)

Protocol: 1.0; Track C version: 0.1; package version: 0.1.0

This is the retained and migrated Track C source plan. It supersedes conflicting
draft statements in its prior version, but does not authorize experiments, qrels
evaluation, confirmation, GPU, paid API, or external data access.

## 1. Purpose and claim boundary

Track C tests mechanism-grounded candidate recovery, not legal novelty,
infringement, validity, or FTO. Its working novelty is an auditable
zero-tuned-versus-metric-tuned decomposition of CrossRoute candidate recovery.

The active program path is Track C -> frozen C1 harness -> Track S.

There is no independent ranking track. Ranking and evidence headroom remain a
post-freeze Track C diagnostic. Claim/passage evidence R2 is deferred to a
qualitative appendix or a separately gated transfer lane.

## 2. Shared split, independent firewalls

Track C and Track S use a shared query membership commitment:

| Field | Locked value |
|---|---:|
| seed | 42 |
| development/train IDs | 250 |
| selection IDs | 125 |
| joint sealed test IDs | 872 |

The identical membership does not permit shared execution surfaces. Track C and
Track S have independent evaluators, optimizers, budgets, manifests, artifacts,
and firewalls. The protected joint test membership, qrels, confirmation IDs,
per-query outcomes, evaluator/statistics implementation after freeze, corpus
membership, parser semantics, and family mapping remain outside the agent
workspace.

The actual OUT-positive counts and hashes are Owner-run protected outputs.
The preliminary values 181/91/633 are estimates only and must never be reported
as frozen facts.

## 3. Locked controls and arms

All comparisons retain the same corpus, family aggregation, evaluator, query
membership, and final cutoff.

| Arm | Locked definition |
|---|---|
| B0 | Llama-Embed-Nemotron-8B TAC dense top-400 at revision aa3b43a495a9b280d1bdb716da37c54bb495d630 |
| B1 | B0 encoder plus BM25 min-max fusion, weights 0.7/0.3 |
| B2 | Naive TAC/Abstract/Claim1 RRF |
| secondary | Pure BM25 and patembed-base |
| C0 | Zero-tuned CrossRoute |
| C1 | Metric-tuned CrossRoute |

C0 has six atomic routes:

1. TAC BM25, quota 100.
2. TAC dense, quota 100.
3. Independent-claim BM25, quota 50.
4. Independent-claim dense, quota 50.
5. Grounded-mechanism BM25, quota 50.
6. Grounded-mechanism dense, quota 50.

C0 uses raw budget 400, RRF k=60, family deduplication, deterministic
tie-breaking, and final top-100.

C1 may edit only route enablement, quotas, fusion, RRF, and pool/rerank depths.
Its raw budget remains at most 400. Prompts, query views, encoder revision, and
reranker instructions are frozen. C1 may consider at most 100 valid
configurations on C_TRAIN; it submits at most five Pareto finalists to
C_SELECTION once. The selection score must be strictly greater than the
incumbent; ties are rejected.

The G3 C1 handover records separate frozen C1 harness and C1 policy hashes. A
future Track S typed overlay may bind both hashes but cannot replace or mutate
them. It is limited to at most twelve scalar values over the already permitted
C1 dimensions; it cannot carry code, prompts, dynamic policy, executable tools,
or changes to the frozen query views, encoder, reranker instructions, corpus,
evaluator, split, qrels, family map, provider, or budget.

## 4. Data and leakage contract

Candidate generation is qrel-blind. It may use the query patent's TAC,
deterministically parsed independent claims, and mechanism views grounded to
query spans. It must not use:

- qrels, relevance summaries, target identifiers, target text, or target
  citation information;
- direct or indirect query-target citation routes;
- protected joint-test data, confirmation aggregates, or Track S selection
  information;
- external search that can reveal known targets during measured work;
- unjudged families as negatives.

Every generated expansion term retains source span, route, prompt/model hash,
grounding status, and a quarantine reason when rejected. Network re-download is
disabled during measured optimization.

## 5. Metrics and interpretation

The primary Track C comparison is C1 - C0 on paired family-level OUT Recall@100
over the untouched joint test. The additional confirmatory Holm family is
C0 - B1 and C1 - B1. There is no multiplicity correction for the single primary
comparison.

A full-1,247-query report is descriptive only and occurs after every arm is
frozen. It is not unseen confirmation when DAPFAM qrels informed development.

Confirmation reporting, when authorized, uses paired delta, exact eligible n,
deterministic 10,000-resample paired-bootstrap 95% confidence interval,
rank-biserial effect, and win/loss/tie counts. delta > 0 is an observed
improvement. A confidence-interval lower bound above zero supports a stronger
superiority claim. MDE is prospective sensitivity, never an observed-result
threshold.

## 6. Diagnostic, not a standalone track

C_DIAGNOSTIC runs only after C0/C1 freeze and only on the identical frozen
candidate pool. It verifies pool hash equality and reports:

- the no-rerank order;
- a frozen reranker;
- oracle and reachable nDCG;
- promotion and demotion;
- failure layer attribution.

The diagnostic cannot adaptively optimize ranking, create a separate gate, or support
an independent ranking claim.

## 7. Phases and gates

| Phase | Task | Required condition |
|---|---|---|
| F1 | F1.1 protocol-matched B0/B1/B2 reproduction contract | G1, future run |
| D0 | D0.1 shared split/firewall; D0.2 C-MARGIN and C-SOEI audits | G2 |
| C0 | C0.1 freeze and validate zero-tuned recipe | G2 |
| C1 | C1.1 train search; C1.2 one-batch selection | G2 |
| CF | CF.1 freeze C0/C1, hashes, C1 harness, diagnostic spec | G3 |
| Q | Q.1 joint test; Q.2 C diagnostic; Q.3 full descriptive benchmark | G6 |
| PC | PC.1 Track C manuscript | G8 |

C_MARGIN_VALUES_TBD_BLOCKING requires Owner selection of delta_IN and delta_ALL
from {0, 0.0025, 0.005} after the baseline-only audit, with
delta_ALL <= delta_IN. C_SOEI_VALUE_TBD_BLOCKING requires an Owner-signed
smallest effect of interest before C1 search. It informs interpretation only.

## 8. Freeze and artifacts

CF freezes code, configuration, prompts, skills, model revisions, environment,
budgets, pool hashes, C0/C1 manifests, and the frozen C1 harness before the
Owner confirmation request. The active artifact structure is:

    02_tracks/00_C_crossroute/
      C_artifacts/{configs,manifests,diagnostics,results,receipts}/
      C_documents/

No artifact may include protected qrels, membership, per-query confirmation
outcomes, credentials, or raw provider payloads. Results are immutable and
aggregate-only at confirmation ingress.

## 9. Manuscript and evidence discipline

The Track C IEEE manuscript uses C_-prefixed sections for Abstract, Introduction,
Related Work, Methodology, Results, Discussion, Conclusion, References, and two
appendices. Result-dependent sections explicitly say Results: n/a and
**wating for results** until validated artifacts exist. No figures, scores, or
outcome claims may be created in advance.

The final manuscript uses only literature records verified in the project
catalog, including U011, U012, U049, U082, U151, U152, and U153 where
appropriate. This planning file does not invent bibliographic entries.

## 10. Non-authorizations and limitations

This migration does not change uv.lock, execute an experiment, access protected
data, invoke a model provider, use GPU resources, or emit a confirmation
request. Every measured run remains contingent on the applicable Owner gate and
validated immutable manifest. The system is decision support, not legal advice.
