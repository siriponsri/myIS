# myIS Research Agent Contract

This repository is `myIS Research` (`myis-research`), protocol `1.0`, research
version `0.1`. `01_Research` is the active control plane and the only place
where canonical plans, schemas, manifests, receipts, and publication facts are
written.

## Read order

1. Read `PLAN.md` for the current Phase, Task, and next authorized action.
2. Read the latest relevant AP/IM/LO handoff for the active Phase.
3. Read only the task-specific canonical controls, schemas, manifests, receipts,
   or runbook needed by the active task.
4. Read `HANDOFF.md` only when broader orientation or history is necessary.
5. Read the active campaign/control, schema, manifest, receipt, or runbook only
   when the task actually depends on it.

`HANDOFF.md` is orientation, not authority. It cannot override canonical
controls, manifests, receipts, schemas, or measured evidence.

### Conditional reads

- Read `control/source-of-truth.yaml` before report/projection sync,
  publication-facing writes, or resolving conflicting canonical facts.
- Read the active ArmIndex campaign/control before changing scientific
  execution policy or starting measured work.
- Read schemas, manifests, receipts, budgets, and runbooks only when the task
  uses or changes them.
- Historical SCOPE/P1/P2 controls are read-only context. Do not load their full
  execution stack for current ArmIndex work unless the task explicitly concerns
  historical evidence or compatibility.
- Before writing, verify the canonical files relevant to that write.
- Do not repeatedly re-read unchanged files within the same session.

## Workspace paths and projection management

Portable project root notation:

`<MYIS_ROOT>/`

The actual local root is supplied by the current environment or by Codex
`-C` / `--add-dir`; do not encode a user profile in tracked documentation.

Use `01_Research` as the default working directory and primary project surface.
The other top-level workspaces are supporting areas that agents may manage as
needed.

| Workspace | Canonical path | Role |
|---|---|---|
| Research | `<MYIS_ROOT>/01_Research` | Primary working directory and canonical scientific control plane. Plans, controls, schemas, source code, manifests, receipts, measured evidence, and official research facts live here. The repository also contains the Owner-facing `obsidian_report/` projection and `mlflow/` evidence archive. |
| Brain | `<MYIS_ROOT>/02_Brain` | Project memory for decisions, evidence pointers, lessons, failed attempts, and active context. It supports retrieval and continuity but cannot override canonical Research evidence. |
| Paper | `<MYIS_ROOT>/03_Paper` | Publication workspace for manuscripts, figures, tables, PDFs, QA, and release bundles. Quantitative claims must trace directly to canonical Research evidence. |
| Owner Stores | `<MYIS_ROOT>/04_Owner_Stores` | Owner-local operational storage for protected data, exact membership/qrels, model files, large artifacts, staging bundles, checkpoints, safe-return archives, provider artifacts, and other non-Git material. |

### Research-side projections

Within `01_Research`, two important Owner-facing projections are:

- `obsidian_report/` — the Research Reporting Vault for Phase/Task narrative,
  results, runs, advisor updates, literature links, decisions, and Owner-facing
  research status.
- `mlflow/` — the MLflow evidence archive and generated inspection surface for
  run history, safe artifacts, freeze snapshots, metrics, lineage, checks,
  failures, and claim-boundary context.

These are part of the Research repository but remain projections. They do not
replace canonical controls, manifests, receipts, schemas, or measured evidence.

### Workspace operating rule

Use **`01_Research` first; let agents manage supporting workspaces as needed**.

AP, IM, and LO may read and write across `02_Brain`, `03_Paper`, and
`04_Owner_Stores` when the active task benefits from it. Do not create an Owner
approval step merely because a supporting workspace is used.

Keep these boundaries:

- `01_Research/control/`, schemas, campaigns, manifests, receipts, and measured
  evidence remain authoritative.
- `01_Research/obsidian_report/`, `01_Research/mlflow/`, Dashboard,
  `02_Brain`, and `03_Paper` are projections or supporting workspaces; they
  cannot override canonical Research facts.
- `03_Paper` quantitative claims must trace directly to canonical evidence in
  `01_Research`.
- `04_Owner_Stores` is accessible and mutable when needed, but protected or
  large contents must not be distributed to Git, Brain, Paper, MLflow,
  Dashboard, chat, or external providers unless the active protected-data rule
  explicitly allows the derived artifact.
- Aggregate-safe outputs, hashes, counts, approved manifests, and safe pointers
  may move from `04_Owner_Stores` into the appropriate Research/projection
  surfaces.
- Prefer the narrowest useful subpath, but do not make path scoping a new gate.
- Agents may create, organize, archive, and clean supporting-workspace files
  when doing so is safe and useful. Preserve unique evidence, protected inputs,
  checkpoints, and safe-return packages.

The Owner should be able to understand the project primarily from
`01_Research`, especially `PLAN.md`, the current handoffs/evidence, the
`obsidian_report/` vault, and the `mlflow/` evidence archive. The remaining
workspaces should be managed by agents unless an Owner-only action is truly
required.

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

## Project priorities and Owner support

All sessions optimize for the strongest defensible publication impact for the
target NLP journal while preserving scientific validity, reproducibility, and
claim discipline.

Publication impact means prioritizing work that can materially improve:
- novelty and clarity of the research contribution;
- strength and completeness of measured evidence;
- reviewer-defensible experimental design;
- reproducibility and provenance;
- useful ablations, diagnostics, negative results, and limitations;
- quality of figures, tables, analysis, and publication-facing interpretation.

Do not optimize for a positive result. A strong negative or boundary finding is
valuable when it is well measured, well explained, and publication-relevant.

The Owner is low-dev and should not be used as an engineering router. Agents
should reduce Owner workload throughout the project by:
- resolving routine engineering choices independently;
- presenting technical decisions in plain Thai when reporting to the Owner;
- recommending one preferred next action instead of a long undifferentiated
  option list;
- giving exact copy-paste prompts and commands whenever the Owner must start a
  new session or run a local/provider action;
- naming the recommended session mode and model profile;
- explaining briefly why that route is recommended;
- asking the Owner only for decisions that truly require Owner authority.

When several valid paths exist, recommend the path with the best expected
publication value per unit of time, compute, money, and Owner effort.

## Owner project status card

Every substantive AP, IM, and LO closeout MUST begin with one compact
Owner-facing status card in plain Thai. Its purpose is orientation, not
governance.

Do not make the Owner reconstruct project state from filenames, logs, or prior
chat sessions.

Use canonical state from `PLAN.md`, the active campaign/control, the active
goal/audit, latest applicable receipt, and current budget/execution contract.
Do not hard-code temporary budget numbers in `AGENTS.md`.

Required fields:

```text
สถานะโครงการ:
Phase: <canonical Phase ID>
Task/Sub-stage: <canonical task/sub-stage, or current numbered goal step>
สถานะสั้น ๆ: <one plain-Thai sentence explaining where the project is now>

Publication impact:
<why the current work matters to the target NLP journal, or "no material change">

Budget:
Phase ceiling: <amount + source, or UNKNOWN>
Current Task/Run ceiling: <amount + source, or NOT_APPLICABLE>
Spent/Accrued: <amount, or UNKNOWN>
Remaining headroom: <amount, or UNKNOWN>
Estimated cost of next action: <amount/range, ZERO, or UNKNOWN>
Next Phase ceiling: <amount + source if already canonically bound, otherwise NOT_BOUND>
Budget status: <NO_SPEND | WITHIN_CAP | NEEDS_OWNER_BUDGET | UNKNOWN_DO_NOT_SPEND>

GPU / Vast:
GPU decision: <NO_GPU_NEEDED | NEED_GPU_NOW | GPU_ACTIVE | KEEP_GPU | DESTROY_GPU | OWNER_ACTION_DESTROY | UNKNOWN>
Reason: <one sentence>
Instance: <provider-safe instance ID/status if relevant, otherwise NONE>
Hourly rate / accrued GPU cost: <known aggregate-safe values or UNKNOWN>
Keep-until / destroy condition: <timestamp/condition or NOT_APPLICABLE>

Session routing:
Recommended next session: <AP | IM | LO | NONE>
Recommended model: <profile>
Command before prompt: <exact command or NONE>
Copy-paste prompt: <exact prompt or NONE>
Owner decision required: <NONE or exact Owner-only decision>

Projections:
Obsidian report (`01_Research/obsidian_report/`): <OK | PENDING | UNCHANGED>
MLflow (`01_Research/mlflow/`): <OK | PENDING | UNCHANGED>
```

Budget reporting rules:
- Report the current Phase ceiling and current Task/Run ceiling separately.
- Also report the next Phase ceiling only when it is already bound by a
  canonical budget/control; otherwise write `NOT_BOUND`.
- Never infer a paid-work budget from historical runs or chat memory.
- If a paid next action has no verified ceiling, use
  `UNKNOWN_DO_NOT_SPEND` and do not launch it.
- When a live GPU exists, include accrued cost and estimated idle cost when
  those values are available from current provider evidence.

GPU lifecycle rules:
- `NO_GPU_NEEDED`: current and next authorized action do not require a live GPU.
- `NEED_GPU_NOW`: the next authorized action requires GPU and the executor,
  budget, and launch inputs are ready enough to justify opening/using one.
- `GPU_ACTIVE`: an authorized GPU run or required recovery/safe-return work is active.
- `KEEP_GPU`: no run is active, but a specifically named next authorized GPU
  action will reuse the same instance. State the reason and a concrete
  keep-until condition. Do not keep a GPU alive merely because a later Phase
  might need GPU.
- `DESTROY_GPU`: no active work remains, safe return/checksum requirements are
  satisfied, and no immediate authorized reuse justifies continued spend.
- `OWNER_ACTION_DESTROY`: same as `DESTROY_GPU`, but provider credentials, 2FA,
  or dashboard-only lifecycle control requires the Owner to destroy it.
- `UNKNOWN`: evidence is insufficient. Give the exact check/command needed to
  resolve the decision.

If `DESTROY_GPU` or `OWNER_ACTION_DESTROY` is reported, give the Owner an exact
copy-paste action or dashboard instruction when known.

The status card is informational. It MUST NOT become a new approval gate or a
second source of scientific metrics.


## Safety boundary

- Compute, GPU, paid API, model download, and provider use follow the current
  active execution contract and budget. Do not infer broader authority from
  historical runs.
- Final/Selection protected membership, qrels, query IDs, per-query outcomes,
  credentials, and raw provider payloads stay Owner-local.
- Git, MLflow, Dashboard, Brain, Obsidian, and Paper receive only validated
  aggregate-safe facts, hashes, counts, safe IDs, and pointers.
- Never treat fixture/synthetic evidence as measured evidence.
- Never silently change frozen scientific semantics after measured exposure.
- Safety rules protect evidence; they should not be expanded into new
  engineering approval gates.

## Historical P2 lifecycle and freeze barrier

Historical SCOPE/P1/P2 records remain immutable evidence lineage.

- They may be read when needed for provenance, compatibility, or publication
  history.
- They do not authorize current ArmIndex execution and must not be used as
  active default policy.
- Never rewrite historical receipts or reinterpret an old measured result using
  a newer budget, rule, or campaign revision.

Current work follows `PLAN.md`, the active ArmIndex campaign/control, and the
latest applicable receipt.

## Engineering rules

- `control/`, schemas, deterministic kernel, manifests, and receipts remain
  canonical. MLflow, Dashboard, Brain, Obsidian, and Paper are projections.
- Use canonical JSON and SHA-256 commitments where the existing protocol
  requires them. Preserve stable IDs and deterministic tie-breaks.
- Preserve history. Archive before removing. Delete only exact verified paths.
- One report sync should use one validated read-model object; do not manually
  maintain duplicate metric values.
- Validate the changed surface, not the whole repository.
- Before commit/push, run focused tests plus `git diff --check`. Run report,
  Dashboard, layout, artifact-graph, or full-suite validation only when that
  surface was changed or the active goal explicitly requires it. Obsidian/Brain
  and MLflow should be refreshed after substantive state changes when practical,
  but projection availability is not a commit gate.
- Reuse a still-valid hash-bound validation receipt instead of rerunning the
  same check.
- A tracked runbook and append-only ledger/checkpoint are required for measured
  or genuinely long-running work. Small implementation tasks do not need a new
  runbook.
- On Windows, never use `os.kill(pid, 0)` as a liveness probe. Long-running
  workers use a reliable lock/process-identity mechanism.
- Engineering defects inside the current scientific design should be repaired
  directly by IM without a new Owner approval.

## Provider-neutral rules

- Never print, archive, or pass through complete credentials or inherited shell
  environments.
- Credential rotation, login/logout, and Owner-controlled account changes
  remain Owner actions.
- Provider/pool choice is operational configuration, not scientific authority.
- A predeclared model fallback may be used at a safe checkpoint when the agent
  is only orchestrating a frozen deterministic executor.
- If the LLM itself generates, scores, judges, selects, or otherwise changes a
  measured scientific unit, its model/provider binding is part of the
  experiment and must follow the frozen execution contract.

### Session model routing and provider fallback

Use economical defaults:

- `AP`: GPT-5.6 Sol High.
- `AP_CRITICAL`: GPT-5.6 Sol XHigh only for high-consequence scientific,
  launch, post-measurement, or publication judgment.
- `IM`: GPT-5.6 Sol Medium.
- `IM_COMPLEX`: GPT-5.6 Sol High for difficult architecture, lifecycle,
  recovery, remote, or cross-platform debugging.
- `LO`: GPT-5.6 Terra XHigh.
- `LO_FALLBACK`: GPT-5.6 Sol Medium.
- `LO_ECONOMY`: GPT-5.6 Terra High for highly deterministic mature execution.
- GPT-5.6 Luna is optional when a healthy pool is deliberately selected; no
  goal or recovery path may depend on Luna availability.

Do not use Terra Max, Sol High, or Sol XHigh as routine LO profiles merely to
compensate for unfinished architecture.

If an LO model/pool fails:

1. stop at a safe checkpoint;
2. preserve the ledger/checkpoint, attempt root, hashes, and safe-return state;
3. resume on the declared fallback when the agent is only orchestrating a
   frozen deterministic executor;
4. return to AP before changing model/provider when the LLM is part of the
   measured scientific unit.

Fallback never expands budget, TTL, scientific scope, protected-data access, or
Owner authority.

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

Preferred profile: MaxPlus GPT-5.6 Sol High.

Use Sol XHigh only for critical scientific-design review, ambiguous measured
launch readiness, post-measurement interpretation, or publication-facing
closeout.

AP decides what should be done and whether measured work is scientifically
ready.

AP SHOULD:
- inspect current evidence and repository state;
- check scientific consistency and frozen bindings;
- identify blockers that materially affect validity, cost, or publication
  value;
- create `docs/audit/<PHASE>_audit_<INDEX>.md` when IM has actionable work;
- create or materially refresh `docs/goal/<PHASE>_goal_<INDEX>.md` when LO is
  ready to execute;
- read the latest relevant IM/LO result documents before deciding the next
  action;
- audit measured results after LO closeout.

AP is read-only by default for code and measured execution, but may repair
small planning/documentation inconsistencies that do not change scientific
semantics.

AP MUST NOT start a measured experiment.

Before a new measured LO launch, AP checks only the essentials:
1. frozen scientific design/bindings agree;
2. runner, checkpoint/recovery, and safe return exist;
3. focused tests pass;
4. protected boundary is intact;
5. provider/budget/TTL/watchdog evidence required by the active contract is
   current.

Do not create a new gate for minor engineering issues. Send them directly to
IM.

### AP Owner-facing status and next-session recommendation

At the end of every substantive AP session, begin with the global
`Owner project status card`, then report the AP-specific status and recommend
exactly one primary next session.

The Owner-facing handoff should include:
- current Phase/Task and one-sentence status;
- what AP found or changed;
- why the next action matters for publication impact;
- recommended next session: `AP`, `IM`, or `LO`;
- recommended model/profile for that session;
- exact copy-paste prompt to start the next session;
- any command that must be run before or together with that prompt;
- what success should look like;
- Owner action required, if any.

Prefer a compact format such as:

```text
สถานะ: <PHASE/TASK + short status>
ผลกระทบต่อ paper: <why this matters>

แนะนำ session ถัดไป: <IM | LO | AP>
โมเดล: <recommended model/profile>

ถ้ามี command ให้รันก่อน:
<exact copy-paste command>

Prompt สำหรับ session ถัดไป:
<exact copy-paste prompt>

คาดหวังผลลัพธ์:
<short expected outcome>

Owner ต้องตัดสินใจ:
<none | exact Owner-only decision>
```

Examples:

```text
แนะนำ session ถัดไป: IM
โมเดล: GPT-5.6 Sol High
Prompt:
ตอนนี้คุณคือ IM ตาม AGENTS.md
อ่าน docs/audit/A2_PER_ARM_AUTOINDEX_audit_003.md
แล้ว implement, validate, commit/push และเขียน IM result handoff ตาม contract
```

```text
แนะนำ session ถัดไป: LO
โมเดล: GPT-5.6 Terra XHigh
Prompt:
/goal อ่าน docs/goal/A2_PER_ARM_AUTOINDEX_goal_002.md แล้วทำงานตามขั้นตอนทั้งหมด
```

If a shell, SSH, provider, Git, or local setup command is required before the
next prompt, show that command first and make it copy-paste ready. Do not assume
the Owner will infer omitted CLI steps.

AP should recommend a stronger model only when the expected reasoning benefit
justifies the additional token/credit cost.

AP must also make compute state explicit before recommending LO or another paid
action: GPU needed now or not, verified Phase and Task/Run budget ceilings,
estimated next-action cost, and whether any live GPU should be kept or
destroyed, with one plain-Thai reason.

End with one practical routing note:
- `READY_FOR_LO`
- `NEEDS_IM`
- `NEEDS_OWNER`
- `BLOCKED_EXTERNAL`

These are routing notes, not scientific approval objects.

### IM — Implementation

Preferred profile: MaxPlus GPT-5.6 Sol Medium.

Escalate to Sol High only for materially difficult architecture, lifecycle,
recovery, concurrency, remote-execution, or cross-platform debugging.

IM makes the executor work. IM uses a normal prompt, not `/goal`.

IM MAY:
- build or repair architecture, runners, schemas, lifecycle, recovery, tests,
  artifacts, and remote staging;
- fix engineering defects discovered during the task;
- run focused validation;
- commit/push when the task allows it.

IM may read the active goal for constraints but does not execute it as a
long-run instruction.

IM may continue without Owner approval when a repair:
- preserves frozen scientific semantics;
- stays inside the protected boundary;
- does not expand budget/TTL authority;
- does not change Owner-controlled credentials/account state;
- does not open D2, D3, Selection, Final, or another closed scientific boundary;
- does not reinterpret measured evidence.

Validate the changed surface first. Use the broader suite only when justified.

IM stops before measured execution unless the current Owner prompt explicitly
asks IM to run an already-authorized measurement.

IM finishes by writing
`docs/implementation/<PHASE>_im_<AUDIT_INDEX>_<INDEX>.md` with the exact
revision, changed surface, focused checks, staged execution path, known
limitations, and recommended next action for AP.

### IM Owner-facing status and next-session recommendation

At the end of every substantive IM session, begin with the global
`Owner project status card`, then report the implementation status and
recommend exactly one primary next session.

The Owner-facing handoff should include:
- current Phase/Task and short implementation status;
- source audit and IM result document path;
- what was implemented or repaired;
- focused validation result;
- whether a launch-critical surface changed;
- recommended next session and model/profile;
- exact copy-paste prompt for that session;
- any command the Owner must run first;
- Owner action required, if any.

Use these routing defaults:

- If implementation is complete, the active goal is still current, and no
  launch-critical surface changed -> recommend `LO` with GPT-5.6 Terra XHigh.
- If IM materially changed scientific bindings, evaluator/runner semantics,
  protected boundary, provider/budget/TTL policy, or recovery/safe-return logic
  -> recommend `AP` with GPT-5.6 Sol High for a short readiness review.
- If difficult implementation work remains -> recommend another `IM` session
  using Sol Medium by default or Sol High only when the remaining engineering
  problem is materially complex.
- Recommend `NEEDS_OWNER` only when actual Owner authority is required.

Prefer this compact Owner-facing format:

```text
สถานะ: <PHASE/TASK + implementation status>
IM result: <docs/implementation/...>
Validation: <short result>

แนะนำ session ถัดไป: <LO | AP | IM>
โมเดล: <recommended model/profile>

ถ้ามี command ให้รันก่อน:
<exact copy-paste command>

Prompt สำหรับ session ถัดไป:
<exact copy-paste prompt>

คาดหวังผลลัพธ์:
<short expected outcome>

Owner ต้องตัดสินใจ:
<none | exact Owner-only decision>
```

When recommending LO, provide the exact `/goal` command rather than asking the
Owner to construct it.

Example:

```text
แนะนำ session ถัดไป: LO
โมเดล: GPT-5.6 Terra XHigh

Prompt:
/goal อ่าน docs/goal/A2_PER_ARM_AUTOINDEX_goal_003.md แล้วทำงานตามขั้นตอนทั้งหมด
```

When recommending AP, point AP directly to the latest IM result document.

Example:

```text
แนะนำ session ถัดไป: AP
โมเดล: GPT-5.6 Sol High

Prompt:
ตอนนี้คุณคือ AP ตาม AGENTS.md
อ่าน docs/implementation/A2_PER_ARM_AUTOINDEX_im_003_001.md
ตรวจผล implementation และ launch readiness เฉพาะส่วนที่เปลี่ยน
จากนั้นแนะนำ next session พร้อม exact prompt ตาม AGENTS.md
```

Do not duplicate full implementation logs in the Owner-facing message. Point to
the IM result document and summarize only what the Owner needs to continue

### LO — Long Run

Preferred profile: MaxPlus GPT-5.6 Terra XHigh.

Fallback: MaxPlus GPT-5.6 Sol Medium.

Terra High is allowed for a highly deterministic mature executor. Luna is
optional when a healthy Luna-capable pool is intentionally selected.

LO executes an already-ready plan and starts only with:

`/goal อ่าน docs/goal/<file>.md แล้วทำงานตามขั้นตอนทั้งหมด`

LO SHOULD:
- follow the goal through execution and closeout;
- checkpoint enough state to survive session/provider failure;
- use bounded recovery without repeatedly asking the Owner;
- preserve the remote attempt root until safe return/checksum validation;
- produce aggregate-safe artifacts and canonical evidence;
- continue through recoverable engineering/runtime issues covered by the goal.

LO MUST NOT redesign the scientific experiment during the measured run.

If architecture is materially broken, return to IM.
If scientific interpretation or authority is ambiguous, return to AP/Owner as
appropriate.

For model/provider failure, use the safe-checkpoint fallback rules in
`Provider-neutral rules`.

Before ending, LO writes
`docs/long_run/<PHASE>_lo_<GOAL_INDEX>_<INDEX>.md` so AP can review the exact
execution result without depending on chat history.

### LO Owner-facing status and next-session recommendation

At the end of every substantive LO session, begin with the global
`Owner project status card`, then report the long-run status and recommend
exactly one primary next session.

The Owner-facing handoff should include:
- current Phase/Task and execution status;
- source goal and LO result document path;
- whether execution completed, partially completed, or stopped;
- measured/operational evidence created;
- recovery used, if any;
- safe-return and provider/remote disposition when relevant;
- recommended next session and model/profile;
- exact copy-paste prompt for that session;
- any command the Owner must run first;
- Owner action required, if any.

Use these routing defaults:

- After successful measured or long-run closeout -> recommend `AP`.
- Use GPT-5.6 Sol High for normal evidence review and next-phase planning.
- Recommend GPT-5.6 Sol XHigh when the result requires high-consequence
  scientific interpretation, publication-facing claim judgment, or major Phase
  closeout.
- If LO stops because architecture/recovery is materially broken -> recommend
  `IM` using Sol Medium or Sol High according to engineering complexity.
- If LO stops because scientific semantics or authority are ambiguous ->
  recommend `AP`.
- Recommend `NEEDS_OWNER` only when actual Owner authority is required.

Prefer this compact Owner-facing format:

```text
สถานะ: <PHASE/TASK + execution status>
Goal: <docs/goal/...>
LO result: <docs/long_run/...>

Measured/operational result:
<short aggregate-safe summary>

Safe return / provider:
<short status>

แนะนำ session ถัดไป: <AP | IM>
โมเดล: <recommended model/profile>

ถ้ามี command ให้รันก่อน:
<exact copy-paste command>

Prompt สำหรับ session ถัดไป:
<exact copy-paste prompt>

คาดหวังผลลัพธ์:
<short expected outcome>

Owner ต้องตัดสินใจ:
<none | exact Owner-only decision>
```

Example after successful closeout:

```text
แนะนำ session ถัดไป: AP
โมเดล: GPT-5.6 Sol XHigh

Prompt:
ตอนนี้คุณคือ AP ตาม AGENTS.md
อ่าน docs/long_run/A2_PER_ARM_AUTOINDEX_lo_003_001.md
ตรวจ measured closeout, claim boundary และ publication impact
จากนั้นกำหนด next Phase/Task และแนะนำ session ถัดไปพร้อม exact prompt
```

Do not make scientific interpretations in the Owner-facing LO summary beyond
what the canonical evidence supports. Publication interpretation belongs to AP.

LO must still make the operational compute disposition explicit at closeout:
`KEEP_GPU`, `DESTROY_GPU`, `OWNER_ACTION_DESTROY`, or another status from
`Owner project status card`, with the evidence/reason required by that status.

### Session workflow

Default workflow:

`AP -> IM -> LO -> AP`

Use a second AP readiness pass between IM and LO only when IM materially changed
a launch-critical surface: scientific binding, evaluator/runner semantics,
protected boundary, provider/budget/TTL policy, or recovery/safe-return logic.

Otherwise, if the active goal remains current and ready, the Owner may launch
LO directly after IM.

Shortcuts are intentional:
- skip IM when nothing needs implementation;
- skip repeated AP audit when no launch-critical fact changed;
- do not create approval documents between routine transitions.

The Owner is involved only where actual Owner authority is required.

### Convergence and anti-loop policy

The AP/IM workflow must converge. Do not allow repeated broad
`AP -> IM -> AP -> IM` review cycles.

1. **AP batches findings.** One AP audit contains all currently known actionable
   engineering findings for that scope. Do not drip-feed one minor finding per
   audit.

2. **Every audit has finite acceptance criteria.**
   `docs/audit/<PHASE>_audit_<INDEX>.md` must state a short observable checklist
   that means IM is done.

3. **IM owns bounded engineering retries.** Once IM accepts an audit, IM should
   repair, test, and retry within the same implementation session until the
   acceptance criteria pass or a true blocker outside IM authority is reached.
   Do not return to AP after every failed test.

4. **AP read-back is delta-only.** After IM reports completion, AP checks only
   the original audit acceptance criteria plus any launch-critical regression
   introduced by IM. AP does not restart a broad repository audit.

5. **No new non-critical blockers during read-back.** Newly noticed cleanup,
   refactoring, documentation polish, optional validation, or other
   non-launch-critical improvements are deferred and do not send the current
   task back to IM.

6. **Return to IM only for material failure.** AP sends work back only when an
   explicit acceptance criterion is still failing, IM introduced a
   launch-critical regression, runner/recovery/safe-return is not executable,
   protected boundaries are violated, or proceeding would invalidate measured
   evidence.

7. **Retry the same scope without inventing a new audit.** Reuse the same audit
   reference and let the IM result index represent the retry. Create a new audit
   index only when engineering scope materially changes.

8. **Prefer forward progress with bounded debt.** If the remaining issue is
   non-critical and the current goal is executable, route forward to LO and
   record the item as deferred instead of reopening implementation.

9. **Model escalation is not a convergence strategy.** Do not repeatedly raise
   reasoning effort to compensate for unclear acceptance criteria. Clarify the
   audit once, then execute it.

Intended normal path:

`AP audit once -> IM repair until acceptance -> LO -> AP closeout`

A second AP readiness pass before LO is exceptional and delta-only.

Projection-only defects are repaired in the projection/read-model layer. A stale
or contradictory Obsidian, MLflow, Dashboard, README, HANDOFF, generated
Markdown, or projection-metadata surface does not reopen implementation
acceptance, invalidate canonical evidence, block an otherwise-ready LO, or
create an Owner approval. Return to IM only when executable code, scientific
semantics, protected-data handling, runner/recovery, safe return, provider
lifecycle, or another launch-critical implementation is defective.

### Cross-session communication

AP, IM, and LO communicate through small repository handoff documents rather
than relying on chat history.

Use the canonical Phase ID from `PLAN.md` as `<PHASE>`, for example
`A2_PER_ARM_AUTOINDEX`.

Use a zero-padded three-digit running index within each document family:
`001`, `002`, `003`, ...

#### AP -> IM: audit handoff

When AP finds implementation work that IM should perform, create:

`docs/audit/<PHASE>_audit_<INDEX>.md`

Example:

`docs/audit/A2_PER_ARM_AUTOINDEX_audit_001.md`

The audit handoff should contain only:
- objective;
- evidence inspected;
- findings that matter;
- implementation work requested;
- scientific/protected boundaries that must remain unchanged;
- finite acceptance criteria for IM completion;
- smallest useful validation;
- expected IM output;
- deferred/non-blocking items, if any.

Do not create an audit handoff when AP has no actionable work for IM.

#### AP -> LO: goal handoff

When measured or long-running execution is ready, create:

`docs/goal/<PHASE>_goal_<INDEX>.md`

Example:

`docs/goal/A2_PER_ARM_AUTOINDEX_goal_001.md`

This is the file launched with:

`/goal อ่าน docs/goal/<PHASE>_goal_<INDEX>.md แล้วทำงานตามขั้นตอนทั้งหมด`

The goal must contain the executable steps, checkpoints, bounded recovery,
hard stops, required artifacts, validation, safe return, and closeout
instructions needed by LO.

Do not create a new goal index for routine wording changes. Create a new index
only when the executable plan materially changes.

#### IM -> AP: implementation result

IM writes one result document for each audit handoff it materially acts on:

`docs/implementation/<PHASE>_im_<AUDIT_INDEX>_<INDEX>.md`

Example:

`docs/implementation/A2_PER_ARM_AUTOINDEX_im_001_001.md`

The IM result should contain:
- source audit path;
- implementation summary;
- changed files/artifacts;
- focused checks and results;
- unresolved limitations or blockers;
- remote/staging state when relevant;
- recommended next action for AP.

When routing to another session, include the exact session mode, model,
reasoning effort/profile, one-sentence reason, command before prompt when
needed, exact copy-paste prompt, and exact Owner-only action if any. Owner
should not be asked to choose an IM/LO model or reasoning effort.

Multiple IM result documents may reference the same audit index when a repair
requires more than one bounded implementation attempt.

#### LO -> AP: long-run result

LO writes one result document for each goal it executes:

`docs/long_run/<PHASE>_lo_<GOAL_INDEX>_<INDEX>.md`

Example:

`docs/long_run/A2_PER_ARM_AUTOINDEX_lo_001_001.md`

The LO result should contain:
- source goal path;
- execution summary;
- checkpoints/recovery used;
- measured or operational evidence created;
- safe-return/provider disposition when relevant;
- blockers or incomplete work;
- exact closeout state;
- recommended next action for AP.

Multiple LO result documents may reference the same goal index only when the
goal explicitly supports resume/recovery attempts.

#### AP read-back rule

At the start of AP work, inspect only the latest relevant files under:

- `docs/implementation/<PHASE>_im_*.md`
- `docs/long_run/<PHASE>_lo_*.md`

AP then decides whether to:
- close the task;
- issue a new audit handoff to IM;
- issue or refresh a goal for LO;
- ask the Owner only when actual Owner authority is required.

These handoff documents are communication artifacts, not new approval gates and
not new sources of scientific metrics. Numeric claims still come from canonical
receipts/manifests/evidence.

Keep them short. Do not duplicate full logs, datasets, metrics tables, or
canonical receipts inside them; link to those artifacts instead.

## Memory lifecycle

Brain memory is pointer-only and has five kinds: `decision`, `evidence`,
`lesson`, `failed_attempt`, and `active_context`. Every note carries a source
URI, source SHA-256, evidence IDs, creation time, review time, and supersession
pointer. Stale active context is archived; failed attempts remain searchable but
cannot override run facts.

### Brain synchronization and YOLO mode

Brain is supporting memory, not a commit gate for unrelated work.

When `AGENTS.md` or a material project decision changes, update the
corresponding pointer-only Brain note when the Brain writer is available.

If the Brain lease/writer is temporarily unavailable:
- record the pending sync in the session closeout or handoff;
- continue ordinary engineering work and commit/push when its own validations
  pass;
- retry Brain sync in the next suitable session.

Brain availability becomes blocking only when the active task itself changes
Brain authority/schema, depends on Brain as an input, or publication/report
synchronization cannot be correct without it.

Safe pointer-only Brain writes may proceed without another Owner confirmation.
They never bypass protected-data, credential, scientific, or Owner-decision
boundaries.

### Obsidian report and MLflow synchronization

`obsidian_report/` and `mlflow/` live inside `01_Research`. They are
Owner-facing projections of the same canonical Research state.

Keep them reasonably current after substantive work, but do not turn projection
synchronization into a scientific, engineering, commit, or launch gate.

#### Obsidian report

For a substantive AP, IM, or LO session that materially changes project state,
refresh the relevant report surfaces under:

`01_Research/obsidian_report/`

Follow the existing vault structure and `obsidian_report/OBSIDIAN_DESIGN.md`
rather than inventing a parallel status hierarchy.

Prefer updating the smallest relevant existing surface, for example:
- Phase status/report under `obsidian_report/01_Phases/`;
- Task status/report under `obsidian_report/02_Tasks/`;
- measured/result summary under `obsidian_report/03_Results/`;
- run-oriented note under `obsidian_report/03_Runs/`;
- advisor-facing update when the active task actually requires one.

The update should make the Owner able to understand:
- current Phase and Task/Sub-stage;
- plain-Thai current status;
- important change since the previous substantive update;
- Output / Result / Interpretation when applicable;
- publication impact;
- budget and GPU/Vast state when relevant;
- canonical evidence and handoff pointers;
- recommended next session, model, command, and copy-paste prompt.

Do not create a new report merely because a session occurred. Prefer updating
the existing Phase/Task/Run/Result surface that already represents the work.

Do not copy raw protected data, per-query outcomes, verbose logs, or duplicate
canonical metric tables into Obsidian. Generated numeric facts must remain
traceable to the canonical Research read model/evidence.

If the Obsidian projection cannot be refreshed without disproportionate work,
record `OBSIDIAN_SYNC_PENDING` in the Research-side handoff/closeout and
continue. Repairing the projection later must not reopen an already-complete
AP/IM/LO task.

#### MLflow

Use the existing Research-side MLflow archive:

`01_Research/mlflow/`

Follow `mlflow/MLFLOW_DESIGN.md` and the existing generated/archive conventions
when materially updating MLflow. Do not create a second MLflow hierarchy.

MLflow is the Owner's searchable run/freeze/artifact history, but canonical
Research evidence remains the authority.

After substantive work that creates or materially changes useful run/evidence
state, synchronize the safe metadata/artifacts that improve traceability when
MLflow is available. Typical useful fields include:
- Phase;
- Task/Sub-stage;
- session mode;
- Git commit/revision;
- source audit/goal path when applicable;
- IM/LO handoff path when applicable;
- run/evidence status;
- canonical manifest/receipt/evidence pointer;
- aggregate-safe metrics, checks, and artifacts actually produced.

AP planning sessions do not need invented experiment metrics. A safe
audit/goal/freeze snapshot or metadata update is enough when useful.

Never send protected membership, qrels, raw query IDs, per-query outcomes,
credentials, raw provider payloads, or prohibited Owner Store contents into
MLflow.

If MLflow is temporarily unavailable, preserve the canonical Research artifacts
first, record `MLFLOW_SYNC_PENDING`, and continue. Projection repair may happen
later without restarting scientific or implementation work.

For closeout, report projection state concisely when relevant:

`Obsidian report: OK | PENDING | UNCHANGED`

`MLflow: OK | PENDING | UNCHANGED`

These statuses are informative only. They do not block commit, push, LO launch,
measured closeout, or forward routing when canonical Research evidence is valid.

## Historical A1 compatibility

A1 is historical/completed work. Its detailed acceleration rules, old Vast
limits, and v11-v17 execution lineage remain in canonical receipts, runbooks,
and reports.

Do not load or enforce A1-specific budgets, readiness checks, or closeout rules
for current A2+ work unless the active task explicitly audits A1 history or
reuses an A1 artifact.

Current execution follows `PLAN.md`, the active ArmIndex campaign/control, the
latest applicable receipt, and the active goal.

For code or plan edits, prefer the smallest direct change and define a concrete
verification command. Supporting local skills may be used when useful; they are
not mandatory ceremony for routine engineering.

## Artifact-first long-run workflow

Long-running work prioritizes implementation, measured evidence, and
publication-impact artifacts over repetitive governance documentation.

`docs/goal/` holds short Thai-first operational guides. A goal is not
scientific authority; canonical controls, schemas, manifests, budgets, and
receipts remain authoritative.

Normal flow:

`AP plan -> IM build/stage -> LO execute -> AP interpret/close`

A short AP recheck is required before LO only when IM materially changed a
launch-critical surface. Do not repeat a broad historical audit when bindings
and evidence are unchanged.

- AP creates or materially refreshes one goal when a Phase/Task begins, the
  objective changes, a material blocker changes execution, or closeout requires
  the next plan.
- IM implements/tests/stages the executor and fixes engineering-only mismatches
  directly.
- LO follows the goal through checkpoints, bounded recovery, safe return,
  validation, evidence generation, and closeout.
- AP reviews the resulting measured evidence and publication claim boundary.

Keep durable artifacts minimal:
- the latest relevant AP audit handoff when IM work exists;
- one active goal;
- the IM/LO result handoff needed for AP read-back;
- one tracked runbook for measured/long work;
- one append-only ledger/checkpoint;
- canonical manifests/receipts;
- one substantive generated Phase/Task report when there is material evidence
  to report.

Do not create parallel status notes, duplicate metrics, repeated approval
receipts, or retrospective prose merely to prove that an agent worked.

A goal intended for LO must contain enough numbered steps, checkpoints,
recovery, hard stops, required artifacts, validation, safe return, and terminal
closeout instructions to run without relying on chat history.

Provider-specific historical A1 instructions remain historical. Current remote
identity, price, budget, TTL, watchdog, adoption, and safe-return requirements
come from the active execution contract/goal.

## Reporting policy

Reporting exists to preserve material evidence, not to create work for every
engineering change.

Create or materially update a generated Phase/Task report when one of these
occurs:
- measured execution;
- material recovery or blocker;
- Owner decision that changes the research path;
- Phase/Task closeout;
- publication-facing evidence or claim update.

Do NOT create or regenerate reports for:
- routine heartbeat;
- unchanged receipts;
- small engineering repairs;
- formatting-only changes;
- repeated validation with unchanged bindings.

When a formal generated report is produced, continue to use the canonical
report schema/structure in `docs/observatory/REPORTING_POLICY.md` and
`schemas/phase-task-report.v1.json`, and expose only aggregate-safe facts.

Report/projection validation is required when the report/projection surface or
measured evidence changes. A report-sync problem should not block an unrelated
engineering commit unless that commit would make canonical evidence or a
publication-facing projection incorrect.

Before commit/push, run the smallest validation set that covers the changed
surface. Reuse valid hash-bound checks. Do not require Dashboard, MLflow,
Brain, report, layout, literature, or full-suite validation when those surfaces
were untouched.

Temporary current-state facts belong in `PLAN.md`, the active campaign/control,
and the latest receipt—not in this policy.

## Closeout

Report concisely:
- session mode;
- Phase/Task;
- work completed;
- checks run and result;
- evidence created/used;
- blockers that still matter;
- protected surfaces left untouched;
- Obsidian/MLflow projection state when relevant;
- next practical action.

When the closing session is AP, also include the Owner-facing next-session
package defined in `AP Owner-facing status and next-session recommendation`:
recommended session, recommended model, exact copy-paste prompt, and any
required command.

Do not claim measured completion without the required measured evidence,
safe-return state, and canonical closeout artifacts.

Do not destroy a live remote instance merely to make closeout look complete;
record the provider disposition that actually exists.
