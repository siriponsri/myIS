สถานะโครงการ:
Phase: A2_PER_ARM_AUTOINDEX
Task/Sub-stage: A2.1 / v3 pre-authority closeout review
สถานะสั้น ๆ: LO ได้ fresh admission แต่หยุดก่อน stage เพราะ remote root เป้าหมายมีอยู่ก่อนและ ownership ไม่สามารถพิสูจน์ได้ จึงยังออก authority v3 ไม่ได้

Publication impact:
ไม่มี measured metric หรือ publication claim ใหม่ การหยุดรักษา provenance ของ A2 และป้องกันการปนหลักฐานจาก root ที่ไม่รู้เจ้าของ

Budget:
Phase ceiling: USD 150 (`PLAN.md` / active campaign)
Current Task/Run ceiling: USD 50 (`control/budgets/a2-execution-readiness-v1.json`)
Spent/Accrued: UNKNOWN; no candidate execution occurred
Remaining headroom: UNKNOWN
Estimated cost of next action: ZERO for local orchestration; provider execution remains capped at USD 50
Next Phase ceiling: NOT_BOUND
Budget status: UNKNOWN_DO_NOT_SPEND

GPU / Vast:
GPU decision: KEEP_GPU
Reason: Goal 004 may perform the Owner-authorized exact-root forensic recovery; destroy is the fallback if checks fail
Instance: `47782993` / running at the last authenticated observation; GPU/A2 process counts `0/0`
Hourly rate / accrued GPU cost: projected whole-workload USD `48.836444444444438412` for 84h; accrued UNKNOWN
Keep-until / destroy condition: destroy after Owner confirms no other authorized work or safe-return activity uses this instance

Session routing:
Recommended next session: LO
Recommended model: GPT-5.6 Terra XHigh
Command before prompt: NONE
Copy-paste prompt: `/goal อ่าน docs/goal/A2_PER_ARM_AUTOINDEX_goal_004.md แล้วทำงานตามขั้นตอนทั้งหมดใน one orchestrated session`
Owner decision required: exact-root forensic recovery is authorized; destroy instance `47782993` only if the forensic checks fail
Canonical next-session prompt: `/goal อ่าน docs/goal/A2_PER_ARM_AUTOINDEX_goal_004.md แล้วทำงานตามขั้นตอนทั้งหมดใน one orchestrated session`

Projections:
Obsidian report (`01_Research/obsidian_report/`): OK
MLflow (`01_Research/mlflow/`): OK

# A2 AP Audit 012: unsafe remote-root stop and publication routing

- Session mode: `AP`
- Phase/Task: `A2_PER_ARM_AUTOINDEX / A2.1 FROZEN_FIVE_ARM_EXECUTION`
- Source LO handoff: `docs/long_run/A2_PER_ARM_AUTOINDEX_lo_003_001.md`
- Source goal: `docs/goal/A2_PER_ARM_AUTOINDEX_goal_003.md`
- Attempt: `a2-ap-audit011-v3-full-a2`
- Decision: `OWNER_AUTHORIZE_EXACT_ROOT_RECOVERY_OR_DESTROY_FALLBACK`

## Evidence review

LO's fresh authenticated observation for instance `47782993`, provider binding,
admission, input derivation, and CPU-local deployment package validation passed.
The quote was USD `48.836444444444438412` for the frozen whole workload, with
fresh 84-hour TTL and zero GPU/A2 processes. No candidate retrieval, qrels,
membership, evaluator, REP-DEV measurement, or protected output occurred.

Before stage, the verifier found the exact required target
`/opt/myis/a2-ap-audit011-v3-full-a2` already existed. It recorded only a safe
structural observation (directory, non-symlink, four top-level entries, no
worker processes), did not inspect or modify its contents, and removed only the
separately ownership-checked incoming transfer. This is an unsafe-root stop,
not an executor defect and not evidence that the target belongs to this
attempt.

## Authority and claim decision

Do not issue authority v3 for this attempt. No valid stage receipt, execution
adoption receipt, transport-check receipt, or authority-level transport hash
exists. Goal 002/v2 and all prior provider/root artifacts remain immutable
historical lineage. The exact target root may be inspected only through a
new-owner-authorized forensic recovery action that records structural metadata,
confirms zero workers, and never exposes protected payloads. If and only if the
checks pass, the root may be cleared and adopted by Goal 004 under a new
attempt ID, new stage/adoption/transport receipts, and a fresh v3 authority.

The pre-authority work supports only an operational readiness claim. It supports
no A2 quality, latency, cost, reserve, winner, or publication claim. The
publication-positive action is to preserve this negative boundary finding and
start a genuinely isolated successor only after the provider disposition is
closed.

## Provider disposition and next attempt

The instance is running with no authorized worker and no safe-return activity
remaining. AP therefore routes `OWNER_AUTHORIZE_EXACT_ROOT_RECOVERY_OR_DESTROY_FALLBACK`.
The Owner may authorize a read-only forensic probe followed by clearing only
the exact root `/opt/myis/a2-ap-audit011-v3-full-a2` after the probe proves it is
non-symlink, attempt-unclaimed, and worker-free. The clear must be exact-path,
hash/metadata recorded, and performed under Goal 004's new attempt identity.
The executor must not destroy the instance or clear any other path. If any
check is ambiguous, stop and use the Vast dashboard to select instance
`47782993` and choose **Destroy**.

Goal 004 must create a new attempt ID and receipt chain, rebind the provider,
and obtain a new authenticated observation before any stage. It may use the
cleared exact root only after the forensic receipt proves the clear; otherwise
it must create a clean replacement root or follow the destroy fallback. The old
v3 bundle may be reused only as a code bundle if its closure is unchanged; its
failed attempt/admission/root must not be reused as execution identity.

## Resume versus new goal

Do not resume Goal 003: its lifecycle is `CLOSED` and its attempt identity is
terminal failed-preauthority lineage. Create one Goal 004 that carries the
orchestrator through exact-root recovery (or destroy fallback), fresh
admission, isolated stage, v3 authority binding, measured A2, safe return,
evidence audit, and publication closeout. Keep Goal 003 and this audit as the
negative provenance record; only Goal 004 may write the successor receipts.

`OWNER_AUTHORIZE_EXACT_ROOT_RECOVERY_OR_DESTROY_FALLBACK`
