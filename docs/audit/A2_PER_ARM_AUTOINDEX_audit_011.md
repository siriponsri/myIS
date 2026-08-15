สถานะโครงการ:
Phase: A2_PER_ARM_AUTOINDEX
Task/Sub-stage: A2.1 / successor v3 pre-authority readiness
สถานะสั้น ๆ: AP ยืนยัน v3 closure และสร้าง bundle ใหม่แล้ว แต่ authority วัดผลยังออกไม่ได้จนกว่าจะมี provider binding, admission, manifest, transport และ adoption สด

Publication impact:
เส้นทางนี้รักษา A2 full lifecycle ที่ deterministic และทำให้ REP-DEV evaluation เกิดเฉพาะ Owner-local โดยมี commitment ตรวจสอบได้

Budget:
Phase ceiling: USD 150 (`PLAN.md` / active campaign)
Current Task/Run ceiling: USD 50 (`control/budgets/a2-execution-readiness-v1.json`)
Spent/Accrued: UNKNOWN
Remaining headroom: UNKNOWN
Estimated cost of next action: UNKNOWN (fresh provider quote required)
Next Phase ceiling: NOT_BOUND
Budget status: UNKNOWN_DO_NOT_SPEND

GPU / Vast:
GPU decision: UNKNOWN
Reason: new authenticated observation is required before an instance can be admitted or retained
Instance: NONE
Hourly rate / accrued GPU cost: UNKNOWN
Keep-until / destroy condition: NOT_APPLICABLE

Session routing:
Recommended next session: LO
Recommended model: GPT-5.6 Terra XHigh
Command before prompt: NONE
Copy-paste prompt: `/goal อ่าน docs/goal/A2_PER_ARM_AUTOINDEX_goal_003.md แล้วทำงานตามขั้นตอนทั้งหมด`
Owner decision required: NONE

Projections:
Obsidian report (`01_Research/obsidian_report/`): PENDING
MLflow (`01_Research/mlflow/`): PENDING

# A2 AP Audit 011: v3 successor pre-authority readiness

- Session mode: `AP`
- Phase/Task: `A2_PER_ARM_AUTOINDEX / A2.1 FROZEN_FIVE_ARM_EXECUTION`
- Inputs: audit 010; IM 010-001; commits `dd1999613f4ba62b118bce6b68ce3e11033c1f52`
  and `aecd01a34dd46a636a1a88c082e9e2582aadf8cb`
- Successor attempt: `a2-ap-audit011-v3-full-a2`
- Decision: `READY_FOR_LO_PREAUTHORITY`

## Independent AP findings

The v3 closure preserves authority v2 and Goal 002 as historical failed-
prelaunch lineage. The new implementation fails closed before Owner-local
evaluation under v2, requires a v3 authority for evaluation, keeps remote
transport free of protected evaluator inputs, and binds v3 transport to the
v2 pending-AP commitment. The candidate universe, frozen order and program
hashes, model/data bindings, metrics, strict tie policy, matched-first reserve
lifecycle, ARM-01/02 non-advancement, A3/Selection/Final closure, 84-hour TTL,
40-hour floor, USD 50 Task/Run ceiling, and USD 150 Phase ceiling are unchanged.

The new clean pushed bundle was created from commit
`aecd01a34dd46a636a1a88c082e9e2582aadf8cb` / tree
`2144b32afe9a8a8ddced56c60327910e8be040d0`. Its bundle SHA-256 is
`a5006482f92e8ea535744cd5e44f665e3582d19d91f4d626406d08b89f0fd81c`,
and its receipt self-hash is
`3222119cbf2307c74633739470506e9aa5e465c71cef41b1a6afa0782b9e6ac5`.

## Authority issuance decision

AP does not issue v3 authority in this session. The v3 schema requires a real
fresh `provider_instance_id`, execution-adoption receipt hash, Owner-local
manifest hashes, and transport request hash. Those values do not yet exist,
and fabricating them would defeat the frozen provenance contract. The v2
provider observation/admission/transport/adoption and remote root are stale
and prohibited from reuse.

Goal 003 therefore authorizes the smallest necessary pre-authority sequence:
fresh authenticated observation, binding, admission, safe Owner-local inputs,
isolated stage, non-measured transport/recovery validation, adoption, and
aggregate-safe LO handoff. It does not authorize candidate execution or any
scientific measurement. After that LO closeout, AP must validate the equality
chain, issue tracked authority v3 plus a measured Goal 004, and route LO again
for the actual frozen A2 execution.

## Required AP review after Goal 003

Verify before authority issuance that the fresh provider identity, quote and
TTL meet the active budget; the new root is isolated; process counts are zero;
bundle/adoption/transport/manifest commitments equal; bundle commit is an
ancestor of clean pushed `main`; the full execution closure is unchanged; and
all protected-output checks pass. A failure returns to IM only for an
engineering defect, or stops for a provider/budget fact without measuring.

`READY_FOR_LO_PREAUTHORITY`
