# Owner Handoff / สรุปสำหรับ Owner

อัปเดตจาก canonical records และ measured evidence ณ 2026-07-31 เอกสารนี้ใช้เพื่อ
orientation เท่านั้น หากขัดกับ control files, schemas, manifests, receipts หรือ
measured evidence ให้ยึด `control/source-of-truth.yaml`

## สถานะตอนนี้

- Phase: `P1_CPU_BASELINE`
- Task: `P1.3`
- Phase status: `complete`
- Evidence state: `P1_CPU_MEASURED_COMPLETE`
- Evidence class: measured train/selection, descriptive only
- Source execution commit: `df9582c94bce5c32a65717b140f66dbe8fea87b2`
- Request: `dapfam-p1-fulltext-c058a3aa7357c782`
- `P2_SCOPE_DEVELOPMENT`: ready, not started
- `D2_OPEN_FINAL` และ `D3_SUBMIT_RELEASE`: `waiting_owner`
- Standing authorization: `D1_START_CAMPAIGN`
- GPU: ไม่ใช้และไม่ต้องเปิด Vast Instance สำหรับงานปิด P1 นี้

## Phase 1 - ผลรวม

Owner-local CPU run เสร็จใน `10835.097` วินาที หรือประมาณ `3.01` ชั่วโมง โดยมี
ค่าใช้จ่าย `$0` และสร้าง evidence matrix ครบ 4 ช่อง:

| Arm | Train | Selection | สถานะ |
|---|---|---|---|
| `R0` | valid | valid | complete |
| `R0-W` | valid | valid | complete |

ขนาดข้อมูล aggregate ที่ตรวจรับแล้ว:

- 45,336 patent families
- 45,336 R0 family documents
- 127,019 R0-W windows
- 250 train queries และ 125 selection queries
- Final 872 ยังปิดและไม่ถูกใช้

Package ภายในมี SHA-256
`b5626b59484f429bcaa13f914ba9b7b3175a2013715d0b10d8f9c1c5638b34b3`
และ package file มี SHA-256
`f505e5d0834cbb41776b084071a7e71e21856aa11d3371e6b0c96db5379b266c`
manifest 4 ไฟล์และ validation report 4 ไฟล์ผ่านครบโดยมี blocker `0`
artifact-only rigor review ได้ `Strong Accept`, mean `4.67`

## Task P1.1 - R0 flat BM25

- สถานะ: `complete`
- วิธี: BM25 หนึ่ง full TAC document ต่อ patent family
- Train OUT Recall@100: `0.076057227485`
- Selection OUT Recall@100: `0.062392548637`
- Evidence: valid train/selection manifests, validation reports และ aggregate receipt

## Task P1.2 - R0-W deterministic window MaxP

- สถานะ: `complete`
- วิธี: non-overlapping 512-token full TAC windows และ family-level MaxP
- Train OUT Recall@100: `0.085847360337`
- Selection OUT Recall@100: `0.074661067156`
- Evidence: valid train/selection manifests, validation reports และ aggregate receipt

Observed delta ของ R0-W เทียบ R0 เท่ากับ `+0.009790132852` บน train/OUT และ
`+0.012268518519` บน selection/OUT ตัวเลขนี้เป็น descriptive development
evidence เท่านั้น ไม่ใช่ statistical superiority, confirmation หรือ final claim

## Task P1.3 - Evidence import และ closeout

- สถานะ: `complete`
- นำ package, receipt, manifests และ validation reports เข้า canonical control plane
- Rigor review ผูก hash กับ package และไม่มี blocking finding
- MLflow ลงทะเบียน parent 1 run และ child 4 runs ใน external governed store
- `protected_artifacts_mirrored=false`; legacy `mlflow-p1` ไม่ถูกแตะ
- Legacy aggregate receipt ยังคง `historical_invalid_superseded` และไม่ถูก promote
- Campaign, read model, Dashboard, Obsidian, Brain และ Paper แสดง P1 measured ตรงกัน

## Progress และ monitoring

- Accepted run รอบนี้เริ่มก่อน progress contract ใหม่ จึงมี aggregate completion กับ
  total latency แต่ไม่มี heartbeat ย้อนหลัง
- Runner ปัจจุบันมี TTY progress bar
- non-TTY mode ส่ง privacy-safe JSON heartbeat ทุก `120` วินาที
- Heartbeat มีเฉพาะ stage, processed/total, elapsed time และ capped ETA
- ห้ามส่ง item identifier, query identifier หรือ outcome รายรายการ
- interval 120 วินาทีเหมาะกับ batch ระดับชั่วโมงและลด CLI polling ที่ไม่จำเป็น

## Projection status

- Shared read-model revision:
  `fa1e4eacaf735fa488214cb9854fe10e91cca84a521dbba34cc56c07da366527`
- Shared read-model SHA-256:
  `513a512b2cba60ff82893c039e678c8553046f44ee6039cee0f1c567e5a38389`
- Obsidian generated manifest: 190 files, manifest SHA-256
  `1f680e29f6c2a0a40e182dd390ea55e52c44334e90a7be350689c3deedecf18b`
- Obsidian แยกรายงาน Phase 1 และ Task P1.1/P1.2/P1.3 พร้อม metric,
  evidence, interpretation boundary และ progress contract
- Brain มี MOC, phase/task status, datasets, experiments, publication readiness,
  weekly summary และรายงาน P0-P4 จาก read model v2 เดียวกัน
- Brain scoped commit: `26dc919`; Brain ไม่มี remote จึงไม่มีปลายทาง push
- Dashboard/API แสดง `P1_CPU_MEASURED_COMPLETE`, 4 runs และ 12 metric rows
- Paper readiness และ publication source lock ชี้ read model v2 และคง
  `train_selection_only`
- Projection sync ล่าสุดใช้ MLflow run `414662ec1d684526b94a95bb003b0e5f`

## ผลตรวจ

- Full tests: `131 passed`, มี 1 Starlette deprecation warning เดิม
- Dashboard/API/launcher focused tests: `19 passed`
- Layout validator: PASS
- Report sync/check: PASS, no drift
- Advisor validation: PASS
- Asset registry quick validation และ P1.3 query: PASS
- Brain literature validation: PASS, U001-U154 มี ID/hash ไม่ซ้ำ
- MLflow doctor: PASS, 13 archive runs, 13 receipts, 152 safe artifacts
- Session capsule audit ก่อนเพิ่ม closeout capsule: PASS, unresolved invalid `0`
- Git diff check จะรันซ้ำก่อน commit

## ไฟล์และระบบที่เปลี่ยน

- Canonical campaign status, fresh P1 request/receipt/package/manifests/validation reports
- P1 adapter, deterministic kernel binding และ reusable progress reporter
- Read-model builder, report generator และ projection identity fingerprint
- MLflow registration/aggregate archive index
- Dashboard regression assertion และ projection/progress/P1 tests
- Obsidian Phase/Task/Result/Advisor/Literature projection set
- Brain generated reports และ active-context pointer
- Paper readiness, source lock และ GEPA project-context boundary
- `PLAN.md`, `README.md` และ `HANDOFF.md`

## ขอบเขตที่ยังไม่แตะ

ไม่ได้เปิดหรือคัดลอก final-872, protected qrels, split membership, query IDs,
per-query outcomes, rankings payload, credentials หรือ raw provider payloads เข้า Git,
Brain, MLflow, Dashboard, Obsidian หรือ Paper และไม่ได้ใช้ GPU, paid API,
network model download หรือ provider fallback

ไฟล์ Owner-local ต่อไปนี้ไม่ถูกแตะและจะไม่ถูก stage:

- `obsidian_report/.obsidian/graph.json`
- `obsidian_report/Untitled.canvas`

## สิ่งที่ Owner ต้องทำ

ไม่มี Owner decision ที่ต้องให้เพื่อปิด P1 งานนี้จะ commit/push และตรวจ CI ให้จบก่อนหยุด
Owner สามารถเปิด `dashboard/open-dashboard.cmd` เพื่อตรวจผลและ evidence chain

## Next automatic action

หลัง commit/push และ CI ผ่าน ให้หยุดรอ Owner review `P2_SCOPE_DEVELOPMENT` พร้อมเริ่ม
แต่ยังไม่เริ่มอัตโนมัติ เพราะ execution envelope ปัจจุบันอนุญาตถึง P1 เท่านั้น
การเริ่ม P2 ต้องเป็นงานแยกที่กำหนด execution policy แบบ reversible, CPU-first และยังไม่เปิด
`D2_OPEN_FINAL` ส่วน `D3_SUBMIT_RELEASE` ยังคงปิดจนถึง Phase 4

ระบบนี้เป็น decision support ไม่ใช่คำแนะนำทางกฎหมาย
