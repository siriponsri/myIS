# A2 AP Audit 007: pushed-HEAD provenance and remote recovery remain launch blockers

- Session mode: `AP`
- Phase/Task: `A2_PER_ARM_AUTOINDEX / A2.1 FROZEN_FIVE_ARM_EXECUTION`
- Source IM handoff: `docs/implementation/A2_PER_ARM_AUTOINDEX_im_006_001.md`
- Reviewed revision: `be9db975ee0b9045520eaf4f85dfe43903dda643`
- Date: `2026-08-15`
- Routing: `NEEDS_IM`

## AP decision

Canonical readiness closure, the Owner-local measured-input manifest, the fresh
non-measured transport receipt, and the pushed-HEAD bundle are structurally
valid. Measured LO is still closed. IM must complete the acceptance criteria in
this audit once, then return to AP for a short pass/fail readiness review. This
audit does not authorize measured A2, candidate evaluation, REP-DEV measurement,
Selection, Final, or any GPU scientific worker.

The current implementation is valuable pre-measurement infrastructure, but the
evidence chain is not yet safe for a multi-hour measured run. The blockers are
launch-critical provenance and recovery defects, not changes to the frozen
scientific design.

## Evidence reviewed

### Pushed-HEAD and Owner-local bundle closure

- Git `main == origin/main`: `be9db975ee0b9045520eaf4f85dfe43903dda643`.
- Bundle SHA-256: `d404dfdf07277d694a79fedebd190ecc7181c5c18edf52208d11e895450cf497`.
- Bundle receipt self-hash: `12c4ef46c4f0493c76c3151fa36d37380339176a6010dc15bf10fe70b8881971`.
- Bundle commit/tree: `be9db975ee0b9045520eaf4f85dfe43903dda643` /
  `ca7452b4733f625dc396d4e6f9380f7cd0a4011a`.
- Owner-local root:
  `../04_Owner_Stores/armindex/a2/a2-im-audit006-owner-input-20260815/`.
- Owner-local manifest SHA-256:
  `08ead13760d7d2aca924a0a1741f1b641ee3ee4fdfd54a8b9866693e36029263`.
- Owner-local manifest self-hash:
  `af15f696e3186350fcc38c06393130cc5b89319d58f2d36b81823c4eb0790c3c`.
- Remote manifest SHA-256:
  `b66540c9675cb3cfb43a602c4443aecd17fb3925fd21e5170a89c7463ed31c59`.
- Transport receipt: `PASS_A2_REMOTE_TRANSPORT_CHECK`.
- Transport receipt self-hash:
  `fb8d5c405ea90d35170901fab184f73fcad0c9a224a762e0d43a3fb1f106a4e5`.
- The transport observation recorded zero GPU compute/A2 processes, no
  measurement, no candidate evaluation, and no protected payload return.

### Focused validation

- Bundle structural validation: `PASS`.
- Owner-local manifest validation: `READY`.
- Focused changed-surface tests: `74 passed in 115.48s`.
- Ruff: `PASS`.
- Entry preflight: `PASS`; measured authority remains false.
- Synthetic operational dry-run: `PASS_A2_SYNTHETIC_OPERATIONAL_DRY_RUN`,
  `52/52`.
- Fresh non-measured remote transport check: `PASS_A2_REMOTE_TRANSPORT_CHECK`.

No measured A2, candidate evaluation, REP-DEV measurement, Selection, Final,
or production CUDA worker was started.

## Launch blockers

1. **Attempt identity is inconsistent.** The adoption receipt identifies
   `a2-im-audit005-final`, the Owner manifest/transport identifies
   `a2-im-audit006-20260815`, and the final bundle receipt identifies
   `a2-im-audit006-final`. The production executor requires adoption attempt
   and execution attempt to be equal and therefore fails closed
   (`src/myis_research/armindex/a2_operational_executor.py:2424`).

2. **Adoption is bound to an old bundle while transport uses pushed HEAD.** The
   existing adoption binds bundle
   `2ba3793e775734f0620850bec088222124d5cf9ed8d972285512bad58ce3d7e2`, while
   the transport runs bundle
   `d404dfdf07277d694a79fedebd190ecc7181c5c18edf52208d11e895450cf497`.
   The execute path does not compare transport bundle SHA, commit, and tree to
   adoption before producing measured receipts
   (`src/myis_research/armindex/a2_operational_executor.py:585` and `:1420`).
   This could make a receipt claim the old adoption while executing new code.

3. **Measurement-authority provenance is not enforced end to end.** The
   transport config declares prospective authority hash
   `6ff16323959c04812fda68e099e7a942b9147ba62c34ea253d5693cc4d479e6d`, but no
   tracked canonical authority file contains it. The remote transport validates
   the request internally but does not compare
   `config.measurement_authority_sha256` to the canonical authority commitment
   (`src/myis_research/armindex/a2_remote_transport.py:242`). No LO goal or
   measured authority may be created until this is repaired.

4. **Remote recovery/process identity is incomplete.**
   `RemoteExecutor.__call__()` discards `heartbeat_path` and `process_path`.
   Remote candidate execution therefore lacks durable per-candidate process
   identity, heartbeat, cancellation, reaping, and resume evidence
   (`src/myis_research/armindex/a2_remote_transport.py:242`; retrieval state
   is also scoped as `rep_dev_measured=false` in
   `src/myis_research/armindex/a2_remote_retriever.py:121`). A session
   interruption cannot prove whether a worker stopped, survived, or was
   duplicated on recovery.

5. **Canonical pointers are stale.** `PLAN.md`, `docs/goal/A2_goal.md`, and
   `control/source-of-truth.yaml` still describe audit 006 transport/manifest
   implementation as pending. The runbook still states a 48-hour staging
   target and does not state the deterministic reserve floor
   `53848` seconds. These are documentation/control inconsistencies and must be
   repaired without changing scientific semantics.

## Provider, TTL, and budget disposition

- Vast instance: `47700074`, running and verified, `4x RTX 3090`, idle at the
  last safe observation; no GPU/A2 process is active.
- Owner-approved TTL: **60 hours total**.
- New absolute deadline: `2026-08-16T22:35:12.980077Z` UTC /
  `2026-08-17T05:35:12.980077+07:00` Bangkok.
- Observed rate: USD `0.575817794/hour`; projected 60-hour compute/storage is
  about USD `34.56`, plus the existing USD `0.30` network reserve, for an
  aggregate envelope about USD `34.85`.
- A2 forward hard stop remains USD `35`; no budget-ceiling increase is needed.

The instance may be kept only for the immediate IM 007 repair and its focused
non-measured checks. IM must stop and AP must reassess when acceptance is
complete, the deadline is no longer sufficient, or the repair cannot be
validated promptly. Do not keep the GPU for a later speculative LO.

## IM 007 acceptance criteria

IM must complete all items below in one implementation session. These are
engineering acceptance tests, not new scientific gates:

1. Reuse instance `47700074`, the uploaded model/wheel/A1 assets, and the
   existing Owner-local manifest. Upload only changed bundle/control files.
2. Unify one attempt ID across Owner manifest, remote transport config,
   adoption, execution, lifecycle ledger, and all derived receipts.
3. Rebuild the clean pushed-HEAD bundle and bind adoption and transport to the
   same bundle SHA, Git commit, and Git tree. The execute path must fail closed
   on any equality mismatch before worker launch or measured receipt creation.
4. Add a tracked canonical measurement-authority commitment and require the
   remote transport to equal it. Do not create an authority that authorizes a
   run; the authority remains absent/false in IM and must be created only after
   this audit's AP review.
5. Add durable per-candidate remote process identity, heartbeat, cancellation,
   reaping, and recovery/resume behavior. A resumed candidate must never be
   duplicated after a durable receipt.
6. Run synthetic/non-measured interruption, stale-heartbeat, cancellation,
   reaping, transport equality, and process-zero checks. Demonstrate that an
   interrupted attempt fails closed and can be recovered without measurement.
7. Refresh provider observation/admission metadata using the 60-hour deadline
   and USD 35 hard stop. Do not destroy, reprovision, or log in/out of the
   provider. Do not re-upload model bytes.
8. Refresh `PLAN.md`, `docs/goal/A2_goal.md`, `control/source-of-truth.yaml`,
   and `control/runbooks/A2_PER_ARM_AUTOINDEX_EXECUTION_V1.md` so they point to
   audit 007, distinguish the initial 40-hour admission floor from the
   deterministic reserve floor `53848s`, and state that measured execution is
   closed pending AP.
9. Run focused tests, Ruff, JSON/YAML parse, synthetic transport checks, and
   `git diff --check`; commit and push tracked aggregate-safe evidence.
10. Write
    `docs/implementation/A2_PER_ARM_AUTOINDEX_im_007_001.md` containing the
    exact revision, changed surfaces, checks, non-measured evidence, remaining
    limitations, and one exact AP prompt.

### Explicit prohibitions

IM must not start measured A2, candidate evaluation, REP-DEV measurement,
Selection, Final, a production CUDA worker, or any protected-data export. IM
must not mutate frozen candidate bytes, metric semantics, evaluator semantics,
budget ceiling, TTL authority, or Owner credentials.

## Next-session routing and loop breaker

After IM writes the result document, run exactly one short AP readiness review
against the acceptance criteria above. That AP either routes to LO or returns
one specific failed acceptance criterion to IM. Do not repeat AP -> IM cycles
without a concrete failed criterion; do not start LO from this audit alone.

Recommended next session: **IM 007**, GPT-5.6 Sol High. Exact prompt:

```text
ตอนนี้คุณคือ IM ตาม AGENTS.md
อ่าน docs/audit/A2_PER_ARM_AUTOINDEX_audit_007.md แล้วทำ acceptance criteria ทั้งหมดให้จบ
ให้ unify attempt identity, bind adoption/transport/measurement authority กับ final pushed-HEAD bundle แบบ end-to-end, เพิ่ม durable remote per-candidate process/heartbeat/cancellation/reaping/recovery, refresh provider observation/admission ตาม Owner-approved TTL 60h และ USD 35 hard stop, ใช้ instance 47700074 และ assets เดิม, รันเฉพาะ synthetic/non-measured interruption and transport checks, ห้ามเริ่ม measured A2/candidate evaluation/REP-DEV measurement
จากนั้น commit/push และเขียน docs/implementation/A2_PER_ARM_AUTOINDEX_im_007_001.md พร้อม exact AP prompt
```

Expected outcome: all acceptance criteria pass, `main == origin/main`, no
measured counter changes, and AP can perform a short pass/fail review without
requesting another architecture cycle.
