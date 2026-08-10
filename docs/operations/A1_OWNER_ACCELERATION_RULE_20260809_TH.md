---
title: "Owner acceleration rule for A1 long-run"
status: active
owner_decision: "OWNER_A1_LONG_RUN_ACCELERATION_20260809"
phase: A1_BASELINES_AND_MULTI_ARM_SCREENING
task: A1.2
evidence_class: governance_decision
scientific_authority: false
claim_boundary: "This note authorizes execution workflow acceleration; it is not a retrieval result or publication claim."
---

# กติกาเร่งงาน A1 ระยะยาว

## เป้าหมาย

เหลือเวลา 7 วัน Owner อนุญาตให้ทีมปิด `A1/A1.2` ด้วย long run เดียวที่ต่อเนื่อง
ตั้งแต่ admission ไปจนถึง safe return, evaluation, closeout และ provider
destruction โดยยังหยุดก่อน `A2` และไม่เปิด `HARNESS-DEV`, `Selection` หรือ `Final`.

## สิ่งที่แก้ได้

- executor, launcher, SSH coordinator, checkpoint, safe-return, evaluator,
  integration tests และรายงาน
- การนำ executor หรือ artifact ที่ตรวจ hash แล้วกลับมาใช้
- การแก้ bug ที่ทำให้ runner รันจริงไม่ได้
- การจัดลำดับงานให้ขนานกัน และลดการตรวจซ้ำที่ใช้หลักฐานเดิม

ทุกการแก้ต้องเป็น additive หรือเป็นการซ่อม engineering path เท่านั้น ต้องไม่
แก้ model weights, split, tokenizer, P02-FIRST-CLAIM, dense-overflow policy,
metrics, evaluator semantics, candidate rule หรือ promotion rule ของ v11-v15.

## Critical checks ที่ยังห้ามลด

1. instance/provider/SSH identity ต้องตรงกับ instance ใหม่ที่ fresh admission
   bind ไว้และ fingerprint ที่ pin สำหรับ attempt นั้น; instance `47256937`
   เป็น r13 ที่ถูกทำลายแล้วและห้าม reuse
2. runtime ต้องเป็น linux/amd64, Python 3.11, Torch 2.6.0+cu118 และ 4x RTX 3090
3. live all-fee quote และ whole-workload budget ต้องอยู่ใน active v16 limits:
   common screen `$27`, A1 `$32`, campaign `$150`; historical v15
   `$18/$23/$100` เป็นข้อมูลอ้างอิงเดิมเท่านั้น
4. watchdog/TTL ต้องผ่าน โดย active v16 TTL คือ `40` ชั่วโมง และความสามารถทำลาย instance ต้องพร้อมก่อนเริ่มวัด
5. protected boundary ต้องไม่รั่ว และ Git/report/Brain/MLflow รับเฉพาะ aggregate-safe data
6. ต้องได้ผลครบ `25/25`; 20/25 หรือ 24/25 ไม่ถือว่าปิด A1
7. safe return, hash validation, deterministic replay และ teardown ต้องผ่าน

## วิธีลดเวลา

ตรวจซ้ำเฉพาะเมื่อ hash, attempt, provider identity หรือ runtime state เปลี่ยน
การตรวจที่มี receipt เดิมและยังสดให้ reuse pointer/hash ได้ ไม่ต้องรันซ้ำทั้งชุด
แต่ต้องบันทึกว่า reuse หลักฐานใดและเหตุใดจึงยัง valid ใน ledger.

## กรอบคิดแบบ grill-with-docs

**คำถาม 1: งานนี้จะสำเร็จเมื่อใด?** เมื่อมี aggregate-safe A1 closeout receipt,
ผล 25/25, frozen promotion และ instance ถูกทำลายพร้อมหลักฐาน endpoint unreachable.

**คำถาม 2: อะไรคือความเสี่ยงสูงสุด?** input artifact ขาด, topology ผิด,
งบ/TTL หมด, safe-return ไม่ครบ หรือ hash drift. สิ่งเหล่านี้หยุดงานทันที.

**คำถาม 3: อะไรไม่ใช่เหตุผลให้ซ่อม outcome?** metric ต่ำหรือ arm ไม่ชนะไม่ใช่
เหตุผลให้เปลี่ยน semantics, model, split หรือ rule. เก็บผลตามจริงและใช้ rule frozen.

**คำถาม 4: สิ่งใดส่งออกได้?** เฉพาะ counts, metric aggregates, hashes และ
repository-relative pointers. ห้ามส่ง qrels, membership, query IDs, rankings,
per-query outcomes, credentials หรือ raw provider payload.

## Owner action

Owner ดูแล Vast lifecycle และต้อง destroy instance ที่ admission bind ไว้ที่ A1
closeout gate หลัง Codex ยืนยัน safe return และรายงานพร้อมแล้ว. ถ้า budget/TTL
หรือ identity ไม่ปลอดภัย ให้หยุด, เก็บ aggregate-safe evidence และปิด instance.

## External skill sources

- Karpathy guidelines: <https://github.com/multica-ai/andrej-karpathy-skills/blob/main/skills/karpathy-guidelines/SKILL.md>
- Grill with docs: <https://github.com/mattpocock/skills/tree/main/skills/engineering/grill-with-docs>

ทั้งสอง skill ถูกอ่านจาก source ล่าสุดใน session นี้; catalog ในเครื่องยังไม่มี
ชื่อดังกล่าว จึงบันทึกคำถาม/คำตอบและ ADR/glossary เทียบเท่าไว้ในเอกสารนี้.
