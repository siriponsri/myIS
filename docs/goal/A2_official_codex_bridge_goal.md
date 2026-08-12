---
title: "A2 preparation goal: Official Codex Bridge and five-arm candidate freeze"
phase_id: A2_PER_ARM_AUTOINDEX
status: CLOSED_PASS
lifecycle: COMPLETE
evidence_class: engineering_validation
scientific_authority: false
claim_boundary: "Engineering preparation and immutable representation-candidate freeze only; no candidate evaluation or measured A2"
last_material_update: 2026-08-12
next_authorized_action: OWNER_LAUNCH_DOCS_GOAL_A2_WITH_FRESH_PREFLIGHT
---

# A2 preparation: Official Codex Bridge and five-arm candidate freeze

> **Closeout 2026-08-12:** `CLOSED_PASS`. Official bridge identity is
> `gpt-5.6-sol` / `high` / SDK+CLI `0.144.4`; the immutable universe is
> `40 matched + 12 dormant reserve`. Independent audit
> `141e616d49a48caf889aedc5cec04e8c1a75b05c5afd55845b292e10b222d8f0`
> passed with zero findings. Final Official credit is Plus, `13%` used,
> `87%` remaining, reset `2026-08-18T00:45:40Z`, limit not reached. Measured A2,
> REP-DEV measurement, GPU, provider admission/adoption, HARNESS-DEV, Selection,
> and Final remain unopened. The publication projection target is
> `../03_Paper/01_ArmIndex`; canonical artifact indexes remain in Research.

Owner launch command:

```text
/goal อ่าน docs/goal/A2_official_codex_bridge_goal.md แล้วทำงานตามขั้นตอนทั้งหมดจน bridge และ five-arm candidate freeze ผ่าน จากนั้น commit/push และหยุดก่อน measured A2
```

เอกสารนี้เป็นคู่มือสำหรับ MaxPlus `gpt-5.6-sol` reasoning `xhigh` เท่านั้น เป้าหมายคือ
เตรียม A2 ให้ auditor ตรวจได้ แล้วจึงส่ง `docs/goal/A2_goal.md` ให้ Luna Max ทำ long run
ภายหลัง ห้าม session นี้รัน candidate evaluation, เปิด REP-DEV สำหรับการวัด, ส่ง A2 worker,
ทำ provider admission/adoption เพื่อเริ่มงานวัด หรืออ้างว่า A2 เริ่มแล้ว

หลักการเร่งงาน: checkpoint ในไฟล์นี้เป็น progress record ไม่ใช่ Owner gate ใหม่ MaxPlus ต้อง
แก้ dependency, schema, test, prompt-template, bridge และ integration bug ต่อเองโดยไม่หยุดถาม
Owner ใช้เฉพาะ focused checks ที่ครอบคลุม changed surface และ reuse receipt/hash ที่ยัง valid
ห้ามทำ repository-wide audit หรือ historical-document sweep ที่ไม่จำเป็นต่อ bridge/freeze

## 1. Starting state and fixed decisions

- A1.2 attempt `a12-v16-20260811-r15` ปิด `PASS` ที่ `25/25`; promotion เดิมคือ
  `ARM-03`, `ARM-05`, `ARM-04` และห้ามตีความใหม่
- Vast instance `47411176` มี disposition `REUSE_ELIGIBLE`; รักษา instance และ A1 root เดิม
  ห้าม destroy, overwrite หรือใช้ A1 adoption receipt เป็น A2 authority
- MaxPlus Sol XHigh เป็น orchestrator และ canonical repository writer
- Official Codex profile คือ `.codex-official`, model `gpt-5.6-sol`, reasoning `high`;
  ใช้เป็น representation proposer และ independent reviewer
- Luna Max เป็น executor ของ session ถัดไปหลัง auditor PASS เท่านั้น
- Official OpenAI documentation สำหรับ Python SDK:
  <https://learn.chatgpt.com/docs/codex-sdk> ระบุ package `openai-codex`, Python 3.10+,
  local app-server JSON-RPC และ published build ที่รวม pinned Codex runtime
- Full prompts, responses, events และ raw logs อยู่ Owner-local เท่านั้น Git รับเฉพาะ templates,
  schemas, hashes, counts, aggregate-safe receipts และ relative/opaque pointers
- ห้ามส่ง qrels, query IDs, membership, rankings, per-query outcomes, final split, credentials,
  inherited full environment, provider payloads หรือ protected text เข้า Official Codex
- ไม่ขอ ไม่จัดเก็บ และไม่อ้าง hidden chain-of-thought; ใช้เฉพาะ structured final outputs/rationales

## 2. Five-arm evidence design to adopt

ปรับ campaign/control แบบ additive ก่อนสร้าง candidate จริง โดยไม่แก้ A1 receipts หรือ historical
envelopes:

| Tier | Arms | Candidate count | Advancement effect |
|---|---|---:|---|
| matched | `ARM-01` ถึง `ARM-05` | `8/arm` = สอง batch x สี่ roles | เก็บหลักฐานครบห้า arms |
| conditional reserve | `ARM-03`, `ARM-05`, `ARM-04` | `4/arm` = หนึ่ง dormant batch | activate ได้เฉพาะ frozen strict-improvement rule |
| diagnostic | `ARM-01`, `ARM-02` | ไม่มี batch ที่สาม | ห้ามเปลี่ยน promotion/downstream eligibility/primary winner |

Candidate universe สูงสุดจึงเป็น `52` รายการ: matched `40` และ conditional reserve `12`.
ต้อง generate/review/compile/freeze ทั้งหมดก่อน measured work; reserve candidates อยู่สถานะ
`dormant_conditional` และห้ามสร้าง candidate ใหม่จากผลวัดภายหลัง แต่ละ batch ใช้ role order เดิม
`exploit`, `matched_ablation`, `orthogonal`, `diversity`. Candidate design ต้อง matched ด้าน count,
roles, evaluator bindings และ budget แต่ยัง retriever-conditioned ต่อ arm ได้

แก้ `control/campaigns/armindex-multiretriever-v2.yaml`, A2 execution envelope, budget,
contracts/schemas และ tests ที่เกี่ยวข้องให้ revision/hash ใหม่ผูก design นี้อย่างชัดเจน A2 ยังคง
`ready/not started`; A3, HARNESS-DEV, Selection, Final, D2 และ D3 ปิดอยู่

## 3. Required implementation steps

### Step 0: Focused audit and plan

1. อ่าน `PLAN.md`, active campaign, A2 sections ใน research plan, representation schemas,
   `src/myis_research/armindex/autoindex.py`, existing `scripts/orchestrator/`, tests และ
   controls ที่จะเปลี่ยนเท่านั้น
2. รัน `git status --short` และ A2 entry preflight เพื่อยืนยัน A1 terminal lineage โดยไม่เปิด A2
3. บันทึก assumptions, exact changed surface และ smallest verification commands ใน tracked
   runbook/append-only ledger สำหรับ preparation attempt นี้ ห้ามสร้าง status doc ซ้ำ

**Checkpoint 0:** A1 PASS ยังตรง, measured A2 counters เป็นศูนย์, candidate manifest ยังไม่มี

### Step 1: Adopt the five-arm contracts

1. ทำ additive campaign revision และ A2 control set ที่แยก `primary_advancement_arms` กับ
   `diagnostic_non_advancing_arms`
2. Freeze matched-tier `8/arm`, conditional reserve `4/primary arm`, activation predicate,
   candidate roles, stable lexical IDs, seed, metrics, evaluator, compiler/verifier hashes,
   A1 baseline/promotion bindings และ budget formula
3. Diagnostic arms อาจมี within-arm diagnostic result ใน A2 ภายหลัง แต่ต้องไม่มี field/path ที่
   ทำให้เปลี่ยน promotion, A3 eligibility, Selection eligibility หรือ primary winner
4. Budget/TTL model ต้องครอบคลุม matched 40 รายการและ reserve 12 รายการแบบ conditional;
   ห้าม infer default และห้าม launch จาก preparation session นี้

**Checkpoint 1:** schema/contract tests พิสูจน์ counts `40+12`, arm roles และ non-advancement

### Step 2: Build the Official Codex Bridge

1. Audit/reuse bounded CLI orchestrator assets; สร้าง Python bridge ด้วย stable pinned
   `openai-codex` SDK และ SDK-bundled pinned runtime ไม่พึ่ง global `codex-cli` เว้นแต่มี
   explicit compatibility test และ ADR อธิบายเหตุผล
2. Endpoint ฟังเฉพาะ `127.0.0.1`, ไม่มี remote bind, ไม่มี generic arbitrary-prompt route และ
  มี allowlisted operations เท่านั้น:
   - `representation_propose`
   - `representation_review`
   - `engineering_refactor_review`
3. ใช้ explicit environment allowlist; child/app-server ต้องได้ `CODEX_HOME` ที่ resolve ไปยัง
   `.codex-official` และต้องไม่รับ `MYIS_STORE`, `MYIS_MLFLOW_STORE`, credentials หรือ full
   inherited environment จาก caller
4. แต่ละ operation ใช้ versioned English prompt template และ JSON Schema output แยกกัน
   request ต้อง schema-validate ก่อนเรียก Official และ response ต้อง validate ก่อนยอมรับ
5. Pin model `gpt-5.6-sol` และ reasoning `high` ด้วย SDK/app-server field ที่ตรวจจาก installed
   SDK จริง หาก pin/observe ไม่ได้ให้วิเคราะห์ compatibility, แก้ integration และ retry ก่อน;
   ห้ามเดา parameter หรือยอมรับ identity ที่ตรวจไม่ได้
6. ทุก call บันทึก Owner-local append-only event: request ID, operation, prompt/template/input/
   response/schema SHA-256, SDK/runtime/CLI version, model/effort, start/end, usage เมื่อ SDK ให้,
   retry count, exit/verdict และ Git commit ห้ามบันทึก secret หรือ full prompt/response ใน Git
7. `representation_propose` และ `representation_review` ต้อง reject หลัง freeze lock ถูกสร้าง
   `engineering_refactor_review` ใช้หลัง freeze ได้เฉพาะ redacted engineering failure ไม่มี
   metrics/outcomes และห้ามเสนอการเปลี่ยน scientific payload/semantics

**Checkpoint 2:** mocked tests + `WhatIf` + one synthetic Official-Codex smoke test ผ่าน โดย
`protected_data_accessed=false`, `measured_execution_performed=false`, parent environment ไม่เปลี่ยน

### Step 3: Generate and independently review the 52 candidates

1. สร้าง safe context bundle จาก public controls, arm metadata, A1 aggregate-safe summary,
   representation schema และ frozen role/axis quotas เท่านั้น
2. Official proposer สร้าง schema-valid candidates ครบ `52`; MaxPlus ห้ามเติม fallback
   scientific candidates เอง หาก output ไม่ครบให้แก้ template/schema/integration และ retry
   ต่อได้ทันทีโดยไม่ขอ Owner ตราบใดที่ยังไม่ใช้ measured outcome
3. Official reviewer ใช้ fresh thread/request และเห็นเฉพาะ frozen context + candidate payload
   ที่ validate แล้ว ไม่รับ proposer transcript ทบทวน falsifiability, role fit, duplication,
   protected-boundary safety, arm compatibility และ publication interpretability
4. Candidate ที่ reviewer reject แก้ได้ก่อน freezeผ่าน versioned propose/review round ที่ bounded;
   ห้ามใช้ measured outcome เพราะ session นี้ไม่มี measured outcome
5. Stable IDs ต้อง encode arm/tier/batch/role ตาม lexical convention และ payload hashes ต้อง
   unique ตาม contract; primary reserve candidates ต้องถูกสร้างตอนนี้และ mark dormant

**Checkpoint 3:** proposer/reviewer receipts ครบทุก batch, `52/52` accepted, raw material Owner-local

### Step 4: Compile, verify and freeze immutably

1. แปลง proposal เป็น canonical representation program ด้วย existing schema/compiler surface
   ที่เล็กที่สุด ห้ามสร้าง speculative abstraction
2. Compile candidate แต่ละรายสองครั้งจาก clean state และต้องได้ hash เดียวกัน ใช้ synthetic
   fixture เมื่อ compiler ต้องการข้อมูล; ห้ามแตะ REP-DEV/final/protected corpus เพื่อวัดผล
3. Independent deterministic verifier ตรวจ schema, allowed axes, source fields, model/token limits,
   family identity, no silent truncation, stable IDs, uniqueness, prompt/response lineage และ
   advancement restrictions
4. สร้าง canonical candidate manifest และ freeze receipt ที่ bind candidate IDs/hashes,
   proposer/reviewer request hashes, templates/schemas, compiler/verifier, campaign/envelope/budget,
   A1 terminal/promotion, source commit/tree และ counts `40 matched + 12 dormant`
5. สร้าง freeze lock ให้ bridge ปฏิเสธ representation proposal/review ครั้งต่อไป Candidate/spec/rule
   mutation หลัง freeze ต้องใช้ campaign revision ใหม่และห้าม reinterpret manifest เดิม

**Checkpoint 4:** independent replay ตรวจ manifest/self-hash, compile-twice และ freeze lock ผ่าน;
measured counters, REP-DEV access, GPU work และ provider admission/adoption ยังคงศูนย์/false

### Step 5: Closeout for auditor review

1. Update A2 Phase/Task generated report จาก read-model เดียว เฉพาะ material preparation/freeze
   evidence; เก็บตัวเลขจาก canonical manifest/receipt ไม่คัดลอกเป็น source of truth ใหม่
2. Update `docs/goal/A2_official_codex_bridge_goal.md` เป็น `CLOSED_PASS` เมื่อ receipt ยืนยันจริง
   และคง `docs/goal/A2_goal.md` เป็น `BLOCKED_PENDING_AUDITOR_REVIEW`; ห้าม activate A2 เอง
3. สร้าง pointer-only session capsule ภายใต้ Brain writer lease และใช้ aggregate-safe hashes เท่านั้น
4. รัน focused tests/scoped Ruff, Markdown links, report check, session validation, artifact/checksum/
   protected-path scans และ `git diff --check`
5. Commit/push เฉพาะ aggregate-safe code, controls, schemas, tests, templates, receipts, report
   pointers และ goal routing ตรวจว่า `main == origin/main`
6. รายงาน terminal summary พร้อม exact changed files, candidate counts/hashes, smoke-test status,
   untouched protected surfaces, zero measured counters, blockers และคำสั่งถัดไปว่าให้ auditor
   ตรวจ readiness ก่อนเท่านั้น

Auditor review หลัง goal นี้ต้องเป็น one-pass focused review ตรวจเพียง Official identity/isolation,
protected boundary, five-arm counts/roles, manifest/freeze hashes และ zero measured work Auditor
แก้ engineering, test, pointer หรือ documentation mismatch เล็กน้อยเองได้และ activate
`A2_goal.md` ได้ทันทีเมื่อ invariants เหล่านี้ผ่าน ห้ามบังคับ rerun full suite หรือสร้าง gate เพิ่ม

## 4. Recovery and hard stops

- แก้ engineering bug, dependency, schema, SDK compatibility และ retry synthetic/bridge operation
  ได้ทันที บันทึก retry ใน append-only ledger; เมื่อ prompt/input เปลี่ยนให้สร้าง request hash ใหม่
  อย่างตรงไปตรงมา ไม่ต้องสร้าง campaign revision หาก scientific design ยังเดิมและยังไม่วัด
- Reviewer/compile/verifier/test failure ก่อน freeze เป็นงาน repair ไม่ใช่ terminal blocker ให้แก้และ
  รันต่อจนได้ manifest ครบ
- หยุดแบบ fail closed เฉพาะเมื่อ protected data/credential รั่ว, measured A2 เกิดก่อน freeze,
  Official identity/model/effort ยังตรวจไม่ได้หลัง compatibility repair, candidate universe/hash
  ไม่สามารถทำให้ครบ/stable, freeze ถูก mutate หรือ five-arm non-advancement ขัดกันเชิง semantics
- ห้ามแก้ candidate จาก metric, เปิด REP-DEV เพื่อเลือก candidate, ลด `8/arm`, เพิ่ม batch ให้
  diagnostic arms, เปลี่ยน primary metrics/evaluator/A1 promotion หรือเริ่ม A2 measured work
- ห้าม destroy/reprovision Vast instance จาก goal นี้

## 5. Required artifacts

- versioned Python bridge, loopback launcher/config, operation registry และ tests
- English prompt templates + JSON Schemas สำหรับสาม allowlisted operations
- Owner-local raw-event store pointer policy และ aggregate-safe bridge smoke receipt
- additive five-arm campaign/envelope/budget/contract revisions
- canonical `52`-candidate manifest, independent verification receipt และ freeze lock/receipt
- tracked preparation runbook + append-only ledger, generated report update, session capsule
- auditor handoff ที่ระบุชัดว่า `A2_NOT_STARTED` และ `BLOCKED_PENDING_AUDITOR_REVIEW`

## 6. Equivalent grill-with-docs decision record

Local `grill-with-docs` skill ไม่มีใน skill registry ปัจจุบัน จึงใช้ workflow เทียบเท่าตาม
<https://github.com/mattpocock/skills/tree/main/skills/engineering/grill-with-docs>:

**Questions and answers**

1. ทำไมไม่รัน A2 ใน goal นี้? เพราะ Owner ต้องการ auditor ตรวจ bridge, controls และ immutable
   universe ก่อนให้ Luna ใช้ GPU/REP-DEV
2. ทำไมต้อง freeze reserve candidates ล่วงหน้า? เพื่อป้องกัน outcome-driven generation หลังเห็น
   metric แต่ยังรักษา frozen strict-improvement activation rule
3. ทำไมมี five-arm matched tier? เพื่อให้ journal มี symmetric evidence รวม null/negative results;
   advancement ยังคงจำกัด primary arms ตาม A1
4. ทำไมไม่ใช้ generic prompt endpoint? เพราะทำให้ boundary, provenance และ operation semantics
   audit ไม่ได้

**ADR-A2-PREP-001:** ใช้ loopback Python SDK bridge แบบ operation allowlist, Official Codex
Sol High เป็น proposer/reviewer, pre-freeze `40+12` candidate universe และ require auditor PASS
ก่อนเปิด measured A2. Status: accepted for implementation; scientific authority: false until
canonical controls/manifests/receipts validate.

**Glossary:** `matched tier` = สอง batch ที่ count/roles/budget เท่ากันทุก arm;
`conditional reserve` = batch ที่สามซึ่ง freeze แล้วแต่ยัง dormant;
`diagnostic non-advancing` = เก็บ evidence แต่ไม่มีสิทธิ์เปลี่ยน promotion/winner downstream;
`freeze lock` = machine-enforced rejection ของ representation propose/review หลัง manifest freeze.

## 7. Terminal report format

```text
phase/task: A2_PER_ARM_AUTOINDEX / OFFICIAL_CODEX_BRIDGE_AND_CANDIDATE_FREEZE
status: CLOSED_PASS | FAILED_CLOSED | BLOCKED
official_bridge: <sdk/runtime/model/effort/smoke receipt>
five_arm_design: <campaign/envelope/budget hashes>
candidate_freeze: matched=40 conditional_dormant=12 total=52 <manifest/receipt hashes>
measured_a2_started: false
rep_dev_accessed_for_measurement: false
provider_admission_or_adoption_performed: false
protected_surfaces_untouched: <aggregate-safe statement>
changed_files: <exact paths>
checks: <commands and results>
next_action: AUDITOR_REVIEW_ONLY
```
