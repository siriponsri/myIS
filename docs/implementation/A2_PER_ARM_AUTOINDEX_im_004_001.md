# A2 IM 004-001: fresh-instance deployment readiness

- Session mode: `IM`
- Phase/Task: `A2_PER_ARM_AUTOINDEX / A2.1 FROZEN_FIVE_ARM_EXECUTION`
- Source audit: `docs/audit/A2_PER_ARM_AUTOINDEX_audit_004.md`
- Implementation revision: `62a91784740519f2943e520be82c4405752ce293`
- Routing: `READY_FOR_AP_FRESH_INSTANCE_STAGING`

## สรุปงาน

ปิดงาน CPU-local ตาม audit 004 โดยรักษา historical A2 v1 artifacts ไว้เดิม และเพิ่ม
v2 readiness chain สำหรับ Vast instance ใหม่แบบ runtime-supplied ตั้งแต่ provider
observation, instance binding, admission, live remote probe, isolated stage จนถึง
execution adoption. Instance เดิม `47411176` ถูกปฏิเสธโดยตรง และไม่มี receipt ใหม่
ใดผูกกับ instance นี้

TTL ของ v2 คำนวณจาก fresh absolute deadline เทียบกับ remote observation time และ
ตรวจ admission floor อย่างอิสระด้วย local post-probe time โดยยอม clock lead ได้ไม่เกิน
60 วินาที Live probe ตรวจว่าไม่มี GPU compute/A2 process และ re-probe instance,
runtime, model, data, GPU UUID และ SSH host-key identity ก่อน stage/adoption. Stage
ตรวจ immutable original bundle receipt ซ้ำและ fail closed เมื่อ source/remote identity
paths ไม่ครบ

เพิ่ม deployment package แบบ metadata/hash-only ซึ่งมีสมาชิกเพียง
`A2_DEPLOYMENT_MANIFEST.json` และตรวจ assets ที่มีอยู่แล้วโดยไม่ดาวน์โหลดโมเดลซ้ำ:

- model manifests `ARM-02..05`: `12/12` files ต่อ arm
- Linux wheelhouse: `14/14` declared files พร้อม PASS sidecar
- A1 baseline/journal/closeout handoffs: `28/7/11` files
- A1 safe-return SHA-256:
  `cdbfa4f1073eb738bff54d383f6d17ad0701448e8eef8158559efc24933522f3`
- frozen A1 execution bundle SHA-256:
  `70077bfdbd7f821dc0ec67f99df90cdffe962f011ced3c3da2d50d76dd2e1bf5`
- canonical A1 v16 SSH runtime receipt schema/self-hash, frozen A1 receipt และ final
  A2 bundle/receipt

Validator ปฏิเสธ mutation, symlink, protected-name paths, extra archive members,
caller-created runtime identity ที่ไม่ผ่าน canonical schema/self-hash และ destroyed
instance binding. Package ไม่บรรจุ model bytes, protected payload หรือ provider raw
payload

## Changed surface

- additive A2 readiness controls/envelope v2 และ provider-instance binding
- provider observation/admission/live-probe/stage/adoption/ledger schemas v2
- A2 operational executor, entry preflight และ deployment-package builder/validator
- staging, immutable receipt reuse, TTL/clock-skew และ destroyed-instance regressions
- canonical source-of-truth/read-model/report mapping และ successor ledger record
  `A2EXEC-EV0004`
- `PLAN.md`, `HANDOFF.md`, A2 goal wording และ tracked execution runbook
- generated aggregate-safe report projections

Generated A2 phase/task reports แสดงสถานะตรงกันเป็น
`NEEDS_IM_NEW_INSTANCE_REBIND_MEASUREMENT_LOCKED` และยังคง
`scientific_authority=false`. Production adapter และ matched-first reserve lifecycle
จาก IM 003 ไม่ถูกย้อนกลับเป็น pending

## Focused checks

- focused A2/read-model/report suite: `123 passed` (`31 + 92`)
- Ruff on changed A2/report source and tests: `PASS`
- A2 entry preflight: `PASS`; `a2_execution_authorized=false`
- synthetic operational dry-run: `PASS_A2_SYNTHETIC_OPERATIONAL_DRY_RUN`, 52/52,
  `provider_contacted=false`, `measured_a2_started=false`,
  `protected_payload_included=false`
- `myis-report check`: `PASS`, drift `false`
- `myis-assets validate --mode quick`: `PASS`
- historical readiness v1 contract/envelope/admission/probe/stage/adoption diff:
  `PASS_V1_UNCHANGED`
- `git diff --check`: `PASS`

## Bundle and deployment receipt

Final clean execution bundle และ deployment package สร้างหลัง final handoff commit/push
จาก `main == origin/main` เพื่อให้ bind pushed HEAD จริง โดยเก็บไว้นอก Git ที่
`../04_Owner_Stores/armindex/a2/a2-im-audit004-final-head-20260813/`.
ไฟล์ Owner-local receipt ใน directory เดียวกันเป็น authority สำหรับ final
`git_commit`, `git_tree`, execution bundle/package hashes, manifest hash และ receipt
self-hash. ไม่เขียนค่าเหล่านี้กลับเข้า Git เพราะจะทำให้เกิด commit/bundle hash cycle

คำสั่ง exact สำหรับ deployment build/validate, fresh bind/admit, asset transfer,
isolated stage, watchdog verification, resume, safe return และ closeout อยู่ใน
`control/runbooks/A2_PER_ARM_AUTOINDEX_EXECUTION_V1.md`. Stage แยกจาก measured
`execute` โดยชัดเจน

## Boundaries and next action

IM ไม่ได้ติดต่อหรือ provision provider, ไม่ทำ remote staging, ไม่ดาวน์โหลดโมเดล,
ไม่เปิด protected data และไม่เริ่ม measured A2. Frozen candidate bytes ทั้ง 52,
metrics/tie policy, matched-first reserve predicate, ARM-01/02 non-advancement,
48-hour target, 40-hour admission floor และ USD 35 hard stop ไม่เปลี่ยน

AP ขั้นถัดไปตรวจ Owner-local pushed-HEAD receipts แล้วทำ fresh-instance admission
และ isolated staging เท่านั้น. Measured A2 ยังปิดจนกว่าจะมี separate LO goal และ
tracked measured authority ที่ผ่าน current contract
