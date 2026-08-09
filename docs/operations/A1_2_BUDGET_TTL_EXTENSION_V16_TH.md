# A1.2 ขยายงบและ TTL รุ่น v16

สถานะเอกสาร: `OWNER_APPROVED_PENDING_LIVE_PROVIDER`

เอกสารนี้เป็นบันทึกการตัดสินใจแบบ aggregate-safe สำหรับการรัน A1.2 long run
เพียงครั้งเดียว โดยไม่เปิดเผยข้อมูลชุดทดสอบ, query, qrels, ranking, credential
หรือ raw provider payload

## ผลการตัดสินใจ

Owner อนุมัติ policy แบบ additive รุ่น v16 เพื่อให้มีเวลารันครบทั้ง workload และ
มีพื้นที่สำหรับ recovery ที่ไม่เปลี่ยนสมมติฐานทางวิทยาศาสตร์ ค่า canonical อยู่ใน
ไฟล์ [whole-workload-budget-extension.v16.json](../../control/armindex/a1.2/whole-workload-budget-extension.v16.json)
และ schema อยู่ใน [a1.2-whole-workload-budget-extension.v16.json](../../schemas/armindex/a1.2-whole-workload-budget-extension.v16.json)

- เพดาน common screen: USD 27
- เพดานรวม A1: USD 32
- เพดาน campaign: USD 150
- TTL: 40 ชั่วโมง นับจากการ provision instance
- ต้องรับ workload ครบทั้ง 25 program-arm cells; partial-arm admission ไม่อนุญาต
- ต้องใช้ fresh provider identity และ fresh all-fee quote ก่อน admission
- ตอนนี้ provider contact, launch, adoption และ measured execution ยังเป็น `false`
- preparation counters และ measured counters ยังคงเป็นศูนย์

ค่า v15 เดิมยังเป็น historical reference ที่อ่านได้และไม่ถูกเขียนทับ: common
screen USD 18, A1 USD 23, campaign USD 100 และ TTL 20 ชั่วโมง การเปลี่ยนนี้เป็น
policy extension สำหรับการตัดสินใจครั้งปัจจุบันเท่านั้น ไม่ใช่การตีความผลเก่าใหม่

## คำถามทบทวนแบบ Grill

**โจทย์คืออะไร**  ต้องให้ long run มีเวลาพอสำหรับ setup, 25/25 results, safe
return และ exact recovery โดยไม่ลด protected boundary หรือเปลี่ยน scientific
semantics

**ทางเลือกที่พิจารณา**  (1) คงค่าเดิม ซึ่งเสี่ยงหยุดกลางงาน; (2) ขยายเฉพาะ
common screen ซึ่งยังเสี่ยงชน A1 หรือ campaign cap; (3) เพิ่มทั้ง common screen,
A1, campaign และ TTL เป็น revision ใหม่ ซึ่งตรวจสอบและ rollback ทางเอกสารได้ชัดเจน

**เหตุผลที่เลือก**  เลือกข้อ (3) ตาม Owner approval เพราะ whole-workload admission
ต้องผ่านทุกเพดานพร้อมกัน และ TTL ต้องครอบคลุมการทำงานทั้งก้อน ไม่ใช่เฉพาะช่วง
คำนวณผลลัพธ์

**สิ่งที่ยังไม่เปลี่ยน**  split, qrels, query reservation, models, tokenizer,
evaluator, metrics, promotion rule, protected compiler, safe-return contract
และ publication contract ยังคงอ้างอิง v11-v15 เดิม

## สูตรและขอบเขต

ตัวประเมิน v16 ใช้สูตร all-fee เดิม:

`ceil(ttl_seconds / billing_granularity_seconds) * billing_granularity_seconds / 3600 * compute_hourly_rate_usd + storage_fee_usd + network_fee_usd + platform_or_other_fee_usd + tax_or_surcharge_usd`

ตัวประเมินรับเฉพาะ quote ที่ Owner ส่งแบบ sanitized และต้องมี fee fields ครบทุกตัว
จึงไม่ติดต่อ Vast เอง ไม่เก็บ provider identity และไม่ทำให้ policy นี้กลายเป็น
authorization โดยอัตโนมัติ หาก quote เกินอายุ, มี fee หายไป, workload ไม่ครบ หรือ
projected spend เกินเพดาน ให้ผล `BLOCKED_BUDGET`

## ผลต่อ publication impact

งบสำรองนี้ช่วยลดความเสี่ยงที่หลักฐาน A1 จะขาด 25/25 cells หรือ safe-return ไม่ครบ
ซึ่งเป็นประโยชน์ต่อ reproducibility ของบทความ Journal แต่ไม่ใช่หลักฐานว่า method
ดีขึ้น และไม่อนุญาตให้เลือกผลลัพธ์ตาม outcome ระหว่างรัน ผล publication claim ต้อง
รอผลที่ผ่าน evaluator และ phase ถัดไปตามกติกาเดิม

## Glossary

- **All-fee quote**: quote ที่แยก compute, storage, network, platform/other และ tax/surcharge
- **Whole-workload admission**: การคำนวณ worst-case ต้องผ่าน common screen, A1 และ campaign พร้อมกัน
- **TTL**: เวลาสูงสุดที่ instance ใช้ได้ นับจาก provision ไม่ใช่เวลาที่เริ่มวัดผล
- **Safe return**: การส่งกลับเฉพาะ aggregate, hash, count และ pointer ที่ตรวจสอบแล้ว

## การตรวจสอบ

ตัวประเมินและ receipt schema อยู่ที่ [a1_2_whole_workload_budget_extension_v16.py](../../src/myis_research/armindex/a1_2_whole_workload_budget_extension_v16.py)
และ [a1.2-whole-workload-budget-extension-result.v16.json](../../schemas/armindex/a1.2-whole-workload-budget-extension-result.v16.json)
การตรวจที่ต้องผ่านคือ focused v16 tests, scoped Ruff และ `git diff --check`
ก่อนนำ policy ไปผูกกับ provider admission จริง
