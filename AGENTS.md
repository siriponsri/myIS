# myIS Research Agent Contract

This repository is `myIS Research` (`myis-research`), protocol `1.0`, research
version `0.1`. `01_Research` is the active control plane and the only place
where canonical plans, schemas, manifests, receipts, and publication facts are
written.

## Read order

1. Read `HANDOFF.md` for orientation only.
2. Read `PLAN.md`.
3. Read only the files owned by the active task.
4. Read additional control files only when required by the conditional rules below.

`HANDOFF.md` is a concise orientation document, not a canonical source. It cannot override plans, control files, schemas, manifests, receipts, or measured evidence.

### Conditional reads

- Read `control/assets/reusable_assets.yaml` and
  `control/assets/REUSABLE_ASSET_MAP.md` only when discovering, selecting, or
  adapting reusable App assets.
- Read `control/campaigns/scope-autoindex-v1.yaml` before changing or executing
  the active campaign.
- Read `control/execution-envelope.yaml` before starting an experiment,
  measured run, or execution-policy change.
- Read `control/execution-envelope-p2.yaml` and
  `control/budgets/p2-r1-primary-v1.yaml` before changing P2 execution policy
  or preparing a P2 request. The P1 envelope remains hash-bound historical
  authorization and must not be overwritten.
- Read `control/source-of-truth.yaml` before report sync, projection writes,
  publication work, or resolving conflicting facts.
- Read schemas, manifests, receipts, and evidence files only when the active
  task uses or changes them.
- Before writing, verify every canonical file relevant to that specific write.
- Do not re-read an unchanged file repeatedly within the same session.

## Active vocabulary

Use only `P0_FOUNDATION`, `P1_CPU_BASELINE`, `P2_SCOPE_DEVELOPMENT`,
`P3_FINAL`, and `P4_PUBLICATION`. Use arms `R0`, `R0-W`, and `R1`.
`D1_START_CAMPAIGN` is the one-time standing campaign authorization;
`D2_OPEN_FINAL` and `D3_SUBMIT_RELEASE` are the only writable Owner decisions.
Do not add micro-gates. Historical vocabulary remains under `archive/` only.

## Safety boundary

- CPU-only, zero paid API, no GPU, no network model download, and no provider
  fallback through P2 readiness and any approved deterministic R1 run.
- Final split, qrels, membership, query IDs, per-query outcomes, credentials,
  and raw provider payloads stay in the Owner-local protected store.
- Git, MLflow, Dashboard, Brain, Obsidian, and Paper receive only validated
  aggregates, hashes, counts, and pointers.
- Never treat fixture evidence as measured evidence or a dashboard preview as
  authorization. This is decision support, not legal advice.

## P2 lifecycle and freeze barrier

- A P2 request must bind `budget_profile_id` and `budget_profile_sha256`; no
  runtime may infer missing limits from a default.
- One P2 scientific run proceeds through candidate generation, train
  evaluation, deterministic shortlist, immutable shortlist-freeze receipt, and
  at most one selection exposure.
- The shortlist receipt must bind candidate IDs, SCOPE spec hashes,
  compiler/config/retriever/evaluator hashes, campaign revision, and budget
  profile hash before selection can open.
- Baseline reproduction, train evaluation, or freeze validation failure stops
  before selection. After selection exposure, candidate/spec/rule/search
  mutation is forbidden.
- Exact ties are rejected. A budget change after the first measured run needs a
  new campaign revision and cannot reinterpret the old result.

## Engineering rules

- `control/`, schemas, deterministic kernel, manifests, and receipts are
  canonical. MLflow is an additive mirror; Dashboard and Obsidian are
  projections.
- Use the reusable-asset registry before adapting App material. Keep App data
  in place and use pointers.
- Use canonical JSON and SHA-256 commitments. Stable IDs and lexical tie-breaks
  are mandatory for deterministic output.
- One report sync builds one read-model object and passes that object to every
  projection writer. Never copy metric values into manually edited notes.
- Preserve history. Archive before removing. Delete only exact, verified paths.
- Before commit/push run tests, layout, report drift, MLflow doctor, Brain
  literature validation when touched, and `git diff --check`.

## Provider-neutral rules

- Agents may record a sanitized provider label for engineering provenance, but
  may not login, logout, copy credentials, edit keyrings, or switch the active
  provider without an explicit Owner action.
- Provider-specific user configuration is not canonical project authority.
- Any future LLM-in-the-loop measurement must freeze provider/model/revision,
  instructions, hashes, budget, seed, Git commit, and request hash under a
  separate execution contract. Provider switching is not scientific evidence.

## Token-efficient operations

- Search for filenames, symbols, headings, or exact terms before opening files.
- Open only the relevant files and line ranges. Do not read entire large files
  when a focused range is sufficient.
- Do not recursively inspect the whole repository unless the task explicitly
  requires a repository-wide audit.
- For Git, inspect `status --short` or `diff --stat` first, then inspect only
  the relevant file diff.
- Run the smallest relevant test first. Use concise output and short tracebacks
  before running a full test suite.
- Store verbose logs in files. Report only the result summary, failures,
  important counts, and exact log paths.
- Do not print complete datasets, JSONL files, generated artifacts, MLflow
  payloads, or long command outputs into the conversation.
- For PDF and image review, inspect only the required pages or figures.
- Keep visual-review sessions separate from long implementation sessions.
- Carry verified findings between sessions through `HANDOFF.md`, not through
  repeated image inspection.
- When RTK is installed and `rtk --version` succeeds, prefer:
  - `rtk ls`
  - `rtk read`
  - `rtk grep`
  - `rtk git status`
  - `rtk git diff`
  - `rtk git log`
  - `rtk pytest`
  - `rtk ruff check`
- If compact output hides information needed to diagnose a failure, rerun only
  the affected command with narrowly scoped raw output.

## Agent responsibilities

Logical responsibilities are: Kernel, SCOPE/adapter, CPU baseline, Projection,
MLflow, Brain/memory, and Paper. Use actual agents only when a bounded task is
independent. The Owner only decides D2 and D3; routine defaults are encoded in
the campaign file and execution envelope.

## Memory lifecycle

Brain memory is pointer-only and has five kinds: `decision`, `evidence`,
`lesson`, `failed_attempt`, and `active_context`. Every note carries a source
URI, source SHA-256, evidence IDs, creation time, review time, and supersession
pointer. Stale active context is archived; failed attempts remain searchable but
cannot override run facts.

## Closeout

Report the exact phase, task, status, checks, changed files, untouched
protected surfaces, evidence class, blockers, and next automatic action. Do not
claim P1 measured completion unless a protected Owner-local run actually
completed. Keep the next action reversible and CPU-only until D2 is requested.
