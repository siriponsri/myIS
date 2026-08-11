---
managed_by: myis-a1.2-thai-closeout-v16
edit_policy: generated_do_not_edit
status: completed
evidence_class: measured_development_aggregate
scientific_authority: true
attempt_id: a12-v16-20260811-r15
source_summary_sha256: a765de9a6cede2aff10510e909551fc880c982924632dc44a11279f35e4efb2f
source_terminal_sha256: efd836c775b9bfabeadeb6d22c37cc16bfc3790d43d389ad1d277169a52b7bb7
---

# รายงานปิด A1.2 ภาษาไทย

เอกสารนี้สร้างอัตโนมัติจาก receipt ที่ผ่านการตรวจสอบแล้ว ห้ามแก้ตัวเลขด้วยมือ
เพราะ canonical JSON เป็นแหล่งตัวเลขเพียงแห่งเดียว

## สรุปสำหรับ Owner

- สถานะ A1 / A1.2: `COMPLETE` / `PASS 25/25`
- ค่าใช้จ่ายของ A1 attempt นี้: `$11.161632`
- สถานะ instance หลังปิด A1: `REUSE_ELIGIBLE`
- Arms ที่ผ่าน frozen promotion rule: `ARM-03, ARM-05, ARM-04`
- A2, HARNESS-DEV, Selection และ Final: ยังไม่เริ่ม

## Metric ที่วัดได้

Primary metric คือ `OUT Recall@100` หมายถึงสัดส่วน family ที่เกี่ยวข้องซึ่งพบภายใน 100 อันดับแรก
Secondary metrics คือ `OUT nDCG@100` และ `OUT nDCG@10` ซึ่งสะท้อนคุณภาพการจัดลำดับผลลัพธ์
ค่าด้านล่างเป็นค่าเฉลี่ยจาก common programs 5 แบบต่อ arm ส่วน wall time เป็นผลรวมของทั้ง 5 programs

| Arm | OUT Recall@100 | OUT nDCG@100 | OUT nDCG@10 | Search p95 ms | Wall seconds |
|---|---:|---:|---:|---:|---:|
| ARM-01 | 0.191200 | 0.172717 | 0.160011 | 441.520 | 762.533 |
| ARM-02 | 0.269933 | 0.231377 | 0.198497 | 235.203 | 19847.315 |
| ARM-03 | 0.413400 | 0.347812 | 0.289856 | 212.062 | 29444.640 |
| ARM-04 | 0.340667 | 0.284546 | 0.235538 | 214.207 | 15878.488 |
| ARM-05 | 0.363733 | 0.307930 | 0.256706 | 217.099 | 40309.513 |

## การตีความที่อนุญาต

ผลนี้ใช้เปรียบเทียบ retriever arms บน REP-DEV ภายใต้ frozen A1 contract ได้
และใช้กำหนด promoted-arm set สำหรับเตรียม A2 เท่านั้น ยังไม่ใช่ผลยืนยันบน Final split
ผลนี้ไม่ใช่ข้อสรุปด้าน novelty, validity, infringement หรือ freedom to operate ทางกฎหมาย

## หลักฐาน

- Measured summary: `campaigns/armindex-multiretriever-v2/evidence/a1.2-result-summaries/a12-v16-20260811-r15.summary.v16.json`
- Terminal receipt: `campaigns/armindex-multiretriever-v2/evidence/a1.2-terminal-attempts/a12-v16-20260811-r15.receipt.v16.json`
- Current pointer: `campaigns/armindex-multiretriever-v2/evidence/a1.2-current-attempt.v16.json`

## ขั้นตอนถัดไป

หยุดก่อน A2 งาน A2 ต้องผ่าน entry preflight, fresh provider admission และ fresh execution adoption
รวมทั้งใช้ remote root ใหม่ที่แยกจาก A1 โดยยังเก็บ A1 artifacts เดิมไว้แบบ read-only
