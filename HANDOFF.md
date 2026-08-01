# Owner Handoff / สรุปสำหรับ Owner

อัปเดตจาก canonical records และ measured evidence ณ 2026-07-31 เอกสารนี้ใช้เพื่อ
orientation เท่านั้น หากขัดกับ control files, schemas, manifests, receipts หรือ
measured evidence ให้ยึด `control/source-of-truth.yaml`

## สถานะตอนนี้

- Phase: `P1_CPU_BASELINE`
- Task: `P1.3`
- Phase status: `complete`
- Evidence state: `P1_CPU_MEASURED_COMPLETE`
- Evidence class: measured train/selection, descriptive only
- Source execution commit: `df9582c94bce5c32a65717b140f66dbe8fea87b2`
- Request: `dapfam-p1-fulltext-c058a3aa7357c782`
- `P2_SCOPE_DEVELOPMENT`: ready, not started
- `D2_OPEN_FINAL` และ `D3_SUBMIT_RELEASE`: `waiting_owner`
- Standing authorization: `D1_START_CAMPAIGN`
- GPU: ไม่ใช้และไม่ต้องเปิด Vast Instance สำหรับงานปิด P1 นี้

## Phase 1 - ผลรวม

Owner-local CPU run เสร็จใน `10835.097` วินาที หรือประมาณ `3.01` ชั่วโมง โดยมี
ค่าใช้จ่าย `$0` และสร้าง evidence matrix ครบ 4 ช่อง:

| Arm | Train | Selection | สถานะ |
|---|---|---|---|
| `R0` | valid | valid | complete |
| `R0-W` | valid | valid | complete |

ขนาดข้อมูล aggregate ที่ตรวจรับแล้ว:

- 45,336 patent families
- 45,336 R0 family documents
- 127,019 R0-W windows
- 250 train queries และ 125 selection queries
- Final 872 ยังปิดและไม่ถูกใช้

Package ภายในมี SHA-256
`b5626b59484f429bcaa13f914ba9b7b3175a2013715d0b10d8f9c1c5638b34b3`
และ package file มี SHA-256
`f505e5d0834cbb41776b084071a7e71e21856aa11d3371e6b0c96db5379b266c`
manifest 4 ไฟล์และ validation report 4 ไฟล์ผ่านครบโดยมี blocker `0`
artifact-only rigor review ได้ `Strong Accept`, mean `4.67`

## Task P1.1 - R0 flat BM25

- สถานะ: `complete`
- วิธี: BM25 หนึ่ง full TAC document ต่อ patent family
- Train OUT Recall@100: `0.076057227485`
- Selection OUT Recall@100: `0.062392548637`
- Evidence: valid train/selection manifests, validation reports และ aggregate receipt

## Task P1.2 - R0-W deterministic window MaxP

- สถานะ: `complete`
- วิธี: non-overlapping 512-token full TAC windows และ family-level MaxP
- Train OUT Recall@100: `0.085847360337`
- Selection OUT Recall@100: `0.074661067156`
- Evidence: valid train/selection manifests, validation reports และ aggregate receipt

Observed delta ของ R0-W เทียบ R0 เท่ากับ `+0.009790132852` บน train/OUT และ
`+0.012268518519` บน selection/OUT ตัวเลขนี้เป็น descriptive development
evidence เท่านั้น ไม่ใช่ statistical superiority, confirmation หรือ final claim

## Task P1.3 - Evidence import และ closeout

- สถานะ: `complete`
- นำ package, receipt, manifests และ validation reports เข้า canonical control plane
- Rigor review ผูก hash กับ package และไม่มี blocking finding
- MLflow ลงทะเบียน parent 1 run และ child 4 runs ใน external governed store
- `protected_artifacts_mirrored=false`; legacy `mlflow-p1` ไม่ถูกแตะ
- Legacy aggregate receipt ยังคง `historical_invalid_superseded` และไม่ถูก promote
- Campaign, read model, Dashboard, Obsidian, Brain และ Paper แสดง P1 measured ตรงกัน

## Progress และ monitoring

- Accepted run รอบนี้เริ่มก่อน progress contract ใหม่ จึงมี aggregate completion กับ
  total latency แต่ไม่มี heartbeat ย้อนหลัง
- Runner ปัจจุบันมี TTY progress bar
- non-TTY mode ส่ง privacy-safe JSON heartbeat ทุก `120` วินาที
- Heartbeat มีเฉพาะ stage, processed/total, elapsed time และ capped ETA
- ห้ามส่ง item identifier, query identifier หรือ outcome รายรายการ
- interval 120 วินาทีเหมาะกับ batch ระดับชั่วโมงและลด CLI polling ที่ไม่จำเป็น

## CI และ cross-platform closeout

- GitHub Actions run `30646599835` พบ projection drift หลัง commit และ raw SHA drift
  จาก Git LF/CRLF normalization ใน clean Windows checkout
- แก้ด้วย byte policy `-text` สำหรับ canonical P1 JSON, MLflow registration evidence
  และ generated Obsidian vault โดยยกเว้น Owner Notes, `.obsidian` และ `.canvas`
- เพิ่ม regression tests ที่ตรวจ source contract, package-to-rigor binding,
  MLflow registration SHA, generated vault manifest hashes และ checkout policy
- clean committed checkout ที่ `1ca7b167221b59f3910213fc0db819e9a5e44a64`
  ผ่าน full suite `133 passed`, layout PASS และ read-model-only check PASS
- GitHub Actions run `30648584198` ผ่านครบทุก step:
  `https://github.com/siriponsri/myIS/actions/runs/30648584198`

## Projection status

- Shared read-model revision:
  `c94fb4ea49324cecc9d452a7c120fd54ec658a389dd77f6a441fef8864455cb5`
- Shared read-model SHA-256:
  `9ed1a20bba710370a552ed03768c005b39b90efb7238fb9a758eb098eb23589d`
- Obsidian generated manifest: 190 files, manifest SHA-256
  `1e3ccc7a67ab4ffaa903fa304631a61fe2c92df86aa74649b37d266cf0c222ad`
- Obsidian แยกรายงาน Phase 1 และ Task P1.1/P1.2/P1.3 พร้อม metric,
  evidence, interpretation boundary และ progress contract
- Brain มี MOC, phase/task status, datasets, experiments, publication readiness,
  weekly summary และรายงาน P0-P4 จาก read model v2 เดียวกัน
- Brain scoped commits: `26dc919` (P1 closeout) และ `d41544b` (CI projection sync);
  Brain ไม่มี remote จึงไม่มีปลายทาง push
- Dashboard/API แสดง `P1_CPU_MEASURED_COMPLETE`, 4 runs และ 12 metric rows
- Paper readiness และ publication source lock ชี้ read model v2 และคง
  `train_selection_only`
- Projection sync ล่าสุดใช้ MLflow run `aff1615bf1e44cc0b95086dda86b5d86`

## ผลตรวจ

- Full tests บน main worktree: `132 passed` ก่อนเพิ่ม generated-vault regression
- Full tests บน clean committed checkout: `133 passed`, มี 1 Starlette deprecation warning เดิม
- Dashboard/API/launcher focused tests: `19 passed`
- Layout validator: PASS
- Report sync/check สองรอบ: PASS, no drift
- Clean-checkout read-model-only check: PASS, no drift
- Advisor validation: PASS
- Asset registry quick validation และ P1.3 query: PASS
- Brain literature validation: PASS, U001-U154 มี ID/hash ไม่ซ้ำ
- MLflow doctor: PASS, 14 archive runs, 14 receipts, 164 safe artifacts
- Session capsule audit ก่อนเพิ่ม CI closeout capsule: PASS, unresolved invalid `0`
- GitHub Actions `30648584198`: PASS
- Git diff check: PASS

## ไฟล์และระบบที่เปลี่ยน

- Canonical campaign status, fresh P1 request/receipt/package/manifests/validation reports
- P1 adapter, deterministic kernel binding และ reusable progress reporter
- Read-model builder, report generator และ projection identity fingerprint
- MLflow registration/aggregate archive index
- Dashboard regression assertion และ projection/progress/P1 tests
- Obsidian Phase/Task/Result/Advisor/Literature projection set
- Brain generated reports และ active-context pointer
- Paper readiness, source lock และ GEPA project-context boundary
- Cross-platform byte policy และ clean-checkout regression tests
- `PLAN.md`, `README.md` และ `HANDOFF.md`

## ขอบเขตที่ยังไม่แตะ

ไม่ได้เปิดหรือคัดลอก final-872, protected qrels, split membership, query IDs,
per-query outcomes, rankings payload, credentials หรือ raw provider payloads เข้า Git,
Brain, MLflow, Dashboard, Obsidian หรือ Paper และไม่ได้ใช้ GPU, paid API,
network model download หรือ provider fallback

ไฟล์ Owner-local ต่อไปนี้ไม่ถูกแตะและจะไม่ถูก stage:

- `obsidian_report/.obsidian/graph.json`
- `obsidian_report/Untitled.canvas`

## สิ่งที่ Owner ต้องทำ

ไม่มี Owner decision ที่ต้องให้เพื่อปิด P1 ตัวแก้ CI ถูก commit/push และ workflow ผ่านแล้ว
Owner สามารถเปิด `dashboard/open-dashboard.cmd` เพื่อตรวจผลและ evidence chain

## Next automatic action

หลังปิด P1 และ CI ผ่าน ให้หยุดรอ Owner review `P2_SCOPE_DEVELOPMENT` พร้อมเริ่ม
แต่ยังไม่เริ่มอัตโนมัติ เพราะ execution envelope ปัจจุบันอนุญาตถึง P1 เท่านั้น
การเริ่ม P2 ต้องเป็นงานแยกที่กำหนด execution policy แบบ reversible, CPU-first และยังไม่เปิด
`D2_OPEN_FINAL` ส่วน `D3_SUBMIT_RELEASE` ยังคงปิดจนถึง Phase 4

ระบบนี้เป็น decision support ไม่ใช่คำแนะนำทางกฎหมาย

## P2 Readiness Refactor (2026-08-01)

สถานะยังคงเป็น `P1_CPU_MEASURED_COMPLETE` และ
`P2_SCOPE_DEVELOPMENT=ready/planned, not measured` โดยมี measured P2 runs และ
selection accesses เท่ากับศูนย์ `final-872` ยังปิด และไม่ใช้ GPU, paid API,
network model download หรือ provider fallback

P2 profile คือ `p2-r1-primary-v1` ที่
`control/budgets/p2-r1-primary-v1.yaml` ใช้ candidates สูงสุด 32 รายการ,
adaptive สูงสุด 20 รายการ, 5 iterations, wall-clock 72 ชั่วโมง และ timeout
ต่อ candidate 3 ชั่วโมง ทุก measured request ต้องมี profile ID และ SHA-256

P2 ใช้ run เดียวและ hard freeze barrier: generate และ train ให้เสร็จก่อน,
สร้าง immutable shortlist-freeze receipt แล้วจึงเปิด selection ได้ครั้งเดียว
และเฉพาะ frozen shortlist เท่านั้น หาก baseline/train/freeze ไม่ผ่านให้หยุด
ก่อน selection

Canonical blocker audit อยู่ที่
`outputs/audits/rigor/p2-readiness-20260801.json` ส่วน P1 envelope เดิมยังคง
hash-bound และไม่ถูกเขียนทับ; P2 ใช้ `control/execution-envelope-p2.yaml`

## P2 Readiness Refactor implementation closeout (2026-08-01)

The approved readiness refactor is implemented. Canonical P2 budget/request,
candidate-ledger, shortlist-freeze, selection, manifest, and package schemas
are hash-bound; `myis-p2` exposes preflight and fixture-pilot only. The state
machine enforces the 4/8/20 allocation, 32-candidate and index-build limits,
strict-greater/tie-reject rule, early-stop rule, immutable freeze barrier, and
one-shot selection boundary.

The shared read model now reports P2 profile/hash, runtime, resource limits,
freeze status, candidate/selection counts, and an explicit
`ready_planned_not_measured` result. Dashboard, MLflow archive index, Obsidian,
Brain, and Paper projections are regenerated from that same revision. P2
measured runs and selection accesses remain `0`.

Provider switching is documented with credential-free, process-scoped
PowerShell launchers under `scripts/dev/`; no login, logout, credential copy,
keyring access, or active-provider switch was performed.

## Final verification (2026-08-01)

- Full test suite: `149 passed` with one pre-existing Starlette/httpx deprecation warning.
- Read-model: revision `37737829b02c78dc1b973fe95ff8c607c54e52c8b1c702e40cacfdf11dfa9e6e`, SHA-256 `1ebf16c8aff675d2636deb8a9b1de89986da28b2fec6a8cf690eb3a2ae005e63`.
- Projection sync: `PASS`; latest aggregate-only MLflow run `0451604936c84ffea8f504d6d720c9ee`.
- MLflow doctor: `PASS`; legacy experiments preserved and the store remains outside the Git worktree.
- P2 baseline reproduction is an explicit state-machine gate; failure blocks shortlist and selection.

## Official Round 1 P2 contract repair (2026-08-01)

The eight repository-safe findings in
`orchestration/results/official-research-20260801T070313825Z-5daa6cb1.json`
are repaired. P2 artifacts now receive recursive aggregate-only protection,
share one explicit aggregate metric schema, and bind the canonical budget
profile. Baseline reproduction is an immutable hash-bound receipt. Adaptive
iterations require consecutive four-candidate membership and derive their
scores from recorded train outcomes. A full package graph must pass semantic
validation before the read model can promote fixture or measured evidence,
and every frozen finalist requires exactly one selection aggregate.

Local verification passed with `196` synthetic/unit tests, `44` focused P2
tests, two stable report sync/check cycles, layout validation, fixture-pilot
what-if, isolated aggregate-only MLflow doctor, Brain literature validation,
and `git diff --check`. The isolated sync did not access the Owner MLflow
store. `P2_SCOPE_DEVELOPMENT` remains `ready/planned, not measured` with
`measured_runs=0`, `candidate_count=0`, and `selection_accesses=0` in canonical
campaign state. D2/D3, final-872, protected data, GPU, paid APIs, downloads,
and provider fallback remain untouched. Official Round 2 was not run.

The next reversible action is Owner review of the repaired contract package
or an explicitly requested Official Round 2 review. Do not start measured P2
or selection exposure automatically.

## Official Round 2 P2 contract repair (2026-08-01)

The three remaining findings in
`orchestration/results/official-research-20260801T083801135Z-7e429bcf.json`
are repaired without starting fixture-pilot, measured execution, or selection.
Candidate decisions now use `myis.p2-train-metric.v1` objects with fixed
train/OUT/primary Recall@100 semantics, shared `n`, denominator, and
dataset/config/retriever/evaluator lineage. Scalar `train_score`,
`best_score`, and caller-supplied shortlist thresholds are no longer P2
decision authority.

One `myis.p2-baseline-commitment.v1` artifact must be created after the four
controls and eight preregistered candidates are registered but before the
first train outcome. It binds the `R0-W` baseline to the repository-safe P1
aggregate receipt by raw file SHA-256 and `metrics[8]`. Package validation
resolves and validates that receipt, maps its `maximize` direction to the P2
`higher_is_better` contract, and verifies the expected value, `n`, denominator,
dataset lineage, and evaluator lineage. Baseline reproduction copies the
committed expectation/tolerance and its observed metric must equal the same
candidate's ledger train metric exactly.

Verification passed with `70` focused P2 tests, `222` full tests, one positive
synthetic package validation, two stable report sync/check cycles, layout
validation, isolated MLflow doctor, Brain literature validation, Ruff, and
`git diff --check`. The shared read-model revision is
`876971c17cc8c9bdf513f3c313aa6eb847837e924abda35c019ace4f516a5a96`;
the isolated aggregate-only MLflow run is
`77f08ce884544c89985a8f753bea23bb`. P2 remains
`ready_planned_not_measured` with `measured_runs=0`, `candidate_count=0`, and
`selection_accesses=0`. D2/D3, final-872, protected stores/data, the P2 budget
profile, GPU, paid APIs, downloads, and provider fallback remain untouched.
Official Round 3 was not run.

The next reversible action is Owner review or an explicitly requested Official
Round 3 static review. Do not start measured P2 or selection automatically.

## Official Round 3 P2 static review (2026-08-01)

Official Round 3 is complete with verdict `accept`. The three-round audit is
preserved under `orchestration/audits/p2-readiness/` and the root catalog is
under `orchestration/audits/`. Verdict history is Round 1 `revise`, Round 2
`revise`, and Round 3 `accept`.

This is engineering provenance from a bounded read-only static review, not
scientific or measured evidence. The sanitized runtime record is provider
`openai`, model `gpt-5.6-sol`, Codex CLI `0.146.0`, sandbox `read-only`.
`protected_data_accessed=false`, `fixture_pilot_executed=false`, and
`measured_execution_performed=false`; measured runs, candidates, and selection
accesses remain `0`.

P2 remains `ready_planned_not_measured`. D2/D3, final-872, protected stores and
data, GPU, paid APIs, network model downloads, and provider switching remain
untouched. Round 3 `accept` permits no automatic transition into measured P2
or selection.

## Next action

ถัดไปให้ Owner ตรวจ P2 readiness report และกำหนดรายการ frozen controls ทั้งสี่
รายการก่อน measured campaign freeze จากนั้นจึงรัน fixture/pilot runtime แบบ
ไม่แตะ selection. ห้ามแก้ budget profile หลัง measured run แรก; หากต้องแก้ให้
ออก campaign revision ใหม่
