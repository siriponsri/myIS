# Goal Documents

## Current goal registry

| Goal document | Lifecycle | Status | Authorized use |
|---|---|---|---|
| [A2_PER_ARM_AUTOINDEX_goal_003.md](A2_PER_ARM_AUTOINDEX_goal_003.md) | `ACTIVE` | `READY_FOR_PREAUTHORITY_ADMISSION` | Fresh provider admission/staging only; measured execution remains closed |

## Historical goal registry

| Goal document | Lifecycle | Status | Authorized use |
|---|---|---|---|
| [A1_2_goal.md](A1_2_goal.md) | `CLOSED` | `HISTORICAL_SUPERSEDED_BY_A1_2_RERUN_GOAL` | ประวัติ fail-closed ของ r13 เท่านั้น |
| [A1_2_rerun_goal.md](A1_2_rerun_goal.md) | `CLOSED` | `CLOSED_PASS` | หลักฐานส่งต่อ A1.2 r15; ห้าม launch ซ้ำ |
| [A2_official_codex_bridge_goal.md](A2_official_codex_bridge_goal.md) | `CLOSED` | `CLOSED_PASS` | Historical bridge and candidate freeze; preserved for provenance only |
| [A2_PER_ARM_AUTOINDEX_goal_001.md](A2_PER_ARM_AUTOINDEX_goal_001.md) | `CLOSED` | `HISTORICAL_PRELAUNCH_STOP` | Historical cyclic-provenance prelaunch stop |
| [A2_PER_ARM_AUTOINDEX_goal_002.md](A2_PER_ARM_AUTOINDEX_goal_002.md) | `CLOSED` | `HISTORICAL_PRELAUNCH_AUTHORITY_CONTRADICTION` | Historical v2 prelaunch stop; never reuse for execution |

เมื่อ canonical receipt/ledger/checkpoint ยืนยันการปิดงาน ให้แก้ทั้ง frontmatter,
ตารางสถานะรายขั้น และทะเบียนนี้ใน session เดียวกัน ห้ามปิด goal จาก chat หรือ
preview เพียงอย่างเดียว

ทุกไฟล์ active `docs/goal/*_goal.md` เป็นคู่มือปฏิบัติงานแบบ executable สำหรับ long run
ไม่ใช่บันทึกความคืบหน้าหรือแหล่งตัวเลขวิทยาศาสตร์ ให้เริ่มงานด้วยคำสั่งนี้:

```text
/goal อ่าน docs/goal/<ชื่อไฟล์>.md แล้วทำงานตามขั้นตอนทั้งหมด
```

คู่มือ active แต่ละไฟล์ต้องอ่านแล้วทำงานต่อได้โดยไม่ต้องถามซ้ำ โดยต้องมีอย่างน้อย:

1. เป้าหมายเชิง publication และเกณฑ์ความสำเร็จที่ตรวจได้
2. สถานะเริ่มต้น, input/control ที่ freeze, และขอบเขต engineering ที่แก้ได้
3. ขั้นตอน numbered แบบทีละขั้น พร้อม checkpoint หลังช่วงสำคัญ
4. artifact ที่ต้องสร้าง, ตำแหน่งจัดเก็บ, hash/receipt และ validation command
5. recovery ที่อนุญาต, hard stop/fail-closed และข้อมูลที่ห้ามเผยแพร่
6. ขั้นตอน closeout, commit/push, รายงาน terminal และ next action

คำว่า checkpoint ใน goal เป็นจุดตรวจและบันทึกความคืบหน้าเท่านั้น ไม่ใช่
micro-gate ใหม่และไม่เพิ่มอำนาจ launch; การอนุญาตยังยึด canonical controls,
schemas, manifests และ receipts เดิม

กฎการเลือกไฟล์:

- session วางแผนใช้ reasoning สูงสร้างหรือปรับ goal เมื่อ phase/task หรือ
  objective เปลี่ยนอย่างมีสาระ
- session implement อ่าน goal ที่สั่ง, `PLAN.md`, และ control เฉพาะที่จำเป็น
  แล้วทำตาม numbered steps จนจบหรือหยุดตาม hard stop
- ใช้ runbook/ledger และ canonical receipts เป็นหลักฐานถาวร; goal เปลี่ยน
  เฉพาะเมื่อมี decision, blocker, recovery หรือ closeout ที่มีสาระ

active campaign, schemas, manifests, receipts และ protected Owner-local
evidence ยังคงเป็น canonical ห้ามใส่ raw protected data, ranking, qrels,
credentials, token หรือ provider payload ใน goal, Git, report หรือ projection
ไฟล์ที่มี `status: HISTORICAL_SUPERSEDED_*` เป็น redirect/history เท่านั้น
ห้ามใช้ launch และต้องชี้ไปยัง goal active ล่าสุด คู่มือมุ่งหลักฐานที่เพิ่ม publication impact เช่น measured coverage ครบ,
deterministic provenance, aggregate-safe artifacts และ claim boundary ที่ชัด
ไม่ใช่การเพิ่มปริมาณเอกสาร

ทุก goal ต้องมี `lifecycle: ACTIVE | BLOCKED | CLOSED` ใน frontmatter และ goal
ที่กำลังทำต้องมีตารางสถานะขั้นงานใกล้ต้นไฟล์ ใช้สถานะ `COMPLETE`,
`IN_PROGRESS`, `IMPLEMENTED_PENDING_RESULT`, `PENDING` หรือ `BLOCKED` เท่านั้น
อัปเดตจาก canonical receipt/ledger/checkpoint ที่ตรวจแล้ว ไม่ยกสถานะจาก chat,
preview หรือไฟล์ที่เพียงเตรียม implementation ไว้ งานที่ปิดหรือถูก supersede ต้อง
เปลี่ยน `lifecycle` ใน session เดียวกัน ส่วนตัวเลขวิทยาศาสตร์ยังอ้าง canonical
artifact เท่านั้น ห้ามคัดลอกเป็น numeric source of truth ชุดที่สองใน goal
