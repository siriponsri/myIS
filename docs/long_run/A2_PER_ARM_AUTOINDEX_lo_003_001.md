สถานะโครงการ:
Phase: A2_PER_ARM_AUTOINDEX
Task/Sub-stage: A2.1 / successor v3 pre-authority admission and staging
สถานะสั้น ๆ: LO เก็บ fresh provider/admission และส่งข้อมูล pre-stage ได้ แต่หยุดก่อน stage เพราะ remote root ที่ goal ผูกไว้ไม่ใช่ fresh isolated root.

Publication impact:
หยุดก่อน measured execution เพื่อไม่ให้ผล A2 ปนกับ remote root ที่ provenance ไม่พิสูจน์ได้; จึงยังไม่มี publication metric หรือ claim ใหม่.

Budget:
Phase ceiling: USD 150 (`PLAN.md` / active ArmIndex campaign)
Current Task/Run ceiling: USD 50 (`control/budgets/a2-execution-readiness-v1.json`)
Spent/Accrued: UNKNOWN; no candidate execution occurred
Remaining headroom: UNKNOWN
Estimated cost of next action: ZERO for AP review; provider idle cost UNKNOWN
Next Phase ceiling: NOT_BOUND
Budget status: UNKNOWN_DO_NOT_SPEND

GPU / Vast:
GPU decision: OWNER_ACTION_DESTROY
Reason: instance remains running with no GPU/A2 worker, while the pre-authority attempt cannot safely continue on the non-fresh root.
Instance: 47782993 / running at last authenticated observation
Hourly rate / accrued GPU cost: projected whole-workload USD 48.836444444444438412 for 84 hours; accrued UNKNOWN
Keep-until / destroy condition: destroy after AP confirms no safe-return activity and no replacement attempt will reuse this instance

Session routing:
Recommended next session: AP
Recommended model: GPT-5.6 Sol High
Command before prompt: NONE
Copy-paste prompt: ตอนนี้คุณคือ AP ตาม AGENTS.md อ่าน docs/long_run/A2_PER_ARM_AUTOINDEX_lo_003_001.md แล้วตรวจ fresh admission, unsafe remote-root evidence, safe return และ claim boundary; จากนั้นกำหนดว่าจะทำ successor attempt/root ใหม่เพื่อ publication impact หรือปิด A2 พร้อม exact next-session prompt
Owner decision required: หลัง AP ยืนยันว่าไม่ reuse instance ให้ทำลาย Vast instance 47782993; LO ไม่ทำลาย provider ใน executor

Projections:
Obsidian report (`01_Research/obsidian_report/`): PENDING
MLflow (`01_Research/mlflow/`): PENDING

# A2 LO 003-001: fresh provider pre-authority staging stop

- Session mode: `LO`
- Source goal: `docs/goal/A2_PER_ARM_AUTOINDEX_goal_003.md`
- Attempt: `a2-ap-audit011-v3-full-a2`
- Outcome: `STOP_PREAUTHORITY_UNSAFE_REMOTE_ROOT`
- Scientific authority: `false`
- Measured execution: not started

## Completed pre-authority work

The fresh authenticated observation passed for instance `47782993` with four
RTX 3090 GPUs, zero GPU compute processes, zero A2 processes, a fresh 84-hour
TTL, and an all-fee whole-workload quote of USD 48.836444444444438412. The
fresh binding and admission passed. New safe metadata artifacts were derived
for the Owner-local input manifest, remote retrieval input, and transport v3;
protected qrels and membership were not opened by the derivation helper.

The CPU-local deployment package and its validation passed in hash-only mode.
The session transferred only six pre-stage artifacts to the new incoming root:
instance identity, runtime, model lockset, data handoff, corpus, and queries.
The transfer verification confirmed all six hashes. No qrels, membership,
evaluator, model weights, candidate results, or per-query payloads were
transferred.

## Hard stop

The transfer verifier observed that the exact future remote root
`/opt/myis/a2-ap-audit011-v3-full-a2` existed before the stage command could
create it. A safe structural observation recorded that it was a directory,
not a symlink, with four top-level entries and no GPU/A2 process. The session
did not inspect or modify those entries, did not upload a bundle or watchdog,
and did not run `transport-check`. Goal 003 requires a fresh isolated root and
forbids overwriting, clearing, or silently reusing an existing root, so LO
stopped before stage/adoption.

The incoming root created by this session was independently ownership-checked
and removed. The unexpected target root remains preserved for AP review. No
candidate retrieval, evaluation, REP-DEV measurement, reserve, winner,
Selection, Final, A3, D2, or D3 exposure occurred.

## Evidence pointers

- Fresh provider observation: `../04_Owner_Stores/armindex/a2/a2-ap-audit011-v3-preauthority-20260815/provider-evidence/provider-observation.v2.json`; observation SHA-256 `43e02a0d975e8c6ba5af14df329bfb98da1a65c41506dd712f54e630c2e14864`.
- Fresh instance binding: `stage/provider-instance-binding.v1.json`; binding SHA-256 `8ac9f81ecebad977bbf6049356e17fd91be2c78b639f51febd834f0e1943693a`.
- Fresh provider admission: `stage/provider-admission.v2.json`; receipt SHA-256 `c84ecc1416725b7f6c9c68cc27664a2c2e8ab1e5ce72393d005e2f44e5251f18`.
- v3 pre-authority input derivation: `v3-preauthority-input-derivation.receipt.v1.json`; receipt SHA-256 `f098429e29b2f9674abf01a58ba3983b756c4f05e0f78194f5483db124390176`.
- Deployment package receipt: `deployment-package.receipt.v1.json`; receipt SHA-256 `8d734c75a468fc4eaac86689bfc32a7dcffed476bf03fabc7ff4b0f121c89a8e`.
- Pre-stage verification diagnostic: `remote-prestage-verification-diagnostic.v1.json`; diagnostic SHA-256 `597d8545d26214e9541fab5c35ad6e188df85f9b417add7c8635b0192ab18a12`.
- Unsafe-root observation: `unsafe-remote-root-observation.receipt.v1.json`; receipt SHA-256 `a89e22ccb7cbf433dfbed132867873256214fc94fdc3706ee3cb5751ab59c724`.
- Incoming-only safe return: `remote-prestage-incoming-safe-return.receipt.v1.json`; receipt SHA-256 `94e24f2348db08b437f2a55fd4a2f1c8ce006debc0d4fc5175ada2c9cdb719ba`.

## Recovery and provider disposition

No candidate worker, watchdog, stage receipt, adoption receipt, lifecycle
worker checkpoint, or safe-return archive for the unexpected root was created.
The only remote content created by this LO session was the incoming transfer;
it was removed after exact ownership and hash checks. The unexpected root is
preserved because it was not proven to belong to this attempt. The provider
instance is not destroyed by LO; AP/Owner must decide whether to destroy it or
bind a separately authorized successor attempt.

## AP return checkpoint

AP must not issue authority v3 for this attempt from the current root. A valid
continuation requires a fresh isolated root and fresh hash-bound stage/adoption
chain, or a documented stop if the expected publication impact does not justify
new provider work. This handoff contains operational evidence only and supports
no scientific performance claim.
