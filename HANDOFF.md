# Owner Handoff / สรุปสำหรับ Owner

อัปเดตจาก canonical records และ worktree ณ 2026-07-30 เอกสารนี้ใช้เพื่อ
orientation เท่านั้น ไม่แทนที่ control files, schemas, manifests, receipts หรือ
measured evidence หากข้อความขัดกันให้ยึดหลักฐานตาม `control/source-of-truth.yaml`

## สถานะปัจจุบัน

- Phase: `P1_CPU_BASELINE`
- Active work: P1 evidence recovery, Integrated Research Control Center และ graph scan
  ที่ Owner อนุมัติแล้ว
- Evidence state ที่หลักฐานรองรับ: `P1_BLOCKED_WITH_EVIDENCE`
- `P2_SCOPE_DEVELOPMENT`: ยังไม่เริ่มและห้ามเริ่มก่อนงานปัจจุบันผ่าน acceptance,
  commit และ push
- `D2_OPEN_FINAL` และ `D3_SUBMIT_RELEASE`: `waiting_owner`; decision ledger ว่างและ
  final split ยังปิด
- Standing authorization: `D1_START_CAMPAIGN` ยัง active
- Execution boundary: reversible, CPU-only, ไม่มี GPU, paid API, network model
  download หรือ experiment ใหม่
- Git: `HEAD` และ local `origin/main` อยู่ที่
  `7a32cdd61be385628760f2be2b67d6c40bb05d25`; worktree ยังไม่ clean และยังไม่มี
  commit/push สำหรับงานปัจจุบัน

## P1 evidence truth

- `control/source-of-truth.yaml` กำหนดให้ run facts ต้องมาจาก canonical manifests
  ร่วมกับ Owner-local store
- `campaigns/scope-autoindex-v1/manifests/` ยังว่าง และยังไม่มี campaign validation
  report จึงยังไม่มี hash-bound four-slot matrix ครบ `R0`/`R0-W` x
  `train`/`selection`
- Aggregate-only receipt
  `campaigns/scope-autoindex-v1/evidence/legacy-p1-receipt.v2.json` มีสถานะ
  `accepted`, stage `train_selection`, 12 metric rows และรายงาน cost `USD 0` แต่
  receipt นี้ไม่ใช่ canonical run manifest และยัง promote เป็น measured fact ไม่ได้
- Session capsule `20260730T180521Z-p1-legacy-certification-v1.json` เป็น
  `agent-observed`; manifest, validation report และ evidence references ยังว่าง
- MLflow registration evidence มี parent 1 และ child 2 records (`R0`, `R0-W`) ใน
  external store แต่ยังไม่ถูก promote เข้า read model และไม่ทำให้ P1 complete
- Checked-in read model v1 แสดง campaign/P1/publication readiness เป็น `blocked` และ
  ไม่มี promoted runs, metrics หรือ evidence แต่ยังมี task/status บางจุดเขียนว่า
  `measured`
- `PLAN.md` และ `control/campaigns/scope-autoindex-v1.yaml` ยังอ้าง
  `P1_CPU_MEASURED_COMPLETE`/`measured` ซึ่งขัดกับหลักฐานข้างต้นและต้องแก้ก่อน
  closeout
- Historical exposure รองรับเพียง
  `active_final_872_global_untouched: not_claimable`; ห้ามอ้างว่า final 872 globally
  untouched

## Integrated Research Control Center

- มี uncommitted implementation สำหรับ read-model v2, schema v2, integrated report
  generator/Obsidian vault และ Dashboard tool controller แล้ว
- การ build และ schema/hash validation ของ read-model v2 ในหน่วยความจำผ่าน โดยยัง
  ให้ state เป็น `P1_BLOCKED_WITH_EVIDENCE` และไม่มี promoted runs/metrics/evidence
- Projection ที่ checked in ยังมีเพียง `projections/read-model/read-model.v1.json`;
  `read-model.v2.json` ยังไม่ได้ sync ขณะที่ report CLI และ generator คาดหวัง v2
- `control/source-of-truth.yaml` ยังชี้ projection contract ไป v1 จึงต้องทำ migration
  ให้สอดคล้องและตรวจ drift ใหม่
- Dashboard routes/UI, MLflow archive/searchable registry, Obsidian sync, shared
  revision binding และ cross-surface consistency ยังไม่ผ่าน acceptance ครบ
- Legacy launchers ทั้งสามมี pending deletions ใน worktree ต้อง restore/คงไว้จนกว่า
  unified launcher จะผ่าน Windows health, security, duplicate-process และ rollback
  tests แล้วจึงลบเฉพาะรายการ obsolete
- ใช้ได้เฉพาะ safe aggregate fixtures สำหรับ integration tests; fixture หรือ UI
  preview ไม่ใช่ measured evidence

## Project intelligence

- Graph plan มี 737 files แบ่งเป็น 65 batches
- Fragment files ครอบคลุม logical batches 1-60 แล้ว; batches 61-65 ยังไม่ทำ
- ผล batch ทั้งหมดต้องผ่าน main-agent audit เทียบ `batches.json` ก่อน merge;
  final graph, layers/tour/fingerprints/meta และ `llm-wiki/` ยังไม่เสร็จ
- เก็บ graph/wiki changes แยกจาก implementation commit

## ผลตรวจล่าสุด

- `uv run --no-sync pytest -q`: FAIL, 72 passed / 5 failed / 1 warning
- จุดที่ fail: Dashboard/read-model tests ยัง expect v1, legacy launcher files หาย,
  validation-message assertion ไม่ตรง และ valid P1 fixture ยังไม่ promote
- `uv run --no-sync myis-report check --repository-root .`: FAIL
  `read_model_missing` เพราะยังไม่มี `projections/read-model/read-model.v2.json`
- `uv run --no-sync python -m py_compile src/myis_research/dashboard/tools.py`: PASS
- Final layout, privacy/security, MLflow doctor/viewer, two-cycle sync/check, launcher
  integration และ Playwright desktop/mobile acceptance ยังไม่ได้ผ่านครบ

## Next automatic action

1. แก้ P1 measured claims ใน `PLAN.md`, campaign และ generated projections ให้ตรงกับ
   evidence state แบบ blocked
2. ทำ read-model v2 migration และ integrate Dashboard, MLflow, Obsidian ให้ใช้ object,
   revision และ hash ชุดเดียวกัน
3. Restore/คง legacy launchers แล้วทำ unified Windows launcher acceptance ก่อนลบของเก่า
4. อ่าน `02_Brain/AGENTS.md` และ `03_Paper/AGENTS.md` ก่อน sync ข้าม repository;
   รักษา Owner-authored files และทำ sync/check สองรอบโดยไม่ drift
5. ทำ graph batches 61-65, audit ทุก fragment, merge/finalize graph และสร้าง wiki
6. รัน acceptance suite ทั้งหมด audit diff แล้ว commit/push เฉพาะไฟล์ที่เกี่ยวข้อง
7. ยืนยัน worktree state และหยุดก่อน P2; Dashboard/review ใดไม่เปิด D2 อัตโนมัติ

## Protected boundary

ห้ามนำ qrels, query IDs, split membership, per-query outcomes, rankings, raw provider
payloads, credentials หรือ protected data เข้า Git, Dashboard, MLflow, Obsidian,
Brain หรือ Paper งานนี้เป็น decision support ไม่ใช่คำแนะนำทางกฎหมาย
