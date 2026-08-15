# A2 IM 008-001: non-cyclic provenance and successor launch readiness

- Session mode: `IM`
- Phase/Task: `A2_PER_ARM_AUTOINDEX / A2.1 FROZEN_FIVE_ARM_EXECUTION`
- Source LO handoff: `docs/long_run/A2_PER_ARM_AUTOINDEX_lo_001_001.md`
- Implementation revision: `adbddd5123367798693690961bdd482830dbfd24`
- Successor attempt ID: `a2-im-audit008-provenance-v2`
- Routing: `READY_FOR_AP`

## Outcome

IM repaired the cyclic provenance contract that stopped LO 001 before launch.
Measured authority v1 now fails closed. Authority v2 binds the execution-adoption
receipt, bundle commit, and bundle tree; the bundle commit must be an ancestor of
the clean pushed authority HEAD, and every path in the immutable execution-bundle
closure must be unchanged between those revisions. This allows AP authority and
goal commits after bundle creation without permitting executor, schema, control,
budget, recovery, model, or frozen-candidate drift.

The frozen 52-candidate universe, primary and secondary metrics, model bindings,
ARM-01/02 non-advancement, 60-hour target TTL, 40-hour initial admission floor,
deterministic `53848s` reserve floor, and protected-data boundary are unchanged.
The Owner explicitly expanded only the successor A2 task/run hard stop by USD 10,
from USD 35 to USD 45. The USD 150 campaign ceiling is unchanged. Historical
USD 35 authority/admission artifacts remain read-only lineage and are not reusable.

No provider admission, staging, candidate execution, measured A2, candidate
evaluation, REP-DEV measurement, Selection, Final, model download, or protected
input access occurred in this IM session.

## Changed surface

- authority v2 schema and v1 fail-closed commitment contract;
- bundle-to-authority ancestor and unchanged-closure validation;
- end-to-end adoption commit/tree binding in execute, result, transport, and
  reserve paths;
- current v2 provider admission and reserve hard stop at USD 45, with historical
  USD 35 receipt schema compatibility but current-validator rejection;
- active readiness budget, v2 envelope, v2 readiness contract, runbook, PLAN,
  goal, source-of-truth, and read-model routing;
- regression coverage for authority/adoption commit/tree mismatch, non-ancestor,
  closure drift, v1 supersession, USD 44 admission, USD 45.01 rejection, reserve
  identity, interruption/resume, remote transport, and candidate recovery.

## Focused validation

- A2 readiness and execution-contract suites: `26 passed`.
- Authority, bundle-lineage, and reserve subset: `15 passed`.
- Remote transport and remote candidate suites: `19 passed`.
- Operational executor excluding the isolated interruption test: `38 passed`.
- Isolated interruption/resume test: `1 passed`.
- Ruff on changed Python and test surfaces: `PASS`.
- JSON parse: `7` changed canonical/schema files; YAML parse: `2`; readiness
  budget self-hash: `PASS`.
- `git diff --check`: `PASS`.

The monolithic operational-executor invocation previously exceeded a 360-second
session timeout. The same 39 tests passed when partitioned as 38 plus the isolated
interruption/resume test; there is no assertion failure or uncovered test node.

## Staged execution path

AP can proceed without another IM repair:

1. Review this handoff and LO 001 against implementation revision
   `adbddd5123367798693690961bdd482830dbfd24`.
2. From clean pushed `main`, build a successor immutable bundle/adoption for
   attempt `a2-im-audit008-provenance-v2` using the existing Owner-local assets.
3. Refresh aggregate-safe provider observation and v2 admission for Vast
   instance `47700074`; require 4x RTX 3090 identity, target TTL 60h, at least
   40h remaining, complete all-fee quote no greater than USD 45, process zero,
   pinned SSH/runtime/model/data hashes, and valid management authority.
4. Run only synthetic/non-measured transport, interruption, cancellation,
   reaping, recovery, and safe-return checks.
5. If the successor bundle/adoption passes, write authority v2 and a new current
   LO goal. The bundle commit may precede the authority HEAD only when the full
   execution closure is unchanged.
6. Route directly to LO. Do not start measured work inside AP.

## Claim boundary and limitations

This is launch-critical engineering readiness, not scientific evidence. The
tracked commitment remains scientific authority `false`; AP must still create
the separate authority v2 and current LO goal. Fresh provider observation is
required because GPU cost and TTL continue to change. A fresh quote above USD 45,
less than 40 hours remaining, provider identity drift, process nonzero, closure
drift, or protected-data leakage remains a hard stop. Any further budget increase
requires prior Owner approval.

## Exact AP prompt

```text
ตอนนี้คุณคือ AP ตาม AGENTS.md
อ่าน docs/implementation/A2_PER_ARM_AUTOINDEX_im_008_001.md และ
docs/long_run/A2_PER_ARM_AUTOINDEX_lo_001_001.md แล้วตรวจ launch readiness เฉพาะ
provenance v2, current USD 45 successor budget และ changed surface ให้จบในรอบเดียว
ยืนยันว่า authority v1 fail-closed, bundle commit เป็น ancestor ของ clean pushed
authority HEAD, execution-bundle closure ไม่เปลี่ยน, frozen candidate/metric/model/
TTL/protected-data semantics คงเดิม และ remote recovery tests ผ่าน
จากนั้นใช้ attempt a2-im-audit008-provenance-v2 กับ instance 47700074 และ assets เดิม
refresh fresh aggregate-safe provider observation/admission ภายใต้ target TTL 60h,
initial floor 40h, reserve floor 53848s, USD 45 hard stop และ process-zero; รันเฉพาะ
synthetic/non-measured transport/interruption/cancellation/reaping/recovery checks
ห้ามเริ่ม measured A2/candidate evaluation/REP-DEV measurement
ถ้าผ่านให้สร้าง successor bundle/adoption, authority v2 และ current LO goal แล้ว
แนะนำ LO พร้อม exact /goal prompt โดยไม่ส่งกลับ IM; ถ้ามี paid quote เกิน USD 45
หรือต้องขยาย TTL/budget ให้หยุดและแจ้ง Owner ก่อน
```
