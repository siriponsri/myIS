# Goal Documents

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
