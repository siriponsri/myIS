สถานะโครงการ:
Phase: A2_PER_ARM_AUTOINDEX
Task/Sub-stage: A2.1 / FROZEN_FIVE_ARM_EXECUTION
สถานะสั้น ๆ: LO ซ่อม runtime dependency แบบ offline ได้ แต่หยุดก่อนวัดเพราะ executor ปัจจุบันจะเปิด qrels และ REP-DEV ที่ authority ยังปิดอยู่

Publication impact:
ป้องกันผลวัดที่ละเมิด protected boundary และทำให้ claim ของงานวิจัยไม่สามารถปกป้องได้

Budget:
Phase ceiling: USD 150 (`PLAN.md` / active campaign)
Current Task/Run ceiling: USD 50 (Goal 002 / authority v2)
Spent/Accrued: UNKNOWN
Remaining headroom: UNKNOWN
Estimated cost of next action: ZERO (IM engineering repair)
Next Phase ceiling: NOT_BOUND
Budget status: UNKNOWN_DO_NOT_SPEND

GPU / Vast:
GPU decision: OWNER_ACTION_DESTROY
Reason: ไม่มี LO work ที่อนุญาตให้รันต่อ และต้องผ่าน IM/AP successor chain ก่อนเปิดการวัดใหม่
Instance: 47700074 / no GPU or A2 process observed
Hourly rate / accrued GPU cost: USD 0.575817794/hour from last bound quote / accrued UNKNOWN
Keep-until / destroy condition: Destroy after confirming no Owner-local safe-return activity is running

Session routing:
Recommended next session: IM
Recommended model: GPT-5.6 Sol High
Command before prompt: NONE
Copy-paste prompt: ตอนนี้คุณคือ IM ตาม AGENTS.md อ่าน docs/long_run/A2_PER_ARM_AUTOINDEX_lo_002_001.md แล้วแก้ production A2 executor ให้ Goal 002 รัน retrieval-only โดยไม่เปิด qrels, membership หรือ REP-DEV; rebuild and validate successor provenance artifacts, แล้วเขียน IM result handoff ตาม contract
Owner decision required: Destroy Vast instance 47700074 in the dashboard

Projections:
Obsidian report (`01_Research/obsidian_report/`): UNCHANGED
MLflow (`01_Research/mlflow/`): UNCHANGED

# A2 LO 002-001: prelaunch runtime repair and execution-authority hard stop

- Session mode: `LO`
- Phase/Task: `A2_PER_ARM_AUTOINDEX / A2.1 FROZEN_FIVE_ARM_EXECUTION`
- Source goal: `docs/goal/A2_PER_ARM_AUTOINDEX_goal_002.md`
- Measured authority: `control/armindex/a2/measured-authority/a2-im-audit008-provenance-v2.authority.v2.json`
- Attempt: `a2-im-audit008-provenance-v2`
- Date: `2026-08-15`
- Outcome: `STOPPED_PRELAUNCH_EXECUTOR_AUTHORITY_CONFLICT`
- Routing: `NEEDS_IM`

## Result

LO did not launch a measured candidate after this closeout. No A2 measured
result, candidate evaluation, REP-DEV measurement, Selection exposure, Final
exposure, or canonical metric was created by this session.

The first two production `execute` calls failed closed before a remote
supervisor or worker started. The append-only Owner-local lifecycle ledger is
paused at zero completed candidates and one failed prelaunch attempt, with
`resume_allowed=true`. The post-repair transport check reports zero GPU compute
processes and zero A2 processes.

## Prelaunch Runtime Repair

The aggregate-safe diagnostic isolated `ModuleNotFoundError: pydantic` during
the remote launch-binding import. Under the Owner's explicit LO repair
authorization, LO repaired only that frozen runtime dependency omission.

The repair used the existing Linux/Python 3.11 offline supplement from the
Owner Store. It hash-validated and installed only `annotated-types 0.8.0`,
`pydantic 2.13.4`, `pydantic-core 2.46.4`, `typing-extensions 4.16.0`, and
`typing-inspection 0.4.2`, using offline pip with no dependency resolution or
bytecode compilation. It did not upload model or data bytes, access a protected
input, launch a candidate, or use network package resolution.

Owner-local repair receipt:

```text
../04_Owner_Stores/armindex/a2/a2-ap-audit009-provenance-v2-20260815/outputs/runtime-repair-pydantic.v1.json
receipt_sha256: 3c1244910c2c18d0f0840037ba25d3fad8718e8ef6b67436f3cd6b41ff96fb0e
```

The repair receipt binds the source supplement validation and SHA256SUMS,
every wheel hash, the dedicated remote repair directory, and validated package
versions. Afterwards the safe diagnostic returned
`PASS_REMOTE_LAUNCH_BINDINGS`, and remote transport returned
`PASS_A2_REMOTE_TRANSPORT_CHECK` with GPU/A2 process counts of `0/0`.

## Execution-Authority Conflict

Static inspection of the repository-owned production path found that it cannot
execute the retrieval-only scope authorized by Goal 002. The `execute` CLI
constructs `RemoteExecutor` with the Owner-local manifest, which invokes
`a2_owner_local_engine.evaluate_remote_retrieval_result` after each remote
retrieval result. That function opens the Owner-local qrels and membership,
computes OUT metrics, and emits `rep_dev_measured=true`.

Authority v2 and Goal 002 explicitly set candidate evaluation and REP-DEV
measurement to false. Executing the current command after the runtime repair
would therefore cross a closed scientific and protected-data boundary. LO
stopped before that command and did not create a fresh launch admission for it.

## Required Recovery

IM must repair the production A2 execution path so the current LO goal can
perform only frozen retrieval and aggregate-safe lifecycle evidence without
opening qrels, membership, or REP-DEV metrics. The repair must preserve the
frozen candidate universe, ordering, models, metrics, cost ceiling, TTL policy,
and protected-data boundary.

Because the executor and its execution closure will change, IM must rebuild and
validate the successor bundle/adoption chain. AP must then review the changed
launch-critical surface and issue a replacement measured authority and LO goal
before any measured relaunch. A future LO run must obtain a new provider
observation, binding, and admission within the quote freshness window.

## Provider Disposition

`OWNER_ACTION_DESTROY`: no authorized remote work is active, and the required
IM/AP recovery is not an immediate reuse condition. The executor did not
destroy the instance. In the Vast dashboard, open instance `47700074`, confirm
that no Owner-local safe-return activity is in progress, then select **Destroy**.

The remote attempt root is retained until the Owner completes that provider
action. No safe-return archive was created because no candidate result or
remote measured artifact exists.
