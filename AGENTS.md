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
- Read `control/execution-envelope-p2.yaml`,
  `control/execution-envelope-p2-v2.yaml`,
  `control/budgets/p2-r1-primary-v1.yaml`,
  `control/budgets/p2-r1-primary-v2.yaml`, and
  `control/runbooks/P2_MEASURED_AUTORESEARCH_V2.md` before changing P2
  execution policy or preparing a P2 request. The P1 and P2-v1 envelopes
  remain hash-bound historical authorization and must not be overwritten.
- Read `control/source-of-truth.yaml` before report sync, projection writes,
  publication work, or resolving conflicting facts.
- Read schemas, manifests, receipts, and evidence files only when the active
  task uses or changes them.
- Before writing, verify every canonical file relevant to that specific write.
- Do not re-read an unchanged file repeatedly within the same session.

## Active vocabulary

Use only `A0_MIGRATION_FOUNDATION`,
`A1_BASELINES_AND_MULTI_ARM_SCREENING`, `A2_PER_ARM_AUTOINDEX`,
`A3_TRANSFER_COMPLEMENTARITY_AND_HARNESSOPT`,
`A4_PRODUCTION_TRANSFER_AND_SELECTION`, `A5_FINAL_CONFIRMATION`, and
`A6_PUBLICATION_AND_RELEASE` for active work. Use arms `ARM-01` through
`ARM-05`. `D1_START_CAMPAIGN` is the one-time standing campaign authorization;
`D2_OPEN_FINAL` and `D3_SUBMIT_RELEASE` are the only writable Owner decisions.
Do not add micro-gates. The P0-P4 phases and `R0`, `R0-W`, and `R1` arms remain
readable only as historical SCOPE/P1/P2 vocabulary and evidence lineage.

## Safety boundary

- CPU-only, zero paid API, no GPU, no network model download, and no provider
  fallback through A0 migration and any separately approved deterministic
  ArmIndex run.
- Final split, qrels, membership, query IDs, per-query outcomes, credentials,
  and raw provider payloads stay in the Owner-local protected store.
- Git, MLflow, Dashboard, Brain, Obsidian, and Paper receive only validated
  aggregates, hashes, counts, and pointers.
- Never treat fixture evidence as measured evidence or a dashboard preview as
  authorization. This is decision support, not legal advice.

## Historical P2 lifecycle and freeze barrier

- These rules remain binding for any historical P2 request or continuation and
  do not authorize new P2 execution.
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
- Before a long-running worker or implementation begins, create a tracked
  runbook plus append-only ledger/checkpoint. Chat state and ignored inbox
  files are launchers only and cannot be the sole execution plan.
- On Windows, never use `os.kill(pid, 0)` as a liveness probe. Long-running
  measured workers use an OS-held advisory lock and process creation identity.

## Provider-neutral rules

- Agents may record a sanitized provider label for engineering provenance, but
  may not login, logout, copy credentials, edit keyrings, or switch the active
  provider without an explicit Owner action.
- Never print, archive, or pass through a complete inherited shell environment.
  Long-running workers, candidate subprocesses, and proposer subprocesses use
  explicit environment allowlists. Credential rotation remains an Owner action.
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

## Session operating modes

Repository work uses three explicit session operating modes: `AP`, `IM`, and
`LO`. A session mode controls how the agent is allowed to act; it does not
replace canonical scientific controls, Owner decisions, execution envelopes,
manifests, receipts, or protected-data rules.

The Owner may activate a mode using either its short name or natural language,
for example:

- `ตอนนี้คุณคือ AP`
- `ทำหน้าที่ Auditor/Planner ตาม AGENTS.md`
- `ตอนนี้ทำ IM ตาม AGENTS.md`
- `Implementation session`
- `/goal อ่าน docs/goal/<file>.md แล้วทำงานตามขั้นตอนทั้งหมด`

Once explicitly declared, the mode remains active for the current session until
the Owner changes it. Never silently switch from AP or IM into LO.

If no mode is explicitly declared:
- planning, review, audit, readiness, architecture-analysis, and publication-
  impact requests default to AP behavior;
- bounded code/engineering requests default to IM behavior;
- measured long-running execution NEVER starts by inference;
- LO measured execution requires an explicit `/goal` launch naming the goal
  document.

Session mode constrains execution behavior only. It never grants authority that
is otherwise closed by the campaign, execution envelope, protected boundary,
budget contract, or Owner-only decisions.

### AP — Auditor and Planner

Preferred profile: MaxPlus GPT-5.6 Sol XHigh.

AP is the evidence auditor, scientific planner, and launch-readiness authority.

AP MUST:
- inspect evidence and repository readiness read-only by default;
- analyze scientific consistency, blockers, budget, TTL, lifecycle safety,
  execution adoption, reproducibility, and publication impact;
- verify that proposed work remains consistent with frozen manifests,
  campaigns, schemas, receipts, and claim boundaries;
- create or materially update the relevant `docs/goal/<task>_goal.md`;
- produce a bounded implementation prompt for IM when engineering work remains;
- audit IM output and remote readiness before a long run;
- activate or refresh the goal only when launch readiness is satisfied;
- audit measured results after LO closeout and prepare the next phase/task goal.

AP MAY:
- make planning/documentation changes needed to keep the active goal correct;
- repair minor planning inconsistencies that do not alter scientific semantics;
- route minor engineering mismatches directly to IM without asking the Owner.

AP MUST NOT:
- start a measured experiment;
- consume paid execution budget merely to validate a plan;
- redesign frozen scientific semantics after measurement exposure;
- bypass Owner-only decisions, protected boundaries, or execution admission.

AP launch-readiness audit is intentionally narrow. Before activating a goal for
LO, verify only the critical axes:

1. Scientific design and frozen manifest are mutually consistent.
2. Runner, lifecycle, safe-return path, and focused tests exist and pass.
3. Protected boundaries remain closed and aggregate-safe.
4. Fresh provider identity, quote, budget, TTL, and watchdog evidence exist.
5. The execution bundle is correctly staged and execution adoption passes.

Do not turn minor engineering mismatches into new governance gates. If an issue
is engineering-only and does not alter scientific semantics, protected
boundaries, Owner decisions, budget authority, or measured interpretation,
return it directly to IM.

AP should finish with exactly one operational disposition:

- `READY_FOR_LO`
- `RETURN_TO_IM`
- `OWNER_DECISION_REQUIRED`
- `BLOCKED_EXTERNAL`

These are routing dispositions, not new scientific gates or Owner decisions.

### IM — Implementation

Preferred profile: MaxPlus GPT-5.6 Sol XHigh.

IM is the bounded engineering and staging session.

IM is launched with a normal prompt, not `/goal`.

IM MUST:
- implement or repair architecture, runners, schemas, lifecycle controls,
  recovery paths, tests, artifact generation, and remote staging requested by
  the AP/Owner prompt;
- preserve frozen scientific semantics and protected boundaries;
- run the smallest focused validation sufficient for the changed surface;
- prepare remote execution without silently starting measured work;
- commit/push when authorized and required by the task;
- leave a concise Luna-ready handoff containing exact commit, staged bundle,
  checks, remaining blockers, and launch command/context.

IM MAY read the active goal document for constraints and context when relevant,
but MUST NOT treat it as an executable `/goal` instruction.

IM MAY immediately fix engineering-only mismatches discovered during its work
without returning to the Owner, provided the fix:
- does not alter frozen scientific design;
- does not increase or reinterpret budget authority;
- does not cross the protected-data boundary;
- does not change provider credentials or Owner-controlled provider state;
- does not open Selection, Final, D2, D3, or another closed phase;
- does not reinterpret measured evidence.

IM MUST stop before measured execution unless the Owner's current prompt
explicitly authorizes that measured execution under an already-valid execution
contract.

A task-scoped explicit Owner authorization may override the default
pre-measurement stop for that specific task only. Never infer such an override
from historical authorization.

### LO — Long Run

Preferred profile when Luna is available:
MaxPlus GPT-5.6 Luna Max.

Use Luna Max by default for measured work with long execution, recovery,
checkpointing, safe return, evaluation, and multi-step closeout.

Luna XHigh may be used when the workload is highly deterministic, the executor
and recovery path are already complete, and the goal primarily requires
execution rather than architectural reasoning.

When uncertain, prefer Luna Max for measured Phase/Task closeout.

LO is launched only with:

`/goal อ่าน docs/goal/<file>.md แล้วทำงานตามขั้นตอนทั้งหมด`

LO MUST:
- treat the referenced goal as its operational execution guide;
- follow its numbered steps, checkpoints, recovery rules, hard stops,
  validation, safe return, artifact creation, commit/push, and terminal report;
- obey canonical campaigns, controls, schemas, manifests, receipts, budget
  profiles, and protected-data rules over the goal document;
- continue through recoverable execution states defined by the goal without
  unnecessary Owner interaction;
- perform measured closeout only within the authority already granted by the
  canonical execution contract.

LO MUST NOT:
- redesign architecture during a measured run;
- silently change scientific semantics, manifests, evaluator behavior,
  selection rules, provider identity, budget authority, or protected boundary;
- invent missing launch authority;
- treat the goal document as a second source of scientific truth.

If LO discovers an architectural or scientific blocker that is not covered by
the goal's bounded recovery instructions, it stops safely and returns the work
to AP/IM with exact evidence.

### Session workflow

The normal execution loop is:

AP audit and plan
-> IM implementation/readiness work using a normal prompt
-> AP implementation + remote-readiness audit
-> AP marks/refines the goal as ACTIVE and returns `READY_FOR_LO`
-> LO executes `/goal` through measured closeout
-> AP audits measured evidence and publication impact
-> AP prepares the next Phase/Task goal

The objective is separation of concerns:

- AP decides whether the work is scientifically and operationally ready.
- IM makes the executor ready.
- LO executes an already-ready measured plan.
- The Owner is involved only where Owner authority is actually required.

## Memory lifecycle

Brain memory is pointer-only and has five kinds: `decision`, `evidence`,
`lesson`, `failed_attempt`, and `active_context`. Every note carries a source
URI, source SHA-256, evidence IDs, creation time, review time, and supersession
pointer. Stale active context is archived; failed attempts remain searchable but
cannot override run facts.

### Brain synchronization and YOLO mode

Any change to this `AGENTS.md` MUST update or create the corresponding
pointer-only Brain note in the same session, with a link back to this file and
the canonical source. If the Brain serial-writer lease cannot be acquired or
validated, stop before commit or push and report the blocker.

Brain YOLO mode is effective immediately for safe pointer-only memory work:
after acquiring the Brain serial-writer lease, an agent may write/update the
required Brain note without another confirmation prompt. YOLO mode is limited
to aggregate-safe status, decisions, lessons, failed-attempt summaries, hashes,
and repository-relative pointers. It never bypasses Owner decisions, the
protected-data boundary, credential rules, deletion approval, serial-writer
lease, measured execution gates, or commit/push authorization.

## Owner-authorized A1 acceleration

For the bounded A1.2 long-run requested on 2026-08-09, the Owner authorizes
additive engineering repair, integration, reuse of valid assets, and direct
measured execution work needed to close A1 within the available seven-day
window. This scoped instruction supersedes preparation-only next-action wording
from earlier v11-v15 handoff projections while the same A1 closeout is active;
it does not reinterpret historical receipts or open A2, HARNESS-DEV, Selection,
Final, D2, or D3.

To reduce delay, do not repeat validation that has an unchanged hash-bound
receipt from the same attempt. Run only the smallest checks needed for the
current transition, plus the required critical checks below. Never reduce or
skip the protected-data boundary, credential redaction, frozen v11-v15
scientific semantics, split/query reservation, whole-workload budget and TTL,
SSH/provider identity, artifact integrity, safe return, or the 25/25 result
requirement. A failure in any critical check remains fail-closed. The active
Owner-approved v17 limits for the current rerun are common screen `$55`, A1
`$60`, campaign `$150`, and TTL `40` hours; v16 values `$27/$32/$150` and v15
values `$18/$23/$100` are historical only and must not be used for current
admission.

Before code or plan edits, apply the local Karpathy guidelines: state
assumptions, choose the smallest direct change, avoid speculative abstraction,
and define a concrete verification command. For plans, architecture, or
publication-impact decisions, use the `grill-with-docs` workflow when the local
skill is available; otherwise record the equivalent questions, answers, ADR,
and glossary in the relevant Thai documentation and link the external source:
`https://github.com/mattpocock/skills/tree/main/skills/engineering/grill-with-docs`.
The Karpathy source is
`https://github.com/multica-ai/andrej-karpathy-skills/blob/main/skills/karpathy-guidelines/SKILL.md`.

## Artifact-first long-run workflow

Owner decision 2026-08-10: long-running work prioritizes implementation and
publication-impact evidence over repetitive documentation. `docs/goal/` holds
short, Thai-first operational goal documents. A goal document is an operational
execution guide, not scientific authority: the active campaign, controls,
schemas, manifests, execution envelopes, budget contracts, and receipts remain
canonical.

Long-running work follows the session separation defined in
`Session operating modes`:

`AP audit/plan -> IM implement/stage -> AP launch-readiness audit -> LO /goal -> AP closeout audit`

* The AP session creates or materially refreshes
  `docs/goal/<phase_or_task>_goal.md` only when a Phase/Task begins, its material
  objective changes, or measured closeout requires a new execution plan. The
  goal names the publication-facing hypothesis, allowed implementation surface,
  required evidence, artifact plan, numbered execution steps, checkpoints,
  recovery rules, hard stops, validation, commit/push requirements, terminal
  reporting, and the smallest useful verification command.

* When engineering work is still required, AP produces a bounded implementation
  prompt for IM. The prompt should identify the exact implementation objective,
  allowed files/surfaces, frozen scientific constraints, focused validation,
  staging requirements, and expected Luna-ready handoff. It must not delegate
  unresolved scientific design or Owner-only decisions to IM.

* IM uses a normal prompt rather than `/goal`. IM reads `PLAN.md`, the active
  goal when relevant for constraints and context, and only the canonical controls
  required by the implementation task. IM builds or repairs architecture,
  runners, schemas, lifecycle controls, recovery, tests, artifact generation,
  execution bundles, and remote staging without waiting for historical-document
  sweeps.

* IM may fix engineering-only mismatches immediately when the fix does not alter
  frozen scientific semantics, protected boundaries, budget authority, provider
  identity, measured interpretation, or Owner-only decisions. Minor engineering
  mismatches do not require a new Owner gate.

* IM runs the smallest focused validation set that covers the changed surface,
  commits/pushes when authorized by the task, and leaves a Luna-ready handoff
  containing the exact revision, staged execution bundle, checks performed,
  remaining blockers, and execution context needed by AP/LO.

* IM stops before measured execution by default. It must not start a measured
  experiment merely because the executor is ready or because a goal document
  exists. Measured execution from IM requires explicit authorization in the
  Owner's current task under an already-valid execution contract.

* After IM completes, AP performs a focused launch-readiness audit rather than
  a broad historical re-audit. The critical launch axes are:

  1. Scientific design and frozen manifests remain mutually consistent.
  2. Runner, lifecycle, safe-return path, and focused tests exist and pass.
  3. The protected boundary remains closed and aggregate-safe.
  4. Fresh provider identity, quote, budget, TTL, and watchdog evidence exist.
  5. The execution bundle is correctly staged and execution adoption passes.

* AP does not create new micro-gates for minor implementation details. An
  engineering-only mismatch returns directly to IM. Escalation to the Owner is
  reserved for an actual change to scientific semantics, protected boundaries,
  budget/authority, provider-controlled state, or an Owner-only decision.

* When launch readiness passes, AP ensures that exactly one active executable
  goal exists for the Phase/Task, that its canonical bindings are current, and
  that no known architecture work remains unresolved. AP then routes the task
  to LO with disposition `READY_FOR_LO`.

* LO is the measured long-run execution session. The Owner launches LO with:

  `/goal อ่าน docs/goal/<file>.md แล้วทำงานตามขั้นตอนทั้งหมด`

* LO treats the referenced goal as its operational execution guide and follows
  its numbered steps through checkpointing, bounded recovery, measured
  execution, safe return, evaluation, artifact generation, validation,
  commit/push, reporting, and terminal closeout.

* LO does not redesign architecture or scientific semantics during measured
  execution. Canonical campaigns, controls, schemas, manifests, receipts,
  execution envelopes, budget contracts, and protected-data rules override the
  goal document whenever there is a conflict. A goal may route to canonical
  controls, but it may not replace them or become a second source of scientific
  metrics.

* If LO encounters a blocker covered by the goal's bounded recovery procedure,
  it executes that recovery and continues. If the blocker requires architectural
  redesign, scientific reinterpretation, new authority, budget expansion,
  provider-state modification, or protected-boundary change, LO stops safely
  and returns exact evidence for AP/IM or Owner review.

* After LO terminates, AP audits the measured closeout before preparing the next
  Phase/Task goal. AP verifies canonical evidence, completeness, reproducibility,
  claim boundaries, publication impact, safe return, provider disposition, and
  the next authorized action. Measured results are not promoted into the next
  scientific decision merely from chat state or an LO narrative.

* Prefer work that improves a journal submission's reproducible evidence:
  complete measured coverage, deterministic provenance, valid aggregate-safe
  artifacts, clearly bounded claims, and reviewer-reproducible analysis. Do not
  optimize wording, documentation volume, or outcomes instead of evidence.

* Keep only these durable documents for a long run: one active goal document,
  the tracked runbook and append-only ledger/checkpoint, canonical
  receipts/manifests, and one generated Phase/Task report. Do not create parallel
  status notes, duplicate metrics, redundant approval documents, or retrospective
  edits unless a canonical fact is wrong.

* Preserve remote attempt roots and allowlisted artifacts until safe return and
  checksum validation pass. Safe local return, hash manifests, aggregate
  receipts, and reproducible analysis are the publication artifact set; raw
  protected inputs and provider payloads remain Owner-local.

* Reducing documentation or separating work across AP, IM, and LO never reduces
  the protected-data boundary, frozen scientific semantics, identity/runtime
  checks, whole-workload budget and TTL checks, execution adoption, watchdog,
  safe return, deterministic replay, or complete-result rule.

* A1 live monitoring prefers authenticated provider CLI. If Vast TFA/API is
  unavailable, the Owner-authorized fallback is aggregate-safe dashboard
  identity/price/TTL evidence plus independently pinned SSH runtime/GPU checks
  and `OWNER_MANUAL_DASHBOARD_DESTROY_READY`. This fallback records provider
  authentication as false and never invokes API destruction. At A1 closeout,
  provider disposition is either validated `REUSE_ELIGIBLE` or actual
  `DESTROYED`; destruction is not required solely to close A1.

* Owner decision 2026-08-11 permits the current Vast instance to remain live
  after A1 safe return and frozen evaluation pass. `REUSE_ELIGIBLE` requires a
  fresh provider identity/status observation, all-fee quote, accrued A1 charge,
  SSH reachability, remaining TTL, watchdog, and management-authority check.
  It does not authorize A2 execution: A2 still requires fresh provider
  admission, fresh execution adoption, and a new isolated remote root. Never
  reuse the A1 adoption receipt or overwrite the A1 attempt root.

* Every active `docs/goal/*_goal.md` intended for LO is an executable long-run
  guide. It must contain numbered steps, checkpoints, recovery, hard stops,
  required artifacts, validation, commit/push, and terminal-report instructions.
  Goal activation means the execution plan is ready for LO; it does not itself
  grant scientific authority, budget authority, access to a closed Phase, or an
  Owner-only decision.

* Session state is not durable project authority. AP findings, IM readiness, LO
  progress, recovery state, and measured closeout must be carried between
  sessions through the repository's canonical artifacts, runbook,
  ledger/checkpoints, receipts, generated report, and bounded handoff rather
  than relying on chat history alone.

## Mandatory reporting policy

Every Phase and every Task MUST have one substantive generated Obsidian report.
The report is created when the work starts, updated only for a measured run,
material recovery/blocker, Owner decision, or closeout, and finalized or marked
blocked when the work closes. A Phase report summarizes its Tasks; it does not
replace them. Do not create a new report for an unchanged receipt, routine
heartbeat, or engineering micro-change. Report sync must regenerate all
generated notes from one validated read-model object and must fail closed on
missing, contradictory, stale, protected, or fixture-as-measured state.

Generated notes are reproducible and use `managed_by: myis-report` with
`edit_policy: generated_do_not_edit`. Owner-authored notes live only under
`obsidian_report/80_Owner_Notes/` (or the explicitly separated Owner area) and
must never be overwritten by sync. Generated notes expose only aggregate-safe
IDs, hashes, counts, safe pointers, and claim boundaries; qrels, membership,
query IDs, rankings, per-query outcomes, secrets, absolute personal paths,
provider payloads, and full protected prompts remain Owner-local.

Every Phase and Task report carries lifecycle fields
`status`, `evidence_class`, `scientific_authority`, `claim_boundary`,
`generated_from_revision`, `last_material_update`, and
`next_authorized_action`. Its canonical machine record and Markdown projection
must agree and must contain the fifteen-section structure defined in
[`docs/observatory/REPORTING_POLICY.md`](docs/observatory/REPORTING_POLICY.md):
Objective; Starting State; Inputs and Frozen Bindings; Work Performed;
Artifacts Produced; Metrics; Result; Interpretation; Supported Claims;
Unsupported Claims; Failures and Recovery; Governance and Safety; Decision;
Next Action; Evidence Links. Do not add a second numeric source of truth in
prose.

Before commit or push, run the smallest validation set that covers the changed
surface: report schema/content and sync/check when a projection changes,
artifact graph/checksum and protected-path scans when evidence changes, session
audit, Dashboard/API, MLflow doctor, layout/assets/Brain literature validation
when touched, focused tests, scoped Ruff, and `git diff --check`. Reuse a
still-valid hash-bound receipt instead of rerunning an unchanged validation.
The current state must agree everywhere: ArmIndex is active, SCOPE is
historical read-only, A0 and A1.1 are complete, Selection and Final are closed,
and A1.2 status/next action come only from its latest canonical receipt and
active goal document. A pre-measurement receipt requires zero measured
counters; a live A1.2 receipt may record only validated aggregate-safe
progress/results and must retain the frozen v11-v15 boundary. The long run
still requires the clean bound bundle, protected handoff/transfer receipts,
25 compiled bindings, fresh provider identity/quote, whole-workload budget,
and watchdog/destroy readiness before scientific work.
Historical facts still agree that accepted SCOPE Round 3 is `accept`, the P2
fixture is `passed`, and measured P2 was not started. A stale narrative is a
validation failure, not a documentation preference.

The authoritative report structure and machine-field contract are maintained
in `docs/observatory/REPORTING_POLICY.md` and
`schemas/phase-task-report.v1.json`.

## Closeout

Report the exact phase, task, status, checks, changed files, untouched
protected surfaces, evidence class, blockers, and next automatic action. Do not
claim A1 measured completion unless the protected Owner-local run, safe return,
and frozen evaluation actually completed. Do not destroy a live instance merely
to satisfy closeout; record validated `REUSE_ELIGIBLE` or actual `DESTROYED`
disposition according to evidence. `D2_OPEN_FINAL` remains closed and does not
authorize A2, Selection, or Final.
