---
title: "A2 goal: frozen five-arm AutoIndex execution"
phase_id: A2_PER_ARM_AUTOINDEX
status: BLOCKED_PENDING_MEASURED_ADAPTER_AND_RESERVE_LIFECYCLE
lifecycle: BLOCKED
evidence_class: engineering_execution_readiness
scientific_authority: false
claim_boundary: "This guide consumes the immutable 52-candidate freeze only. It does not generate or mutate candidates, and it does not authorize measured A2 until fresh admission and adoption receipts pass."
last_material_update: 2026-08-12
next_authorized_action: RUN_IM_AUDIT_003_DO_NOT_LAUNCH_THIS_GOAL
---

# A2: คู่มือ long run หลัง five-arm candidate freeze

## สถานะและเส้นทาง

Candidate freeze ผ่านแล้ว แต่ A2 ยังไม่เริ่มวัดผล. Universe ที่อนุญาตมีเพียง
`40` matched และ `12` conditional reserve ที่เป็น `dormant_conditional` รวม `52`
รายการตาม manifest ที่ freeze แล้ว. ห้าม generate, replace, edit, re-score เพื่อเลือก
candidate ใหม่ หรือ reinterpret manifest เดิม.

`ARM-01` และ `ARM-02` เป็น diagnostic non-advancing: เก็บผล within-arm ได้หลัง
launch ที่ถูกต้อง แต่ห้ามมีผลต่อ promotion, A3 eligibility, Selection eligibility หรือ
primary winner. `ARM-03`, `ARM-05`, `ARM-04` เป็น primary advancement arms. Reserve
เปิดใช้ได้เฉพาะ predicate ที่ freeze แล้ว: two matched batches complete, strict primary
improvement, grounded axis remaining และ fresh budget admission PASS.

ก่อน Owner launch ต้องผ่าน `AP audit` แบบ one-pass เฉพาะ Official identity/isolation,
protected boundary, count/role/non-advancement, manifest/freeze hashes และ zero measured
work. Auditor แก้ได้เฉพาะ engineering/test/pointer/documentation mismatch ขนาดเล็ก;
ห้าม mutate candidate หรือเปิด measured A2.

Goal นี้ยังห้าม launch. AP audit 003 พบว่า production measured adapter และ
matched-first reserve lifecycle ยังไม่ครบ; staging bundle ปัจจุบันจะถูก invalidated
ทันทีเมื่อแก้สองส่วนนี้. ใช้ `docs/audit/A2_PER_ARM_AUTOINDEX_audit_003.md` กับ IM ก่อน.

```text
DO_NOT_LAUNCH: return to IM audit 003.
```

การ launch นี้ยังไม่ใช่อำนาจให้วัดผล. Session นี้ต้องจบก่อน measured retrieval,
REP-DEV measurement, candidate evaluation, worker execution หรือเปิด A3, HARNESS-DEV,
Selection, Final, D2 หรือ D3.

## หลักฐานที่ต้องตรึง

- Manifest: `campaigns/armindex-multiretriever-v2/manifests/a2-five-arm-candidate-manifest.v1.json`
  SHA-256 `f6276e3a15e760187152270418e00ce4cae4d8efe45b13edb02c4742e3b3049e`.
- Freeze receipt: `campaigns/armindex-multiretriever-v2/evidence/a2-five-arm-candidate-freeze.receipt.v1.json`
  SHA-256 `ea93db368c3e740f7914e07e2bdfc15052991f6f05976f6924acdce717392e10`.
- Freeze lock: `control/armindex/a2/candidate-freeze.lock.v1.json`
  SHA-256 `c01f683b909e6f4c6310c01855b3f79319a183b7950f91338d43baa8a2d57952`.
- Readiness envelope, budget และ contract: `control/execution-envelope-a2-readiness-v1.yaml`,
  `control/budgets/a2-execution-readiness-v1.json`,
  `control/armindex/a2/execution-readiness-contract.v1.json`.
- A1 terminal/promotion/evaluator bindings อยู่ใน readiness contract และ freeze receipt;
  ห้ามใช้ A1 adoption receipt เป็น A2 authority หรือเขียนทับ A1 root.

## ขั้นตอนปฏิบัติ

1. AP audit ก่อนเปิด A2

   1. อ่าน goal นี้, `PLAN.md`, readiness envelope, budget, contract, runbook และ ledger
      เท่านั้น. ห้าม historical sweep, protected store หรือ REP-DEV.
   2. ยืนยัน freeze replay, count `40+12=52`, ARM-01/02 non-advancement, counters เป็น
      zero และ bridge lock ปฏิเสธ `representation_propose`/`representation_review`.
   3. รัน focused audit commands:

      ```powershell
      uv run --no-sync pytest -q tests/test_armindex_a2_candidate_freeze.py tests/test_armindex_a2_execution_contracts.py tests/test_armindex_a2_execution_readiness.py
      uv run --no-sync ruff check src/myis_research/armindex/a2_candidate_freeze.py src/myis_research/armindex/a2_execution_readiness.py tests/test_armindex_a2_candidate_freeze.py tests/test_armindex_a2_execution_contracts.py tests/test_armindex_a2_execution_readiness.py
      uv run --no-sync python -m myis_research.armindex.a2_entry_preflight_v16 --repository-root .
      ```

   Checkpoint AP: all focused checks pass; no protected data, candidate evaluation,
   measured A2, provider admission/adoption, GPU scientific work, or REP-DEV measurement.
   On failure, repair only the failing engineering surface and rerun AP. Do not launch LO.

2. Deferred until IM audit 003 closes: fresh readiness and staging

   1. Re-run the A2 entry preflight. It must report A1 terminal PASS, planned A2,
      `a2_execution_authorized=false`, fresh A2 provider admission/adoption required and
      a new isolated root required.
   2. Build and validate the clean hash-bound bundle. It may contain allowlisted code,
      controls, schemas, hashes and aggregate-safe pointers only.
   3. Collect fresh aggregate-safe provider evidence for instance `47411176`: identity,
      4x RTX 3090, runtime/model/data hashes, SSH evidence, all-fee quote and management
      authority. Prefer authenticated Vast CLI. `OwnerDashboardSsh` is valid only with
      pinned SSH runtime/GPU evidence and `OWNER_MANUAL_DASHBOARD_DESTROY_READY`.
   4. Apply the Owner-approved target of `48` hours remaining and require all-fee
      whole-workload admission for all 52 candidates with at least `40` hours
      remaining from the fresh absolute deadline, USD `35` forward hard stop,
      no unknown fee and no partial-arm quote. Do not
      login/logout, destroy/reprovision the provider, infer a budget default or reuse an
      A1 admission/adoption receipt.
   5. Only after admission PASS, create a new `/opt/myis/a2-<attempt-id>` root, stage and
      hash-validate the bundle, install the watchdog and write the append-only lifecycle
      checkpoint and A2 execution-adoption receipt. A1 root stays read-only.
   6. Emit `EXTERNAL_EXECUTION_REQUESTED_NOT_LAUNCHED`, append one material ledger entry,
      and stop. This is the terminal state for the launch/readiness session.

   Checkpoint after IM and AP restaging: bundle, provider-admission, isolated root, watchdog and adoption receipts
   are hash-bound to the immutable freeze. `measured_retrieval_allowed=false`; no child
   worker, retrieval, candidate evaluation, REP-DEV measurement or result receipt exists.

3. Measured-A2 handoff only

   A later explicitly authorized measured-execution session may consume the A2 adoption
   receipt and frozen manifest. It must never generate/mutate candidates, must preserve
   ARM-01/02 non-advancement, and must fail closed on exact ties, hash drift, budget/TTL
   violation, lifecycle failure, protected output or incomplete coverage. This guide grants
   no authority to begin that session.

## Recovery and hard stops

- Before LO, audit 003 is an engineering repair loop only. Preserve append-only evidence;
  do not alter frozen candidate bytes or the v1 campaign/envelope/budget/execution contract.
- During LO, stop before staging on stale/partial quote, quote above USD `35`, TTL below `40` hours remaining,
  missing management authority, wrong instance/GPU/runtime/model/data hash, protected output,
  manifest/receipt/lock drift or any nonzero measured counter.
- Stop immediately on a request to create/mutate candidates, access REP-DEV for measurement,
  run GPU scientific work, start a worker, use A1 root as A2 output, destroy/reprovision the
  instance, or open A3/HARNESS-DEV/Selection/Final/D2/D3.
- A candidate/spec/rule change after freeze requires a new campaign revision. Never reinterpret
  the frozen manifest, combine partial attempts or use outcome-driven repair.

## Required artifacts and closeout

- Preserve the existing manifest, freeze receipt and lock exactly.
- Maintain only `control/armindex/a2/execution-ledger.v1.jsonl` for material LO transitions.
- Produce hash-bound bundle, provider-admission, execution-adoption and lifecycle-checkpoint
  receipts only when their prerequisites actually occur; raw provider payloads, credentials,
  qrels, membership, query IDs, rankings and per-query outcomes remain Owner-local.
- Run the focused tests/Ruff above, `git diff --check`, and only the report/session validation
  implicated by an actual projection or Brain change. Commit/push only aggregate-safe changes
  and verify `main == origin/main`.

Terminal report for this guide:

```text
phase/task: A2_PER_ARM_AUTOINDEX / FROZEN_FIVE_ARM_READINESS
ap_audit: PASS | FAILED_CLOSED
lo_readiness: PASS_NOT_LAUNCHED | FAILED_CLOSED | NOT_STARTED
candidate_freeze: matched=40 conditional_dormant=12 total=52 <manifest/receipt/lock hashes>
diagnostic_non_advancing_arms: ARM-01, ARM-02
measured_a2_started: false
rep_dev_accessed_for_measurement: false
provider_admission_or_adoption_performed: <actual aggregate-safe status>
protected_surfaces_untouched: <aggregate-safe statement>
changed_files: <exact paths>
checks: <commands and results>
next_action: OWNER_AUTHORIZATION_FOR_SEPARATE_MEASURED_A2_SESSION
```
