สถานะโครงการ:
Phase: A2_PER_ARM_AUTOINDEX
Task/Sub-stage: A2.1 / authority and executor successor design after Goal 002 hard stop
สถานะสั้น ๆ: AP ยืนยันว่า A2 เต็มรูปแบบต้องเปิดเฉพาะการประเมิน aggregate บน Owner-local เพื่อใช้กฎ reserve และ winner ที่ freeze แล้ว

Publication impact:
ทำให้การค้นหา per-arm AutoIndex มีเส้นทางวัดผลที่สอดคล้องกับกฎคัดเลือกและปกป้องข้อมูล จึงทำให้ผล A2 นำไปอ้างอิงใน paper ได้อย่างตรวจสอบได้

Budget:
Phase ceiling: USD 150 (`PLAN.md` / active campaign)
Current Task/Run ceiling: USD 50 (Goal 002 / authority v2; historical failed prelaunch lineage)
Spent/Accrued: UNKNOWN
Remaining headroom: UNKNOWN
Estimated cost of next action: ZERO (IM design and validation only)
Next Phase ceiling: NOT_BOUND
Budget status: UNKNOWN_DO_NOT_SPEND

GPU / Vast:
GPU decision: OWNER_ACTION_DESTROY
Reason: ไม่มี LO action ที่ current authority อนุญาตหลัง prelaunch hard stop และ successor IM/AP chain ต้องเสร็จก่อนใช้ compute อีกครั้ง
Instance: `47700074`; latest recorded GPU/A2 process count `0/0`
Hourly rate / accrued GPU cost: USD `0.575817794`/hour from last bound quote / accrued UNKNOWN
Keep-until / destroy condition: Vast dashboard -> instance `47700074` -> Destroy, after confirming no Owner-local safe-return activity

Session routing:
Recommended next session: IM
Recommended model: GPT-5.6 Sol High
Command before prompt: NONE
Copy-paste prompt: `ตอนนี้คุณคือ IM ตาม AGENTS.md อ่าน docs/audit/A2_PER_ARM_AUTOINDEX_audit_010.md แล้ว implement authority/executor successor contract ตามที่ระบุ, run focused validation, commit/push และเขียน IM result handoff; ห้ามเริ่ม measured A2 หรือ provider action`
Owner decision required: Destroy Vast instance `47700074` in the dashboard

Projections:
Obsidian report (`01_Research/obsidian_report/`): UNCHANGED
MLflow (`01_Research/mlflow/`): UNCHANGED

# A2 AP Audit 010: coherent full-execution successor design

- Session mode: `AP`
- Phase/Task: `A2_PER_ARM_AUTOINDEX / A2.1 FROZEN_FIVE_ARM_EXECUTION`
- Inputs reviewed: `docs/goal/A2_PER_ARM_AUTOINDEX_goal_002.md`,
  `control/armindex/a2/measured-authority/a2-im-audit008-provenance-v2.authority.v2.json`,
  `docs/long_run/A2_PER_ARM_AUTOINDEX_lo_002_001.md`, and the current execution closure
- Date: `2026-08-15`
- Decision: `NEEDS_IM`

## AP decision

Goal 002 and authority v2 are preserved as immutable **failed-prelaunch
lineage**. They must not be amended, reused for a measured relaunch, or
reinterpreted as candidate evaluation authority.

AP selects this coherent successor design for full A2: frozen retrieval may
perform **Owner-local, aggregate-only REP-DEV candidate evaluation solely to
apply the already-frozen strict-improvement, reserve activation, and
winner/advancement rules**. This is an A2 execution necessity, not permission
to generate or mutate candidates, optimize a new program, open A3, or change
any frozen scientific rule.

The design is required because current Goal 002 excludes candidate evaluation
and REP-DEV measurement, yet requires reserve activation from a strict
improvement predicate and winner/advancement receipts. The current production
adapter correctly reveals this conflict: it evaluates returned opaque rankings
through the Owner-local evaluator, where qrels and membership are opened only
locally. Suppressing that evaluation would leave no valid current receipt,
reserve decision, or winner closeout path.

## Frozen successor boundary

The successor authority and successor LO goal must state all of the following
as explicit, hash-bound fields rather than infer them from implementation:

- `candidate_generation_allowed: false` and `candidate_mutation_allowed: false`.
- `candidate_evaluation_allowed: true`, limited to the existing 52 frozen
  candidate IDs, exact frozen order, frozen candidate hashes, and the already
  declared five arms.
- `rep_dev_measurement_allowed: true`, limited to aggregate `Recall@100`,
  `nDCG@100`, `nDCG@10`, latency, cost, coverage, deterministic strict-tie
  handling, reserve predicate, and winner/advancement receipts for A2.
- `evaluation_location: owner_local_only` and
  `evaluation_output_class: aggregate_safe_only`. Qrels, split membership,
  query IDs, rankings, per-query outcomes, token maps, credentials, and raw
  provider payloads remain prohibited from Git, remote transport/logs,
  lifecycle receipts, safe-return archives, projections, Paper, and chat.
- Exact evaluator, qrels commitment, membership commitment, token-map
  commitment, Owner-local manifest, runtime/model/data bindings, bundle,
  adoption, and transport hashes. The authority may expose commitments and
  aggregate numbers, never protected bytes or identifiers.
- `a3_allowed: false`, `selection_allowed: false`, and `final_allowed: false`.
  HARNESS-DEV, Selection, Final, D2, and D3 remain closed.

This successor does not alter the candidate universe, model weights, primary
metric, tie policy, arms, reserve floor, 84-hour total TTL, initial 40-hour
admission floor, USD 50 Task/Run hard stop, or USD 150 Phase ceiling.

## Required IM implementation

IM must implement the following launch-critical repair without starting a
measured run or contacting/provisioning/destroying a provider instance:

1. Introduce a new versioned measured-execution authority schema and validator
   path. Do not relax v2. The new schema must distinguish retrieval authority
   from the narrowly scoped Owner-local aggregate evaluation authorization and
   require the boundary and binding fields above. Update the authority
   commitment contract/version so it hash-binds the new schema, not v2.
2. Update the operational executor, remote transport, Owner-local evaluator,
   candidate-result receipt contract, reserve decision/continuation, winner
   receipt, and closeout validation so the measured route is legal only when
   the new authority explicitly enables this exact Owner-local evaluation.
   The executor must reject evaluation under v2 and reject any incomplete or
   remote evaluation binding.
3. Keep remote retrieval free of qrels, membership, evaluator payloads, and
   evaluation execution. The only permitted evaluation transition is after a
   valid remote retrieval result has returned to the Owner-local protected root.
   Aggregate outputs and hash commitments must remain allowlisted and
   protected-output scans must fail closed.
4. Preserve exact frozen matched-first and reserve behavior. A reserve decision
   may consume only the authorized aggregate results and frozen incumbents;
   it must not use a new candidate, free-form judgment, or a changed tie rule.
5. Build a new clean, pushed execution bundle after the code/control change;
   create a new attempt ID, isolated remote root, deployment/stage evidence,
   Owner-local manifest, transport config, execution adoption receipt, and
   successor provenance chain. Do not reuse the v2 bundle, authority,
   admission, or remote root. The stale/current quote is not reusable.

Focused tests must cover at least:

- new authority schema and validator acceptance for the narrow successor only;
- v2 continuing to reject candidate evaluation and REP-DEV measurement;
- rejection for evaluation on the remote process or in remote transport;
- rejection for qrels/membership/query IDs/rankings/per-query outcomes in any
  aggregate-safe output, archive, log, or projection;
- exact frozen candidate/order/hash binding, matched barrier, reserve predicate,
  strict-tie rejection, ARM-01/02 non-advancement, and A3/Selection/Final
  closure;
- clean-pushed bundle lineage and failure on any execution-closure drift;
- lifecycle/recovery plus safe-return behavior under the new authority;
- regression for the current contradiction: no authority that has
  `rep_dev_measurement_allowed: false` may reach the Owner-local evaluator.

IM must write its implementation result handoff with the exact revision,
changed closure, tests, known limitations, and a statement that measured A2,
provider contact, and protected-data exposure outside the Owner-local boundary
remain zero.

## Required successor sequence

After IM passes focused validation, AP must independently review the changed
launch-critical closure and issue a new measured authority and successor LO
goal. Only that AP successor may authorize a fresh authenticated provider
observation, instance binding, admission, staging, and measured launch. LO
must then use a new isolated remote root and a quote within the freshness
window; it may not reuse any v2 admission or attempt artifact.

No measured execution, candidate evaluation, REP-DEV measurement, provider
operation, A3, Selection, Final, D2, or D3 was started by this audit.

## Routing

สถานะ: A2.1 ต้องซ่อม authority/executor contract ให้สอดคล้องกับ full A2 ที่ freeze แล้ว
ผลกระทบต่อ paper: ทำให้ผล candidate selection และ reserve logic มีหลักฐานที่ปกป้องได้โดยไม่รั่ว protected data

แนะนำ session ถัดไป: IM
โมเดล: GPT-5.6 Sol High

Prompt สำหรับ session ถัดไป:
```text
ตอนนี้คุณคือ IM ตาม AGENTS.md
อ่าน docs/audit/A2_PER_ARM_AUTOINDEX_audit_010.md
แล้ว implement authority/executor successor contract ตามที่ระบุ, validate changed surface,
commit/push และเขียน IM result handoff ตาม contract
ห้ามเริ่ม measured A2, provider action, candidate generation/mutation, A3, Selection, Final, D2 หรือ D3
```

คาดหวังผลลัพธ์: clean pushed successor implementation พร้อมหลักฐาน focused validation เพื่อให้ AP ออก authority/goal ใหม่ได้

Owner ต้องตัดสินใจ: Destroy Vast instance `47700074` ใน Vast dashboard

`NEEDS_IM`
