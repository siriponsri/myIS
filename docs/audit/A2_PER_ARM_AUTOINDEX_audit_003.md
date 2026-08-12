# A2 AP Audit 003: measured adapter and reserve lifecycle

- Session mode: `AP`
- Phase: `A2_PER_ARM_AUTOINDEX`
- Task: `A2.1 / FROZEN_FIVE_ARM_EXECUTION`
- Source IM handoff: `docs/implementation/A2_PER_ARM_AUTOINDEX_im_002_001.md`
- Reviewed revision: `1eb6e8c7d36a8f62554b0dfd2d66cb5ea96fb389`
- Owner decisions: A2 TTL target `48h`, forward hard stop `USD 35`, and exceptional AP staging approved
- Routing: `NEEDS_IM`
- Date: `2026-08-12`

## วัตถุประสงค์

ปิด launch-critical gap สุดท้ายก่อน AP ทำ fresh admission/staging และเปิด measured LO:
ต้องมี production A2 candidate adapter ที่วัด frozen representation programs จริง และต้องมี
two-stage matched/reserve lifecycle ที่ตัดสิน batch ที่สามจาก frozen predicate โดยไม่เลือก reserve
ก่อนเห็นผล matched สอง batch.

## หลักฐานที่ตรวจ

- `PLAN.md`, `HANDOFF.md`, `control/source-of-truth.yaml`
- `docs/implementation/A2_PER_ARM_AUTOINDEX_im_002_001.md`
- frozen manifest/receipt/lock และ active A2 readiness controls
- `src/myis_research/armindex/a2_operational_executor.py`
- `src/myis_research/armindex/a2_execution_readiness.py`
- `src/myis_research/armindex/compiler.py`
- `src/myis_research/armindex/autoindex.py`
- A1 v16 measured runner/materializer และ focused A2 tests
- `vast-ssh.md` เฉพาะ aggregate-safe identity/lifecycle fields

## Findings ที่มีผลต่อ launch

1. **Critical - production A2 adapter ยังไม่มี:** `a2_operational_executor execute`
   ต้องรับ `--command-argv-json`, แต่ repository ไม่มี concrete command ที่ compile frozen A2
   program กับ Owner-local DAPFAM inputs, เรียก frozen ARM-01..05 retrievers/evaluator และคืน
   `myis.armindex-a2-external-candidate-result.v1`. `armindex/compiler.py` ประกาศชัดว่าเป็น
   fixture-only และไม่ resolve model adapters. A1 v16 runner รับเฉพาะ common program IDs เดิม;
   การนำมาใช้กับ 52 A2 programs โดยตรงจึงเปลี่ยน scientific unit.
2. **Critical - reserve authority ถูกกำหนดเร็วเกินไป:** measured authority ระบุ
   `active_reserve_candidate_ids` ก่อน `execute` และ executor เดิน candidate universe รอบเดียว.
   Frozen rule ต้องครบ matched สอง batches แล้วจึงตรวจ strict primary improvement,
   grounded axis remaining และ fresh budget admission. Authority ที่ activate reserve ตั้งแต่ต้น
   จึง outcome-independent ผิดกติกา; authority ที่ไม่ activate จะเขียน dormant receipts แล้วปิด
   exact-52 coverage ก่อนมีโอกาสรัน reserve.
3. Provider provenance, absolute TTL, live SSH probe, watchdog และ adoption hardening จาก audit
   002 ผ่าน focused validation แล้ว. Owner อนุมัติ target TTL 48 ชั่วโมงภายใต้ USD 35 และอนุญาต
   AP stage เป็นกรณีพิเศษ แต่ staging ตอนนี้จะ bind bundle ที่ยังขาดสองส่วนข้างต้นและต้องทิ้งหลัง
   implementation เปลี่ยน จึงยังไม่สร้าง remote A2 root และไม่ใช้ TTL กับ bundle ที่ไม่พร้อมวัด.

## งาน implementation ที่ขอ

1. เพิ่ม production A2 candidate adapter/CLI ที่ reuse frozen A1 v16 runtime, model roots,
   protected materialization/evaluator boundary และ aggregate-safe output โดยรองรับ representation
   program schema จริง: field selection/order/labels, unitization, normalization, duplicate policy และ
   family aggregation. ห้ามใช้ fixture compiler เป็น measured authority และห้ามเปลี่ยน retriever,
   model, query view, REP-DEV membership/qrels, metric หรือ tie policy.
2. ให้ adapter รับ candidate identity/program hash จาก allowlisted environment, ตรวจ program bytes
   กับ frozen manifest, ใช้ Owner-local input paths เท่านั้น และคืน exact external-result schema
   โดย stdout มี JSON object เดียว; verbose/protected logs อยู่ Owner-local และไม่เข้า Git.
3. ทำ matched-first orchestration: รัน 40 matched candidates แบบ resume-safe, สร้าง aggregate-only
   per-arm batch evidence และเรียก deterministic `advance_autoindex()`/`strict_primary_improvement()`
   ตาม batch order ที่ freeze. `grounded_axes_remaining` ต้อง derive จาก frozen remaining reserve
   batch ไม่ใช่ caller boolean ที่เดาเอง; fresh budget admission ต้องยัง valid ที่ checkpoint.
4. เพิ่ม hash-bound reserve-activation decision receipt/schema. จากผล matched สอง batch ให้ activate
   ทั้ง 4 reserve IDs ของ arm เฉพาะเมื่อ predicate ผ่าน; arm อื่นต้องมี dormant receipts. รองรับ
   authority continuation/update หลัง checkpoint โดย preserve attempt/adoption/freeze identity และ
   ห้าม rerun completed matched candidates.
5. ทำ concrete `command-argv-json`, Owner-local input manifest contract, remote launch/resume,
   safe-return และ closeout commands ให้ LO เรียกได้โดยไม่เดา path. Bundle closure ต้องรวม code/schema/
   runbook ใหม่ทั้งหมด.
6. เพิ่ม failure-injection tests อย่างน้อย: program/hash drift, fixture adapter rejection, protected
   output, matched interruption/resume, tie/no improvement, no grounded axis, stale budget at reserve
   checkpoint, partial reserve batch, authority continuation drift และ exact 52 accounting.
7. อัปเดต runbook/goal wording ให้ TTL หมายถึง `>=40h remaining`; Owner-approved target คือ 48h.
   ห้าม provider login/logout, destroy/reprovision, remote staging หรือ measured executionใน IM.
8. Commit/push บน `main`, archive tip ก่อนลบ branch หากมี และจบด้วย `main == origin/main`,
   worktree clean. สร้าง clean Owner-local bundle หลัง final commit เพื่อให้ AP stage ได้ทันที.

## ขอบเขตที่ห้ามเปลี่ยน

- manifest/freeze receipt/lock และ candidate bytes ทั้ง 52
- primary metric `recall_at_100/out`, secondary/operational metric semantics และ strict tie rejection
- ARM-01/02 diagnostic non-advancement; primary arm order `ARM-03`, `ARM-05`, `ARM-04`
- REP-DEV/HARNESS-DEV/Selection/Final membership, qrels, query IDs และ per-query outcomes
- model/runtime/data/evaluator bindings, USD 35 forward hard stop, D2/D3 และ A1 evidence/root

## Validation ขั้นต่ำ

```powershell
uv run --no-sync pytest -q tests/test_armindex_a2_candidate_freeze.py tests/test_armindex_a2_execution_contracts.py tests/test_armindex_a2_execution_readiness.py tests/test_armindex_a2_operational_executor.py <new A2 adapter/reserve tests>
uv run --no-sync ruff check <changed A2 source and tests>
uv run --no-sync python -m myis_research.armindex.a2_entry_preflight_v16 --repository-root .
uv run --no-sync python -m myis_research.armindex.a2_operational_executor --repository-root . --attempt-id a2-im-audit003-dryrun --dry-run
uv run --no-sync myis-assets validate --mode quick
uv run --no-sync myis-report check --repository-root .
git diff --check
```

## ผลส่งกลับที่คาดหวัง

เขียน `docs/implementation/A2_PER_ARM_AUTOINDEX_im_003_001.md` พร้อม final revision,
changed surface, concrete measured command, Owner-local input contract, matched/reserve state machine,
focused checks, final bundle path/hash และข้อจำกัดที่เหลือ. กลับ `READY_FOR_AP_STAGING` เมื่อไม่มี
launch-critical gap; measured A2, provider contact และ protected-data accessต้องยังไม่เริ่ม.
