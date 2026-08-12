# A2 AP Audit 001: operational executor and evidence handoff

- Session mode: `AP`
- Phase: `A2_PER_ARM_AUTOINDEX`
- Task: `A2.1 / FROZEN_FIVE_ARM_EXECUTION`
- Routing: `NEEDS_IM`
- Date: `2026-08-12`

## วัตถุประสงค์

ทำให้ A2 พร้อมส่งต่อ LO โดยเร็วที่สุด: มี operational orchestrator ที่ทำงานจริง,
fresh provider admission, isolated staging, watchdog/checkpoint/recovery,
measured-result receipt path, safe return และ closeout ที่เก็บหลักฐานพอสำหรับงาน
journal โดยไม่เปลี่ยน frozen scientific semantics หรือข้าม measured authority.

## หลักฐานที่ตรวจ

- `PLAN.md`, `HANDOFF.md`, `control/source-of-truth.yaml`
- `control/campaigns/armindex-multiretriever-v2.yaml`
- `control/decisions/D1_START_CAMPAIGN.yaml`
- `docs/goal/A2_goal.md`
- `control/execution-envelope-a2-readiness-v1.yaml`
- `control/budgets/a2-execution-readiness-v1.json`
- `control/armindex/a2/execution-readiness-contract.v1.json`
- `control/runbooks/A2_PER_ARM_AUTOINDEX_EXECUTION_V1.md`
- `control/armindex/a2/execution-ledger.v1.jsonl`
- `src/myis_research/armindex/a2_execution_readiness.py` และ focused tests
- A2 freeze independent audit และ A1 r15 remote-retention audit
- owner-local `vast-ssh.md` เฉพาะ aggregate-safe operational fields; ไม่คัดลอก credential

## Findings ที่มีผลต่อการส่งต่อ

1. Candidate freeze ปิด `PASS`: `40 matched + 12 dormant reserve = 52`;
   manifest/freeze/lock self-hashes คือ `f6276e...3049e`, `ea93db...2e10`,
   `c01f68...7952`; ARM-01/02 ต้องคง diagnostic non-advancing.
2. A1 r15 ปิด measured `25/25`, safe return ผ่าน และ instance เคยถูกจัดเป็น
   `REUSE_ELIGIBLE`; ห้ามรวมกับ r13 และห้ามเขียนทับ A1 root.
3. A2 admission attempt ล่าสุดคือ ledger `A2EXEC-EV0002 / FAILED_CLOSED` เพราะ
   ยังไม่มี fresh complete all-fee quote, TTL และ management authority. AP recheck แบบ
   read-only วันที่ 2026-08-12 ติดต่อ TCP/SSH ได้, พบ GPU `4`, GPU worker `0` และ A2
   root `0`; instance จึงพร้อมให้ IM ตรวจ/stage แต่ admission ยังต้องพิสูจน์จาก fresh
   complete provider evidence และห้ามอนุมานจากข้อความ `RUNNING` เพียงอย่างเดียว.
4. Readiness library ผ่าน 23 focused tests และ Ruff แต่ยังไม่ใช่ executor จริง:
   `A2MeasuredRunner` ระบุว่าไม่เริ่ม process/provider call, ต้อง injected executor,
   ส่วน train evaluator/receipt รับ synthetic fixture เท่านั้น. ไม่มี CLI ที่ทำ
   bundle -> admit -> stage -> watchdog -> execute/resume -> safe return -> closeout.
5. Local `main` อยู่ที่ `9ccb271e` และนำ `origin/main` (`929f6927`) สอง commits;
   มี generated projection/Obsidian changes ค้าง 280 tracked files. ห้าม discard หรือ
   เขียนทับโดยไม่ตรวจที่มา. Clean-pushed bundle requirement ต้องแก้ด้วย workflow ที่
   preserve งานเดิม เช่น validated commit แยกและ clean temporary worktree.
6. Measured A2 ยังถูก lock โดย active envelope/contract. IM สร้างและทดสอบ executor,
   ทำ fresh admission/adoption และ stage ได้ตาม readiness envelope แต่ห้ามเริ่ม
   candidate evaluation หรือ measured retrieval.
7. `control/decisions/D1_START_CAMPAIGN.yaml` ยังบันทึก campaign/scope แบบ historical
   SCOPE/P1/P2 ขณะที่ active ArmIndex controls อ้าง D1 เป็น standing authorization และ
   lock measured A2 ไว้ `false`. IM ห้ามแก้ authority หรือเปิด measurement; หลัง IM
   ต้องให้ AP ตรวจและ material-refresh active goal/execution authorization ตาม canonical
   ArmIndex policy โดยไม่สร้าง Owner micro-gate เพิ่ม.

## งาน implementation ที่ขอ

1. สร้าง CLI/orchestrator production path โดย reuse A1 v16 lifecycle/worker/safe-return
   patterns และ A2 frozen library ปัจจุบัน. ต้องรองรับคำสั่งแยกชัดเจนอย่างน้อย:
   preflight/bundle, provider admission, isolated stage/adoption, dry-run, resume,
   measured execution (locked by authority), safe return และ closeout.
2. ทำให้ remote workflow ใช้งานจริง: SSH host/key/fingerprint มาจาก owner-local
   `vast-ssh.md` โดยไม่พิมพ์หรือ commit credential; ตรวจ instance/GPU/runtime/model/data
   hashes, fresh all-fee quote อายุไม่เกิน 900 วินาที, TTL 40 ชั่วโมง, hard stop USD 35,
   management authority และ zero workers. ใช้ authenticated Vast CLI ก่อน; ถ้าใช้
   `OwnerDashboardSsh` ต้องครบ fallback evidence และ
   `OWNER_MANUAL_DASHBOARD_DESTROY_READY`. ห้าม login/logout, rotate credential,
   reprovision หรือ destroy instance.
3. หลัง admission `PASS` เท่านั้น ให้สร้าง root ใหม่ `/opt/myis/a2-<attempt-id>`,
   stage/rehash bundle, ติดตั้ง watchdog ที่หยุดงานได้จริง, บันทึก process identity,
   heartbeat และ append-only checkpoint/ledger. A1 root เป็น read-only.
4. เติม production measured-result and evaluator adapter path ที่ consume frozen executor
   output และสร้าง canonical aggregate-safe receipts ได้จริง; test-only fixture ต้องไม่
   ถูก promote เป็น measured evidence. ผูก candidate/arm/program/data/evaluator/code/model,
   primary/secondary metric, latency, cost, coverage, failure/resume, reserve predicate,
   input/output hashes และ deterministic tie handling โดยไม่ส่ง qrels, query IDs,
   membership, rankings หรือ per-query outcomesเข้า Git/MLflow/Dashboard/Paper.
5. ทำ exact-coverage closeout สำหรับ 52 frozen candidates และ per-arm winner receipts;
   reserve 12 ตัวคง dormant จน predicate เดิมผ่าน, ties ต้อง fail closed, ARM-01/02
   ห้าม advance. ห้ามสร้าง/แก้/re-score candidate และห้ามเปลี่ยน metric semantics.
6. ทำ safe-return archive allowlist, checksum validation, protected scan, worker teardown,
   same-attempt evidence และ canonical closeout/claim-evidence pointers. หลักฐานสำหรับ
   journal ต้องแยก engineering/operational/measured ชัดเจน และ numeric claims ทุกค่า
   resolve ไป immutable receipts/manifests ไม่ใช่ log หรือ projection.
7. รักษา dirty worktree เดิม. ตรวจ deterministic generated changes ที่ค้างก่อนตัดสินใจ
   commit; stage เฉพาะไฟล์ที่ตรวจแล้ว. Push aggregate-safe commits ที่จำเป็นเพื่อสร้าง
   clean hash-bound bundle. อย่ารอ Owner สำหรับ engineering repair ที่อยู่ในขอบเขตนี้.
8. ถ้า remote ยัง unreachable ให้ทำ local implementation, synthetic end-to-end dry-run,
   tests และ bundle preparation ให้ครบก่อน แล้วบันทึก `BLOCKED_EXTERNAL` เฉพาะขั้น
   fresh provider admission/staging; ห้ามหยุดเพื่อถาม Owner เว้นแต่ต้องใช้ Owner-only
   dashboard fact หรือ credential/account action จริง ๆ.

## ขอบเขตที่ต้องคงเดิม

- Frozen candidate bytes, roles, count, hashes, primary/secondary metrics และ reserve
  predicate ห้ามเปลี่ยน.
- ห้าม measured A2, REP-DEV measurement, A3, HARNESS-DEV, Selection, Final, D2, D3,
  paid API, model download หรือ provider switch ใน session IM.
- Protected membership/qrels/query IDs/per-query outcomes, credentials และ raw provider
  payloads ต้องอยู่ Owner-local.
- Historical r13/r15 receipts และ remote A1 root ห้ามแก้หรือรวมผล.
- IM ห้ามเปลี่ยน D1/D2/D3 หรือ measured authorization; ส่งประเด็น authority binding
  กลับ AP พร้อม implementation result.

## Validation ขั้นต่ำ

```powershell
uv run --no-sync pytest -q tests/test_armindex_a2_candidate_freeze.py tests/test_armindex_a2_execution_contracts.py tests/test_armindex_a2_execution_readiness.py <new focused tests>
uv run --no-sync ruff check <changed A2 source and tests>
uv run --no-sync python -m myis_research.armindex.a2_entry_preflight_v16 --repository-root .
<new A2 CLI> --dry-run --repository-root .
git diff --check
```

เพิ่ม failure-injection tests สำหรับ stale/partial quote, hash drift, wrong root, dead
watchdog, interrupted worker/resume, incomplete 52 coverage, exact tie, protected member,
safe-return checksum และ ARM-01/02 advancement rejection. รัน report/projection validation
เฉพาะเมื่อ IM เปลี่ยน surface นั้น.

## ผลส่งกลับที่คาดหวัง

เขียน `docs/implementation/A2_PER_ARM_AUTOINDEX_im_001_001.md` ระบุ revision, exact
changed surface, checks, CLI/staging path, remote disposition, journal-evidence artifacts,
ข้อจำกัด และ routing เดียวสำหรับ AP. หาก launch-critical semantics/boundary/recovery
เปลี่ยนให้ส่ง `NEEDS_AP`; ถ้าไม่เปลี่ยนและ remote staging/adoption พร้อมให้ส่ง
`READY_FOR_LO`. ห้ามสร้าง LO prompt หรือเริ่ม measured run ใน session IM.
