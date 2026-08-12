---
schema_version: "myis.obsidian-note.v2"
read_model_revision: "b5589b7a4747ebd5ad0c90040234cb689a81157edb268bc3e59e8d0beaddd415"
read_model_sha256: "6ebdba6643a45ffab264fd9b75c9b309044cd57c9df488b480e2321ebfeedc60"
source_commit: "07ec01023a8692646d21514954beef18e62fd58c"
projection_schema_version: "myis.integrated-projection.v2"
source_run_ids: []
source_manifest_sha256: ["38856e94d73c3df677471ba28062707cfded090da10d669758d8af48b8baf884","1e1adc521a726926449259a33e4c2667a1b9250cfbb1c483bd829620a842dcff"]
related_literature_ids: []
related_decision_ids: ["D2_OPEN_FINAL","D3_SUBMIT_RELEASE"]
evidence_class: "pre_measurement_owner_local_input_validation"
scientific_authority: false
claim_boundary: "P02 coverage and deterministic replay passed, but frozen ARM-03 x P00 exceeds its effective input limit without truncation. No retrieval or provider work was performed."
generated_from_revision: "b5589b7a4747ebd5ad0c90040234cb689a81157edb268bc3e59e8d0beaddd415"
last_material_update: "2026-08-12T11:14:59Z"
next_authorized_action: "Owner decides an additive pre-measurement program-limit compatibility repair or ARM-03 disposition; do not admit a provider or measured retrieval."
managed_by: "myis-report"
edit_policy: "generated_do_not_edit"
safe_to_present: true
created_at: "2026-08-12T11:14:59Z"
updated_at: "2026-08-12T11:14:59Z"
note_id: "A1-2-P02-FIRST-CLAIM-INPUT-LIMIT-AUDIT"
note_type: "history_report"
phase_id: "A1_BASELINES_AND_MULTI_ARM_SCREENING"
task_id: "A1.2"
workflow_status: "blocked"
evidence_maturity: "engineering"
claim_level: "none"
---

# A1.2 P02-FIRST-CLAIM Repair and Effective Input-Limit Audit

## Objective

ปิด blocker เดิมของ P02 ด้วย additive repair ก่อน measurement โดยไม่แก้ historical v11/v12-r3/v13 และตรวจต่อว่าทั้ง 25 program-arm cells สามารถรักษา zero silent truncation ได้จริงหรือไม่

## Starting State

REP-DEV/HARNESS-DEV split ถูก freeze แล้วที่ 150/100 แต่ P02 เดิมต้องการ independent-claim marker ซึ่ง DAPFAM ไม่มี ground truth ที่เชื่อถือได้ จึงยังสร้าง protected bindings ไม่ได้

## Inputs and Frozen Bindings

- Additive repair contract: `control/armindex/a1.2/p02-first-claim-repair.v1.json` (`5d661e6859f44eaafa29172d369c87eba4d86ad251a80c908edd00d04cd98fc1`)
- Frozen parser: `p02-first-claim-boundary-parser-v1` (`c038480fa96d72d961944115469d423a79d099af46294a196d66620fc0a8d0a5`)
- DAPFAM revision: `a59a74ce31384165065af1823a83c6f94ccafd48`
- V13 remains OUT Recall@100 primary and OUT nDCG@100 / nDCG@10 secondary.

## Work Performed

รัน claim-boundary parser สองรอบบน corpus และ frozen REP-DEV membership โดยไม่ใช้ dependency regex จากนั้นโหลด frozen ARM-03 tokenizer แบบ offline และตรวจ rendered P00 input โดยไม่ truncate หรือเริ่ม retrieval

## Artifacts Produced

- P02 aggregate-safe audit: `outputs/audits/armindex/a1.2-p02-first-claim-repair-20260808.json` (`38856e94d73c3df677471ba28062707cfded090da10d669758d8af48b8baf884`)
- Effective input-limit blocker: `outputs/audits/armindex/a1.2-effective-input-limit-blocker-20260808.json` (`1e1adc521a726926449259a33e4c2667a1b9250cfbb1c483bd829620a842dcff`)
- Matching P02 receipt remains Owner-local; no protected membership or text was exported.

## Metrics

REP-DEV availability `150/150`; corpus availability `45336/45336`; parse failures `0`. The first fail-closed binding is `ARM-03--P00-TAC-DOC` with rendered length `971` against limit `512`. These are engineering validation counts, not retrieval metrics.

## Result

P02 repair status **PASS** with deterministic replay **PASS**. Whole 25/25 protected compilation status **BLOCKED_CONTRACT_DEFECT** because the frozen input exceeds its declared limit.

## Interpretation

P02 blocker ถูกปิดแล้วโดยไม่สร้าง independent/dependent semantics ใหม่ แต่ v11 common-screen contract ยังไม่ executable แบบ zero-truncation สำหรับ ARM-03 x P00 ดังนั้นการฝืนสร้าง 20/25 หรือ truncate จะลดความเที่ยงตรงและขัด Owner decision

## Supported Claims

รองรับเฉพาะข้อสรุปว่า P02-FIRST-CLAIM มี coverage ครบและ replay ได้ และ validator พบ input-limit incompatibility อย่างน้อยหนึ่ง cell ก่อน measurement

## Unsupported Claims

ยังไม่รองรับ retrieval-quality, ranking, interaction, complementarity, superiority, publication, legal หรือ provider-cost claim ใด ๆ

## Failures and Recovery

Compiler ต้อง fail closed ที่ `ARM-03--P00-TAC-DOC`; ไม่มี truncation, fallback, partial-screen promotion, provider contact หรือ measured retrieval เกิดขึ้น การ recover ต้องใช้ Owner-approved additive pre-measurement compatibility decision เท่านั้น

## Governance and Safety

v11/v12-r3/v13 และ original P02 ยังเป็น immutable lineage; exact membership/text อยู่ Owner-local; Selection และ Final ปิด; paid API และ provider contact เป็น false

## Decision

คง `COMPILED_BINDINGS_25_OF_25=BLOCKED` และ `ZERO_TRUNCATION_CHECK=FAIL_OVERLENGTH_INPUT`; ไม่ commit/push เพราะ conditional authorization ยังไม่ครบ

## Next Action

Owner decides an additive pre-measurement program-limit compatibility repair or ARM-03 disposition; do not admit a provider or measured retrieval.

## Evidence Links

- P02 receipt: `1f7b99583a38101ea8e4a1e77f51f6c8787e70a9113b6f0e1487e59728e82c98`
- Input-limit audit: `c60b00595e8b32ff4549ea0e559ab0c002c33a5975ed1ce6831bf32e13ec5733`
- Historical split audit and EDA remain preserved at their existing paths.
