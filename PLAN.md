# IS1 Research V0.1 Canonical Execution Plan

Status: `IMPLEMENTATION_FOUNDATION_ACTIVE_SCIENTIFIC_EXECUTION_GATED`
Protocol family: `candidate-exposure-freeze-ranking-v1`
Active identity: `IS1 Research V0.1` (`Paper E` is a historical alias only)
Execution authority: this file, interpreted with `AGENTS.md` and
`00_governance/OWNER_GATES.md`.

This is a goal-based plan with exactly two planning levels: Phase and Task.
Completing a task means satisfying its acceptance criteria, not obtaining a
positive metric. Owner approval opens only the named scope. F1-Q scientific
execution remains gated even when its contracts and offline tests are present.

## Phase F0 - Integrity and documentation migration

### Task F0.1 - Prove repository, import, and dependency integrity

- **Goal:** establish canonical bytes and a replayable Python environment before
  any scientific development.
- **Execution model:** GPT-5.6 Sol High for implementation and diagnosis; local
  deterministic Python only for checks.
- **Objective:** make `validate_restructure.py` and `validate_integrity.py`
  explain every integrity decision, including the three BATCH_2A records, without
  auto-repairing expected hashes.
- **Contracts:** `RuntimeEnvironment`, Git index/worktree byte identity,
  line-ending-aware semantic parsing, Python 3.11, `pyproject.toml + uv.lock` as
  the sole dependency authority.
- **Files/modules:** `.python-version`, `.gitattributes`, `pyproject.toml`,
  `uv.lock`, `05_code/scripts/capture_environment.py`,
  `05_code/scripts/validate_integrity.py`, `05_code/scripts/validate_restructure.py`,
  `05_code/tests/test_integrity.py`, and the read-only BATCH_2A QA records.
- **Inputs:** Git HEAD/index/worktree; BATCH_2A manifest expectations and current
  bytes; selected uv groups/extras; OS and accelerator metadata.
- **Outputs:** passing integrity reports and an environment JSON that records
  exact Python patch, uv version, OS/architecture, accelerator/CUDA stack,
  groups/extras, and `uv.lock` SHA-256.
- **Hashes:** compare worktree SHA-256, Git blob representation, manifest hash,
  semantic record hash, and `uv.lock` SHA-256. Canonicality requires provenance:
  producer/source record, historical Git blob, independent semantic validation,
  and backlink consistency. A green validator alone is insufficient.
- **Tests:** `IntegrityTests.test_import_hashes_match_worktree_and_git_index`,
  `test_semantic_parsers_ignore_line_ending_representation`,
  `test_environment_capture_binds_uv_lock_and_selections`, and
  `test_environment_json_is_canonicalizable`.
- **Acceptance:** both validators pass from `uv run --no-sync`; all three
  mismatches have recorded diagnoses; clean replay uses
  `uv sync --locked` with the recorded groups/extras.
- **Owner Gate:** G0 approves the migration evidence; a changed canonical hash or
  provenance interpretation requires a new decision record.
- **Budget/stop:** local CPU only; stop on unresolved producer provenance,
  ambiguous canonical bytes, dependency drift, or a non-Python-3.11 runtime.
- **Rollback:** revert only F0 implementation files to the pre-task commit; never
  rewrite or delete QA provenance. Restore a prior lock only from Git.
- **Scientific validity risk:** blessing current bytes merely because they parse
  would erase evidence of source drift.
- **Dependencies:** none.

### Task F0.2 - Consolidate active documentation without deleting evidence

- **Goal:** provide one small, complete active documentation set for IS1 V0.1.
- **Execution model:** GPT-5.6 Sol High.
- **Objective:** semantic-merge the migration overlay; use active identity IS1
  Research V0.1; preserve Paper D and historical `Paper E` provenance; deprecate
  rather than delete conflicting active documents until exact Owner approval.
- **Contracts:** active docs are `README.md`, `AGENTS.md`, `PLAN.md`,
  `FULL_RESEARCH_TRACK_PLAN.md`, `LOCAL_RESEARCH_HARNESS_BUILD_PLAN.md`, and the
  three governance runbooks. PLAN hierarchy remains Phase -> Task only.
- **Files/modules:** those active docs, `CLAUDE.md`, track READMEs, literature
  README, `.agents/skills/`, `.codex/config.toml.example`, manifest template, and
  `00_governance/config/project.yaml`.
- **Inputs:** current repo, migration overlay, implemented symbols/tests, Owner
  decisions in the task record.
- **Outputs:** coherent active docs, exact cleanup-candidate list, backlinks to
  replacements, and no modification to historical QA/provenance.
- **Hashes:** record source overlay commit `f85404a9c00da8d3192142528b85f8d4048e2b3e`
  and final Git commit; preserve literature/PDF/digest hashes unchanged.
- **Tests:** active-name/conflict `rg`, Markdown link resolution, manifest-template
  schema lint, and `git diff --check`.
- **Acceptance:** no active instruction retains the four-arm/both-metrics win
  rule, direct confirmation access, requirements-as-authority, remote dashboard,
  or MLflow-as-truth semantics. Historical evidence may retain old wording.
- **Owner Gate:** G0; deletion of any duplicate/obsolete path requires a separate
  exact path approval even when replacement backlinks exist.
- **Budget/stop:** documentation/offline only; stop if an apparent conflict is
  embedded in frozen provenance rather than an active instruction.
- **Rollback:** restore active docs from the pre-migration commit; do not touch
  historical artifacts.
- **Scientific validity risk:** changing historical wording would create false
  provenance; leaving conflicting active rules would permit protocol drift.
- **Dependencies:** F0.1 diagnosis informs hash language but does not require
  changing historical bytes.

### Task F0.3 - Verify governance dashboard, ledgers, and MLflow mirror

- **Goal:** make local Owner observability useful without widening write or data access.
- **Execution model:** GPT-5.6 Sol High; local CPU services only.
- **Objective:** provide a professional same-origin console for the canonical
  plan, Phase/Task evidence state, process, flow, harness rules, tools, typed
  Owner decisions, allowlisted PDF access receipts, and rebuildable MLflow
  projection with an enforced read-only browser viewer.
- **Contracts:** `DecisionLedger`, dashboard Host/Origin/session/CSRF rules,
  backend OS actor identity, immutable approval records, `PDFViewer` allowlist
  and local receipt chain, `MLflowMirror` explicit-file projection.
- **Files/modules:** `05_code/src/myis_research/ledger.py`, `dashboard/*`,
  `mlflow_mirror.py`, `06_forntend/dashboard/`, `06_forntend/mlflow/`,
  `00_governance/approvals/`, PDF allowlist template, MLflow configs, and tests.
- **Inputs:** metadata/digests and explicit allowlisted files only; never qrels,
  membership, confirmation outcomes, credentials, protected per-query artifacts,
  or unapproved PDF bytes.
- **Outputs:** loopback Owner console, deterministic Phase/Task snapshot,
  immutable decisions, local tamper-evident PDF receipts, optional Git-tracked
  chain-head anchors, MLflow receipts/rebuild plan, and a read-only MLflow UI.
- **Hashes:** each decision records evidence-manifest hashes, Git commit, and
  prior-record hash; each PDF receipt records file hash and prior-record hash;
  mirror receipts bind canonical source and artifact hashes.
- **Tests:** `DashboardSecurityTests`, `DecisionLedgerTests`, `PDFViewerTests`,
  and `MLflowMirrorTests`, including protected-data negative tests.
- **Acceptance:** services bind only `127.0.0.1`, fail closed on remote/multi-user
  conditions, use `no-store`, expose no generic mutation route, distinguish task
  evidence from gate authorization, never overwrite decisions/receipts, and
  prevent the MLflow browser process from mutating the canonical store.
- **Owner Gate:** G0 for code; every actual canonical decision write requires
  preview plus explicit confirmation. PDF allowlist/anchor writes require their
  named Owner decisions.
- **Budget/stop:** local CPU and disk only; stop on actor ambiguity, ACL/path
  escape, chain corruption, remote bind, or missing canonical source hash.
- **Rollback:** stop service, quarantine a corrupt local receipt/MLflow store,
  verify canonical Git artifacts, then replay. Never auto-repair canonical data.
- **Scientific validity risk:** a writable dashboard or mirrored protected data
  would create an untracked path to alter or learn the experiment.
- **Dependencies:** F0.1, F0.2.

## Phase F1 - Reproduce DAPFAM baselines

### Task F1.1 - Reproduce BM25, dense, and Hybrid RRF

- **Goal:** establish one protocol-matched primary baseline for Gate C and the
  no-rerank baseline used after pool freeze for Gate R.
- **Execution model:** GPT-5.6 Sol High for implementation; deterministic local
  CPU for BM25/cached evaluation; any new embedding/API/GPU work requires G1 plus
  a scoped compute approval.
- **Objective:** rerun DAPFAM BM25 passage, dense passage, and Hybrid RRF K=30
  under identical corpus, query IDs, family mapping, evaluator, field view, and
  top-100 protocol. Published scores are tolerance targets only.
- **Contracts:** family-level aggregation, deterministic tie-break
  `score desc -> best component rank asc -> family_id asc`, manifest v3,
  `RuntimeEnvironment`, `StatisticsContract`, and explicit primary baseline ID.
- **Files/modules:** baseline adapters/configs under `03_experiments/config/`,
  `harness/candidate_ledger.py`, `harness/metrics.py`, `harness/statistics.py`,
  `harness/manifest.py`, reproduction scripts/tests to be added under
  `05_code/scripts/` and `05_code/tests/`.
- **Inputs:** frozen DAPFAM corpus/query/qrels/family/evaluator snapshots and
  split commitments authorized for reproduction.
- **Outputs:** immutable BM25/dense/Hybrid bundles; ALL/IN/OUT Recall@100 and
  nDCG@100; per-route ranks; a single preregistered Gate C baseline manifest.
- **Hashes:** corpus, dataset manifest, family map, parser, query view, query IDs,
  qrels snapshot, evaluator, config, model/revision, index, environment, and every
  output artifact.
- **Tests:** metric fixtures, family dedup/tie-break replay, index determinism,
  manifest v3 validation, and protocol equality across baselines.
- **Acceptance:** local scores are reproducible within a preregistered tolerance;
  differences from published values are diagnosed rather than hidden; all
  baselines can be rerun on identical future confirmation IDs externally.
- **Owner Gate:** G1 Reproduction.
- **Budget/stop:** preregister wall-clock/storage/index budget; stop on corpus,
  field, family, evaluator, or query-population mismatch.
- **Rollback:** remove only unvalidated runtime outputs through approved cleanup;
  retain failure manifests and restore previous config/code commit.
- **Scientific validity risk:** choosing the strongest baseline after seeing Gate
  C results would create comparator selection bias.
- **Dependencies:** F0 complete.

## Phase C0 - Exposure, split, oracle, and power audit

### Task C0.1 - Freeze design inputs and quantify exposure headroom

- **Goal:** decide whether candidate exposure is measurable and whether the
  proposed split is adequately sensitive before optimization.
- **Execution model:** GPT-5.6 Sol High for implementation/analysis; deterministic
  local CPU evaluation.
- **Objective:** audit OUT-positive availability/count, zero-hit rate,
  Recall@100/200/1000, judged-query coverage, and oracle ranking inside baseline
  pools; run prospective OUT-primary MDE/power analysis before freezing 60/20/20.
- **Contracts:** `deterministic_stratified_split`, unique query IDs, frozen seed,
  membership hashes, qrels snapshot hashes, descriptive-vs-confirmation labels,
  and no optimizer access to confirmation membership.
- **Files/modules:** `harness/benchmark.py`, new split/power audit module and CLI,
  `03_experiments/config/` split protocol, and focused tests.
- **Inputs:** F1 baseline per-query development outputs and authorized
  adaptation/selection qrels only.
- **Outputs:** power/MDE report, proposed final split ratio, frozen commitments,
  exposure/oracle diagnostics, and no-headroom decision if applicable.
- **Hashes:** seed, stratum definition, membership commitments, qrels snapshot,
  baseline pool and analysis-plan hashes.
- **Tests:** duplicate-ID rejection, deterministic split replay, confirmation
  denial/network re-download denial, and synthetic power-analysis fixtures.
- **Acceptance:** Owner can see exact counts and sensitivity trade-offs; MDE is
  reported as design sensitivity only; the split is not frozen merely because
  60/20/20 was historical code default.
- **Owner Gate:** G2 opens development; G3 later freezes the chosen split/pool.
- **Budget/stop:** offline statistics only; stop if OUT positives are too sparse,
  confirmation isolation cannot be demonstrated, or baseline headroom is absent.
- **Rollback:** retain audit report, revise split proposal with a new hash, and
  never edit a previously frozen membership record.
- **Scientific validity risk:** low OUT-positive counts can make a nominal split
  unstable or underpowered; prior DAPFAM exposure prevents a globally untouched
  claim.
- **Dependencies:** F1.

## Phase C1 - Manual CrossRoute routes and views

### Task C1.1 - Evaluate grounded manual route ablations

- **Goal:** test whether complementary routes recover relevant OUT families under
  a fixed final candidate budget.
- **Execution model:** GPT-5.6 Sol High for implementation; deterministic local
  retrieval; support extraction may use Luna only outside main comparisons and
  only when approved.
- **Objective:** compare manual BM25/dense TAC, claim lexical/dense, grounded
  mechanism/function/structure/process/application views, and eligible
  citation/metadata routes.
- **Contracts:** `QueryViewPolicy`, `RoutePolicy`, `CandidateBudget`,
  `FusionContract`, `HarnessPolicy`, family-level candidate ledger, source-span
  grounding, quarantine of ungrounded terms, fixed final K, and fusion provenance.
- **Files/modules:** `harness/policy.py`, `harness/candidate_ledger.py`, retrieval
  adapters/configs, route contribution reports, and tests.
- **Inputs:** C0-authorized adaptation/selection IDs and qrels, F1 indexes/models,
  source patent title/abstract/claims only.
- **Outputs:** byte-stable family ledgers, overlap matrix, unique relevant-family
  recovery, route latency/cost, and strict selection decisions.
- **Hashes:** policy, query-view schema, every view/source-span mapping, route
  config/index/model, ledger, final pool, and selected-candidate record.
- **Tests:** `test_grounded_policy_and_candidate_ledger_are_deterministic`,
  route quota/depth/budget rejection, ungrounded quarantine, leakage scan,
  batch-order invariance, and deterministic tie-breaking.
- **Acceptance:** selection accepts only `OUT Recall@100(candidate) > current
  best`; ties reject. Route gain must reflect new relevant families after family
  dedup, not publication duplicates or leakage.
- **Owner Gate:** G2 Track C development.
- **Budget/stop:** fixed candidate, route-depth, time, storage, and trial budgets;
  stop on leakage, no unique recovery, or repeated flat selection score.
- **Rollback:** reject candidate and restore incumbent policy hash; retain
  negative result and failure taxonomy.
- **Scientific validity risk:** qrels-informed view construction or changing final
  K would confound route complementarity with tuning privilege.
- **Dependencies:** C0.

## Phase C2 - Bounded policy optimization

### Task C2.1 - Optimize only the typed CrossRoute policy surface

- **Goal:** determine whether bounded policy optimization improves Gate C beyond
  the strongest manual policy.
- **Execution model:** measured optimizer starts GPT-5.6 Sol Medium; escalate to
  Sol High only after documented qrels-blind calibration failure. Implementation
  remains GPT-5.6 Sol High.
- **Objective:** optimize declared view, route, depth/quota, fusion, budget
  allocation, and stopping fields without executable-tool expansion.
- **Contracts:** strict `SelectionDecision`; `ProtectedSurfaceContract`;
  `ProviderExecution`; `ReplicationContract`; patch allowlist/denylist; no silent
  fallback; adaptation/selection qrels only.
- **Files/modules:** `.agents/skills/myis-run-harnessopt/`, `harness/policy.py`,
  `protection.py`, `providers.py`, optimizer adapter/config, manifest v3, tests.
- **Inputs:** frozen C1 incumbent, declared module pool, authorized train/selection
  labels, qrels-blind calibration fixtures.
- **Outputs:** every trial manifest, accepted/rejected decision, all repeat
  outcomes, cost/latency, failure class, and one selected policy hash.
- **Hashes:** initial skill/policy, editable/protected surfaces, model/provider/
  effort, tool pool, repeat/order, prompt, config, evaluator, split, trial outputs.
- **Tests:** `test_strict_selection_rejects_ties`,
  `test_provider_fallback_and_a2_a3_drift_are_rejected`,
  `test_patch_and_aggregate_boundaries_fail_closed`, budget and batch-order tests.
- **Acceptance:** no candidate is accepted on a tie or secondary metric; every
  measured call records requested/resolved identity and cost; no confirmation
  path or network re-download is available.
- **Owner Gate:** G2 plus G5 if optimizer model calls are used.
- **Budget/stop:** preregister trials, tokens, wall time, cost, retries, and
  no-gain patience; stop at first exceeded ceiling, invalid patch, or flat surface.
- **Rollback:** restore incumbent policy/skill hashes; retain all trial manifests
  and negative outcomes.
- **Scientific validity risk:** adaptive over-search on selection qrels and model
  drift can exaggerate apparent gain.
- **Dependencies:** C1 must show a valid responsive surface; otherwise C2 is
  skipped and the negative boundary is reported.

## Phase CF - Freeze candidate pool

### Task CF.1 - Commit the selected Gate C protocol and pool

- **Goal:** create the immutable causal boundary between exposure and ranking.
- **Execution model:** GPT-5.6 Sol High; deterministic local freeze tooling.
- **Objective:** freeze code, policy, query views, routes, indexes, model identity,
  environment, candidate ledger, candidate pool, comparator, split commitments,
  and analysis plan.
- **Contracts:** `freeze_candidate_pool`, `CandidatePoolReference`, immutable
  write-once artifacts, final K/query count, exact pool SHA-256.
- **Files/modules:** `harness/candidate_ledger.py`, manifest/validation modules,
  `03_experiments/` freeze config, `04_outputs/` Owner evidence package.
- **Inputs:** selected C1/C2 valid bundle and C0 split commitments.
- **Outputs:** frozen pool artifact/hash, Gate C preregistration, R input contract,
  and Owner preview.
- **Hashes:** every input artifact plus canonical pool/ledger/policy/environment/
  Git commit hashes.
- **Tests:** replay freeze byte stability, overwrite rejection, pool dimension
  checks, candidate membership equality, and artifact tamper rejection.
- **Acceptance:** a fresh replay produces the same pool hash; no R component can
  expand or substitute candidates; Owner approves exact evidence hashes.
- **Owner Gate:** G3 Track C Freeze.
- **Budget/stop:** no new optimization; stop on dirty/unknown code identity,
  missing artifact hash, or replay mismatch.
- **Rollback:** do not edit a freeze record; create a new superseding proposal
  before confirmation and require a new G3 decision.
- **Scientific validity risk:** freezing a pool with hidden membership drift
  invalidates all downstream ranking attribution.
- **Dependencies:** C1 and optional C2.

## Phase R0 - Ranking headroom

### Task R0.1 - Measure reachable ranking performance on the frozen pool

- **Goal:** establish whether reranking can improve order without changing exposure.
- **Execution model:** GPT-5.6 Sol High; deterministic local evaluation.
- **Objective:** compute no-rerank OUT nDCG@100, oracle/reachable nDCG, coverage,
  promotions/demotions, and evidence-field availability on the CF pool.
- **Contracts:** `FrozenPoolRankingComparison` pool-hash equality; family-level
  metrics; no candidate addition/removal; deterministic ordering.
- **Files/modules:** `harness/benchmark.py`, `harness/metrics.py`, ranking audit
  script/config and tests.
- **Inputs:** exact CF pool and authorized development/selection qrels.
- **Outputs:** headroom report, frozen no-rerank primary baseline ID, and proceed/
  stop recommendation.
- **Hashes:** pool, ranking input order, evaluator, qrels snapshot, baseline
  scores, analysis plan.
- **Tests:** pool-hash mismatch rejection, metric fixtures, tie-breaking, and
  candidate membership invariant.
- **Acceptance:** every ranking comparison binds the identical pool hash; enough
  oracle headroom exists to justify R1 or the track stops with a transparent
  negative result.
- **Owner Gate:** G4 Track R development.
- **Budget/stop:** local CPU; stop on pool drift, missing evidence fields, or no
  plausible headroom.
- **Rollback:** retain R0 diagnosis and do not modify CF.
- **Scientific validity risk:** oracle analysis on confirmation labels is
  forbidden; candidate changes would collapse C/R decomposition.
- **Dependencies:** CF.

## Phase R1 - Claim/passage-aware ranking

### Task R1.1 - Develop reranking on the identical frozen pool

- **Goal:** improve OUT nDCG@100 while preserving CF exposure exactly.
- **Execution model:** GPT-5.6 Sol High implementation; measured model/provider
  only under G4 and compute approval; PageIndex only as an optional routed pilot.
- **Objective:** compare no-rerank, protocol-matched practical reranker,
  passage-aware scoring, and claim-limitation coverage scoring.
- **Contracts:** `FrozenPoolRankingComparison`; same pool hash; one preregistered
  primary no-rerank baseline; strict selection; PageIndex receives only documents
  routed by BM25/dense candidate retrieval.
- **Files/modules:** ranking/evidence adapters, `harness/benchmark.py`, provider and
  manifest contracts, R configs/tests.
- **Inputs:** CF pool, source claims/passages, authorized development/selection
  qrels, fixed evaluator.
- **Outputs:** ranked family lists, paired per-query development deltas, evidence
  diagnostics, controls, cost/latency, selected R policy.
- **Hashes:** pool, model/revision/provider/effort, prompt, feature schema,
  passage index, PageIndex pilot config if any, ranking outputs.
- **Tests:** candidate-set equality, provider fallback denial, batch-order and
  tie-breaking tests, degraded/scrambled control, PageIndex first-stage bypass
  rejection.
- **Acceptance:** selection accepts only strictly higher OUT nDCG@100; candidate
  membership and pool hash never change; PageIndex is separately reported and
  cannot become the corpus retriever implicitly.
- **Owner Gate:** G4 and separate paid/API/GPU approval as applicable.
- **Budget/stop:** fixed candidates/query, tokens, model calls, latency, cost,
  retries, and trials; stop when controls fail or headroom is exhausted.
- **Rollback:** restore no-rerank/previous incumbent ranking config and retain
  negative/control evidence.
- **Scientific validity risk:** reranker selection on secondary evidence metrics
  or pool mutation would overstate ranking causality.
- **Dependencies:** R0.

## Phase R2 - Evidence package

### Task R2.1 - Produce traceable claim/passage evidence without legal conclusions

- **Goal:** attach publication-level evidence to ranked families for inspection
  and paper examples.
- **Execution model:** GPT-5.6 Sol High implementation; deterministic locator
  first; optional model interpretation only under G4 with exact citations.
- **Objective:** emit family ID, publication ID, route/rank provenance, claim
  limitation, verbatim span, page/section/offset, support status, confidence, and
  unresolved gaps.
- **Contracts:** evidence cannot change qrels, ranking relevance, or pool;
  verbatim text and interpretation remain separate; legal claims are forbidden.
- **Files/modules:** evidence schema/locator/validator, R2 configs, claim-evidence
  renderer, tests, and validated output package.
- **Inputs:** selected R1 ranking, source publications already approved for use,
  and route provenance.
- **Outputs:** immutable evidence records, coverage/error taxonomy, representative
  recovery/failure cases, claim-evidence mapping.
- **Hashes:** source publication, passage index, ranking, evidence schema,
  evidence records, renderer, and final report.
- **Tests:** exact-offset replay, source-hash drift, unsupported conclusion,
  protected-data leakage, and deterministic report projection.
- **Acceptance:** every material statement links to an exact source location;
  missing evidence causes abstention/unclear status; no novelty/FTO verdict appears.
- **Owner Gate:** G4 for development; PDF source access requires allowlist and
  local receipt; publication use waits for G8.
- **Budget/stop:** stop on source/license/privacy ambiguity, hash drift, or
  unsupported interpretation.
- **Rollback:** discard only unvalidated derived package; retain canonical source
  and failure audit.
- **Scientific validity risk:** fluent summaries can conceal incomplete evidence
  or transform benchmark relevance into a legal conclusion.
- **Dependencies:** R1; R2 may document a negative R1 result.

## Phase S - Optional A0-A3 HarnessOpt adaptation study

### Task S.1 - Calibrate and freeze the A0-A3 study

- **Goal:** isolate the effect of skill-only versus skill-plus-policy adaptation.
- **Execution model:** implementation GPT-5.6 Sol High; qrels-blind optimizer
  calibration starts Sol Medium and escalates to High only on validity failure.
- **Objective:** preregister A0 frozen baseline, A1 human seed skill, A2 optimized
  skill/frozen harness, and A3 optimized skill plus allowed typed policy.
- **Contracts:** A2/A3 identical model, provider, effort, budget, initial state,
  data access, evaluator, module pool, repeats, and stopping; Luna only support or
  separately labeled cost ablation; no silent fallback.
- **Files/modules:** `myis-run-harnessopt` skill/reference, provider/protection/
  replication contracts, S manifests/configs/tests.
- **Inputs:** qrels-blind fixtures for calibration and frozen adaptation/selection
  surface for the measured study.
- **Outputs:** calibration report, selected model protocol, A0-A3 preregistration,
  matched repeat schedule.
- **Hashes:** model/provider/effort, initial skill/harness, editable/protected
  paths, budgets, prompts, tools, data commitments, repeats/order.
- **Tests:** A2/A3 drift rejection, patch denylist, fallback rejection, and all
  repeats reported.
- **Acceptance:** the lowest approved Sol effort passing qrels-blind validity is
  frozen identically for A2/A3; third-party provider remains development-only.
- **Owner Gate:** G5 HarnessOpt.
- **Budget/stop:** explicit calibration attempts and measured budgets; stop if a
  matched design cannot be guaranteed.
- **Rollback:** do not run S; C/R publication path remains intact.
- **Scientific validity risk:** changing optimizer identity between arms would
  confound editable surface with model capability.
- **Dependencies:** C1 responsive surface; S is optional and independent of R.

### Task S.2 - Run and report A0-A3 under matched controls

- **Goal:** estimate adaptation-surface quality, cost, stability, and failure rate.
- **Execution model:** frozen model/provider/effort from S.1.
- **Objective:** execute all preregistered repeats, apply strict selection, and
  report every arm/repeat without best-repeat cherry-picking.
- **Contracts:** `ReplicationContract`, `ProviderExecution`, strict primary
  utility/selection score, protected-surface scanner, complete cost lineage.
- **Files/modules:** optimizer runner, S result/statistics reports, manifest v3,
  MLflow scientific mirror projection.
- **Inputs:** S.1 frozen protocol and authorized adaptation/selection data.
- **Outputs:** per-repeat valid bundles, aggregate quality/cost/stability, failure
  taxonomy, separately labeled Luna cost ablation if approved.
- **Hashes:** every run input/output, repeat identity/order, manifest, and mirror
  receipt.
- **Tests:** replay/comparability checks, batch-order drift, protected leakage,
  provider fallback, and mirror failure isolation.
- **Acceptance:** all repeats and invalid runs appear; A2/A3 differ only in the
  declared policy surface; results are optional methods evidence.
- **Owner Gate:** G5.
- **Budget/stop:** preregistered total calls/tokens/time/cost; stop at ceiling or
  repeated diagnosed invalidity.
- **Rollback:** retain results and revert selected skill/policy to their frozen
  starting hashes.
- **Scientific validity risk:** adaptive utility construction or omitted failed
  repeats would bias the methods conclusion.
- **Dependencies:** S.1.

## Phase Q - Prospective external confirmation

### Task Q.1 - Emit a frozen request and validate aggregate-only results

- **Goal:** evaluate Gate C and Gate R once without revealing confirmation data
  to the agent workspace.
- **Execution model:** Owner-run external evaluator; repository-side validation
  uses deterministic local Python. No research agent executes the evaluator.
- **Objective:** emit one hash-only `ConfirmationRequest`; the external one-command
  evaluator runs all preregistered baselines/candidates on identical confirmation
  IDs and returns only `ConfirmationAggregatePackage`.
- **Contracts:** no membership/qrels/protected payload/per-query outcome enters
  the repo; aggregate includes exact n, point estimates, paired deltas, 95% paired
  bootstrap CIs, rank-biserial effects, W/L/T, comparison-family metadata, and
  input/output hashes. Gate C/R remain independent.
- **Files/modules:** `confirmation.py`, request/aggregate schemas, protection
  checks, Q output package, and external evaluator documentation only (external
  evaluator code/data remain outside this repo).
- **Inputs:** frozen submission/config/protocol hashes and Owner authorization.
- **Outputs:** immutable request and validated aggregate package. A full-1,247
  result is labeled descriptive rather than unseen confirmation if DAPFAM qrels
  informed development.
- **Hashes:** Git commit, submission/config/protocol, request, evaluator input/
  output commitments, and aggregate package.
- **Tests:** `test_confirmation_request_and_aggregate_are_hash_only`, aggregate
  schema/classification checks, protected key leakage negatives, request mismatch,
  and replay validation.
- **Acceptance:** primary delta > 0 yields observed improvement; CI lower > 0 is
  statistically supported superiority; positive delta with CI crossing zero is
  higher measured score with uncertain superiority; delta <= 0 is no observed
  improvement. MDE is not used as a pass threshold.
- **Owner Gate:** G6 Confirmation, previewed and recorded in the canonical ledger.
- **Budget/stop:** exactly the preregistered external run; stop on hash mismatch,
  schema violation, unauthorized additional comparison, or protected-data return.
- **Rollback:** aggregate package is never edited; correction is a superseding
  external package and Owner decision. No tuning follows confirmation.
- **Scientific validity risk:** any confirmation feedback entering selection or
  rerunning until positive destroys prospective isolation.
- **Dependencies:** CF for Gate C submission; R1/R2 freeze for Gate R. Either gate
  may be confirmed/reported independently.

## Phase P - Publication package

### Task P.1 - Build the falsifiable claim-evidence and reproducibility package

- **Goal:** publish what the protocol measured, including transparent negative or
  uncertain results.
- **Execution model:** GPT-5.6 Sol High for implementation/drafting; deterministic
  report generators read only validated manifests and aggregate confirmation.
- **Objective:** produce tables/figures for baseline reproduction, route-level
  recovery, exposure/ranking decomposition, frozen-pool ranking, evidence quality,
  paired uncertainty, cost, optional S study, and limitations.
- **Contracts:** claim language follows confirmation classification; Holm applies
  only to preregistered additional comparisons; no logs/MLflow UI become numeric
  truth; DAPFAM is not legal truth.
- **Files/modules:** publication generators under `05_code/`, validated outputs
  under `04_outputs/`, manuscript/figure configs, claim-evidence audit.
- **Inputs:** validated canonical manifests/artifacts, aggregate confirmation
  package, historical Paper D boundary evidence, literature provenance.
- **Outputs:** submission candidate, artifact inventory, reproducibility commands,
  limitations and negative-result narrative.
- **Hashes:** every table/figure input manifest, generator Git commit, output
  artifact, environment, and approval record.
- **Tests:** deterministic table/figure regeneration, claim-to-artifact link
  audit, active-name lint, protected-data scan, and clean replay.
- **Acceptance:** positive strategy arises from a falsifiable contribution,
  route-level recovery, exposure/ranking decomposition, or transparent negative
  boundary. No metric/end point is changed to manufacture a win.
- **Owner Gate:** G8 Publication.
- **Budget/stop:** local generation/review budget; stop on unsupported claim,
  missing provenance, unresolved comparison multiplicity, or protected leakage.
- **Rollback:** withdraw or supersede the publication package; canonical evidence
  remains immutable.
- **Scientific validity risk:** selective reporting, overclaiming uncertain CIs,
  and collapsing C/R into one success statement.
- **Dependencies:** F1 and the completed phases actually claimed; Q is required
  only for confirmatory language, not for a clearly labeled descriptive or
  negative methods report.
