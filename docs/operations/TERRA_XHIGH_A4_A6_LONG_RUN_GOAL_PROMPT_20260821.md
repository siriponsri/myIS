# Terra XHigh `/goal` prompt

คัดลอกข้อความด้านล่างไปเปิด Terra XHigh ได้เลย:

```text
/goal ดำเนิน long run เดียวให้จบ A4 -> A5 -> A6 ตาม protocol myIS Research
โดย Owner อนุญาตให้ rerun A4 บน Vast instance เดิม 47790578 และอนุญาต
conditional D2_OPEN_FINAL ต่อเนื่องอัตโนมัติเมื่อ predicate ผ่านครบ

อ่านก่อนลงมือ:
1) PLAN.md
2) docs/goal/A4_PRODUCTION_TRANSFER_AND_SELECTION_goal_002.md
3) docs/operations/A4_SELECTION_125_OWNER_HANDOFF_20260820.md
4) docs/goal/A5_FINAL_CONFIRMATION_goal_001.md
5) docs/goal/A6_FULL_DAPFAM_MATERIALIZATION_AND_SCALABILITY_goal_001.md
6) control/assets/dapfam-p1-source.v1.json และ A4 readiness binding

ปัญหาปัจจุบัน: A4 เดิมมีเฉพาะ HDEV-100; ไม่มี real Selection-125 handoff,
paired vectors หรือ evaluator handoff. ห้ามใช้ HDEV/REP/fixture/legacy metrics
แทน. ต้องสร้าง Selection-capable runtime ที่ตรวจ exactly 125 และ materialize
query/qrels/membership ใน Owner Store เท่านั้นจาก canonical source + parent split
hash. ถ้า source hash หรือ Arrow-equivalence ตรวจไม่ได้ ให้ fail-closed.

ลำดับงาน:
1. ตรวจ Git, source/split hashes, counters และ Owner Store blocker.
2. ใช้ vastai show instance 47790578 และ fresh authenticated observation,
   all-fee quote, budget, TTL, GPU/disk/process checks. ใช้ fresh A4 attempt ID
   และ fresh remote root ห้าม resume root เก่า. ห้ามสร้าง instance ใหม่เอง.
3. Implement/fix Selection-125 materializer และ runtime โดยคง HDEV-100 path
   เดิมไว้. ทดสอบ focused ก่อน spend. ห้ามส่ง qrels, membership, query IDs,
   rankings หรือ raw payload ไป Git/remote/chat.
4. รัน A4 Selection retrieval จริงบน frozen finalists แล้ว evaluate ใน Owner
   Store. สร้าง handoff ที่
   04_Owner_Stores/armindex/a4/selection-125/<handoff-id>/ โดยมี
   selection_input_sha256, paired_out_vectors_sha256,
   evaluator_handoff_sha256, count 125, population OUT และ vectors ครบ
   recall_at_100/ndcg_at_100/ndcg_at_10 อย่างละ 125 ค่า พร้อม frozen registry
   และ A4 receipts. ตรวจ self-hash, path boundary, disjointness และ protected scan.
5. Consume Selection เพียงครั้งเดียวด้วย scripts/run_a4_selection_owner_local.py
   และเก็บ aggregate-only receipt. selection_accesses ต้องเป็น 1 หลัง consume;
   final_accesses ยัง 0.
6. ตรวจ A4 completeness, safe-return, worker teardown, independent audit,
   exact two finalists, pointer-only A5 bundle, Final-872 hash และ budget reserve.
   เมื่อผ่านครบ ให้ emit append-only PASS_CONDITIONAL_D2_OPEN_FINAL โดยระบุ
   owner_conditional_approval=true. นี่คือการบันทึก Owner-approved D2 ตาม
   preauthorization; ห้าม emit ก่อน predicates และห้ามเปิด Final ก่อน receipt.
7. ทำ A5 ด้วย fresh admission/root บน instance เดิม เปิด Final-872 ครั้งเดียว
   ใช้ exactly two frozen finalists และ fresh evaluator. เก็บ qrels/membership/
   query IDs/per-query outcomes Owner-local. ปิดด้วย PASS_A5_FINAL_CONFIRMATION,
   coverage 872/872, audit และ safe-return.
8. หลัง A5 ผ่านและมี exactly one winner ให้ทำ A6 ด้วย fresh admission/root,
   bind canonical DAPFAM source hash และ materialize full corpus 45,336 rows.
   ห้าม tune, เปลี่ยน winner, reopen Selection/Final หรือ copy raw corpus เข้า Git.
9. ปิด A4/A5/A6, prepare A7 evidence handoff แต่ห้าม D3_SUBMIT_RELEASE.
10. ตรวจ tests, ruff, git diff --check, receipt/self-hashes, HEAD==origin/main
    และ clean worktree; commit + push main.

กติกา recovery: แก้ SSH/package/timeout/OOM/checkpoint ได้ภายใน lineage โดยไม่
เปลี่ยน scientific unit และไม่ผสม partial outputs. Hard-stop เมื่อ hash drift,
protected leak, missing canonical source, duplicate access, Final ก่อน D2,
budget/TTL unknown, finalist mutation หรือ incompatible evidence.

อย่าสร้าง micro-gate หรือขอ Owner ซ้ำสำหรับงาน routine. ปัญหา engineering,
provider transient, retry, staging, dependency, worker restart, timeout,
checkpoint และ path ให้ FIX_FORWARD/REPLAN_INTERNAL แล้วเดิน goal ต่อเอง.
ใช้ BLOCKED_OWNER_ACTION เฉพาะ Owner authority, protected-data, budget/TTL,
scientific binding หรือ evidence-integrity boundary จริงเท่านั้น. Fresh root
ของ A4/A5/A6 และการใช้ instance เดิมเป็นสิ่งที่ goal นี้อนุญาตไว้แล้ว.

จบ goal เฉพาะเมื่อมี terminal receipt ที่ตรวจได้ หรือ fail-closed blocker พร้อม
หลักฐานครบ. รายงานผลเป็นภาษาไทยแบบสั้นแต่มี paths, hashes, counters, tests,
provider disposition และ next action; อย่าขอ Owner ให้ debug งาน routine.
```
