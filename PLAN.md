# myIS Research 1.0 Canonical Execution Plan

Status: `F0_STATE_FROM_G0_LEDGER_F1_REPRODUCTION_G1_GATED`
Active identity: `myIS Research` / `myis-research`
Protocol: `1.0`; Track C/S research version: `0.1`
Migration base: `4dd0f4b5698174a128d3d1c4d4efcdee6dd04f4c`

This file is the Phase -> Task execution authority. Completion means satisfying
acceptance criteria, not obtaining a positive result. Owner approval opens only
the named scope. This migration authorizes documentation, configuration, schema,
tests, dashboard, and projection updates only; no experiment, qrels evaluation,
GPU, paid API, or confirmation execution is authorized.

## Phase F0 - Foundation migration

### Task F0.1 - Capture integrity baseline

- **Goal:** Bind the migration to reproducible repository and dependency bytes.
- **Inputs:** Git HEAD/index/worktree, protected-path inventory, Python and uv metadata.
- **Outputs:** Migration base, protected-path comparison, and environment receipt.
- **Tests:** `validate_restructure.py`, `validate_integrity.py`, `uv lock --check`.
- **Acceptance:** Base and lock hashes are recorded; protected drift is zero.
- **Owner Gate:** G0 Migration.
- **Budget/stop:** Local CPU only; stop on unresolved provenance or lock drift.
- **Rollback:** Restore only migration-owned files; preserve evidence and history.
- **Risk:** A green parser without byte provenance could bless silent drift.
- **Evidence:** Git SHA, SHA-256 inventory, validator output.
- **Dependencies:** None.

### Task F0.2 - Migrate active docs and configuration

- **Goal:** Make C/S protocol 1.0 the only active authority.
- **Inputs:** Owner-approved migration plan and the two untracked C/S source plans.
- **Outputs:** Core docs, governance config, track roots, skills, and manuscript skeletons.
- **Tests:** Active-context scan, Markdown links, YAML parse, `git diff --check`.
- **Acceptance:** Active roots use myIS identity and contain no independent ranking/evidence lane.
- **Owner Gate:** G0 Migration.
- **Budget/stop:** Offline edits only; stop if an active edit overlaps frozen evidence.
- **Rollback:** Revert migration-owned paths to the migration base.
- **Risk:** Rewriting historical wording would create false provenance.
- **Evidence:** Changed-file manifest and protected-path zero-diff.
- **Dependencies:** F0.1.

### Task F0.3 - Update read-only projections

- **Goal:** Mirror the C/S plan in dashboard, MLflow, Brain, and Linear.
- **Inputs:** Final PLAN task graph and PLAN SHA-256.
- **Outputs:** Loopback dashboard, additive MLflow config, Brain notes, Linear mapping.
- **Tests:** Dashboard/API/security tests, MLflow doctor, projection readback.
- **Acceptance:** Projections match 13 phases and 22 tasks and expose no protected data.
- **Owner Gate:** G0 Migration; each canonical decision write remains separately confirmed.
- **Budget/stop:** Local projections only; stop on remote binding, write ambiguity, or data leak.
- **Rollback:** Rebuild projections from Git; never alter canonical run evidence.
- **Risk:** A projection could be mistaken for scientific or approval truth.
- **Evidence:** API snapshot, mirror receipts, Brain/Linear mappings.
- **Dependencies:** F0.2.

## Phase F1 - Protocol-matched baselines

### Task F1.1 - Reproduce B0, B1, and B2

- **Goal:** Establish preregistered Track C comparators on one protocol.
- **Inputs:** Frozen DAPFAM corpus/query/family/evaluator snapshots and G1 approval.
- **Outputs:** Immutable B0/B1/B2 bundles plus secondary-control bundles.
- **Tests:** Family dedup, tie-break, identity, replay, and evaluator equality tests.
- **Acceptance:** B0 dense, B1 0.7/0.3 hybrid, and B2 naive RRF replay identically.
- **Owner Gate:** G1 Reproduction.
- **Budget/stop:** Run-specific compute budget; stop on field/model/query mismatch.
- **Rollback:** Retain failure manifests; remove only approved invalid runtime outputs.
- **Risk:** Post-result baseline choice would bias the comparator.
- **Evidence:** Manifests, hashes, ALL/IN/OUT aggregate metrics.
- **Dependencies:** F0.

## Phase D0 - Shared split and audit design

### Task D0.1 - Freeze shared membership and dual firewalls

- **Goal:** Commit seed 42 membership 250/125/872 without exposing protected IDs.
- **Inputs:** Protected query inventory, strata, qrels snapshot, Owner-run split process.
- **Outputs:** Hash-only memberships and independent C/S firewall commitments.
- **Tests:** Deterministic replay, duplicate rejection, access and re-download denial.
- **Acceptance:** Exact hashes/counts are frozen; C and S evaluators remain isolated.
- **Owner Gate:** G2 C Design.
- **Budget/stop:** Protected local process only; stop on leakage or count mismatch.
- **Rollback:** Supersede, never edit, a failed commitment.
- **Risk:** Shared IDs could accidentally become shared optimizer state.
- **Evidence:** Hash-only split manifest and protected audit receipt.
- **Dependencies:** F1.

### Task D0.2 - Run C-MARGIN and C-SOEI audits

- **Goal:** Quantify baseline-only noninferiority margins and prespecify interpretive SOEI.
- **Inputs:** B0/B1/B2 outputs on authorized audit surface.
- **Outputs:** Margin audit and Owner decision request.
- **Tests:** Paired bootstrap fixture, constraint `delta_ALL <= delta_IN`, no candidate access.
- **Acceptance:** Owner selects C margins from `{0,0.0025,0.005}` and signs SOEI.
- **Owner Gate:** G2 C Design.
- **Budget/stop:** Baseline-only statistics; stop while either value is TBD_BLOCKING.
- **Rollback:** Retain audit and issue a superseding decision request.
- **Risk:** Candidate-informed margins would invalidate interpretation.
- **Evidence:** `C_MARGIN_VALUES_TBD_BLOCKING`, `C_SOEI_VALUE_TBD_BLOCKING` resolutions.
- **Dependencies:** D0.1.

## Phase C0 - Zero-tuned CrossRoute

### Task C0.1 - Freeze and validate the C0 recipe

- **Goal:** Establish the locked zero-tuned six-route arm.
- **Inputs:** Six atomic routes, quotas 100/100/50/50/50/50, raw 400, RRF 60.
- **Outputs:** C0 policy, top-100 family ledger, route attribution, hashes.
- **Tests:** Grounding, quota, raw/final budget, dedup, tie-break, batch-order tests.
- **Acceptance:** No qrels-informed tuning; exact recipe replays byte-stably.
- **Owner Gate:** G2 C Design.
- **Budget/stop:** Authorized retrieval only; stop on leakage or recipe drift.
- **Rollback:** Restore the frozen C0 policy hash and retain invalid attempt metadata.
- **Risk:** Hidden tuning would erase the zero-vs-tuned decomposition.
- **Evidence:** Policy/ledger/index/model/environment hashes.
- **Dependencies:** D0.

## Phase C1 - Metric-tuned CrossRoute

### Task C1.1 - Search the typed C_TRAIN surface

- **Goal:** Find strict OUT Recall@100 improvements over C0 without changing frozen semantics.
- **Inputs:** C0, C_TRAIN, and typed route/fusion/RRF/pool/rerank fields.
- **Outputs:** At most 100 valid trial records and five Pareto finalists.
- **Tests:** Patch allow/deny, budget, tie rejection, protected-data denial.
- **Acceptance:** Prompts/views/encoder/reranker instructions stay frozen; ties reject.
- **Owner Gate:** G2 C Design.
- **Budget/stop:** 100 valid configurations; stop on leakage, flat surface, or budget.
- **Rollback:** Restore incumbent C0/C1 hash; retain all rejected trials.
- **Risk:** Adaptive over-search could overfit the training surface.
- **Evidence:** Trial manifests, strict selection ledger, Pareto rule.
- **Dependencies:** C0.

### Task C1.2 - Evaluate one selection batch

- **Goal:** Select C1 once from exactly five preregistered finalists.
- **Inputs:** Five frozen finalists and C_SELECTION.
- **Outputs:** One selected C1 policy or transparent no-improvement decision.
- **Tests:** One-batch enforcement, finalist hash equality, strict-score comparison.
- **Acceptance:** Selection is opened once and no finalist is added afterward.
- **Owner Gate:** G2 C Design.
- **Budget/stop:** One selection batch; stop on mismatch or prior access.
- **Rollback:** Reject invalid batch and request a new Owner-governed protocol revision.
- **Risk:** Repeated selection access would turn holdout data into training data.
- **Evidence:** Batch receipt, five hashes, paired selection summary.
- **Dependencies:** C1.1.

## Phase CF - Freeze C arms and harness

### Task CF.1 - Freeze C0, C1, and the C1 harness

- **Goal:** Create the immutable boundary consumed by Track S and Track C diagnostics.
- **Inputs:** Valid C0/C1 bundles, split commitments, environment, comparator plan.
- **Outputs:** Frozen C0/C1 artifacts, C1 harness, pool and diagnostic specification.
- **Tests:** Replay byte stability, overwrite denial, dimension and hash equality.
- **Acceptance:** Every downstream consumer binds the same C1 harness/pool hash.
- **Owner Gate:** G3 C Freeze.
- **Budget/stop:** No new optimization; stop on dirty identity or replay mismatch.
- **Rollback:** Do not overwrite; issue a new freeze candidate after correction.
- **Risk:** Pool substitution would break causal attribution.
- **Evidence:** Immutable manifests and complete hash closure.
- **Dependencies:** C1.2.

## Phase S0 - Track S design and preflight

### Task S0.1 - Lock provider, A0, and A1

- **Goal:** Freeze the common starting state and target execution identity.
- **Inputs:** Frozen C1 harness, A0/A1 artifacts, Qwen target, CoreWeave endpoint.
- **Outputs:** Provider/run specs and identical A1 start hash for A2/A2L/A3.
- **Tests:** Model/provider/seed/tool/schema/context/fallback/parameter checks.
- **Acceptance:** CoreWeave preflight passes or execution stops for Owner decision.
- **Owner Gate:** G4 S Preflight.
- **Budget/stop:** Fixture-only preflight; one identical transport retry only.
- **Rollback:** Retain preflight failure and leave endpoint provisional.
- **Risk:** Provider drift would invalidate the causal arm comparison.
- **Evidence:** `COREWEAVE_FINAL_FREEZE_TBD_BLOCKING` resolution and preflight receipt.
- **Dependencies:** CF.

### Task S0.2 - Run the independent S-MARGIN audit

- **Goal:** Set Track S margins without borrowing Track C tuning evidence.
- **Inputs:** Frozen A1 three-seed baseline-only audit surface.
- **Outputs:** S margin report and Owner decision.
- **Tests:** Seed matching, no arm-candidate access, deterministic statistics.
- **Acceptance:** Owner resolves `S_MARGIN_VALUES_TBD_BLOCKING` before S1.
- **Owner Gate:** G4 S Preflight.
- **Budget/stop:** Baseline-only local audit; stop while margins are unsigned.
- **Rollback:** Preserve report and supersede the decision request.
- **Risk:** Shared or post-treatment margins would contaminate Track S.
- **Evidence:** Three-seed audit hashes and signed margin values.
- **Dependencies:** S0.1.

## Phase S1 - Parallel matched-budget optimization

### Task S1.1 - Execute A2 SkillOpt

- **Goal:** Optimize the skill with the harness frozen.
- **Inputs:** A1, SkillOpt v0.2.0 pinned commit, seeds 11/23/47.
- **Outputs:** Three seed finalists and complete lineage.
- **Tests:** Provider, editable-surface, budget, retry, event-order tests.
- **Acceptance:** 160 rollout cap per seed and USD 20 arm cap are enforced.
- **Owner Gate:** G5 S Run.
- **Budget/stop:** 480 rollouts/arm, USD 20; hard global USD 100.
- **Rollback:** Restore A1 hash and retain every failure/invalid trial.
- **Risk:** Undeclared fallback or cherry-picked repeats invalidates the arm.
- **Evidence:** Trial manifests, costs, latency, token and seed receipts.
- **Dependencies:** S0.

### Task S1.2 - Execute A2L SkillOpt-Lite

- **Goal:** Measure the required lightweight optimizer at matched budget.
- **Inputs:** Same A1, adapted pinned Lite commit, seeds 11/23/47.
- **Outputs:** Three seed finalists and complete lineage.
- **Tests:** Equality of start/model/provider/data/evaluator/budget and retry policy.
- **Acceptance:** A2L is a required 160-rollout/seed arm, not post hoc replacement.
- **Owner Gate:** G5 S Run.
- **Budget/stop:** 480 rollouts/arm, USD 20; A2L-P 400/seed remains future only.
- **Rollback:** Restore A1; retain all attempts.
- **Risk:** Treating Lite as optional would bias the adaptation comparison.
- **Evidence:** Matched-budget proof and immutable trial manifests.
- **Dependencies:** S0; parallel with S1.1 and S1.3.

### Task S1.3 - Execute typed A3 HarnessOpt

- **Goal:** Optimize only the declared typed harness surface at matched budget.
- **Inputs:** Same A1, typed allowlist, seeds 11/23/47.
- **Outputs:** Three seed finalists and policy/skill lineage.
- **Tests:** Protected patch denial, tool allowlist, no executable expansion, drift checks.
- **Acceptance:** Broad HarnessOpt A3X is excluded; all matching constraints hold.
- **Owner Gate:** G5 S Run.
- **Budget/stop:** 480 rollouts/arm, USD 20; hard global USD 100.
- **Rollback:** Restore A1 and incumbent typed policy; retain failures.
- **Risk:** Wider edit authority would confound skill and harness effects.
- **Evidence:** Patch ledger, manifests, costs, provider identity.
- **Dependencies:** S0; parallel with S1.1 and S1.2.

## Phase SF - Freeze Track S finalists

### Task SF.1 - Select once and freeze one artifact per arm

- **Goal:** Submit nine seed finalists once and freeze A2/A2L/A3 artifacts.
- **Inputs:** Three finalists from each required arm.
- **Outputs:** One immutable artifact per arm and comparison preregistration.
- **Tests:** Nine-hash equality, one-batch enforcement, seed completeness.
- **Acceptance:** No test access or post-selection edits occur.
- **Owner Gate:** G5 S Run.
- **Budget/stop:** One selection submission; stop on missing seed or hash drift.
- **Rollback:** Reject the entire invalid submission; never patch a frozen arm.
- **Risk:** Selective seed reporting would inflate apparent optimizer quality.
- **Evidence:** Nine-finalist receipt and three frozen manifests.
- **Dependencies:** S1.1-S1.3.

## Phase CT - External transfer

### Task CT.1 - Run frozen PatenTEB retrieval_OUT transfer

- **Goal:** Test transfer without retuning the C/S artifacts.
- **Inputs:** Frozen artifacts and licensed field-compatible PatenTEB surface.
- **Outputs:** Separately labeled transfer bundle or explicit blocked record.
- **Tests:** License/field compatibility, no-retuning, identity/hash equality.
- **Acceptance:** G7 budget/license approval exists; transfer does not block Q or papers.
- **Owner Gate:** G7 Transfer.
- **Budget/stop:** `CT_BUDGET_LICENSE_TBD_BLOCKING`; stop until resolved.
- **Rollback:** Retain blocked/negative transfer record; do not change primary artifacts.
- **Risk:** Incompatible fields could produce a misleading generalization claim.
- **Evidence:** License decision, run manifest, transfer-only metrics.
- **Dependencies:** CF and SF; independent of Q/PC/PS.

## Phase Q - Joint sealed evaluation

### Task Q.1 - Evaluate the untouched joint test

- **Goal:** Run the Owner-only 872-query confirmation once for C and S.
- **Inputs:** Hash-only requests and frozen baseline/C/S artifacts.
- **Outputs:** Schema-validated aggregate comparison packages.
- **Tests:** Request/package schema, hash closure, exact n, paired statistics.
- **Acceptance:** C primary C1-C0 and S primary A3-A2 are reported without leakage.
- **Owner Gate:** G6 Joint Test.
- **Budget/stop:** Owner-run external command only; stop on any hash mismatch.
- **Rollback:** Reject invalid aggregates; never inspect protected per-query data.
- **Risk:** Joint test reuse or membership exposure destroys confirmation status.
- **Evidence:** Aggregate-only package with CI/effect/W-L-T and hashes.
- **Dependencies:** CF and SF.

### Task Q.2 - Run Track C ranking diagnostic

- **Goal:** Explain reachable ranking headroom without creating an independent gate.
- **Inputs:** Identical frozen C pool, no-rerank order, frozen reranker.
- **Outputs:** Pool hash, oracle/reachable nDCG, promotions/demotions, failure layers.
- **Tests:** Pool equality, no expansion, deterministic diagnostic replay.
- **Acceptance:** Diagnostic is labeled non-gating and cannot adapt the ranking system.
- **Owner Gate:** G6 Joint Test.
- **Budget/stop:** Frozen-pool aggregate diagnostics only.
- **Rollback:** Reject mismatched diagnostics and preserve CF.
- **Risk:** Adaptive reranking would resurrect an unauthorized independent lane.
- **Evidence:** `TrackCRankingDiagnostic` aggregate and pool hash.
- **Dependencies:** Q.1 frozen inputs; no independent gate.

### Task Q.3 - Run C0 full-benchmark descriptive evaluation

- **Goal:** Report C0 on all 1,247 queries after every arm is frozen.
- **Inputs:** Frozen C0 and full DAPFAM evaluator.
- **Outputs:** Clearly labeled descriptive aggregate bundle.
- **Tests:** Frozen-artifact equality and descriptive-label enforcement.
- **Acceptance:** No unseen-confirmation language or tuning feedback is used.
- **Owner Gate:** G6 Joint Test.
- **Budget/stop:** Post-freeze descriptive run only.
- **Rollback:** Withdraw mislabeled output; do not change frozen arms.
- **Risk:** Calling qrels-informed full-data results confirmation overstates evidence.
- **Evidence:** Descriptive manifest and aggregate metrics.
- **Dependencies:** CF, SF, and completion of primary freeze.

## Phase PC - Track C publication

### Task PC.1 - Assemble the Track C manuscript

- **Goal:** Publish the zero-vs-tuned CrossRoute study with bounded claims.
- **Inputs:** Frozen protocol, validated C aggregates, diagnostic, citations.
- **Outputs:** IEEE sections, appendices, integrity and independent-review records.
- **Tests:** Citation/claim audit, anonymity/policy check, result binding, PDF assembly.
- **Acceptance:** Null/boundary outcomes remain; no result is invented or cherry-picked.
- **Owner Gate:** G8 Track C Publication.
- **Budget/stop:** Writing only until validated results exist; result sections stay n/a.
- **Rollback:** Revert prose to last integrity-audited revision.
- **Risk:** Diagnostic or retrieval evidence could be overstated as legal truth.
- **Evidence:** Research -> write -> audit -> review -> revise -> final audit chain.
- **Dependencies:** Q for results; may draft protocol sections earlier.

## Phase PS - Track S publication

### Task PS.1 - Assemble the Track S manuscript

- **Goal:** Publish the matched-budget A2/A2L/A3 causal comparison.
- **Inputs:** Frozen protocol, validated S aggregates, optimization lineage, citations.
- **Outputs:** IEEE sections, appendices, integrity and independent-review records.
- **Tests:** Citation/claim audit, arm matching, result binding, PDF assembly.
- **Acceptance:** Primary, Holm family, and exploratory A3-A2L are distinguished.
- **Owner Gate:** Separate G8 Track S Publication record.
- **Budget/stop:** Writing only until validated results exist; result sections stay n/a.
- **Rollback:** Revert prose to last integrity-audited revision.
- **Risk:** Cost or optimizer lineage omissions would weaken causal interpretation.
- **Evidence:** Research -> write -> audit -> review -> revise -> final audit chain.
- **Dependencies:** Q for results; parallel with PC.
