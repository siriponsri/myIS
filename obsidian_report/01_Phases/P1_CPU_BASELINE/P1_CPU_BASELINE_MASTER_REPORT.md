---
schema_version: "myis.obsidian-note.v2"
read_model_revision: "9b764e3304770c10ab2258a841ade4eae600144928ece0549a35518f35ed9cad"
read_model_sha256: "3cc96572c8522d21d2eaa66aef79bd9554903b22852f56ce8c60e9d344c71c93"
source_commit: "cc38e26aaf032b51c5b8cf8c74c51b8317e4fcd4"
projection_schema_version: "myis.integrated-projection.v2"
source_run_ids: ["p1-r0-selection-d9533ba623ce","p1-r0-train-d9533ba623ce","p1-r0ww-selection-d9533ba623ce","p1-r0ww-train-d9533ba623ce"]
source_manifest_sha256: ["31e875e1864cfbf0d7c39cf632b7506e168e753afdc49b7f27ce131d21b4a0f3","6100a8240bcd94ceb5740e805701ea69255a0f2d9e15609b52bc1921c8ae1ff6","8e3e52bf41d49d89f11416b7d9eebaf0cba1be9b2345871c07f152551c386f58","cb8ee4bfa971146ea80ecbe0c9e4b9b2c17f54f7952cb4b6de436bc2beeb12e1"]
related_literature_ids: []
related_decision_ids: ["D2_OPEN_FINAL","D3_SUBMIT_RELEASE"]
managed_by: "myis-report"
edit_policy: "generated_do_not_edit"
safe_to_present: true
created_at: "2026-08-01T04:51:20Z"
updated_at: "2026-08-01T04:51:20Z"
note_id: "P1_CPU_BASELINE-MASTER"
note_type: "phase_report"
phase_id: "P1_CPU_BASELINE"
task_id: null
workflow_status: "complete"
evidence_maturity: "measured_selection"
claim_level: "descriptive"
---

# Phase 1: P1_CPU_BASELINE

รายงาน Phase นี้แยกผล baseline แบบเอกสารเต็มและแบบ window ก่อนเริ่ม SCOPE development

## สถานะตอนนี้

**complete (measured train/selection)**. ใช้ standing authorization `D1_START_CAMPAIGN`; ไม่ได้ร้องขอหรือเปลี่ยน `D2_OPEN_FINAL` และ `D3_SUBMIT_RELEASE`

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
| DAPFAM-FAMILY-CORPUS | one full TAC document per family | documents=45336, families=45336 |
| DAPFAM-QUERY-SET | TAC train/selection queries | final_closed=872, queries=1247, selection=125, train=250 |
| DAPFAM-RELEVANCE-LABELS | positive family relations with released IN/OUT labels | in=19736, out=5193, positive=24929 |
| DAPFAM-R0-CANDIDATES | full TAC family document | documents=45336 |
| DAPFAM-R0W-CANDIDATES | non-overlapping 512-token full TAC windows with family MaxP | windows=127019 |

## Task board

| Task | Work | Status | Evidence |
|---|---|---|---|
| [[P1.1]] | R0 flat BM25 measured CPU baseline | complete | dapfam-p1-fulltext-c058a3aa7357c782 |
| [[P1.2]] | R0-W window MaxP measured CPU baseline | complete | dapfam-p1-fulltext-c058a3aa7357c782 |
| [[P1.3]] | Protected owner-local CPU evidence import | complete | dapfam-p1-fulltext-c058a3aa7357c782 |

## Execution progress / observability

- Accepted measured run elapsed: `10835.097` seconds (`3.01` hours).
- The accepted source run predates the progress contract and records aggregate completion plus total latency only.
- The current runner shows a TTY progress bar and emits privacy-safe JSON heartbeats every `120` seconds for non-TTY execution.
- Heartbeats contain only stage, processed/total, elapsed time, and bounded ETA; no item identifiers or outcomes are emitted.

## Measured results

| Arm | Split | Scope | Metric | Value | n | Retrieved relevant | Relevant total |
|---|---|---|---|---:|---:|---:|---:|
| R0 | train | ALL | recall_at_100 | 0.216200 | 250 | 1081 | 5000 |
| R0 | train | IN | recall_at_100 | 0.258622 | 247 | 1024 | 4062 |
| R0 | train | OUT | recall_at_100 | 0.076057 | 179 | 57 | 938 |
| R0 | selection | ALL | recall_at_100 | 0.196000 | 125 | 490 | 2500 |
| R0 | selection | IN | recall_at_100 | 0.233820 | 121 | 461 | 2005 |
| R0 | selection | OUT | recall_at_100 | 0.062393 | 90 | 29 | 495 |
| R0-W | train | ALL | recall_at_100 | 0.243000 | 250 | 1215 | 5000 |
| R0-W | train | IN | recall_at_100 | 0.287954 | 247 | 1150 | 4062 |
| R0-W | train | OUT | recall_at_100 | 0.085847 | 179 | 65 | 938 |
| R0-W | selection | ALL | recall_at_100 | 0.214000 | 125 | 535 | 2500 |
| R0-W | selection | IN | recall_at_100 | 0.260759 | 121 | 501 | 2005 |
| R0-W | selection | OUT | recall_at_100 | 0.074661 | 90 | 34 | 495 |


## Interpretation

บน selection/OUT ค่า R0-W สูงกว่า R0 โดย observed delta = `+0.012269`. นี่เป็น descriptive development evidence เท่านั้น ไม่ใช่ผลยืนยันเชิงสถิติและไม่ใช่ final-split claim

## Checks และ evidence chain

| Arm | Split | Run ID | Manifest SHA-256 |
|---|---|---|---|
| R0 | selection | `p1-r0-selection-d9533ba623ce` | `6100a8240bcd94ceb5740e805701ea69255a0f2d9e15609b52bc1921c8ae1ff6` |
| R0 | train | `p1-r0-train-d9533ba623ce` | `31e875e1864cfbf0d7c39cf632b7506e168e753afdc49b7f27ce131d21b4a0f3` |
| R0-W | selection | `p1-r0ww-selection-d9533ba623ce` | `8e3e52bf41d49d89f11416b7d9eebaf0cba1be9b2345871c07f152551c386f58` |
| R0-W | train | `p1-r0ww-train-d9533ba623ce` | `cb8ee4bfa971146ea80ecbe0c9e4b9b2c17f54f7952cb4b6de436bc2beeb12e1` |

- `p1-four-slot-package`: `f505e5d0834cbb41776b084071a7e71e21856aa11d3371e6b0c96db5379b266c` at `campaigns/scope-autoindex-v1/packages/dapfam-p1-fulltext-c058a3aa7357c782.package.json`

- `p1-rigor-review`: `4328a6e52b207d211da1cd87f94d702a90d6ebb7e72d72b31417389f13d0fd38` at `outputs/audits/rigor/dapfam-p1-fulltext-c058a3aa7357c782/rigor_review.json`

- `mlflow-p1-registration`: `efb9fd9be3297ec0f220af93f48a69a13b1142b3435caedd1ad578c1ea8ed395` at `evidence/mlflow-p1-registration.v2.json`

## สิ่งที่พูดได้

ผล Recall@100 ที่แสดงเป็น aggregate development evidence สำหรับ train/selection ภายใต้ protocol ที่ระบุ

## สิ่งที่ยังพูดไม่ได้

ห้ามสรุป final performance, statistical superiority, legal novelty, infringement, validity หรือ freedom to operate จากผลนี้

## สิ่งที่ Owner ต้องทำ

ไม่ต้องตัดสินใจ Gate เพื่อปิด P1. การเริ่ม P2 เป็น next automatic CPU-only action; D2/D3 ยังเป็น Owner-only

## ขอบเขตที่ยังไม่แตะ

Final split content, protected labels, per-query outcomes, credentials, paid API, GPU และ provider payload ยังคงอยู่นอก projection

## Evidence revision

Read-model revision: `9b764e3304770c10ab2258a841ade4eae600144928ece0549a35518f35ed9cad`
