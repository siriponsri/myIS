# A2 IM 003-001: production adapter and matched-first reserve

- Session mode: `IM`
- Phase/Task: `A2_PER_ARM_AUTOINDEX / A2.1 FROZEN_FIVE_ARM_EXECUTION`
- Source audit: `docs/audit/A2_PER_ARM_AUTOINDEX_audit_003.md`
- Base implementation commit: `9973d89281c67d85573759ccad75a85da886bdd2`
- Hardened implementation commit: `f2674e3e44ade4521fd1b61877e20211bd5b4406`
- Routing: `READY_FOR_AP_STAGING`

## สรุปงาน

ปิดช่องว่างของ audit 003 ครบในขอบเขต implementation โดยเพิ่ม production A2
adapter/engine ที่ compile frozen representation program จริงทั้ง 52 รายการ และ
reuse binding ของ A1 v16 สำหรับ runtime, model, data และ evaluator โดยไม่ใช้
fixture compiler เป็น measured authority.

Owner-local input ต้องผูก canonical A1 v16 incumbents, REP-DEV handoff และ
artifact commitments, dense-model file manifests/locks, Python 3.11/PyTorch/CUDA
identity, CUDA map `ARM-02..05 = cuda:0..3`, engine code และ exact interpreter.
ผลที่ออกจาก engine เป็น aggregate-safe object เดียว มี measured REP-DEV labels,
nearest-rank search p95 และ charged dense cost จากอัตรา instance/wall time.

Lifecycle รัน 40 matched candidates ก่อนเสมอและ resume เฉพาะ receipt ที่ผูกกับ
attempt/adoption/authority ปัจจุบัน จากนั้นจึงสร้าง per-arm batch evidence,
ใช้ canonical A1 incumbent กับ deterministic `advance_autoindex()`, derive
grounded reserve axes จาก frozen quartet และออก decision/continuation ที่ hash-bound.
แต่ละ primary arm จบด้วย active quartet หรือ dormant quartet เท่านั้น. คำสั่ง
`reserve-admit` สร้าง fresh checkpoint admission ใหม่จาก provider observation และ
source artifacts ที่ตรวจสอบได้ พร้อมคำนวณ TTL จาก absolute deadline และคง hard stop
USD 35.

Bundle closure รวม transitive package/runtime/schema dependencies และมี isolated
extraction/import regression เพื่อพิสูจน์ว่า adapter/engine ไม่ fallback กลับมาใช้
source checkout. Tracked command ใช้ `{python_executable}` และ
`{repository_root}` ที่ validate แล้ว ไม่ใช้ literal `python` หรือ `.`.

## Changed surface

- A2 measured adapter, Owner-local engine, program runtime และ operational executor
- candidate-result, Owner-local input และ reserve-budget schemas
- tracked measured argv และ A2 execution runbook
- execution bundle closure และ focused failure-injection tests
- `PLAN.md`, `HANDOFF.md` และ synchronized aggregate-safe report projections

Frozen candidate manifest/receipt/lock, candidate bytesทั้ง 52, metrics/tie policy,
ARM-01/02 non-advancement, protected boundary, A1 evidence และ USD 35 budget/envelope
ไม่เปลี่ยน.

## Focused checks

- Focused A2 audit suite: `64 passed`
- Ruff on changed A2 source/tests: `PASS`
- Isolated bundle extraction/import: `PASS`
- A2 entry preflight: `PASS_A2_ENTRY_PREFLIGHT`
- Synthetic operational dry-run: `PASS_A2_SYNTHETIC_OPERATIONAL_DRY_RUN`, 52/52,
  `measured_a2_started=false`, `provider_contacted=false`
- `myis-assets validate --mode quick`: `PASS`
- Report sync/check before implementation commit: `PASS`, drift `false`
- `git diff --check`: `PASS`

หลัง commit implementation report check จะเห็น source-commit drift ตาม expected
เพราะ projection บันทึก commit ก่อนหน้า; ไม่ sync/commit ซ้ำเพื่อหลีกเลี่ยงวงจร
commit-identity. AP ควรใช้ canonical facts และ external bundle receipt ด้านล่าง.

## Bundle and staging state

IM ไม่ติดต่อ provider, ไม่สร้าง remote root, ไม่ stage, ไม่เปิด protected data และ
ไม่เริ่ม measured A2. หลัง final handoff commit/push จะสร้าง clean Owner-local bundle
ไว้นอก repository. External receipt ที่อยู่คู่กับ bundle เป็น authority สำหรับ
`git_commit`, `git_tree`, `bundle_sha256`, `bundle_manifest_sha256` และ
`receipt_sha256`; ไม่บันทึก hash เหล่านี้กลับเข้า Git เพื่อไม่ให้เกิด hash cycle.

AP ขั้นถัดไปตรวจ external bundle receipt จาก final pushed HEAD แล้วทำ fresh provider
admission และ isolated staging เท่านั้น. Measured execution ต้องรอ separate LO goal
และ tracked measured authority.
