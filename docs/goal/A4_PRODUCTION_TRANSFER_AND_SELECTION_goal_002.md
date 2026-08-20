---
title: "Terra XHigh long run: A4 Selection-125 rerun, A5 Final-872, and A6 full DAPFAM"
phase_id: A4_PRODUCTION_TRANSFER_AND_SELECTION
task_id: A4.2_A5.1_A6.1
status: ACTIVE_OWNER_AUTHORIZED
lifecycle: ACTIVE
evidence_class: measured_selection_confirmation_and_full_corpus_materialization
scientific_authority: pending_measured_receipts
provider_instance_id: 47790578
owner_authorization: D1_START_CAMPAIGN_AND_CONDITIONAL_D2_OPEN_FINAL
selection_access_limit: 1
final_access_limit: 1
selection_accesses: 0
final_accesses: 0
protected_payloads_allowed: owner_store_only
next_authorized_action: fresh_a4_admission_then_selection_125_materialization
---

# Goal 002: A4 -> A5 -> A6 long run

เอกสารนี้เป็น execution goal สำหรับ Terra XHigh โดยตรง เจ้าของอนุญาตให้
rerun A4 เพื่อสร้าง Selection-125 handoff จริง และอนุญาตให้ต่อเนื่องไป A5 และ
A6 แบบ long run ใน session เดียวเมื่อ predicate ของแต่ละ phase ผ่านครบ

## 1. Owner decision และขอบเขต

Owner ได้อนุมัติล่วงหน้าให้ดำเนินการดังนี้:

- ใช้ instance `47790578` เดิมเท่านั้น เว้นแต่เกิด hard stop ที่ต้องขอ Owner ใหม่
- ทำ A4 rerun ด้วย fresh admission, fresh quote, fresh attempt ID และ fresh root
- materialize และวัด Selection-125 จริงเพียงครั้งเดียว
- เมื่อ A4 automatic predicates ผ่านครบ ให้เขียน conditional `D2_OPEN_FINAL`
  receipt ตาม `build_conditional_d2_receipt(...)` และต่อ A5 โดยไม่ถาม Owner ซ้ำ
- ทำ A5 Final-872 เพียงครั้งเดียวด้วย fresh admission/root
- เมื่อ A5 ผ่าน ให้ทำ A6 full DAPFAM corpus `45,336` rows ด้วย fresh admission/root
- ปิด A4, A5, A6 และเตรียม A7 evidence handoff แต่ห้ามทำ `D3_SUBMIT_RELEASE`

คำว่า “D2 owner approved” ใน goal นี้หมายถึง Owner pre-authorization แบบ
conditional เท่านั้น ไม่ใช่การปลอม receipt ล่วงหน้า ต้องออก receipt จริงหลัง
ผ่าน A4 audit, safe-return, A5 pointer bundle, exact split binding และ budget
reserve ครบทุกข้อแล้วเท่านั้น

ห้ามเปิด Final ก่อน receipt ที่มีสถานะ `PASS_CONDITIONAL_D2_OPEN_FINAL` หรือ
manual `D2_OPEN_FINAL` ที่ตรวจสอบได้

## 2. Canonical facts ที่ห้ามเปลี่ยน

- Parent split: Train `250`, Selection `125`, Final `872`, union `1247`
- Split seed `42`, algorithm `sha256-seed-colon-id-lexical-v1`
- Parent split commitment:
  `33a1818ff3c00775d43951182fdf769255c8ebfc591de183df4fbfdd3b039dc6`
- REP-DEV `150`, HDEV `100`; A4 historical result ใช้ HDEV เท่านั้น
- Canonical source manifest:
  `control/assets/dapfam-p1-source.v1.json`
- Source manifest hash:
  `f829e1827aff84dfb332742f74c1f717da655a1ef962e1aca0260d8d2a450d6c`
- DAPFAM revision `a59a74ce31384165065af1823a83c6f94ccafd48`
- A6 full corpus count `45,336`
- Primary metric `OUT Recall@100`; secondary metrics `OUT nDCG@100` and
  `OUT nDCG@10`
- Selection population `OUT`, exactly `125` paired units

ห้ามเปลี่ยน model weights, representation semantics, candidate depth, evaluator
semantics, split membership, tie policy, bootstrap count (`10,000`) หรือ metric
definitionเพื่อให้ผลดีขึ้น

## 3. ปัญหาปัจจุบันที่ต้องแก้

ตอนนี้ยังไม่มี real handoff ที่
`04_Owner_Stores/armindex/a4/selection-125/<handoff-id>/`

สิ่งที่มีอยู่เป็นเพียง:

- HDEV-100 A4 runtime/rankings เดิม
- `A4_SELECTION_HANDOFF_BLOCKER.json`
- sealed Selection scope ที่ `payload_materialized=false`
- A5/A6 pending templates

`src/myis_research/armindex/a4_remote_ranker.py` และ worker ปัจจุบัน hard-code
HDEV count `100` จึงห้ามนำไปใช้สร้าง Selection vectors โดยตรง ต้องสร้าง
Selection-capable runtime path ที่รับ scope `Selection-125` และตรวจ count `125`
โดยไม่ทำลาย HDEV path เดิม

บน instance เดิมที่ตรวจแล้วไม่มี Selection payload หรือ process วัดผลค้างอยู่
ดังนั้นต้องใช้ fresh A4 root และ fresh admission เท่านั้น ห้าม resume root เก่า
หรือผสม partial outputs

## 4. Execution flow

### 4.1 Startup and audit

1. อ่าน `PLAN.md`, goal นี้, A4 handoff contract, A4/A5/A6 goals, A4 readiness
   binding และ latest blocker
2. ตรวจ `git status`, `HEAD`, `origin/main`, source manifest และ split hashes
3. ตรวจ Owner Store ว่ายังไม่มี real Selection handoff ที่จะถูก overwrite
4. ตรวจ instance ด้วย `vastai show instance 47790578` และ SSH read-only
5. ตรวจ process/GPU/disk/RAM และเก็บ aggregate-safe observation ใหม่
6. ถ้า provider identity, quote, TTL หรือ budget ไม่ผ่าน ให้หยุดก่อน spend

คำสั่งตัวอย่าง (ห้ามพิมพ์ credential):

```powershell
uv run --no-sync vastai show instance 47790578
git status --short
git rev-parse HEAD
rtk pytest -q tests/test_a4_selection_runner.py tests/test_a4_execution_and_bundle.py
```

### 4.2 Owner-local Selection materialization

สร้าง root ใหม่ เช่น:

```text
04_Owner_Stores/armindex/a4/selection-125/sel125-<utc>-x01/
├─ protected/
│  ├─ selection-queries.jsonl
│  ├─ selection-membership.json
│  ├─ selection-qrels.jsonl
│  └─ paired-out-vectors.json
├─ selection-input.json
├─ evaluator-handoff.json
├─ finalist-registry.json
├─ preflight-counter.json
└─ aggregate-safe-manifest.json
```

กติกา materializer:

- ใช้ parent split membership ที่ hash-bound เท่านั้น
- ใช้ source contract และ canonical query/relation source ที่ตรวจ hash แล้ว
- derive opaque query/family tokens ตาม logic เดิมใน
  `scripts/build_a3_train250_owner_package.py`
- derive qrels จาก relation positives และ `eligible_out` จาก `domain_rel=OUT`
- ตรวจว่ามี Selection query ครบ `125`, ไม่มี duplicate/overlap กับ Train/Final
- qrels, membership, query IDs, query text, rankings และ vectors อยู่ Owner Store
  เท่านั้น
- ห้ามคัดลอกจาก HDEV, REP, fixture, legacy metrics หรือ guessed rankings
- ห้าม copy raw corpus/query source เข้า Git หรือ remote bundle
- เขียนแบบ write-once และ reject symlink/path escape

ถ้า source raw JSONL ไม่เทียบเท่า canonical Arrow ตาม source contract ให้หยุด
ด้วย `HARD_STOP_SOURCE_HASH_MISMATCH`; ห้ามใช้ไฟล์ที่ใกล้เคียงแทน

### 4.3 Selection-capable A4 runtime

1. เพิ่ม parameterized scope/count ให้ runtime รองรับ `Selection-125`
2. คง HDEV-100 validator เดิมไว้และเพิ่ม focused tests แยกกัน
3. สร้าง fresh A4 code bundle และตรวจ clean pushed commit/tree
4. ใช้ frozen A4 finalist system hashes จาก registry เดิม ห้าม tune หลังเปิด scope
5. รัน retrieval บน Selection query payload โดย remote worker ไม่รับ qrels หรือ
   membership; ส่งกลับ ranking package แบบ opaque/Owner-local เท่านั้น
6. evaluator Owner-local คำนวณ metric vectors ครบทุก finalist comparison

ห้ามเปิด Selection counter ระหว่าง materialization หรือ smoke test; counter จะ
เปลี่ยนเป็น `1` เฉพาะตอนเรียก `run_a4_selection_owner_local.py` ครั้งเดียว

### 4.4 Real Selection-125 handoff

`selection-input.json` ต้องมีเฉพาะ contract fields ที่ runner รองรับ และต้อง
ผูก self-hash ทุกชั้น โดย aggregate-safe manifest ต้องระบุอย่างน้อย:

- `selection_input_sha256`
- `paired_out_vectors_sha256`
- `evaluator_handoff_sha256`
- `selection_query_count: 125`
- `selection_population: OUT`
- vectors ครบ `recall_at_100`, `ndcg_at_100`, `ndcg_at_10` อย่างละ 125 ค่า
- frozen finalist registry และ A4 receipts
- source/split/evaluator/runtime hashes
- `selection_accesses: 0` ก่อน consume และ `final_accesses: 0`

ก่อน consume ให้ validate path boundary, protected-field scan, self-hash และ
partition/disjointness อีกครั้ง จากนั้น execute:

```powershell
python scripts/run_a4_selection_owner_local.py `
  --registry <owner-store>\finalist-registry.json `
  --preflight-counter <owner-store>\preflight-counter.json `
  --protected-input <owner-store>\selection-input.json `
  --output <owner-store>\selection-receipt.json `
  --owner-store-root <owner-store>
```

ผลลัพธ์ที่ออกจาก runner ต้องเป็น aggregate-only receipt เท่านั้น

### 4.5 Conditional D2 and A5 Final-872

หลัง Selection และ A4 closeout ต้องตรวจครบ:

- A4 FAST/BALANCED/DEEP coverage ครบและ audit ผ่าน
- Selection handoff/receipt self-hash ผ่าน
- finalist registry frozen และ exactly two finalists สำหรับ Final
- legal-transfer isolation ผ่าน
- safe-return และ worker teardown ผ่าน
- A5 pointer-only bundle ผูก Final split hash และ evaluator handoff
- fresh A5 budget reserve/TTL ผ่าน
- clean pushed Git commit/tree ผ่าน

เมื่อครบ ให้เรียก `build_conditional_d2_receipt(...)` และเขียน append-only
receipt โดยมี `owner_conditional_approval=true`, Selection `0|1`, Final `0`
ก่อน launch จากนั้นสร้าง fresh A5 admission/root และเปิด Final เพียงครั้งเดียว

A5 ต้อง:

- ใช้ Final-872 เท่านั้น
- fresh admission/root แยกจาก A4
- exactly two frozen finalists
- evaluator ใหม่และ safe-return ใหม่
- ไม่ใช้ Selection vectors เป็น Final result
- เก็บ qrels/membership/query IDs/per-query outcomes ใน Owner Store เท่านั้น

### 4.6 A6 full DAPFAM

เริ่ม A6 ได้เฉพาะเมื่อมี `PASS_A5_FINAL_CONFIRMATION` และ exactly one frozen
A5 winner แล้วเท่านั้น

- fresh A6 admission/root แม้ใช้ instance `47790578` เดิม
- bind canonical source manifest/hash และ full-corpus inventory `45,336`
- no tuning, no winner change, no Selection/Final reopen
- execution ต้องใช้ frozen winner เดียว
- `execution_permitted=false` จนถึง A5 closeout; หลังเปิดต้องมี A6 admission
- return aggregate scalability metrics และ corpus coverage receipt

## 5. Recovery and fail-closed rules

ซ่อมต่อได้สำหรับ SSH timeout, worker crash, package/path, OOM, checkpoint และ
safe-return plumbing โดยรักษา attempt lineage และไม่รวม partial outputs ต่าง root

### Gate policy: permissive engineering, strict science

Goal นี้ไม่มี micro-gate, sprint gate หรือ Owner approval เพิ่มเติมนอกเหนือจาก
`D2_OPEN_FINAL` แบบ conditional ที่ระบุไว้ข้างต้น. Terra XHigh ต้องเดินงานต่อ
อัตโนมัติเมื่อเป็นปัญหาวิศวกรรมที่ไม่เปลี่ยน scientific unit เช่น dependency,
path, retry, timeout, worker restart, batch size, concurrency, SSH reconnect,
remote staging, checkpoint repair และ provider transient. ให้บันทึก attempt/
recovery lineage แล้ว resume ต่อโดยไม่หยุดถาม Owner.

การหยุดจริงมีเพียงสี่กลุ่ม: scientific binding drift, protected-data boundary,
budget/TTL authority และ evidence integrity. ถ้าปัญหาอยู่ในสี่กลุ่มนี้ให้
preserve evidence และ fail-closed อย่างชัดเจน; อย่าตั้ง blocked เพียงเพราะ
ต้องแก้ code หรือรันซ้ำแบบ deterministic. การใช้ instance เดิมและการสร้าง fresh
root สำหรับ phase ถัดไปเป็น routine continuation ที่ goal นี้อนุญาตแล้ว.

หยุดทันทีเมื่อพบ:

- source/split/evaluator/model hash drift
- missing Selection query/qrels/membership หรือ canonical source ambiguity
- protected data leak
- duplicate/second Selection access หรือ Final access ก่อน D2
- budget/quote/TTL ไม่ทราบหรือเกิน hard stop
- finalist mutation หรือ winner selection ก่อน A5 result
- incompatible partial outputs หรือ worker ownership คลุมเครือ

หากพบปัญหาที่ซ่อมได้ ให้เลือก `FIX_FORWARD` ก่อน `BLOCKED_OWNER_ACTION` เสมอ
และไม่เปลี่ยน protocol เพียงเพื่อให้ implementation สะดวกขึ้น

## 6. Validation and closeout

รันตามลำดับ:

```powershell
rtk pytest -q tests/test_a4_selection_runner.py tests/test_a4_execution_and_bundle.py
rtk pytest -q tests/test_a5_pending_handoff_validator.py tests/test_a6_pending_materialization_validator.py tests/test_a6_materialization.py tests/test_a6_preparation_bundle.py
ruff check src scripts tests
git diff --check
```

ตรวจเพิ่ม:

- owner-store handoff receipt validator
- source/self-hash and partition validator
- protected-field/path-boundary scan
- A4 result-integrity and safe-return audit
- A5 Final coverage `872/872`
- A6 full corpus coverage `45,336/45,336`
- `HEAD == origin/main`, clean worktree

สร้าง long-run closeout และ Terra handoff ใน `docs/long_run/` และอัปเดต goal
status จาก receipts เท่านั้น ห้ามให้ Markdown กลายเป็น numeric authority

## 7. Terminal states

- `PASS_A4_SELECTION_A5_A6_LONG_RUN`
- `STOP_FAIL_CLOSED_SELECTION_HANDOFF`
- `STOP_FAIL_CLOSED_D2_OR_FINAL`
- `STOP_FAIL_CLOSED_A6_SOURCE_OR_WINNER`
- `BLOCKED_OWNER_ACTION` เฉพาะ credential/2FA/manual D3 หรือ hard-stop จริง

`D3_SUBMIT_RELEASE` ไม่อยู่ใน scope ของ Terra XHigh และต้องรอ Owner เสมอ
