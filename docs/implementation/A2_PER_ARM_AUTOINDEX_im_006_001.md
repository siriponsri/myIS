# A2 IM 006-001: hash-bound remote measured transport

- Session mode: `IM`
- Phase/Task: `A2_PER_ARM_AUTOINDEX / A2.1 FROZEN_FIVE_ARM_EXECUTION`
- Source audit: `docs/audit/A2_PER_ARM_AUTOINDEX_audit_006.md`
- Implementation revision: `f519c1b4` (`Implement hash-bound A2 remote measured transport`)
- Routing: `NEEDS_AP`

## Outcome

Implemented the launch-critical remote execution boundary without changing the
frozen A2 candidate membership, ARM-01/02 non-advancement, matched-first barrier,
tie policy, evaluator semantics, checkpoint contract, USD 35 hard stop, or
protected-data policy. The production adapter now requires a hash-bound remote
transport and fails closed instead of silently launching the CUDA-bound engine
on local Windows.

The transport is split at the protected boundary:

- Vast receives only the remote retrieval input manifest, opaque corpus/query
  inputs, frozen model paths, and the tracked pushed-HEAD bundle.
- Vast returns opaque top-100 rankings and aggregate retrieval timing only.
- Owner-local evaluation opens qrels and membership and constructs the final
  aggregate candidate receipt locally.
- Remote transport checks reject qrels/membership/evaluator fields, measured
  flags, non-zero GPU compute processes, and non-zero A2 processes.

## Owner-local measured input manifest

The real manifest was built and validated from the existing A1 v16/runtime/model
and Owner-local protected assets. It is outside Git at:

`../04_Owner_Stores/armindex/a2/a2-im-audit006-owner-input-20260815/input-manifest.json`

Safe manifest file SHA-256: `08ead13760d7d2aca924a0a1741f1b641ee3ee4fdfd54a8b9866693e36029263`.
The derived hash/count-only handoff metadata is alongside it as
`bindings/data-handoff.v16.json`; it combines the A1 v15 protected handoff
commitments with the A1 v16 qrels/membership commitment view. Protected bytes,
qrels, membership, credentials, and model weights were not copied into Git or
the implementation document.

## TTL and budget repair

Initial provider admission remains a separate exact `40 * 3600` second floor.
Reserve admission now derives its minimum remaining TTL from the frozen
runtime projection:

`ceil(worst_case_dense_parallel_critical_path_seconds - matched_dense_parallel_critical_path_seconds + owner_ttl_reserve_seconds)`

Current canonical value: `53848` seconds (about `14.96` hours), using the frozen
unfinished reserve path plus the existing `21600` second / six-hour reserve.
The whole-workload quote and USD `35` forward hard stop remain unchanged.

## Vast transport validation

The existing Vast instance and endpoint from `vast-ssh.md` were reused:

- instance: `47700074`
- endpoint: `root@179.255.148.147:10355`
- remote root: `/opt/myis/a2-im-audit005-final`
- remote bundle SHA before pushed-HEAD refresh:
  `2ba3793e775734f0620850bec088222124d5cf9ed8d972285512bad58ce3d7e2`
- remote bundle Git provenance before pushed-HEAD refresh:
  commit `daf124ace981e070d012cca6d8c0feaed607d41a`, tree
  `4b355ddaf7ccdbda5696080b007e5cdbfd7bf1fe`

The non-measured transport check passed with status
`PASS_A2_REMOTE_TRANSPORT_CHECK`, provider instance `47700074`, GPU compute
process count `0`, A2 process count `0`, candidate evaluation `false`,
REP-DEV measurement `false`, and protected payload returned `false`.
The check also verified the remote bundle bytes, remote retrieval manifest
self-hash, corpus/query hashes, and absence of qrels/membership/evaluator fields.

The Owner-local transport configuration and remote retrieval manifest remain
outside Git at the same Owner store root. No model was re-uploaded. Corpus and
query opaque inputs were transferred once for transport validation; qrels and
membership were not transferred.

## Focused validation

- Focused A2 adapter/owner-engine/operational/remote-transport suite: `74 passed`
- Additional remote transport and measured adapter subset: `17 passed`
- Ruff on all changed Python/test surfaces: `PASS`
- Python bytecode compile check for `src/myis_research/armindex`: `PASS`
- Remote synthetic/non-measured transport check: `PASS_A2_REMOTE_TRANSPORT_CHECK`
- Initial 40-hour floor, reserve `53848` second floor, sufficient/insufficient
  reserve checks: `PASS`
- `git diff --check`: `PASS`

No measured A2, candidate evaluation, REP-DEV measurement, Selection, Final, or
production CUDA worker was started. No measurement authority was created.

## Known limitations and AP handoff

The remote check above used the already staged audit-005 bundle. After this
document commit is pushed, IM must build the clean pushed-HEAD execution bundle
and refresh the Owner-local transport receipt/config to that bundle before AP
reviews launch readiness. The remote retrieval module is included in the new
bundle closure; model bytes remain reused from the existing validated incoming
tree.

Exact AP prompt:

```text
ตอนนี้คุณคือ AP ตาม AGENTS.md
อ่าน docs/implementation/A2_PER_ARM_AUTOINDEX_im_006_001.md
ตรวจผล implementation, Owner-local manifest, reserve TTL separation และ
พิจารณา pushed-HEAD execution bundle/remote transport provenance ที่อยู่ใน
04_Owner_Stores/armindex/a2/a2-im-audit006-owner-input-20260815/
จากนั้นตรวจ launch readiness เฉพาะ surface ที่เปลี่ยน โดยยังห้ามเริ่ม measured
A2, candidate evaluation หรือ REP-DEV measurement และแนะนำ next session พร้อม
exact prompt ตาม AGENTS.md
```

AP should verify the final pushed-HEAD bundle, measurement-authority provenance,
fresh provider evidence, protected boundary, and budget/TTL before creating any
measured LO goal. Measured execution remains closed.
