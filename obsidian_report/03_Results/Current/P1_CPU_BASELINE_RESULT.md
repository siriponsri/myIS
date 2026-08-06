---
schema_version: "myis.obsidian-note.v2"
read_model_revision: "e3165c74caf18b254fab7e0010ab3555c3bdb268c7031c088d678bb3d62fba0d"
read_model_sha256: "e32db4f9a31f6ed1e20108d6d74b29f27e502dec28593ffd20224aa642ad6356"
source_commit: "1e86c432933f3bbf2e6763d04bb64139f81ce396"
projection_schema_version: "myis.integrated-projection.v2"
source_run_ids: ["p1-r0-selection-d9533ba623ce","p1-r0-train-d9533ba623ce","p1-r0ww-selection-d9533ba623ce","p1-r0ww-train-d9533ba623ce"]
source_manifest_sha256: ["31e875e1864cfbf0d7c39cf632b7506e168e753afdc49b7f27ce131d21b4a0f3","6100a8240bcd94ceb5740e805701ea69255a0f2d9e15609b52bc1921c8ae1ff6","8e3e52bf41d49d89f11416b7d9eebaf0cba1be9b2345871c07f152551c386f58","cb8ee4bfa971146ea80ecbe0c9e4b9b2c17f54f7952cb4b6de436bc2beeb12e1"]
related_literature_ids: []
related_decision_ids: ["D2_OPEN_FINAL","D3_SUBMIT_RELEASE"]
evidence_class: "engineering"
scientific_authority: false
claim_boundary: "engineering_provenance_only"
generated_from_revision: "e3165c74caf18b254fab7e0010ab3555c3bdb268c7031c088d678bb3d62fba0d"
last_material_update: "2026-08-06T02:33:36Z"
next_authorized_action: "/goal Execute A0.8_COMPUTE_AND_STORAGE_FEASIBILITY_FIXTURES from the canonical PLAN and control/campaigns/armindex-multiretriever-v2.yaml. Use synthetic fixtures only; do not access protected data, start measured retrieval, download model weights, use GPU or paid APIs, open Selection, or open Final."
managed_by: "myis-report"
edit_policy: "generated_do_not_edit"
safe_to_present: true
created_at: "2026-08-06T02:33:36Z"
updated_at: "2026-08-06T02:33:36Z"
note_id: "P1-CPU-BASELINE-RESULT"
note_type: "result_report"
phase_id: "P1_CPU_BASELINE"
task_id: "P1.3"
workflow_status: "complete"
evidence_maturity: "measured_selection"
claim_level: "descriptive"
result_id: "P1-CPU-BASELINE"
current_scientific_authority: true
---

# P1 CPU Baseline Result

## Output

Validated aggregate results from four slots: R0/R0-W crossed with train/selection

## Result status

Validity: **valid**; maturity: **selection**; claim boundary: **train_selection_only**

## Metric table

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


## Comparison

บน selection/OUT ค่า R0-W สูงกว่า R0 โดย observed delta = `+0.012269`. นี่เป็น descriptive development evidence เท่านั้น ไม่ใช่ผลยืนยันเชิงสถิติและไม่ใช่ final-split claim

## Resource result

CPU-only: `True`; GPU: `False`; paid API: `False`; actual cost USD: `0.0`

## Execution progress / observability

- Accepted measured run elapsed: `10835.097` seconds (`3.01` hours).
- The accepted source run predates the progress contract and records aggregate completion plus total latency only.
- The current runner shows a TTY progress bar and emits privacy-safe JSON heartbeats every `120` seconds for non-TTY execution.
- Heartbeats contain only stage, processed/total, elapsed time, and bounded ETA; no item identifiers or outcomes are emitted.

## Rigor

Grade: `Strong Accept`; mean score: `4.67`; review SHA-256: `4328a6e52b207d211da1cd87f94d702a90d6ebb7e72d72b31417389f13d0fd38`

## Evidence and audit details

| Arm | Split | Run ID | Manifest SHA-256 |
|---|---|---|---|
| R0 | selection | `p1-r0-selection-d9533ba623ce` | `6100a8240bcd94ceb5740e805701ea69255a0f2d9e15609b52bc1921c8ae1ff6` |
| R0 | train | `p1-r0-train-d9533ba623ce` | `31e875e1864cfbf0d7c39cf632b7506e168e753afdc49b7f27ce131d21b4a0f3` |
| R0-W | selection | `p1-r0ww-selection-d9533ba623ce` | `8e3e52bf41d49d89f11416b7d9eebaf0cba1be9b2345871c07f152551c386f58` |
| R0-W | train | `p1-r0ww-train-d9533ba623ce` | `cb8ee4bfa971146ea80ecbe0c9e4b9b2c17f54f7952cb4b6de436bc2beeb12e1` |

- `p1-four-slot-package`: `f505e5d0834cbb41776b084071a7e71e21856aa11d3371e6b0c96db5379b266c` at `campaigns/scope-autoindex-v1/packages/dapfam-p1-fulltext-c058a3aa7357c782.package.json`

- `p1-rigor-review`: `4328a6e52b207d211da1cd87f94d702a90d6ebb7e72d72b31417389f13d0fd38` at `outputs/audits/rigor/dapfam-p1-fulltext-c058a3aa7357c782/rigor_review.json`

- `mlflow-p1-registration`: `efb9fd9be3297ec0f220af93f48a69a13b1142b3435caedd1ad578c1ea8ed395` at `evidence/mlflow-p1-registration.v2.json`

## Interpretation boundary

ผลนี้ใช้วาง baseline สำหรับ P2 เท่านั้น Final 872 ยังปิด และไม่มี confirmatory/statistical claim

## Links

[[P1_CPU_BASELINE_MASTER_REPORT]] · [[P1.1]] · [[P1.2]] · [[P1.3]]
