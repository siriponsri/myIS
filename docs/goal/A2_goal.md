---
title: "A2 goal: frozen five-arm AutoIndex execution"
phase_id: A2_PER_ARM_AUTOINDEX
status: NEEDS_IM_PROVENANCE_AND_REMOTE_RECOVERY_REPAIR
lifecycle: BLOCKED
evidence_class: engineering_execution_readiness
scientific_authority: false
claim_boundary: "Fresh admission, isolated staging, Owner-local manifest, and non-measured remote transport are implemented and validated. This guide still does not authorize measured A2 until IM repairs attempt/bundle/authority provenance and durable remote recovery, then AP performs a short readiness review."
last_material_update: 2026-08-15
next_authorized_action: IM_REPAIR_ATTEMPT_BUNDLE_AUTHORITY_PROVENANCE_AND_REMOTE_RECOVERY_DO_NOT_MEASURE
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

Audit 003 implementation เสร็จแล้ว: tracked production adapter ตรวจ frozen program bytes,
ใช้ A1 v16 runtime/model/materialization/evaluator bindings และปล่อยเฉพาะ aggregate-safe
result; executor รัน 40 matched ก่อนสร้าง fresh reserve decision/continuation เสมอ.
Audit 004 implementation เพิ่ม current v2 fresh-instance binding, แก้ stage probe/TTL
และสร้าง hash-only CPU-local deployment package จาก local assets เดิมแล้ว. Goal นี้ยัง
ห้าม measured launch จน AP read-back, fresh admission/staging และ measured authority ผ่าน.
Audit 005 implementation ปิด canonical bundle closure โดยรวมทั้ง v1/v2 envelope,
เพิ่ม append-only readiness successor และระบุ A2 disposition เป็น
`FRESH_INSTANCE_REQUIRED` โดยตรง; A1 `REUSE_ELIGIBLE` คงอยู่เป็น lineage เท่านั้น.

Audit 006 passed fresh v2 admission and isolated staging on Vast instance
`47700074`, ending at `EXTERNAL_EXECUTION_REQUESTED_NOT_LAUNCHED`. IM 006 then
added the production remote transport and real Owner-local measured input
manifest, and separated the 40-hour initial floor from the frozen-runtime
reserve floor. Audit 007 found that measured LO remains closed because attempt
identity, final pushed-HEAD bundle, canonical authority, and durable remote
recovery are not yet bound end to end. The USD 35 hard stop and frozen
scientific semantics remain unchanged.

```text
DO_NOT_LAUNCH: transport and Owner-local manifest exist, but attempt/bundle/authority provenance and durable remote recovery remain incomplete.
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
- Current readiness envelope, budget และ contract: `control/execution-envelope-a2-readiness-v2.yaml`,
  `control/budgets/a2-execution-readiness-v1.json`,
  `control/armindex/a2/execution-readiness-contract.v2.json`. v1 เป็น historical
  compatibility และห้ามแก้ receipt เดิม.
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

2. AP fresh-instance admission and staging only

   1. Re-run the A2 entry preflight. It must report A1 terminal PASS, planned A2,
      `a2_execution_authorized=false`, fresh A2 provider admission/adoption required and
      a new isolated root required.
   2. Validate the clean pushed-HEAD execution bundle and hash-only deployment package.
      The package contains only manifests, hashes and safe pointers; model/wheel/protected
      bytes remain in Owner-local stores.
   3. Collect fresh aggregate-safe provider evidence for the runtime-supplied new Vast
      instance and build the additive instance-binding receipt: identity,
      4x RTX 3090, runtime/model/data hashes, SSH evidence, all-fee quote and management
      authority. Prefer authenticated Vast CLI. `OwnerDashboardSsh` is valid only with
      pinned SSH runtime/GPU evidence and `OWNER_MANUAL_DASHBOARD_DESTROY_READY`.
   4. Apply the Owner-approved target of `60` hours total and require all-fee
      whole-workload admission for all 52 candidates with at least `40` hours
      remaining from the fresh absolute deadline, USD `35` forward hard stop,
      no unknown fee and no partial-arm quote. Do not
      login/logout, destroy/reprovision the provider, infer a budget default or reuse an
      A1 admission/adoption receipt.
   5. Upload the hash-validated local assets without downloading models. Only after
      admission PASS, create a new `/opt/myis/a2-<attempt-id>` root, re-probe the
      instance/runtime/model/data/GPU/process identity, stage and hash-validate the bundle,
      install the watchdog and write the append-only lifecycle checkpoint and v2 A2
      execution-adoption receipt. A1 root stays read-only.
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

- Before LO, IM must complete audit 007 without changing frozen scientific semantics,
  then AP must perform a short launch-readiness review and create the separate tracked
  measurement authority/LO goal. Preserve append-only evidence and do not alter frozen
  candidate bytes or the v1/v2 campaign/envelope/budget/execution contract.
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
