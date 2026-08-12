---
title: "A2 goal: Per-arm AutoIndex เพื่อเพิ่ม publication impact"
phase_id: A2_PER_ARM_AUTOINDEX
status: READY_FOR_OWNER_LAUNCH_FRESH_PREFLIGHT_REQUIRED
lifecycle: ACTIVE
evidence_class: planning_handoff_only
scientific_authority: false
claim_boundary: "คู่มือ A2 เท่านั้น; A1 terminal PASS และ A2 candidate freeze/audit PASS แล้ว แต่ candidate evaluation และ measured A2 ยังไม่เริ่ม"
last_material_update: 2026-08-12
next_authorized_action: OWNER_LAUNCH_DOCS_GOAL_A2_WITH_FRESH_PREFLIGHT
---

# A2: Per-arm AutoIndex long-run guide

> **Current routing:** [`A2_official_codex_bridge_goal.md`](A2_official_codex_bridge_goal.md)
> ปิด `CLOSED_PASS` และ independent audit ผ่านแล้ว Owner จึง launch goal นี้ได้
> แต่การ launch goal ยังไม่ใช่อำนาจ measured execution: ต้องผ่าน fresh A2 entry preflight,
> provider admission, execution adoption, isolated remote root, budget/TTL/watchdog และ
> protected-boundary checks ในขั้นที่ 0 ก่อน candidate evaluation หรือ REP-DEV measurement

เริ่มเมื่อ Owner สั่ง:

```text
/goal อ่าน docs/goal/A2_goal.md ตรวจ A1 terminal PASS ก่อน แล้ว implement และทำงานตามขั้นตอนทั้งหมดจน A2 closeout โดยไม่เข้า A3, HARNESS-DEV, Selection หรือ Final
```

เอกสารนี้ทำเฉพาะ A2 `A2_PER_ARM_AUTOINDEX` หลัง A1.2 ปิดสมบูรณ์แล้ว ไม่ทำ
A1 rerun, ไม่เปิด HARNESS-DEV/Selection/Final และไม่แก้ v11-v15 scientific
semantics

## สถานะเตรียมงานปัจจุบัน

| งาน | สถานะ | เงื่อนไขถัดไป |
|---|---|---|
| คู่มือ A2 แบบ long run และ publication question | `COMPLETE` | ใช้ได้หลัง A1 terminal PASS |
| A2 entry preflight validator | `COMPLETE` | ต้องรันกับ terminal pointer/read-model จริงหลัง A1 closeout |
| A1 terminal pointer และ baseline handoff | `COMPLETE` | terminal `PASS`; local source 28 files, remote mirror 29 files และ lineage ผ่าน |
| A2 provider reuse policy และ isolated-root plan | `COMPLETE` | ต้องทำ fresh A2 admission/adoption; ห้าม reuse A1 receipt |
| Official Codex bridge และ immutable candidate freeze | `CLOSED_PASS` | `40 matched + 12 dormant reserve`; audit finding `0` |
| Official credit หลัง audit | `PASS` | `gpt-5.6-sol`, Plus, used `13%`, remaining `87%`, reset `2026-08-18T00:45:40Z`, limit `false` |
| A2 candidate evaluation และ measured execution | `NOT_STARTED` | เริ่มตามขั้น 0; ต้องผ่าน fresh entry preflight และ fresh A2 admission/adoption ก่อนวัด |

ดังนั้นคู่มือ A2 พร้อมให้ Owner launch ใน session ถัดไป Candidate universe ถูก freeze แล้ว
แต่ยังไม่มี candidate evaluation, measured A2 run, REP-DEV measurement, HARNESS-DEV,
Selection หรือ Final exposure

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
4. provider disposition ของ A1 เป็น `DESTROYED` หรือ `REUSE_ELIGIBLE` ที่ validate
   แล้ว หากเป็น `REUSE_ELIGIBLE` ต้องมี fresh A2 provider admission, whole-workload
   budget/TTL, watchdog และ execution adoption ใหม่ ห้าม reuse A1 adoption receipt
   และห้ามใช้ A1 remote root เป็น A2 output root

หากข้อใดไม่ครบ ให้คง `BLOCKED_UNTIL_A1_CLOSEOUT` และรายงาน blocker เดียว
ถ้าขาดข้อ 1-2 ให้กลับไปใช้ `A1_2_rerun_goal.md` สำหรับ A1 เท่านั้น; ถ้าขาด
campaign/control ของ A2 ให้คงงาน A2 ไว้ที่ preflight และสร้าง/แก้เฉพาะ A2
contract ตามขั้นที่ 0 โดยไม่ rerun A1 และไม่เริ่ม measured work

## 3. งานที่เตรียมได้ระหว่าง A1 ยังรัน

ทำได้เฉพาะ read-only audit และปรับ goal นี้: สำรวจ code/schema/test/runbook ที่มี,
ทำ reusable-asset map, เขียน dependency/implementation order และคำนวณ budget
formula จาก aggregate A1 timing ห้ามสร้าง candidate จากผล A1 ที่ยังไม่ปิด, ห้าม
เปิด REP-DEV เพิ่ม, ห้ามส่ง A2 worker และห้ามเปลี่ยนไฟล์ frozen A1

Reuse ก่อนสร้างของใหม่:

- `src/myis_research/armindex/autoindex.py`: batch roles, mutable axes, strict
  primary improvement, stopping และ terminal receipt primitives
- `src/myis_research/armindex/scientific_common_programs_v11.py` และ A1 compiler:
  incumbent/common-program lineage; reuse ผ่าน hash/pointer ไม่แก้ v11 bytes
- A1 measured runner, lifecycle, remote launcher, watchdog, safe-return และ
  evaluator-closeout: reuse เฉพาะ engineering pattern/helpers ที่ไม่ bind กับ A1
  attempt; A2 ต้องมี schema/contract/attempt identity ของตนเอง
- `control/plans/ARMINDEX_AUTOINDEX_HARNESSOPT_CONTRACT.md`: canonical mutable/
  frozen surface, four-candidate batch และ stopping rules
- asset registry: `APP-DAPFAM-PROTECTED` ใช้แบบ Owner-local pointer,
  `APP-DAPFAM-TEXT-PRIMITIVES` adapt ได้, `LIT-AUTOINDEX-U154` ใช้เป็น literature
  pointer; `APP-SPARSE-FTS-INDEXES` ไม่ได้อนุญาตสำหรับ A2
- model trees, wheelhouse และ runtime บน instance เดิม reuse ได้เฉพาะเมื่อ hash,
  image, GPU identity และ protected boundary ตรง และ A2 admission อนุญาต
- A1 baseline handoff ใช้จาก Owner-local
  `04_Owner_Stores/armindex-a2/a1-baseline-safe-return/<A1_ATTEMPT_ID>/` ซึ่งต้องมี
  safe-return archive, aggregate receipts 25 รายการ, promotion/evaluator-closeout
  และ `handoff-manifest.v16.json` ที่ hash ผ่าน ห้ามสร้าง repository `data/`
- ค่า A1 สำหรับเปรียบเทียบและ promoted-arm set ต้องอ่านจาก canonical
  `campaigns/armindex-multiretriever-v2/evidence/a1.2-result-summaries/<A1_ATTEMPT_ID>.summary.v16.json`
  ที่ terminal pointer/read-model validate แล้ว ห้ามคำนวณใหม่จาก prose หรือ
  เลือกเฉพาะ cell ที่ให้ผลดี
- Vast อาจมี read-only mirror ที่
  `<REMOTE_A1_ROOT>/handoff/a1-baseline/<A1_ATTEMPT_ID>/`; mirror นี้เป็นสำเนา
  reproducibility เท่านั้น A2 ต้อง validate กับ Owner-local manifest และสร้าง
  fresh A2 root/admission/adoption ก่อนใช้ compute
- A1 embeddings, vector indexes, caches และ tensor checkpoints ไม่ใช่ A2 input
  ที่อนุญาตโดยอัตโนมัติ; ห้ามดึงหรือ reuse เพียงเพราะ instance เดิมยังอยู่

## 4. Frozen controls and allowed surface

ห้ามเปลี่ยน split, qrels, membership, query reservation, model weights,
tokenizer/model revision, evaluator, primary/secondary metrics, protected
boundary และ deterministic tie-break ที่ A1 bind ไว้

แก้ได้เฉพาะ search/engineering surface ที่เขียนไว้ใน A2 contract เช่น
representation parameters, candidate generator, train/dev orchestration,
cache/index implementation, resource accounting และ fault recovery ต้องมี
focused test, source hash และ rationale เชิง reliability/coverage ทุก patch

## 5. ขั้นตอน A2 แบบ long run

เริ่ม session ด้วยคำสั่งเล็กที่สุดก่อน ห้าม scan ทั้ง repository:

```powershell
git status --short
uv run --no-sync python -m myis_research.armindex.a2_entry_preflight_v16 --repository-root .
uv run --no-sync pytest -q tests/test_armindex_phase_scaffolding.py tests/test_armindex_typed_contracts.py
```

คำสั่ง preflight ต้อง exit `0` และ JSON ต้องมี `status=PASS_A2_ENTRY_PREFLIGHT`,
`provider_disposition_status=REUSE_ELIGIBLE|DESTROYED`, `a2_phase_status=planned`,
safe-return/evaluator/promotion hashes, A1 report hash และ access counters เป็นศูนย์
รวมทั้ง measured-result summary hash และ promoted-arm set ที่ตรง terminal lineage
ก่อนทำขั้นที่ 0R/0 หากไม่ผ่านให้รายงาน blocker เดียวและหยุด A2. คำสั่งนี้ตรวจ
terminal pointer, read-model และ A1 report พร้อมกัน; ห้ามใช้ campaign YAML อย่าง
เดียวแทน read-model.

### ขั้นที่ 0R: เลือก provider lifecycle หลัง A1 PASS

1. ถ้า A1 disposition เป็น `REUSE_ELIGIBLE`, ตรวจ instance เดิมซ้ำและสร้าง A2
   attempt/root ใหม่ เช่น `/opt/myis/a2-<attempt-id>`; A1 root/artifacts เป็น
   read-only จน A2 safe staging ผ่าน
2. reuse ได้เมื่อ provider/runtime/model/data hashes ตรง, SSH/provider management
   พร้อม, live quote และ remaining TTL ครอบคลุม whole A2 workload + 6h reserve
   เท่านั้น; ใช้ fresh A2 admission/adoption receipts ทุกครั้ง
3. ถ้า disposition เป็น `DESTROYED`, ห้าม provision, login, reserve GPU, ส่ง worker
   หรือสร้าง candidate manifest. ให้คง A2 `BLOCKED_PROVIDER_PREPARATION`, เก็บ
   blocker เดียว และขอ Owner action ที่ระบุ provider provisioning/admission สำหรับ
   A2 โดยตรง; คำสั่ง `/goal` ไม่ใช่อำนาจสำหรับการกระทำเหล่านี้.
4. ถ้า `REUSE_ELIGIBLE` reuse ไม่ผ่าน ให้คง A2 `BLOCKED_PROVIDER_PREPARATION`, เก็บ blocker เดียว
   และเสนอ fresh instance/destroy decision แก่ Owner ห้ามลด candidate coverage หรือ
   เปลี่ยน hypothesis เพื่อให้พอดีงบย้อนหลัง

**Checkpoint A2-0R:** A1 terminal PASS, provider disposition validated, A2 root
isolated, fresh quote/budget/TTL/admission/adoption PASS และ measured counters ยังศูนย์

### ขั้นที่ 0: เปิด task และสร้าง contract

1. อ่าน `PLAN.md`, A1 closeout report, A2 execution envelope, budget profile,
   runbook และ schemas เฉพาะ A2. ก่อน implementation หรือ measured work ให้สร้าง
   additive required-first-write set นี้ครบ, validate ทุก schema/self-hash และ commit
   control/schema/test bytes ก่อนเปิด worker; ห้ามเดาค่า default:

| Required path | Schema ID / role | Required hash bindings | Focused test |
|---|---|---|---|
| `control/execution-envelope-a2-v1.yaml` | A2 execution policy | campaign revision, A1 terminal/promotion, protected boundary, no-download policy | `tests/test_armindex_a2_contract.py` |
| `control/armindex/a2/execution-contract.v1.json` | `myis.armindex-a2-execution-contract.v1` | envelope, budget, A1 baseline/promotion, evaluator, split, source tree, runtime | `tests/test_armindex_a2_contract.py` |
| `control/budgets/a2-per-arm-autoindex-v1.json` | `myis.armindex-a2-budget-profile.v1` | contract, promoted-arm set, 2/3-batch workload, TTL and 6h reserve | `tests/test_armindex_a2_budget.py` |
| `control/runbooks/A2_PER_ARM_AUTOINDEX.md` and `control/armindex/a2/a2-ledger.v1.jsonl` | tracked runbook and append-only ledger | contract, attempt ID, checkpoint/worker identity | `tests/test_armindex_a2_lifecycle.py` |
| `schemas/armindex/autoindex-batch.v1.json` and `schemas/armindex/autoindex-terminal.v1.json` | kernel batch and terminal receipts | candidate/program/compiler/verifier/frozen-bindings hashes | `tests/test_armindex_a2_autoindex.py` |
| `schemas/armindex/a2-candidate-manifest.v1.json`, `schemas/armindex/a2-train-evaluation-receipt.v1.json`, and `schemas/armindex/a2-winner-receipt.v1.json` | immutable candidate/evaluation/winner records | contract, budget, candidate manifest, evaluator/runtime/checkpoint and terminal incumbent hashes | `tests/test_armindex_a2_manifest.py` |
| `src/myis_research/armindex/a2_entry_preflight_v16.py` | canonical entry/read-model validator | terminal pointer, campaign/read-model, report, zero access counters | `tests/test_armindex_a2_entry_preflight_v16.py` |

   Run `uv run --no-sync pytest -q tests/test_armindex_a2_contract.py tests/test_armindex_a2_entry_preflight_v16.py tests/test_armindex_a2_autoindex.py tests/test_armindex_a2_manifest.py tests/test_armindex_a2_budget.py tests/test_armindex_a2_lifecycle.py` and `uv run --no-sync ruff check src/myis_research/armindex/a2_entry_preflight_v16.py tests/test_armindex_a2_*.py` before the CPU fixture. The entry preflight must print only aggregate-safe PASS/fail fields and must pass before a candidate manifest exists.
2. At task start, create the generated A2 Phase/Task report from one validated read-model, then run `uv run --no-sync myis-report sync --repository-root .` and `uv run --no-sync myis-report check --repository-root .`; keep the same commands in `control/runbooks/A2_PER_ARM_AUTOINDEX.md`. Acquire and validate the Brain serial-writer lease before writing the required pointer-only session capsule. Report sync/check failure is a blocker before measured work.
3. สร้าง A2 contract, runbook และ append-only ledger ที่ bind campaign revision,
   A1 baseline/promotion receipt hashes, candidate cap, seed, split boundary,
   evaluator, source tree, whole-workload budget, TTL/watchdog, runtime identity,
   safe-return archive policy และ protected-data boundary
   พร้อม `ATTEMPT_ID` ใหม่ที่ใช้ร่วมกันใน manifest, worker, receipts และ archive
4. กำหนดต่อ arm ที่ถูก promote จาก A1: candidate set/cap, train/dev coverage,
   stopping rule, primary/secondary metrics, failure/null handling และ resource
   ceiling ก่อนสร้าง candidate manifest; เกณฑ์ PASS คือ candidate ที่ประกาศไว้
   ถูกประเมินครบและมีผู้ชนะ per-arm แบบ deterministic ไม่ใช่ metric ที่ดูดีเพียงบางส่วน
5. ใช้ `AutoIndexState` incumbent ที่ `advance_autoindex()` คืนค่าเป็น per-arm winner:
   รับเฉพาะ strict primary improvement, exact tie เป็น no improvement และคง
   incumbent เดิม. cost/latency/simplicity บันทึกแบบ aggregate-safe เพื่อรายงาน
   เท่านั้นและห้ามใช้ break tie ของ A2; ห้ามเขียน stopping/tie logic ซ้ำใน launcher
   หรือเปลี่ยน rule หลังเห็นผล.
6. ระบุ matched controls และ hypotheses ให้ falsifiable; แยก claim ที่รองรับ
   journal ออกจาก engineering-only/unsupported claim
7. audit implementation gap ก่อนเขียน code แล้วทำตามลำดับขั้นต่ำนี้:
   A2 schemas/contracts -> candidate compiler/generator -> independent verifier ->
   candidate manifest/freeze -> measured runner/checkpoints -> aggregate evaluator ->
   per-arm winner freeze -> safe return/terminal projection ห้ามสร้าง abstraction
   หรือเอกสารอื่นนอกลำดับนี้ถ้าไม่จำเป็นต่อการวัด
8. ใช้ `autoindex.py` เป็น deterministic kernel ห้ามเขียน stopping/tie logic ซ้ำใน
   launcher; เพิ่ม focused tests สำหรับสอง required batches, gated third batch,
   exact-tie no-improvement, duplicate scientific payload, incomplete batch,
   budget stop, timeout/OOM recovery และ immutable terminal state
9. ก่อน GPU measured work ให้รัน CPU fixture/smoke ที่ไม่ใช้ protected outcomes
   เพื่อพิสูจน์ compile-twice hash, 4-candidate topology, checkpoint/resume,
   failure preservation และ safe-return layout แล้วค่อยสร้าง frozen execution bundle

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
5. budget model ต้องคำนวณจากจำนวน promoted arms และ batch waves จริง: สอง batch
   บังคับเท่ากับ 8 candidates/arm; batch ที่สามเพิ่มได้อีก 4 candidates/arm เฉพาะ
   strict improvement + grounded axis + budget PASS. ใช้ A1 aggregate wall-time
   ต่อ arm เป็นฐานและเผื่ออย่างน้อย 6 ชั่วโมงสำหรับ evaluation/safe-return/closeout;
   ราคา/TTL ต้อง re-read สด ห้ามใช้ estimate นี้เป็น admission authority
6. งบไม่พอก่อน arm ใด complete สอง batches เป็น `FAILED_CLOSED`: ห้าม freeze arm,
   claim A2 PASS หรือรวม partial output. หลังสอง complete batches ให้ใช้ terminal
   state จาก `advance_autoindex()` เท่านั้น (`FREEZE_ARM_PROGRAM` หรือ
   `STOP_WITH_EVIDENCE_FLAT_REPRESENTATION_SURFACE`); A2 PASS ได้ต่อเมื่อทุก promoted
   arm มี terminal receipt ตาม contract และไม่มี required candidate ที่ประกาศไว้ตกหล่น.

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

1. ใช้ `advance_autoindex()` กับ primary metric ที่ frozen เพื่อได้ per-arm terminal
   incumbent; exact tie ไม่ปรับ incumbent และไม่ใช้ cost/latency/simplicity หรือ
   lexical candidate ID เป็น A2 winner tie-break
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

## 6. Recovery และ hard stops

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

## 7. Artifacts และ terminal report

ต้องมี A2 contract/runbook/ledger/checkpoints, candidate manifest, train
receipts, immutable per-arm winner receipts, aggregate tables/figures, evidence
graph, generated report และ session capsule ที่ชี้ pointer/hash เท่านั้น
โดย raw qrels, membership, query IDs, rankings, credentials, provider payloads
และ safe-return archive อยู่ Owner-local เท่านั้น. Canonical aggregate pointers
อยู่ `campaigns/armindex-multiretriever-v2/evidence/` และ audits อยู่
`outputs/audits/armindex/`; A2 controls อยู่ `control/armindex/a2/`,
`control/budgets/` และ `control/runbooks/` ตาม schema ที่สร้างในขั้นที่ 0

A2 เริ่มจาก A1 baseline handoff manifest และ aggregate receipts ที่ validate แล้ว
เท่านั้น Local CPU รับผิดชอบ orchestration/compiler/evaluator ส่วน dense
embedding/index/search ใช้ GPU เมื่อ fresh A2 provider admission และ execution
adoption ผ่าน ห้ามตีความการมี A1 remote caches ว่าอนุญาตให้ reuse ข้าม attempt

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
