# IS1 Research V0.1 Agent Contract

This contract applies equally to Codex, Claude, local research agents, and any
future MCP or Brain adapter operating in this repository.

## Read order

1. `PLAN.md` - canonical Phase -> Task execution authority.
2. `FULL_RESEARCH_TRACK_PLAN.md` - scientific protocol and claim boundaries.
3. `LOCAL_RESEARCH_HARNESS_BUILD_PLAN.md` - implementation contracts.
4. `00_governance/OWNER_GATES.md` - authority and approval boundaries.
5. `00_governance/OPERATIONS.md` - exact local commands and recovery steps.
6. The README, source, tests, evidence, and track files owned by the active task.

## Identity and versioning

- The active program is `IS1 Research V0.1`, machine ID `is1-research`,
  research version `0.1`.
- `Paper E` is a historical or legacy alias only. Preserve it in frozen
  evidence, provenance, and citations; do not use it as the active program name.
- V0.2 and V0.3 are additive revisions inside the same protocol architecture.
  A change to the protocol family, protected-data boundary, causal phase order,
  or evaluation architecture requires V1.0 and an Owner decision.
- Bind measured manifests and confirmation requests through
  `ResearchVersionSpec`; package-release versions remain independent.

## Authority and safety

- The Owner is the final decision maker. Silence is not approval.
- Stop on conflicting instructions, unresolved drift, ambiguous scope, or a
  failed hash/provenance check that can change scientific interpretation.
- Preserve user work and historical evidence. Archive or deprecate conflicting
  active docs; delete only exact Owner-approved paths.
- Never access paid APIs, GPU/Vast.ai/vLLM jobs, protected confirmation data, or
  external publication surfaces without the applicable scoped approval.
- Do not modify the App or Brain repository unless the task explicitly names it.
- Git and validated immutable artifacts are canonical. MLflow and Brain are
  projections and pointers, never alternate paper truth.

## Scientific invariants

- Paper D is a frozen historical boundary. Do not rerun or rewrite it by
  implication.
- DAPFAM is a family-level retrieval benchmark, not novelty, infringement, FTO,
  validity, or other legal truth. Report ALL, IN, and OUT where available.
- IS1 follows `Candidate Exposure -> Freeze Pool -> Ranking/Evidence`.
- Gate C primary metric is `OUT Recall@100`.
- Gate R primary metric is `OUT nDCG@100` on the identical frozen candidate pool.
- Gate C and Gate R are independent claims. Failure of one does not erase a
  positive result in the other.
- Track S A0-A3 is an optional adaptation-surface study and is not on the C/R
  critical path.
- Resolve the primary comparator from one preregistered, protocol-matched local
  baseline manifest. Published DAPFAM values are reproduction references only.
- During development/selection, accept a candidate only when its preregistered
  primary selection score is strictly greater than the incumbent; reject ties.
- On sealed confirmation, `delta > 0` is an observed benchmark improvement.
  Report paired delta, exact `n`, 95% paired-bootstrap CI, rank-biserial effect,
  and win/loss/tie counts. CI lower > 0 supports a stronger superiority claim;
  CI is evidence strength, not a hard gate. MDE is prospective design
  sensitivity, never an observed-result threshold.
- Apply Holm correction only to the preregistered family of additional
  confirmatory comparisons, not the single primary comparison for each gate.

## Data and confirmation boundary

Protected surfaces include qrels, split membership, confirmation IDs/outcomes,
evaluator and statistics code after freeze, corpus membership, parser semantics,
family mapping, baseline results, provenance, approval enforcement, redaction,
and manifest validation.

- Freeze the split seed, membership hashes, qrels snapshot, and OUT-positive
  availability/count before development. Run an OUT-primary MDE/power audit
  before permanently freezing the proposed 60/20/20 ratio.
- Expose only adaptation and selection qrels to an optimizer. Keep confirmation
  split membership, qrels, protected payloads, and per-query outcomes outside
  the agent workspace and prevent network re-download during measured
  optimization.
- Confirmation is an Owner-run, one-command evaluator outside this repository.
  The repo may emit only a hash-only `ConfirmationRequest` and may ingest only a
  schema-validated aggregate `ConfirmationAggregatePackage`.
- Re-run every DAPFAM baseline on the identical confirmation query IDs. A result
  over all 1,247 queries is protocol-matched descriptive benchmarking, not
  unseen confirmation, when DAPFAM qrels informed development.

## Harness rule

The deterministic kernel has authority over probabilistic proposals:

- kernel: schemas, lifecycle, approvals, identity, splits, hashes, budgets,
  family deduplication, tie-breaking, metrics, statistics, manifests, redaction,
  protection checks, and immutable writes;
- policy: grounded query views, allowlisted routes, route depth/quota, fixed
  candidate budgets, fusion, reranking, evidence selection, and bounded stopping.

An LLM output is a proposal until typed validation passes. No silent
model/provider fallback is permitted in measured work.

## Dependency and replay rule

- Python 3.11 is required. `pyproject.toml` plus `uv.lock` is the sole dependency
  authority; exported hashed requirements are interoperability artifacts only.
- Every measured manifest records the exact Python patch, uv version, OS,
  architecture, accelerator/CUDA stack, selected groups/extras, and `uv.lock`
  SHA-256.
- Replay in a clean environment with `uv sync --locked` and the exact recorded
  groups/extras.

## Dashboard, ledgers, and PDF viewer

- The dashboard is read-only for experiment artifacts. It binds only to
  `127.0.0.1`, refuses remote/multi-user operation, validates Host and Origin,
  uses session/CSRF protection, disables CDN/CORS and browser caching, and never
  exposes protected evaluation data.
- Canonical dashboard writes are limited to the typed Owner Gate decision API.
  Each decision is one immutable, hash-chained JSON record under
  `00_governance/approvals/`; corrections are superseding records.
- PDF access receipts are the only second write surface. They are append-only,
  hash-chained records in an ignored local audit root, using backend OS identity.
  The local chain is tamper-evident, not tamper-proof. Git tracks only periodic
  Owner-approved chain-head anchors.
- Stream PDFs only from an approved path/hash allowlist after license/privacy
  approval. Reject traversal, unsafe symlinks, hash drift, and protected data.

## Brain, MCP, Skill, and MLflow

- Brain stores concise human-readable decisions/status/pointers through a
  serial writer; it does not store paper metrics in place of manifests.
- MCP adapters are typed, read-only-first, provenance-bearing, bounded by
  timeout/retry/privacy rules, and cannot decide scientific gates.
- Project skills live under `.agents/skills/`. A skill cannot hide an evaluator,
  qrels, split membership, or benchmark answer.
- MLflow is a local, rebuildable mirror for allowlisted docs, results, metrics,
  rubrics, rules, tools, skills, and environment records. It rejects PDFs,
  credentials, qrels, membership, confirmation outcomes, and per-query protected
  artifacts. Mirror failure cannot invalidate a canonical run bundle.

## Model protocol

- Implementation: GPT-5.6 Sol High.
- Measured optimizer: begin GPT-5.6 Sol Medium; escalate to High only after a
  qrels-blind calibration failure, then freeze model/provider/effort/budget
  identically in A2 and A3.
- Luna is for support tasks or a separately reported cost ablation; do not mix
  it into main A2/A3.
- Third-party providers are development-only by default. Record requested and
  resolved model, provider, effort, fallback state, repeat ID, cost, latency,
  tokens, and endpoint class.
- PageIndex is an optional BM25/dense-routed within-document evidence pilot,
  never an automatic replacement for large-corpus candidate retrieval.

## Required execution loop

1. Inspect Git state, active phase/task, approval record, and latest valid manifest.
2. Validate identity, dependency lock, integrity, protected surfaces, and budget.
3. Reproduce the protocol-matched baseline before proposing a new method.
4. State one falsifiable hypothesis and its exact editable surface.
5. Make the smallest bounded change and run deterministic tests first.
6. Evaluate only on the authorized development/selection surface.
7. Compare paired outputs and classify failures by layer.
8. Keep a candidate only on strict primary-score improvement; otherwise reject.
9. Stop at budget, invalidity, leakage, flat surface, or missing headroom.
10. Freeze code/config/prompt/skill/model/environment/pool hashes before an
    Owner confirmation request.

## Completion

Before reporting completion, list changed files and untouched protected
surfaces; run `validate_restructure.py`, `validate_integrity.py`, the relevant
tests, and `git diff --check`; state the exact environment; separate fixture,
development, descriptive, and confirmation evidence; report blockers without
claiming success from partial runs; and repeat that the system is decision
support, not legal advice.
