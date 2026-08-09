# A1.2 r8: ซ่อมการส่ง token IDs ให้ตรงกับแผนที่ freeze ไว้

## สรุปสำหรับ Owner

งาน A1.2 ยัง **ไม่เริ่ม measured retrieval** และยังไม่มีผลทดลองใหม่ ปัญหาของ
attempt r8 อยู่ที่การแยกข้อความยาวเป็นหลาย window: tokenizer จริงบางชนิดไม่สามารถ
แปลง token IDs ของ window กลับเป็นข้อความ แล้วแปลงข้อความกลับเป็น token IDs เดิมได้
เสมอ โดยเฉพาะเมื่อ window เริ่มกลางบริบทของ BPE/SentencePiece

การแก้ไขเก็บ token IDs ที่ compiler วางแผนไว้ในหน่วยความจำ Owner-local แล้วส่ง IDs
ชุดเดิมเข้า frozen SentenceTransformer โดยตรง จึงไม่ต้องใช้ข้อความที่ decode แล้วเป็น
ตัวกลางสำหรับการ encode อีกต่อไป

## สิ่งที่คงเดิม

- โปรแกรม 5 โปรแกรม, 5 arms, REP-DEV, P02-FIRST-CLAIM และกติกา promote
- dense-overflow policy: window ไม่ overlap, ไม่มี token หาย, และใช้
  source-token-count-weighted mean ตามเดิม
- model, tokenizer, precision, pooling, normalization, evaluator, metric และ split
- protected-data boundary: ไม่ส่งข้อความต้นฉบับ, query ID, qrels, ranking หรือ credential
  เข้า Git หรือรายงาน

## หลักฐานการทดสอบ

ทดสอบเฉพาะ synthetic input บน Vast instance เดิม โดยไม่ค้นคืนข้อมูลและไม่สร้าง result
receipt ของ A1:

- ARM-02, ARM-04, ARM-05: ส่ง exact token IDs ผ่าน model path ได้ และ embedding มีค่าปกติ
- ARM-03: ทดสอบ overflow จริงแบบ synthetic ได้ 5 windows, ทุก window ไม่เกิน 512 tokens,
  vector มี dimension 1024 และ L2 norm เท่ากับ 1.0

หลักฐานแบบ aggregate-safe อยู่ที่
`outputs/audits/rigor/a1.2-v16-exact-token-id-adapter-probe-20260809.json`.

## สถานะและขั้นตอนถัดไป

สถานะยังเป็น pre-measurement. ขั้นตอนต่อไปคือ hash-bind การแก้ไขนี้ใน clean commit,
สร้าง bundle ใหม่, แล้ว re-run provider admission และ execution adoption บน instance เดิม
ก่อน retry frozen 25/25 common screen. ยังห้ามเข้า A2, HARNESS-DEV, Selection และ Final.
