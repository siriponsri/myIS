# A1 Provider Reuse and A2 Data Handoff v16

- Phase: `A1_BASELINES_AND_MULTI_ARM_SCREENING`
- Task: `A1.2`
- Scope: engineering closeout and Owner-local artifact handoff only
- Scientific authority: `false`
- Next phase: `A2_NOT_STARTED`

## เป้าหมาย

หลัง A1.2 ได้ผลครบ `25/25` และ Owner-local evaluation ผ่าน ให้ทำสำเนาข้อมูล
ขั้นต่ำที่ A2 ต้องใช้อ้างอิงไว้ใน Owner-local protected store พร้อม SHA-256 โดย
เก็บ A1 remote root และ artifacts ต้นฉบับไว้บน Vast instance เดิม จากนั้น mirror
เฉพาะ handoff package ที่ผ่าน allowlist กลับไปใต้ A1 remote root เพื่อให้ artifacts
ครบทั้ง local และ Vast การทำ handoff นี้ไม่เปิด A2 และไม่เปลี่ยน frozen v11-v15
scientific semantics

คำว่า **safe-return archive** หมายถึงไฟล์บรรจุผลที่ผ่าน allowlist แล้ว ภายในมี
opaque top-100 rankings และ receipts ที่ไม่มี original identifiers ส่วน
**aggregate receipt** หมายถึงสรุปผลระดับรวมที่ไม่เปิดข้อมูลต่อ query

## สิ่งที่ต้องดึงกลับ

สร้าง Owner-local root แยกตาม attempt เช่น:

```text
04_Owner_Stores/armindex-a2/a1-baseline-safe-return/<ATTEMPT_ID>/
  handoff-manifest.v16.json
  safe-return/safe-return.tar.gz
  aggregate/promotion.json
  aggregate/evaluator-closeout.receipt.v16.json
  aggregate/receipts/<25 aggregate receipts>
```

ต้องคัดลอกแบบ exact bytes และบันทึก relative path, size และ SHA-256 ใน
`handoff-manifest.v16.json` เท่านั้น ห้ามบันทึก absolute personal path ใน Git,
reports หรือ projections

## สิ่งที่ห้ามดึงกลับ

- dense embeddings
- vector indexes หรือ FAISS indexes
- caches และ tensor checkpoints
- raw corpus/query inputs
- logs, environment dumps และ provider payloads
- qrels, membership, original query/family/publication IDs และ per-query outcomes
- model weights ที่ Owner-local model store มี byte/hash เดิมอยู่แล้ว

เหตุผลคือ artifacts กลุ่มนี้ไม่อยู่ใน frozen A1 safe-return allowlist มีขนาดใหญ่
และ candidate ของ A2 อาจต้องสร้าง representation ใหม่ จึงไม่ช่วยลดเวลาวัดอย่าง
น่าเชื่อถือ การรัน dense A2 บน CPU local ไม่ใช่ default เพราะเสี่ยงไม่ทันเวลา;
local CPU ใช้สำหรับ compiler, deterministic AutoIndex kernel, protected
evaluation และ receipts ส่วน embedding/index/search ใช้ GPU ภายใต้ A2 contract ใหม่

## ขั้นตอนปิด A1

1. ยืนยัน cell parity ครบ `25/25` ก่อน `finalize`
2. สร้างและ validate safe-return archive ตาม v11 transfer contract
3. รัน Owner-local evaluator และ evaluator closeout ให้ผ่าน
4. รัน `a1_2_measured_result_summary_v16` เพื่อสร้าง canonical aggregate-safe
   summary ใน Git สำหรับ primary/secondary metrics และ promoted arms โดยไม่มี
   per-query data
5. รัน `a1_2_cell_eda_package_v16` เพื่อสร้าง EDA JSON, CSV, quality/efficiency
   figures แบบ PNG/SVG และรายงานภาษาไทยจาก aggregate receipts ชุดเดียวกัน
6. รัน `a1_2_a2_baseline_handoff_v16` เพื่อสร้าง handoff root แบบ write-once
7. ตรวจว่า baseline manifest มี source files `28` รายการ: archive 1, cell receipts 25,
   promotion 1 และ evaluator closeout 1
8. ตรวจผ่าน SSH ว่า A1 remote worker paths ตาม ledger ยังอยู่ก่อน finalize หรือมี
   lifecycle finalize receipt ยืนยันการ cleanup แล้ว หาก `current/` และ `output/`
   ถูกลบหลัง safe return ห้ามสร้าง directory ปลอมกลับขึ้นมา ให้ยอมรับได้เฉพาะเมื่อ
   safe-return archive/hash ผ่าน, job ledgers ยังคงอยู่, worker process เป็นศูนย์ และ
   frozen bundle/model roots ไม่ drift
9. mirror baseline package `29` files (manifest 1 + source files 28) ไปที่
   `<REMOTE_A1_ROOT>/handoff/a1-baseline/<ATTEMPT_ID>/` แล้วตรวจ size/SHA-256
   จาก remote โดยไม่เปิด payload
10. mirror EDA package `8` files (EDA artifacts 7 + handoff manifest 1) ไปที่
    `<REMOTE_A1_ROOT>/handoff/a1-journal-eda/<ATTEMPT_ID>/` แล้วตรวจ size/SHA-256
11. ทำ fresh provider-continuation validation; ถ้าผ่านบันทึก `REUSE_ELIGIBLE`
12. ปิด A1 ด้วย terminal PASS/current pointer และสร้างรายงาน closeout ภาษาไทย
13. mirror aggregate-safe closeout package `12` files (artifacts 11 + manifest 1)
    ไปที่ `<REMOTE_A1_ROOT>/handoff/a1-closeout/<ATTEMPT_ID>/` โดยรวม summary,
    terminal/pointer, provider-continuation, safe provider/runtime/quote/watchdog
    observations และ manifest pointers ของ baseline/EDA
14. หยุดก่อน A2; การมี handoff ครบไม่ใช่ execution adoption ของ A2

ตัวอย่างคำสั่ง:

```powershell
uv run --no-sync python -m myis_research.armindex.a1_2_a2_baseline_handoff_v16 `
  --repository-root . `
  --safe-return-archive <OWNER_LOCAL_SAFE_RETURN_ARCHIVE> `
  --evaluation-attempt-root <OWNER_LOCAL_EVALUATION_ATTEMPT_ROOT> `
  --output-root <OWNER_LOCAL_A2_BASELINE_HANDOFF_ROOT> `
  --remote-root-label <REMOTE_A1_ATTEMPT_ROOT>
```

## Success criteria

- A1 coverage และ aggregate receipts ครบ `25/25`
- safe-return archive hash ตรงกับ evaluation lineage
- measured-result summary self-hash ผ่าน, metrics มาจาก receipt set เดียว และ
  promoted arms ตรง promotion receipt
- handoff manifest self-hash ผ่านและ `a2_execution_authorized=false`
- forbidden artifact classes ไม่ถูกคัดลอก
- remote A1 root ยังอยู่; measured working paths ต้องคง read-only ก่อน finalize
  หรือมีหลักฐาน post-finalize cleanup ตามข้อ 8; baseline mirror `29/29`, EDA mirror
  `8/8` และ closeout mirror `12/12` files hash ตรง โดยไม่เขียนทับ measured root
- instance ไม่ถูก destroy เพียงเพื่อ closeout
- provider disposition เป็น `REUSE_ELIGIBLE` หรือ `DESTROYED` ตามหลักฐานจริง
- `HARNESS-DEV`, Selection และ Final access counters เป็นศูนย์

## Claim boundary

Handoff นี้รองรับ reproducibility และการส่งต่อ baseline ไป A2 เท่านั้น ไม่ใช่
ผล A2, ไม่อนุญาต candidate generation/measured execution และไม่รองรับ publication
claim จนกว่า A1 terminal receipt และ A2 execution contract/adoption จะผ่าน
