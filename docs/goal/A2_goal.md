---
title: "A2 goal: Per-arm AutoIndex เพื่อเพิ่ม publication impact"
phase_id: A2_PER_ARM_AUTOINDEX
status: BLOCKED_UNTIL_A1_CLOSEOUT
evidence_class: planning_handoff_only
scientific_authority: false
claim_boundary: "คู่มือ A2 เท่านั้น ยังไม่ใช่ผลการทดลอง และไม่เปิด execution จน A1 closeout receipt ผ่าน"
last_material_update: 2026-08-10
next_authorized_action: VERIFY_A1_CLOSEOUT_THEN_BIND_A2_CONTRACT
---

# A2: Per-arm AutoIndex long-run guide

เริ่มเมื่อ Owner สั่ง:

```text
/goal อ่าน docs/goal/A2_goal.md แล้วทำงานตามขั้นตอนทั้งหมด
```

เอกสารนี้ทำเฉพาะ A2 `A2_PER_ARM_AUTOINDEX` หลัง A1.2 ปิดสมบูรณ์แล้ว ไม่ทำ
A1 rerun, ไม่เปิด HARNESS-DEV/Selection/Final และไม่แก้ v11-v15 scientific
semantics

## 1. Publication question

ทดสอบว่า representation program ที่ค้นหาแยกตาม retriever arm สามารถเพิ่ม
Recall/nDCG บน development boundary ได้มากกว่าการใช้ common-screen baseline
หรือไม่ ภายใต้ matched budget, fixed evaluator, deterministic search และ
reproducible artifact hashes โดยต้องเก็บ positive, null และ negative results
เพื่อรองรับข้ออ้างระดับ journal อย่างซื่อสัตย์

## 2. Entry conditions

ก่อนทำขั้นที่ 1 ต้องตรวจจาก canonical receipts/read-model เท่านั้นว่า:

1. A1.2 มี closeout receipt และ safe-return validation `PASS`
2. มี 25 aggregate result receipts, frozen promotion receipt และ provider
   disposition/SSH closeout ครบ
3. A1 report ระบุ supported/unsupported claims และ campaign phase status เปลี่ยน
   จาก `locked_until_A1` ตาม canonical read-model; อำนาจเริ่ม campaign มาจาก
   standing `D1_START_CAMPAIGN` เท่านั้น ไม่สร้าง micro-decision หรือเปิด Selection

หากข้อใดไม่ครบ ให้คง `BLOCKED_UNTIL_A1_CLOSEOUT` และรายงาน blocker เดียว
ถ้าขาดข้อ 1-2 ให้กลับไปใช้ `A1_2_rerun_goal.md` สำหรับ A1 เท่านั้น; ถ้าขาด
campaign/control ของ A2 ให้คงงาน A2 ไว้ที่ preflight และสร้าง/แก้เฉพาะ A2
contract ตามขั้นที่ 0 โดยไม่ rerun A1 และไม่เริ่ม measured work

## 3. Frozen controls and allowed surface

ห้ามเปลี่ยน split, qrels, membership, query reservation, model weights,
tokenizer/model revision, evaluator, primary/secondary metrics, protected
boundary และ deterministic tie-break ที่ A1 bind ไว้

แก้ได้เฉพาะ search/engineering surface ที่เขียนไว้ใน A2 contract เช่น
representation parameters, candidate generator, train/dev orchestration,
cache/index implementation, resource accounting และ fault recovery ต้องมี
focused test, source hash และ rationale เชิง reliability/coverage ทุก patch

## 4. ขั้นตอน A2 แบบ long run

### ขั้นที่ 0: เปิด task และสร้าง contract

1. อ่าน `PLAN.md`, A1 closeout report, A2 execution envelope, budget profile,
   runbook และ schemas เฉพาะ A2; หากไฟล์ A2 ยังไม่มี ให้สร้าง additive
   `control/armindex/a2/`, `control/budgets/`, `control/runbooks/` และ schemas
   ที่จำเป็นก่อนวัด โดยห้ามเดาค่า default
2. สร้าง A2 contract, runbook และ append-only ledger ที่ bind campaign revision,
   A1 baseline/promotion receipt hashes, candidate cap, seed, split boundary,
   evaluator, source tree, whole-workload budget, TTL/watchdog, runtime identity,
   safe-return archive policy และ protected-data boundary
   พร้อม `ATTEMPT_ID` ใหม่ที่ใช้ร่วมกันใน manifest, worker, receipts และ archive
3. กำหนดต่อ arm ที่ถูก promote จาก A1: candidate set/cap, train/dev coverage,
   stopping rule, primary/secondary metrics, failure/null handling และ resource
   ceiling ก่อนสร้าง candidate manifest; เกณฑ์ PASS คือ candidate ที่ประกาศไว้
   ถูกประเมินครบและมีผู้ชนะ per-arm แบบ deterministic ไม่ใช่ metric ที่ดูดีเพียงบางส่วน
4. ใช้ stable candidate IDs และลำดับ lexical เป็น tie-break สุดท้ายหลัง metric,
   cost, latency และ simplicity สำหรับการเลือก candidate winner ภายในแต่ละ arm;
   นี่เป็นคนละระดับกับ frozen A1 arm-promotion rule ที่ reject exact arm tie
   ห้ามเปลี่ยน tie policy ใดหลังเห็นผล
5. ระบุ matched controls และ hypotheses ให้ falsifiable; แยก claim ที่รองรับ
   journal ออกจาก engineering-only/unsupported claim

**Checkpoint A2-0:** contract/schema validation ผ่านและ scientific input hashes
ตรง A1 closeout lineage, runtime/admission/budget/TTL bindings ครบ และไม่มี
selection/final access เปิด

### ขั้นที่ 1: สร้าง candidate programs แบบ deterministic

1. สร้าง candidate set ต่อ arm ที่ A1 promotion receipt อนุญาต ตาม search
   surface ใน A2 contract; ห้ามเพิ่ม arm หรือ candidate นอก manifest
2. ใช้ lexical/stable IDs, seed และ deterministic tie-break; บันทึก candidate
   count, generator hash และ rejection reasons แบบ aggregate-safe
3. ตรวจ whole-workload budget, TTL, runtime identity, watchdog/lifecycle และ
   safe-return capacity ก่อนเริ่ม train evaluation; ห้าม infer budget จาก
   environment หรือ dashboard preview
4. เขียน immutable candidate manifest และ commit/hash ก่อนเปิด worker

**Checkpoint A2-1:** candidate manifest immutable, hash-bound และไม่เปิด
selection/final exposure

### ขั้นที่ 2: Train/development evaluation

1. รัน candidate บน train/development boundary ที่ contract ระบุเท่านั้น ตาม
   matched budget และ runtime identity; ก่อนวัดต้องมี provider/adoption,
   watchdog/TTL และ protected-boundary receipts เป็น `PASS` หาก contract เป็น
   CPU/local ให้บันทึกแบบนั้นและไม่จอง GPU
2. เก็บ aggregate metrics, latency, cost, failure rate, coverage และ resource
   usage; raw rankings/qrels/per-query outcomes อยู่ Owner-local
3. เปรียบเทียบกับ A1 baseline โดยใช้ evaluator เดิมและไม่เลือกผลย้อนหลัง
4. ทำ recovery ได้เฉพาะ infrastructure failure; ห้ามเปลี่ยน candidate/rule ตาม
   metric ที่เห็นแล้วโดยไม่สร้าง campaign revision ใหม่
5. ตรวจว่าผล candidate ครบตาม manifest และ checkpoint/worker/process identity
   ถูก hash-bound ก่อนรวมผล

**Checkpoint A2-2:** train evaluation ผ่าน, budget/coverage ครบ และ evidence graph
ตรวจได้จาก receipts โดยไม่เผย protected data

### ขั้นที่ 3: Deterministic per-arm winner freeze

1. ใช้ rule ที่ประกาศก่อนวัดเพื่อจัดอันดับ candidate ต่อ arm และใช้ lexical
   candidate ID เป็น tie-break สุดท้ายตาม contract
2. บันทึก candidate ทุกตัว, metric/uncertainty aggregate, cost/latency,
   failure/null cases และเหตุผลที่ candidate ไม่ผ่านแบบ aggregate-safe
3. สร้าง immutable per-arm winner receipt ที่ bind candidate IDs, compiler/config,
   retriever/evaluator/runtime hashes, campaign revision และ budget/TTL hash

**Checkpoint A2-3:** winner receipt self-hash ผ่าน; หลังจุดนี้ห้าม mutate
candidate/spec/rule/search configuration และยังไม่มี Selection/Final exposure

### ขั้นที่ 4: ปิด A2 โดยไม่เปิด Selection

1. ตรวจว่า A1 baseline, candidate manifest, train evaluation และ per-arm winner
   freeze ผ่านครบ
2. ยืนยัน `selection_accesses=0` และ `final_accesses=0`; Selection อยู่ใน A4
   ตาม active campaign และไม่เปิดจาก A2 goal
3. เก็บผล aggregate-safe พร้อม uncertainty/limitations ที่ schema รองรับ

**Checkpoint A2-4:** winner/freeze receipts ครบ, selection/final counters เป็นศูนย์
และไม่มี outcome-driven repair

### ขั้นที่ 5: วิเคราะห์ publication impact

1. สร้างตาราง/figure aggregate ที่เทียบ A1 baseline กับ A2 ต่อ arm โดยใช้
   artifact hashes และไม่สร้างตัวเลขแหล่งที่สองใน prose
2. รายงาน effect, cost/runtime trade-off, coverage, failure/null/negative cases
   และ reproducibility hashes
3. ตรวจ supported/unsupported claims กับ `myis-review-research-rigor` ก่อน
   manuscript projection; ห้ามเพิ่มตัวเลขแหล่งที่สองใน prose

**Checkpoint A2-5:** artifact graph, checksum, protected-path scan และ report
schema ผ่าน; ผลลัพธ์ยังไม่เปิด Final หรือ release

### ขั้นที่ 6: Closeout

1. อัปเดต generated Phase/Task report จาก read-model เดียว แม้ fail-closed
   ก่อน closeout ต้องมี blocker report และ session capsule แบบ pointer-only
2. รัน focused tests, scoped Ruff, report validation/sync เมื่อ projection
   เปลี่ยน, artifact/checksum/protected scans และ `git diff --check`
3. commit/push เฉพาะ aggregate-safe receipts, hashes, figures, report pointers
   และ goal/runbook/ledger ที่จำเป็น; preserve unrelated dirty worktree
4. บันทึก A2 closeout/blocked decision ตาม canonical campaign; ไม่เปิด
   `D2_OPEN_FINAL`, `D3_SUBMIT_RELEASE`, Selection หรือ Final โดยอัตโนมัติ

## 5. Recovery และ hard stops

หยุดและเก็บหลักฐาน aggregate-safe เมื่อ budget/TTL, hash, seed, evaluator,
protected boundary, candidate freeze, baseline reproduction, train evaluation
หรือ winner rule drift; เมื่อหยุดห้ามตีความ partial result หรือข้าม winner freeze

เก็บ failed attempt และ logs ไว้เพื่อ reproducibility, ใช้ recovery เฉพาะ
infrastructure ที่ไม่เปลี่ยน science การ retry ต้องใช้ `ATTEMPT_ID`, manifest,
ledger/checkpoint chain, runtime/admission receipts และ output root ใหม่ ห้าม
รวม partial candidate outputs ข้าม attempt; สร้าง campaign revision ใหม่เมื่อมี
budget/spec/rule change หลัง measured run. Runtime/worker identity drift,
watchdog/lifecycle failure, TTL/budget violation หรือ safe-return/checksum fail
เป็น `FAILED_CLOSED` ทันที

## 6. Artifacts และ terminal report

ต้องมี A2 contract/runbook/ledger/checkpoints, candidate manifest, train
receipts, immutable per-arm winner receipts, aggregate tables/figures, evidence
graph, generated report และ session capsule ที่ชี้ pointer/hash เท่านั้น
โดย raw qrels, membership, query IDs, rankings, credentials, provider payloads
และ safe-return archive อยู่ Owner-local เท่านั้น. Canonical aggregate pointers
อยู่ `campaigns/armindex-multiretriever-v2/evidence/` และ audits อยู่
`outputs/audits/armindex/`; A2 controls อยู่ `control/armindex/a2/`,
`control/budgets/` และ `control/runbooks/` ตาม schema ที่สร้างในขั้นที่ 0

รายงาน terminal:

```text
phase/task: A2_PER_ARM_AUTOINDEX / <task>
status: PASS | FAILED_CLOSED | BLOCKED
contract/campaign/budget hashes: <aggregate-safe values>
candidate/train/winner-freeze: <counts and receipt IDs>
publication evidence: <aggregate metrics/figure pointers>
changed_files: <รายการ>
protected_surfaces_untouched: <รายการ>
blocker_or_decision: <หนึ่งรายการถ้ามี>
next_action: <Owner-authorized action>
```

ห้ามรายงานว่า A2 สำเร็จหาก baseline/candidate/train/winner-freeze หรือ artifact
validation ไม่ผ่าน และห้ามเข้าสู่ A3, A4, A5, A6, Selection หรือ Final จากคู่มือ
นี้เอง
