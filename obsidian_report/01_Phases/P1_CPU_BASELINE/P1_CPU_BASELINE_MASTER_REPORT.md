---
schema_version: "myis.obsidian-note.v2"
read_model_revision: "859073fa4554d808f2b0302baa2e7eb56488611f355fbfc1a45b2031a0ac9fff"
read_model_sha256: "a2eb51dd773d173b66bebd8d0a9ff9466f4fd4bdf5beb042e74bdede97c2f579"
source_commit: "fa7ca0e3ea23c57740fbb18ac9373b175893d845"
projection_schema_version: "myis.integrated-projection.v2"
source_run_ids: []
source_manifest_sha256: []
related_literature_ids: []
related_decision_ids: ["D2_OPEN_FINAL","D3_SUBMIT_RELEASE"]
managed_by: "myis-report"
edit_policy: "generated_do_not_edit"
safe_to_present: true
created_at: "2026-07-31T12:01:36Z"
updated_at: "2026-07-31T12:01:36Z"
note_id: "P1_CPU_BASELINE-MASTER"
note_type: "phase_report"
phase_id: "P1_CPU_BASELINE"
task_id: null
workflow_status: "blocked"
evidence_maturity: "non_scientific"
claim_level: "none"
---

# Phase 1: P1_CPU_BASELINE

รายงาน Phase นี้แยกผล baseline แบบเอกสารเต็มและแบบ window ก่อนเริ่ม SCOPE development

## สถานะตอนนี้

**blocked with evidence**. ใช้ standing authorization `D1_START_CAMPAIGN`; ไม่ได้ร้องขอหรือเปลี่ยน `D2_OPEN_FINAL` และ `D3_SUBMIT_RELEASE`

## ขอบเขตและ protocol

- Dataset: pinned DAPFAM revision; evaluation unit เป็น patent family
- Query/corpus view: full TAC = title + abstract + claims; ไม่ใช้ description
- R0: หนึ่งเอกสาร TAC ต่อ family
- R0-W: window TAC แบบไม่ซ้อน 512 tokens และรวมผลด้วย family MaxP
- Retriever: deterministic SQLite FTS5 BM25, OR query, top 100 unique families
- Split ที่วัด: train 250 และ selection 125; final 872 ยังปิด
- Compute: CPU-only, zero paid API, zero GPU, zero network model download

## Dataset projections

| Dataset view | Representation | Safe aggregate counts |
|---|---|---|
| DAPFAM-FAMILY-CORPUS | patent family records | families=None, patents=None |
| DAPFAM-QUERY-SET | TAC query records | queries=None |
| DAPFAM-RELEVANCE-LABELS | family relevance labels | n/a |
| DAPFAM-R0-CANDIDATES | one document per family candidate | documents=None |
| DAPFAM-R0W-CANDIDATES | TAC512 passages with family MaxP | passages=None |
| DAPFAM-R1-REFERENCE | section units | n/a |
| DAPFAM-INCOMPATIBLE | element units | n/a |

## Task board

| Task | Work | Status | Evidence |
|---|---|---|---|
| [[P1.1]] | R0 flat BM25 fixture lane | blocked | not measured |
| [[P1.2]] | R0-W window maxP fixture lane | blocked | not measured |
| [[P1.3]] | Protected owner-local CPU handoff | blocked | not measured |

## Measured results

ยังไม่มี measured metric ที่ผ่าน package และ rigor review

## Interpretation

ยังเปรียบเทียบ selection/OUT ไม่ได้ เพราะ evidence matrix ยังไม่สมบูรณ์

## Checks และ evidence chain

ยังไม่มี canonical four-slot run matrix

## สิ่งที่พูดได้

ผล Recall@100 ที่แสดงเป็น aggregate development evidence สำหรับ train/selection ภายใต้ protocol ที่ระบุ

## สิ่งที่ยังพูดไม่ได้

ห้ามสรุป final performance, statistical superiority, legal novelty, infringement, validity หรือ freedom to operate จากผลนี้

## สิ่งที่ Owner ต้องทำ

ไม่ต้องตัดสินใจ Gate เพื่อปิด P1. การเริ่ม P2 เป็น next automatic CPU-only action; D2/D3 ยังเป็น Owner-only

## ขอบเขตที่ยังไม่แตะ

Final split content, protected labels, per-query outcomes, credentials, paid API, GPU และ provider payload ยังคงอยู่นอก projection

## Evidence revision

Read-model revision: `859073fa4554d808f2b0302baa2e7eb56488611f355fbfc1a45b2031a0ac9fff`
