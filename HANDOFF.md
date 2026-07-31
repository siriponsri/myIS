# Owner Handoff / สรุปสำหรับ Owner

อัปเดตจาก canonical records และ implementation acceptance ณ 2026-07-31 เอกสารนี้
ใช้เพื่อ orientation เท่านั้น ไม่แทนที่ control files, schemas, manifests, receipts
หรือ measured evidence หากข้อความขัดกันให้ยึด `control/source-of-truth.yaml`

## สถานะปัจจุบัน

- Phase: `P1_CPU_BASELINE`
- Task: `P1.3`
- Evidence state: `P1_BLOCKED_WITH_EVIDENCE`
- Source implementation commit: `94e979449d11675c57432661b0972d3f32d6bb00`
- `P2_SCOPE_DEVELOPMENT`: ยังไม่เริ่ม
- `D2_OPEN_FINAL` และ `D3_SUBMIT_RELEASE`: `waiting_owner`; final split ยังปิด
- Standing authorization: `D1_START_CAMPAIGN`
- Evidence class ของงานรอบนี้: implementation/projection validation ไม่ใช่ measured
  scientific evidence

## P1 evidence truth

- ยังไม่มี canonical P1 manifest + validation-report matrix ครบ `R0`/`R0-W` x
  `train`/`selection`
- Legacy aggregate receipt คง byte เดิมและมี disposition เป็น
  `historical_invalid_superseded`; ห้าม promote เป็น run, metric, evidence หรือ
  completion claim
- Session `20260730T180521Z-p1-legacy-certification-v1` คงอยู่แบบ append-only แต่
  discovery จัดเป็น `SUPERSEDED` และไม่ surface เป็น latest valid session
- Active read model มี promoted runs `0`, metrics `0`, evidence `0`
- Historical exposure รองรับเพียง
  `active_final_872_global_untouched: not_claimable`

## Integrated Research Control Center

- Dashboard เป็น user-facing start entry point เดียวผ่าน
  `dashboard/open-dashboard.cmd`
- Dashboard มี Overview, Simple/PM boards, Phase/Task detail, timeline, Results,
  Evidence, Governance/RAID, Reports, Tools และ ten-screen Presentation สำหรับ
  Owner/Advisor/Peer
- MLflow เป็น external hash-bound searchable archive; Dashboard เริ่มและเปิด
  read-only viewer on demand โดยฐาน SQLite ไม่เปลี่ยน
- Obsidian reporting vault อยู่ที่ `obsidian_report/` มี 5 Phase masters, 9 Task
  reports, 154 Literature proxies, Research History A-D, Advisor draft lifecycle
  และ 6 Bases
- Dashboard, MLflow projection receipt และ Obsidian manifest ใช้ revision
  `2bb50118006ff0a4ab8c3579bfec3251a8a053c7fb08793ba6ebb5d6d2b86be3`
  กับ model SHA-256
  `267ab7b1d4651440186975f6bef2b95fa391a3bac0d6701f6837f308b4ef3e0b`
- `/api/v1` read routes เป็น migration aliases ที่คืน v2 contract; ไม่มี active
  v1 read-model/schema เป็น source of truth
- Standalone `projections/open-*.cmd` สามไฟล์ถูก archive หลัง unified launcher
  ผ่าน acceptance แล้ว; `projections/run-legacy-p1.cmd` เป็น protected execution
  command ไม่ใช่ UI launcher และไม่ได้ถูกรัน

## ผลตรวจ

- Full tests: `112 passed`, มี 1 existing Starlette deprecation warning
- Layout validator: PASS
- Real report sync/check สองรอบ: PASS, no drift, reuse MLflow run
  `a104ccdf389b43d3b5c15c18c868fa51`
- MLflow doctor: PASS, 5 archive runs, 5 receipts, 56 verified artifacts
- Read-only viewer doctor: PASS, MLflow `3.14.0`
- Obsidian: 190 manifest files, hash/revision/symlink checks PASS;
  `advisor-validate` PASS
- Advisor presented snapshots: `0` ตามข้อเท็จจริง เพราะยังไม่มี meeting snapshot
  จริง; draft/validate/present/correct lifecycle และ tests พร้อมแล้ว
- Windows launcher: health token, malformed port, sequential/concurrent reuse,
  unknown listener preservation, failed-child rollback และ browser-after-health PASS
- Dashboard tools: MLflow start/open/reuse/stop และ exact Obsidian `HOME` open PASS;
  external database SHA-256 คงเดิม
- Browser QA: 1920x1080, 1366x768, 1024x768, 390x844, keyboard, skip link,
  Present/Escape/Print, console/network และ horizontal overflow PASS
- Session capsule audit: PASS, unresolved invalid count `0`
- Acceptance receipt:
  `outputs/audits/dashboard/integrated-dashboard-acceptance-20260731.json`

## Untouched protected surfaces

ไม่ได้เปิดหรือแก้ protected P1 store, `mlflow-p1`, final-872, qrels, query IDs,
split membership, per-query outcomes, rankings, credentials หรือ raw provider
payloads และไม่ได้ใช้ GPU, paid API หรือ network model download

## Next automatic action

หลัง commit/push และยืนยัน clean remote ให้หยุดรอ Owner review ผ่าน Dashboard
การสร้าง measured evidence ครั้งถัดไปต้องเป็น fresh protected Owner-local P1 rerun
ภายใต้ execution envelope เดิม; ห้ามเริ่ม P2, เปิด D2 หรือเขียน D3 อัตโนมัติ

ระบบนี้เป็น decision support ไม่ใช่คำแนะนำทางกฎหมาย
