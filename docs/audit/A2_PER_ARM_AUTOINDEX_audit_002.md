# A2 AP Audit 002: provider evidence and remote-adoption hardening

- Session mode: `AP`
- Phase: `A2_PER_ARM_AUTOINDEX`
- Task: `A2.1 / FROZEN_FIVE_ARM_EXECUTION`
- Source IM handoff: `docs/implementation/A2_PER_ARM_AUTOINDEX_im_001_002.md`
- Reviewed revision: `6a4f2b4e160e80bd2573f70d0f58ef708ccea2b3`
- Routing: `NEEDS_IM`
- Date: `2026-08-12`

## วัตถุประสงค์

ปิด launch-critical evidence gaps ที่เหลือโดยไม่รื้อ operational executor:
ทำให้ provider admission และ remote adoption พิสูจน์จาก hash-bound source artifacts
และ live remote probes จริง ก่อนส่ง LO. ลดภาระ Owner ให้เหลือเฉพาะการต่อ TTL/ยืนยัน
dashboard fact เมื่อ agent ตรวจเองไม่ได้จริง.

## หลักฐานที่ตรวจ

- `PLAN.md`, `HANDOFF.md`, `control/source-of-truth.yaml`
- `docs/audit/A2_PER_ARM_AUTOINDEX_audit_001.md`
- `docs/implementation/A2_PER_ARM_AUTOINDEX_im_001_002.md`
- commits `4b7d84d4`, `eadf27d5`, `374e0a80`, `6a4f2b4e`
- A2 readiness envelope, budget, contract, schemas และ runbook
- `src/myis_research/armindex/a2_execution_readiness.py`
- `src/myis_research/armindex/a2_operational_executor.py`
- focused A2 tests และ clean bundle receipt ใน Owner-local store
- `vast-ssh.md` เฉพาะ aggregate-safe lifecycle/rate/deadline fields

## สิ่งที่ผ่าน

1. Operational executor มี CLI สำหรับ preflight, bundle, admit, stage, execute,
   resume, safe-return และ closeout; exact 52 coverage, tie rejection, ARM-01/02
   non-advancement, interruption/resume และ protected-output guards มี focused tests.
2. Measured authority ถูก harden ให้ต้องเป็น canonical tracked/pushed control,
   worktree clean, `main == origin/main`, bytes ตรง `HEAD` และ goal hash-bound ที่
   ประกาศ authority ตรงกัน. Measured A2 ยังคง `false` และ fail closed.
3. Watchdog แยก identity/heartbeat จาก worker registry และตรวจ PID/start-time/freshness.
4. `33` focused tests, Ruff, report drift, entry preflight และ bundle validation ผ่าน.
   Bundle SHA-256 ปัจจุบันคือ
   `07ac8bde15d7696c7b72a5c304cf2875b006b5a2193da20d7ac2de444cca52d9`.

## Findings ที่ต้องแก้ก่อน LO

1. **Major - provider evidence provenance:** `admit` รับ
   `runtime/model-lockset/data-handoff/management-authority` เป็น raw SHA arguments.
   Admission ตรวจเพียงรูปแบบ hash ไม่ได้พิสูจน์ว่า hash มาจาก file/receipt ใด,
   path ใด, attempt ใด หรือ bytes ปัจจุบันจริง. Provider observation JSON ไม่มี
   required self-hash/source URI binding. Caller จึงสามารถส่ง arbitrary 64-hex values
   แล้วสร้าง PASS receipt ได้หาก fields อื่นผ่าน.
2. **Major - TTL semantics:** admission รับ `ttl_hours=40` จาก caller แต่ไม่มี
   observed `ttl_deadline_utc` หรือการตรวจ remaining time จาก deadline จริง.
   Owner-local record ณ AP review เหลือประมาณ `3.38` ชั่วโมง เทียบกับ minimum
   `32.873` และ required admission `40`; instance ปัจจุบันจึง `NOT_ADMISSIBLE`
   จนกว่าจะมี fresh provider evidence หลังต่อ TTL.
3. **Major - live stage identity:** ก่อน stage มีเพียง `pgrep` ชื่อ A2 process แล้ว
   receipt เขียน `zero_workers_before_stage=true`. ไม่มี live `nvidia-smi` compute
   process check และไม่มีการ re-probe runtime/model/data/SSH identity ให้ตรง admission
   receipt ก่อนสร้าง remote-stage/adoption receipts.
4. **Minor - installed console script:** `pyproject.toml` มี `myis-a2-executor` แต่
   `uv run --no-sync myis-a2-executor` ยังไม่อยู่ใน installed entry points ของ env.
   Module invocation ทำงาน. แก้ packaging test หรือกำหนด module command เป็น canonical;
   ห้ามให้ LO เดาคำสั่ง.

## งาน implementation ที่ขอ

1. เพิ่ม versioned schema/validator สำหรับ sanitized provider observation artifact
   ใน Owner-local store. ต้อง self-hash และ bind อย่างน้อย: attempt, instance,
   observation time, quote time, absolute TTL deadline, remaining seconds/hours,
   all-fee components, management mode/evidence hash, pinned SSH host-key hash,
   live runtime/GPU identity hashes และ source mode. Raw provider payload/credential
   ห้ามเข้า artifact.
2. เปลี่ยน `admit` ให้รับ source artifact paths/receipts แล้วคำนวณ file SHA-256 เอง;
   ห้ามรับ bare runtime/model/data/management hashes เป็น authority. Validate schema,
   self-hash, attempt/freeze bindings, source bytes และ quote age <= 900 วินาที.
3. Admission ต้องคำนวณ remaining TTL จาก `ttl_deadline_utc - now`; require >= 40h
   ตาม active contract และ budget. ห้ามผ่านจาก numeric `ttl_hours=40` ที่ไม่ได้ผูก
   deadline. ถ้าต้องต่อ TTL ให้คืน exact `NEEDS_OWNER_TTL_EXTENSION` เพียง action เดียว;
   หลัง Owner ต่อแล้ว IM ต้องเก็บ fresh evidence และทำงานต่อเอง.
4. ก่อนสร้าง remote stage/adoption receipt ให้ re-probe ผ่าน pinned SSH:
   instance/runtime/GPU UUID set, 4x RTX3090, GPU compute process count = 0,
   A2 worker/process count = 0, model-root hashes, data-handoff hash, bundle hash,
   root absent และ remaining TTL. เปรียบเทียบทุก binding กับ admission receipt.
5. ขยาย remote-stage/adoption schemas ให้ bind live-probe receipt/file hash,
   provider observation hash, absolute watchdog deadline/TTL deadline และ explicit
   zero GPU workers. `zero_workers_before_stage=true` ต้อง derive จาก probe จริง.
6. ทำ failure-injection tests สำหรับ arbitrary-but-valid SHA arguments, source file
   mutation, deadline <40h, stale observation, wrong GPU UUID/runtime/model/data hash,
   nonzero GPU process, nonzero A2 process, SSH host-key drift และ root collision.
7. รักษา measured authority, freeze, metrics, reserve predicate, ARM roles และ
   protected boundaryเดิม. ห้าม provider login/logout, destroy/reprovision หรือ
   measured executionใน IM.
8. Commit/push aggregate-safe changes, verify clean `main == origin/main`, แล้วสร้าง
   clean hash-bound bundle/receipt ใหม่ใน Owner-local storeผูกกับ final commit/tree.

## Validation ขั้นต่ำ

```powershell
uv run --no-sync pytest -q tests/test_armindex_a2_candidate_freeze.py tests/test_armindex_a2_execution_contracts.py tests/test_armindex_a2_execution_readiness.py tests/test_armindex_a2_operational_executor.py <new provider/live-probe tests>
uv run --no-sync ruff check <changed A2 source and tests>
uv run --no-sync python -m myis_research.armindex.a2_entry_preflight_v16 --repository-root .
uv run --no-sync python -m myis_research.armindex.a2_operational_executor --repository-root . --attempt-id a2-im-evidence-dryrun --dry-run
uv run --no-sync myis-report check --repository-root .
git diff --check
```

## ผลส่งกลับที่คาดหวัง

เขียน `docs/implementation/A2_PER_ARM_AUTOINDEX_im_002_001.md` พร้อม final revision,
changed surface, tests, new bundle path/hash, provider/TTL disposition และหลักฐานว่า
live-probe bindings fail closed. Routing:

- `READY_FOR_LO` เมื่อ fresh provider artifact, TTL >=40h, admission, isolated stage,
  watchdog และ adoption พร้อม โดย measured A2 ยังไม่เริ่ม; หรือ
- `NEEDS_OWNER` เฉพาะเมื่อ Owner ต้องต่อ TTL/ยืนยัน dashboard fact ที่ agentทำเองไม่ได้;
  implementation และ tests อื่นต้องเสร็จทั้งหมดก่อนคืน Owner.

ห้ามสร้าง measured-authority control, measured goal หรือเริ่ม candidate execution.
