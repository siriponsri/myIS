# Runbook: A1 Governed Closeout จาก Frozen v15

## ตัวตนของงาน

- Campaign: `armindex-multiretriever-v2`
- Phase: `A1_BASELINES_AND_MULTI_ARM_SCREENING`
- Task: `A1.2`
- Standing authorization: `D1_START_CAMPAIGN`
- Execution source: frozen v15 bundle เท่านั้น
- Frozen commit: `cba9776346cdd5916446bf372f6db9c33e9397d3`
- Frozen tree: `bcf9e3efc0024c5b10820a5e0fc8728b3ff4d81a`
- Frozen bundle SHA-256:
  `e6674aa03b88f88988798b2f063e4bdf6b240f1cbfbc723dfa317b5c87bb4bb9`
- Execution ledger:
  `control/armindex/a1.2/a1-governed-closeout-execution-ledger.v15.jsonl`

Runbook นี้เป็นแผนปฏิบัติการ ไม่ใช่หลักฐานว่ารันสำเร็จ และไม่อนุญาตให้ใช้
โค้ดจาก `HEAD` หรือสร้าง one-off executor เพื่อแทนส่วนที่ไม่มีใน frozen bundle

## เป้าหมาย

ทำ A1.2 common screen ให้ครบ 5 arms x 5 programs หรือ 25/25 cells บน
`REP-DEV` เท่านั้น แล้วประเมินแบบ Owner-local, promote ได้ไม่เกิน 3 arms ตาม
กฎ deterministic ที่ freeze ไว้, ปิด A1, ส่ง artifacts กลับอย่างปลอดภัย และ
ทำลาย Vast instance ก่อนหยุดที่ `A2_NOT_STARTED`

## ขอบเขตที่ห้ามแตะ

- ห้ามเปิด `HARNESS-DEV`, Selection, Final หรือ `D2_OPEN_FINAL`
- ห้ามเปลี่ยน split, evaluator, model, weights, precision, tokenizer, P02,
  overflow policy, metrics, candidate rule หรือ promotion rule
- ห้ามใช้ paid API, provider fallback หรือ runtime model download
- ห้ามส่ง qrels, exact membership, original IDs, token map, evaluator payload,
  credentials, raw provider payload หรือ per-query outcome เข้า Git/Brain/
  MLflow/Dashboard/Obsidian/Paper
- remote ส่งกลับได้เฉพาะ opaque top-100 rankings และ receipts/manifests ที่
  allowlist อนุญาต จากนั้น Owner-local evaluator จึงคำนวณ aggregate metrics

## Gate ก่อน adoption

ทุกข้อด้านล่างต้องผ่านใน attempt เดียวกันก่อน launch:

1. `main` และ `origin/main` ตรงกัน และ frozen bundle/receipt/hash ตรง v15
2. Vast instance ID, SSH fingerprint และ provider identity ตรวจซ้ำได้
3. live quote อายุไม่เกิน 900 วินาที ระบุ compute, storage, network, platform,
   tax/surcharge และ billing granularity ครบ ไม่มี fee ที่ยัง unknown
4. worst-case 6-hour charge ผ่าน hard stops USD 18 common screen, USD 23 A1
   และ USD 100 campaign พร้อมกัน
5. provider destroy command ผ่าน dry-run และ credential มีสิทธิ์ destroy จริง
6. linux/amd64, frozen image/runtime, Python 3.11, PyTorch 2.6.0+cu118,
   CUDA 11.8 และ RTX 3090 24 GiB แยกกันครบ 4 ใบ
7. CPU, RAM, disk, return capacity, TTL, heartbeat และ external watchdog ผ่าน
8. bundle, model, wheelhouse, tokenizer, program, adapter, protected handoff,
   transfer manifest, compiler receipt และ 25 compiled bindings hash ตรง
9. protected/credential scan ผ่าน และ frozen bundle มี measured executor ที่
   hash-bound ครบทั้ง embedding, indexing, search, checkpoint และ safe export
10. provider-admission receipt และ execution-adoption receipt ถูก validate แล้ว

ถ้าข้อใดข้อหนึ่งไม่ผ่าน ให้บันทึก `FAILED_CLOSED_PRE_ADOPTION`, ห้าม launch,
เก็บเฉพาะ allowlisted evidence, พยายาม destroy ผ่าน provider และหยุดรอ Owner
review ห้ามซ่อม scientific semantics ตามผลลัพธ์หรือสร้าง executor ชั่วคราว

## ลำดับรันเมื่อทุก Gate ผ่าน

1. สร้าง attempt ID, advisory lock, process creation identity, TTL deadline,
   heartbeat และ external watchdog
2. stage frozen bundle, protected opaque inputs, model trees และ wheelhouse โดย
  ตรวจ hash ก่อนและหลัง transfer; network fallback ปิดตลอด
3. รัน `ARM-01` บน local CPU และรัน `ARM-02` ถึง `ARM-05` แบบหนึ่ง arm ต่อ
  หนึ่ง GPU บน Vast instance เดียว
4. ใช้ 5 programs เดิม โดย slot P02 ใช้ additive successor
   `P02-FIRST-CLAIM`; dense overflow ใช้ contiguous zero-overlap windows และ
   source-token-count-weighted mean ตาม v14/v15
5. checkpoint หลังแต่ละ program ที่ durable แล้ว และ resume ได้เฉพาะ attempt,
   manifests, hashes, runtime และ semantics เดิม
6. ต้องได้ result receipts ครบ 25/25, deterministic replay ผ่าน, coverage ครบ,
   source-token drop = 0 และ silent truncation = 0
7. safe-export เฉพาะ allowlisted members แล้ว hash-validate ที่ local ก่อนเปิด
   ephemeral identity map หรือ evaluator
8. Owner-local evaluator คำนวณ `OUT Recall@100` เป็น primary และ
   `OUT nDCG@100`, `OUT nDCG@10` เป็น secondary จาก `REP-DEV` เท่านั้น
9. apply frozen deterministic promotion rule และ promote ได้ไม่เกิน 3 arms
10. sync canonical receipt ไป report/read-model, MLflow-safe mirror, Dashboard,
    Brain และ Obsidian จาก read-model object เดียว
11. รัน validation matrix ทั้งหมด จากนั้น destroy instance และตรวจ provider
    absence ก่อนแก้ lifecycle เป็น `DESTROYED`
12. commit/push เฉพาะ aggregate-safe artifacts เมื่อ worktree และ origin สะอาด

## Hard stop ระหว่างรัน

หยุดและ cancel/reap workers ทันทีเมื่อ identity/hash/runtime drift, heartbeat
เกิน 300 วินาที, TTL/budget เสี่ยงเกิน limit, disk ต่ำกว่า 20 GiB, protected
surface ปรากฏ, checkpoint/safe-return ผิด hash, output ไม่ครบ 25/25 หรือ
deterministic replay ไม่ผ่าน การ recover จาก OOM อนุญาตเฉพาะลด batch size หนึ่ง
ครั้งตาม frozen policy; ห้ามเปลี่ยน weights, precision, adapter หรือ program

## หลักฐานและการปิดงาน

ledger ต้อง append-only และแต่ละ entry ต้อง bind `previous_entry_sha256` กับ
`entry_sha256` แบบ canonical JSON SHA-256 รายงานปิดงานต้องระบุ Phase, Task,
status, evidence class, checks, changed files, protected surfaces ที่ไม่แตะ,
blockers, charged USD, safe return, commit/push, instance destruction และ
`NEXT_PHASE=A2_NOT_STARTED` อย่างชัดเจน
