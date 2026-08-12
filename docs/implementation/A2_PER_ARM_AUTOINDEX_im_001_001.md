---
schema_version: myis.research.implementation-handoff.v1
phase: A2_PER_ARM_AUTOINDEX
task: A2.1_FROZEN_FIVE_ARM_EXECUTION
session_mode: IM
source_audit: docs/audit/A2_PER_ARM_AUTOINDEX_audit_001.md
revision: 4b7d84d48263df5e7c1b45d55b6620cbb2cb9497
status: IMPLEMENTED_LOCAL_VALIDATED_REMOTE_BLOCKED
---

# IM Handoff

## Summary

เพิ่ม operational A2 executor แบบ fail-closed และรักษา measured lock เดิมไว้ครบ
local synthetic dry-run ตรวจ frozen universe 52 candidates, winner 5 arms,
dormant reserve 12 candidates, watchdog และ checkpoint/resume ได้โดยไม่ติดต่อ
provider และไม่สร้าง measured evidence

## Changed surface

- `src/myis_research/armindex/a2_operational_executor.py`: CLI `preflight`,
  `bundle`, `admit`, `stage`, `execute`, `resume`, `safe-return`, `closeout`,
  `--dry-run`; owner-local connection parsing; pinned SSH/SCP transport;
  isolated-root staging; watchdog PID/start identity; heartbeat; append-only
  checkpoints; OS-held attempt lock; aggregate result adapter; exact 52 coverage;
  tie rejection; dormant reserve policy; ARM-01/02 non-advancement; separate
  hash-bound measured authority gate.
- `src/myis_research/armindex/a2_execution_readiness.py`: added operational
  executor and receipt schemas to bundle closure; watchdog hash binds script
  bytes; validated bundle receipt now returns its checked fields.
- New schemas: `a2-candidate-result-receipt.v1.json`,
  `a2-remote-stage-receipt.v1.json`, `a2-execution-closeout-receipt.v1.json`,
  `a2-measured-execution-authority.v1.json`.
- `tests/test_armindex_a2_operational_executor.py`: failure-injection,
  exact-coverage, tie, protected-boundary, safe-return, watchdog and resume tests.
- `pyproject.toml`: `myis-a2-executor` entrypoint.

## Checks

- Focused A2 suite: `45 passed`; new operational tests: `8 passed`.
- Ruff changed source/tests: passed.
- New JSON schemas parse successfully.
- A2 entry preflight: `PASS_A2_ENTRY_PREFLIGHT`; `a2_execution_authorized=false`.
- Synthetic dry-run: `PASS_A2_SYNTHETIC_OPERATIONAL_DRY_RUN`; `52` candidates,
  `40` matched, `12` dormant reserve, `5` winners,
  `measured_a2_started=false`, `provider_contacted=false`.
- `git diff --check`: passed.

## Remote disposition

`VAST_CLI_UNAVAILABLE`; fresh all-fee quote, TTL, and management-authority
evidence were unavailable. Existing Owner-local `vast-ssh.md` was not treated
as fresh admission evidence. No remote root, watchdog, worker, provider destroy,
measured A2, retrieval, or REP-DEV access occurred.

## Protected surfaces

Candidate manifest/freeze/lock, A1 receipts/root, qrels, membership, query IDs,
per-query outcomes, credentials, raw provider payloads, D1/D2/D3 and metric
semantics were untouched.

## Next action

AP should review the operational path and provide a new goal-bound authority plus
fresh provider evidence before any measured session. Routing: `NEEDS_AP` for
launch-critical authority/staging review; remote disposition `BLOCKED_EXTERNAL`.
