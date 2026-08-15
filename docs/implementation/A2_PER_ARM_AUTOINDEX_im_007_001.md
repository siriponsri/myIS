# A2 IM 007-001: unified remote provenance and durable candidate recovery

- Session mode: `IM`
- Phase/Task: `A2_PER_ARM_AUTOINDEX / A2.1 FROZEN_FIVE_ARM_EXECUTION`
- Source audit: `docs/audit/A2_PER_ARM_AUTOINDEX_audit_007.md`
- Implementation revision: finalized by the pushed handoff successor recorded below
- Routing: `NEEDS_AP`

## Outcome

IM completed the audit 007 engineering acceptance surface without changing
candidate bytes, model bindings, evaluator/metric semantics, the initial
40-hour admission floor, the deterministic `53848s` reserve floor, the USD 35
forward hard stop, or any protected-data rule. Measured A2, candidate
evaluation, REP-DEV measurement, Selection, Final, and CUDA scientific workers
remain unstarted.

The implementation adds one tracked false measurement-authority commitment and
remote transport v2. The production execute path now fails before output or
worker launch unless attempt ID, bundle SHA, bundle receipt SHA, Git commit,
Git tree, remote root, execution adoption, AP measurement authority, and the
tracked false commitment agree. Remote input validation also binds the same
attempt, Owner-manifest file SHA, remote-input file SHA, and retriever code SHA.

The new Linux candidate supervisor persists PID plus `/proc` start identity,
attempt-bound heartbeat, cancellation, reaping, recovery count, and durable
result. An OS-released per-candidate lock prevents concurrent recovery. A dead
worker's completed stdout is made durable before any relaunch, while a valid
durable result returns without launching a worker.

## Changed surface

- `control/armindex/a2/measurement-authority-commitment.v1.json`
- `schemas/armindex/a2-measurement-authority-commitment.v1.json`
- `schemas/armindex/a2-remote-measured-transport.v2.json`
- `src/myis_research/armindex/a2_execution_readiness.py`
- `src/myis_research/armindex/a2_operational_executor.py`
- `src/myis_research/armindex/a2_remote_transport.py`
- `src/myis_research/armindex/a2_remote_candidate.py`
- focused A2 tests and the active PLAN/goal/source-of-truth/runbook pointers

## Focused validation

- Changed-surface A2 suite: `74 passed`
- Remote/authority subset: `37 passed`
- Candidate supervisor regressions: `7 passed`
- Ruff on changed Python/test surfaces: `PASS`
- JSON/YAML parse: `PASS`
- `git diff --check`: `PASS`
- Synthetic operational dry-run: `PASS_A2_SYNTHETIC_OPERATIONAL_DRY_RUN`,
  `52/52`, provider contacted `false`, measured A2 started `false`

## Pushed-HEAD and remote evidence

The final post-push Owner-local closeout is under:

`../04_Owner_Stores/armindex/a2/a2-im-audit007-final-20260815/`

That directory contains the exact pushed-HEAD bundle/receipt, refreshed
provider observation and v2 admission, unified execution adoption, remote
transport v2 config/request, non-measured transport receipt, and synthetic
interruption/cancellation/reaping/recovery evidence. AP must use the successor
artifacts in that directory, not the older audit 005/006 attempt identities.

Implementation code revision: `PENDING_FIRST_PUSH`.
Final handoff revision: represented by the final pushed `main` used to build
the successor bundle; the exact commit/tree and bundle hashes are in the
Owner-local bundle receipt and transport request.

## Claim boundary and limitations

This is launch-critical engineering evidence only. The tracked commitment says
scientific authority is false and measured A2 is unauthorized. AP must perform
one short readiness review and create a separate tracked measured authority and
current LO goal before any measured launch. Provider lifecycle control remains
Owner-dashboard based; IM did not log in/out, rotate credentials, reprovision,
destroy, or download/re-upload model bytes.

## Exact AP prompt

```text
ตอนนี้คุณคือ AP ตาม AGENTS.md
อ่าน docs/implementation/A2_PER_ARM_AUTOINDEX_im_007_001.md และ
docs/audit/A2_PER_ARM_AUTOINDEX_audit_007.md แล้วตรวจ acceptance criteria แบบ
pass/fail เพียงรอบเดียว โดยตรวจ successor artifacts ใน
04_Owner_Stores/armindex/a2/a2-im-audit007-final-20260815/ ว่า attempt ID เดียวกัน,
final pushed-HEAD bundle/adoption/transport equal กัน, canonical measurement-authority
commitment ยัง false, durable remote interruption/cancellation/reaping/recovery ผ่าน,
provider observation/admission ใช้ TTL 60h และ USD 35 hard stop และ process-zero ผ่าน
ห้ามเริ่ม measured A2/candidate evaluation/REP-DEV measurement ใน AP session นี้
จากนั้นถ้าผ่านให้สร้าง current measured authority/LO goal ตาม contract และแนะนำ exact
next session prompt; ถ้าไม่ผ่านให้คืน IM เพียง acceptance criterion ที่ fail แบบเจาะจง
```
