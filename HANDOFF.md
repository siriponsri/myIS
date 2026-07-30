# Owner Handoff

## สถานะปัจจุบัน

- Phase: `P0_FOUNDATION` ปิดในระดับ implementation/fixture
- Task: `P0.3` projection contracts และ migration closure
- Gate: `D2_OPEN_FINAL` ยัง `pending`
- Standing authorization: `D1_START_CAMPAIGN` ถูกบันทึกครั้งเดียวแล้ว
- P1 measured run: ยังไม่เริ่ม เพราะยังไม่มี protected Owner bundle

## ทำเสร็จแล้ว

- `01_Research` เป็น active control plane เดียว และโครงเก่าถูก archive/pointer
- Dashboard อ่านจาก read-model เดียว มี overview, phase/task, evidence และ
  presentation mode พร้อมแยก `ทำแล้ว / ทำต่อ / รอ Owner / รอคำสั่ง`
- MLflow มี bootstrap, external SQLite store, six experiments, lineage tags,
  read-only viewer และ doctor
- Report generator สร้าง read-model, Brain/Obsidian MOC, backlinks และ Paper
  readiness จากข้อมูลชุดเดียว โดยไม่คัดลอกตัวเลข manually
- Brain literature pointers ผ่านแล้ว `U001-U154`; `U154` คือ AutoIndex
  `arXiv:2607.18603`, Tier A
- legacy Dashboard runtime ที่ไม่ได้ใช้ถูกย้ายไป `archive/legacy-cs/runtime`

## Owner ต้องทำต่อ

1. เตรียม `documents.json`, `queries.json`, `qrels.json`, `splits.json` ใน
   protected directory ของ Owner
2. รัน `myis-owner-local` ด้วย request ที่ผูก hash และเก็บ aggregate receipt
3. ตรวจ receipt และสั่งให้ agent ทำ P1 ต่อได้ โดยไม่ส่ง qrels/query IDs ออกมา

ยังไม่ต้องตัดสินใจ `D2_OPEN_FINAL` หรือ `D3_SUBMIT_RELEASE` ตอนนี้ ทั้งสอง
decision จะใช้เมื่อ evidence ของ phase ก่อนหน้าครบเท่านั้น

## ตรวจแล้ว

`uv sync --locked --all-extras`, `pytest` (30 passed), report sync/check สองรอบ,
layout validator, literature validator, MLflow temporary-store doctor/viewer,
session capsule validation, artifact-only rigor review และ `git diff --check`
ผ่านทั้งหมด

ไม่มีการอ่านหรือย้าย qrels, query IDs, split membership, per-query outcomes,
raw provider payloads, GPU หรือ paid API งานนี้เป็น decision support ไม่ใช่
คำแนะนำทางกฎหมาย
