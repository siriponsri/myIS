# Owner Handoff / สรุปสำหรับ Owner

อัปเดตจาก canonical records, fixture provenance และ measured evidence ณ 2026-08-01 เอกสารนี้ใช้เพื่อ
orientation เท่านั้น หากขัดกับ control files, schemas, manifests, receipts หรือ
measured evidence ให้ยึด `control/source-of-truth.yaml`

## สถานะตอนนี้

- Phase: `P2_SCOPE_DEVELOPMENT`
- Task: `P2.1`
- Phase status: `ready_planned_not_measured`
- Evidence class: fixture engineering provenance; scientific authority `false`
- Source execution commit: `fc4409ebdf7989e2bc0019eef20e8b8cc50030d5`
- Fixture: `p2-fixture-pilot-v1`, status `passed`
- `P1_CPU_BASELINE`: `P1_CPU_MEASURED_COMPLETE`
- `P2_SCOPE_DEVELOPMENT`: fixture passed; measured P2 not started
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

## P2.1 repository-only fixture closeout (2026-08-01)

The deterministic fixture pilot passed on synthetic repository-only inputs.
It exercised 32 synthetic candidates, five adaptive iterations, a four-item
synthetic shortlist, and one fixture-only selection exposure. Two independent
temporary lifecycle runs produced matching canonical hashes, and all 94
fail-closed negative checks rejected as required.

The canonical request remained strictly `myis.p2-request.v1`; fixture metadata
was recorded separately in the validated execution manifest and final fixture
receipt. The receipt SHA-256 is
`6e032d5f4f6ad28d604fe317297eeaa8ea91654611f5ca99de43001fce7bd125`
and the fixture package SHA-256 is
`0f8376e5ff2713fd56484ef8f8df8a36a56defadfcc6faefa18c7e2f5ff8fea9`.
The isolated aggregate-only MLflow run is
`64d48729899745e1a18d6e386ba15187`.

Measured runs, real candidates, real shortlist, and real selection accesses
remain `0`. Protected data, measured stores, final-872, D2/D3, GPU, paid APIs,
network model downloads, and provider fallback were not accessed. This is
engineering evidence only and creates no scientific claim.

## P2 Owner-local preflight and candidate proposal (2026-08-02)

Implementation commit `8b47d3350f99c33f55355b85bd39b222d4181a80`
adds the repository-safe P2 preflight receipt/schema, read-only preflight
runner and CLI, fail-closed validation, projection/report state, and an exact
four-control/eight-candidate Owner-review proposal.

The proposal self-hash is
`38156c8dbcdaf56ad0593b6afad118f83ac23b438ab1ecae6debc9968b9339b8`.
It remains `draft_owner_review` and `not_adopted`; all proposed entries retain
`registered=false` and `hash_locked=false`. The Owner-local preflight was not
executed, so `preflight_status=not_started`. Measured runs, real candidates,
real shortlist, and real selection accesses remain `0`.

The full deterministic suite passed with `262` tests. Report sync/check,
read-model-only drift, report schema/content validation, layout, full asset
validation, session audit, P2 closure and archive-runtime policies,
repository-safe MLflow doctor, Brain literature validation, scoped Ruff, and
`git diff --check` also passed. The final shared read-model revision is
`30c34be047b367a19d18bc8ccb4625ab6c82270394b66a468d22499eaf8d7f03`
with SHA-256
`f1076cad0d68a748483d76a6f8ee62d96ad4a6679c4064b2a6b0b43033743d11`;
the aggregate-only projection sync MLflow run is
`6dea0156a4134f7c8576f2f5a54f2cce`.

Protected store contents, qrels, membership, query IDs, rankings, per-query
outcomes, final-872, D2/D3, GPU, paid APIs, network model downloads, provider
state, measured requests, candidate ledgers, baseline commitments, shortlist
freeze receipts, and real selection receipts remain untouched.

## Next action

ขั้นถัดไปที่ได้รับอนุญาตคือ `Owner-local measured preflight` โดยต้องเริ่มเป็นงาน
แยกต่างหาก ห้ามเริ่ม measured P2, real selection หรือ final evaluation อัตโนมัติ

## P2 preflight completion repair (2026-08-02)

Completion audit `p2-preflight-completion-audit-20260802` initially returned
`Weak Reject` with four blocking gaps: stale live authority, asymmetric
store/worktree overlap, duplicate free-space accounting on one volume, and
incomplete negative-path coverage. Repair commit
`c13592c4ccba4235991459899801c022d6eb8623` closes those gaps and also requires
exact receipt check/failure consistency, rejects unsafe immutable output
traversal, and scans partial or invalid canonical P2 lifecycle artifacts.

Post-repair audit `p2-preflight-completion-repair-20260802` returned `Accept`
with no blocking findings. Focused preflight tests passed `38`; the full suite
passed `292` with one pre-existing Starlette warning. Dashboard/report/policy
focused tests passed `90`, Obsidian/preflight focused tests passed `47`, and
report sync/check passed twice without drift. Layout, full assets, session
audit, P2 closure policy, archive-runtime policy, repository-safe MLflow
doctor, Brain literature validation (`154` notes, `0` errors), scoped Ruff,
and `git diff --check` all passed.

Generated projections were committed separately at
`955e55d6620566edb3e11a8c9797cd1d42fc6f70`. The shared read-model revision is
`b205e5a9ede542334d955e96b0913763261bdf8fec1619f2c2e5645093025957`
with SHA-256
`4bff54d2899142aa4df20dcc25e39fc4e725e1582442bbf2e1b751bb89695c8c`;
the aggregate-only projection sync MLflow run is
`491abbc0c7cf4e6d85bf7636a5c0d9e0`.

Phase/task remains `P2_SCOPE_DEVELOPMENT / P2.1` with status
`ready_planned_not_measured`, preflight `not_started`, proposal
`draft_owner_review` and `not_adopted`, and all real measured-run, candidate,
shortlist, and selection counters at `0`. No measured request, baseline
commitment, protected store access, final-872, D2/D3, GPU, paid API, provider
change, or protected payload access occurred. The exact next authorized action
remains `Owner-local P2 measured preflight`.

## P2 report byte-stability recovery (2026-08-02)

The post-merge completion audit found one additional reporting failure: a clean
Windows checkout passed read-model-only CI but failed the full report check on
17 internal generated paths. Text-normalized content matched the deterministic
renderer; Git had converted LF output to CRLF because the MLflow archive,
compatibility projection, and Phase/Task JSON roots lacked explicit byte
preservation.

Audit `p2-preflight-report-byte-drift-audit-20260802` retained the finding as
`Weak Reject`. Repair commit `f192acb7a5d01227ef91b9594b6a63c312ce31dd`
adds checkout-stable generated-output attributes, a regression over every
repository-local projection byte stream, and the auditable failure/recovery
binding. Post-repair audit `p2-preflight-report-byte-drift-repair-20260802`
returned `Accept` with no blocking findings. Generated projection commit
`9b614a582587175219b594a8355c149b458d15d8` binds the recovery to shared
read-model revision
`c68e57feb22f284e4ff9e98d87c6807c1993dfaa9cb9e5fc0467a28ef09c0f33`
and SHA-256
`54c1762501c339ca506ab48391074674d10105ccb024fa84bf88c04efe9b3aa0`;
the aggregate-only projection sync MLflow run is
`0bbdce0ae1d64a95966d7b4d6ab682bb`.

Verification passed with `293` full tests, `48` focused Obsidian/preflight
tests, two consecutive full report checks without drift, session audit,
layout, P2 closure policy, archive-runtime policy, scoped Ruff, and
`git diff --check`. The P2 Phase/Task records expose both byte-audit artifacts
and one `repaired_and_validated` recovery with `counters_changed=false`.

Phase/task remains `P2_SCOPE_DEVELOPMENT / P2.1`, status
`ready_planned_not_measured`, evidence class engineering/fixture provenance,
scientific authority `false`, preflight `not_started`, and proposal
`draft_owner_review` / `not_adopted`. Measured runs, real candidates,
shortlist, and selection accesses remain `0`. Protected stores and payloads,
final-872, D2/D3, GPU, paid APIs, network downloads, and provider state were
not accessed or changed. The exact next authorized action remains
`Owner-local P2 measured preflight`.

## P2 projection source-hash portability recovery (2026-08-02)

PR #5 exposed a second portability layer after generated output bytes were
stabilized. The Linux contract job reproduced drift in `164` repository-local
files because P0 contract and literature digest hashes were computed from
checkout-dependent source bytes. Paired clean Windows and LF clones then
identified two additional raw-hash surfaces: the P2 proposal source bindings
and the historical P1 execution envelope.

Audit `p2-preflight-projection-source-hash-drift-audit-20260802` retained the
contradiction as `Weak Reject` with three blocking findings. Commits
`890b8e02ce6063969a6bf460032815ea0799e3fd`,
`c5893809edbba2de717b28bd5d28b1b246d7a4d0`, and
`41e2610001e21f47165f99dad5f347e3bc6da23b` preserve committed LF bytes for
every raw-hashed source found by the audit. Recovery audit
`p2-preflight-projection-source-hash-drift-repair-20260802` returned `Accept`
with no blocking findings. Commit
`c2102180da46e7338a6ab41de2a921f3a61e70a1` binds the failure/recovery chain
into the P2 Phase and Task reports, and projection commit
`3b5c7474de243d42ee79089644db22e23f951d92` refreshes the shared graph.

Clean Windows and LF clones produced identical read models and all `225`
repository-local rendered outputs had byte diff `0`; the checkout regression
passed `3` tests in each clone. Verification also passed with `293` full tests,
`48` focused Obsidian/preflight tests, `21` focused Dashboard/API tests, two
consecutive full report checks without drift, session audit, advisor
validation, layout, full assets/map, P2 closure and archive-runtime policies,
repository-safe MLflow doctor, Brain literature validation (`154` notes,
`0` errors), scoped Ruff, unsafe-path scan, and `git diff --check`.

The shared read-model revision is
`964f0aeb17e043c96596c262515fd5c6b611b484416e36ba99b10d0903c1a7d3`
with SHA-256
`4ff3b80ba623058c14ba2561abf9cb2dbc524b7b6cfa6d655547b581aeb09f3a`;
the aggregate-only projection sync MLflow run is
`eeb9bae6422b41528e324c625ba343c6`.

Phase/task remains `P2_SCOPE_DEVELOPMENT / P2.1`, status
`ready_planned_not_measured`, evidence class engineering/fixture provenance,
scientific authority `false`, preflight `not_started`, and proposal
`draft_owner_review` / `not_adopted`. Measured runs, real candidates,
shortlist, and selection accesses remain `0`. Protected stores and payloads,
final-872, D2/D3, GPU, paid APIs, network model downloads, and provider state
were not accessed or changed. The exact next authorized action remains
`Owner-local P2 measured preflight`.

## P2 runtime resilience v2 closeout (2026-08-03)

The interrupted v1 implementation is retained under
`archive/p2-runtime-resilience-v1-interrupted/` with a sanitized patch and
SHA-256 manifest. Its Windows PID liveness probe was unsafe and the attempt had
no tracked continuity ledger, so it is historical and superseded.

Future P2 measured requests use campaign revision
`scope-autoindex-v1-p2-r1-primary-v2`, budget profile
`control/budgets/p2-r1-primary-v2.yaml`, execution envelope
`control/execution-envelope-p2-v2.yaml`, and tracked runbook
`control/runbooks/P2_MEASURED_AUTORESEARCH_V2.md`. The profile permits 32
candidates, a 432000-second wall clock, a 345600-second measurement budget, an
86400-second overhead reserve, and a 10800-second per-candidate timeout.

The measured runtime now uses an OS-held advisory lock, process creation
identity, an immutable hash-chained event journal, a rebuildable state snapshot,
detached `start|resume|status|verify|stop-after-checkpoint` supervision,
checkpointed candidate execution, partial-index quarantine, one infrastructure
retry, terminal scientific failure semantics, selection compare-and-swap, and
allowlisted worker/candidate/proposer environments. Start and resume require
explicit Owner-local store and cache roots.

The first repository-wide retry retained `309 passed / 15 failed` and exposed
three compatibility defects. A later detached synthetic soak found a sanitized
environment bootstrap defect; the child now receives only the resolved package
source root. The first full-suite closeout command was terminated by its
120-second command timeout, then the identical command passed with a longer
ceiling. The recovered closeout passed `328` full tests,
`49` graph/Dashboard/safety tests, `31` focused runtime tests, `20`
compatibility tests, two consecutive zero-drift report checks, and a disposable
clean-checkout regression with `4` tests plus a read-model-only PASS. Session,
advisor, layout, full assets/map, P2 closure, archive-runtime, measured-control,
unsafe-path, repository-safe MLflow doctor, Brain literature (`154` notes,
`0` errors), scoped Ruff, and
`git diff --check` also passed. Recovery audit
`p2-runtime-resilience-v2-recovery-20260803` returned `Accept` with no blocking
finding.

`AGENTS.md` now requires every agent-contract update to create or update a
linked Brain pointer in the same session. Brain YOLO mode is effective for
aggregate-safe pointer memory immediately after acquiring the serial-writer
lease; it does not bypass Owner gates, protected-data rules, deletion approval,
measured authorization, or commit/push authority.

Cross-session capsule
`20260803T133528Z-p2-runtime-resilience-v2-closeout-v1` validates against
implementation commit `831872ff1720117e2d44c115e15e7cba0a4bb236` with six
events, ten immutable references, and three explicit open threads. The
identical audit/projection bytes have SHA-256
`c34dbf628c641d211dac4f1a36039f11bba40b7674e2bc394e8e6bdf146870f1`.

Post-capsule verification passed the full suite again with `328` tests in
`252.40` seconds, two stable report cycles at revision
`5f5277c8ec1d5a80834469743994be33147331784060e2595a5e74376e0a646f`,
read-model SHA-256
`d64276b9c262f42d76cafacb5fced247d589359e70deaa5d8d560de77a789707`,
and repository-safe MLflow doctor with 38 archive runs and 452 safe artifacts.
Scoped Ruff over every Python path changed by this branch passed. A broader
repository-wide Ruff invocation exposed eight pre-existing findings in
unrelated legacy/P1 files; they remain explicit lint debt and were not mixed
into this repair. The Observatory fixture `--check` command also materialized
seven generated fixture files; those command-created changes were restored to
their committed bytes because this closeout does not refresh fixture evidence.

This is engineering preparation only. Measured P2, real candidates, shortlist,
selection, final-872, D2, and D3 remain closed with real counters at zero. The
next authorized action remains exactly `Owner-local P2 measured preflight`.

## P2 tracked Owner-path safety recovery (2026-08-02)

The completion audit expanded the repository-safe path scan beyond P2 JSON
objects and found two tracked personal absolute paths: an MLflow store example
and the default legacy DAPFAM root in the Owner-local P1 launcher. Audit
`p2-preflight-tracked-owner-path-audit-20260802` retained the contradiction as
`Weak Reject` with one blocking finding.

The repair replaces the MLflow example with `%LOCALAPPDATA%`, makes the legacy
launcher fail closed unless the Owner explicitly sets
`MYIS_LEGACY_DAPFAM_ROOT`, and adds a deterministic tracked-artifact scan that
excludes Owner Notes and local Obsidian state. Recovery audit
`p2-preflight-tracked-owner-path-repair-20260802` returned `Accept` with no
blocking findings. The launcher fail-closed probe returned exit code `2`
before any data access.

Verification passed with `294` full tests, `39` focused P2 preflight tests,
`21` focused Dashboard/API tests, two consecutive full report checks without
drift, session audit, advisor validation, layout, full assets/map, P2 closure
and archive-runtime policies, repository-safe MLflow doctor, Brain literature
validation (`154` notes, `0` errors), scoped Ruff, and `git diff --check`.
The aggregate-only projection sync MLflow run is
`0c81d60e46a44a3d87f7d6961686d39d`.

Phase/task remains `P2_SCOPE_DEVELOPMENT / P2.1`, status
`ready_planned_not_measured`, evidence class engineering/fixture provenance,
scientific authority `false`, preflight `not_started`, and proposal
`draft_owner_review` / `not_adopted`. Measured runs, real candidates,
shortlist, and selection accesses remain `0`. Protected stores and payloads,
final-872, D2/D3, GPU, paid APIs, network model downloads, and provider state
were not accessed or changed. The exact next authorized action remains
`Owner-local P2 measured preflight`.
