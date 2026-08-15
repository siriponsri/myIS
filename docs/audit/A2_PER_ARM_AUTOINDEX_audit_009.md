# A2 AP Audit 009: provenance-v2 successor launch readiness

- Session mode: `AP`
- Phase/Task: `A2_PER_ARM_AUTOINDEX / A2.1 FROZEN_FIVE_ARM_EXECUTION`
- Source IM handoff: `docs/implementation/A2_PER_ARM_AUTOINDEX_im_008_001.md`
- Source LO handoff: `docs/long_run/A2_PER_ARM_AUTOINDEX_lo_001_001.md`
- Successor attempt: `a2-im-audit008-provenance-v2`
- Bundle-producing pushed HEAD: `665cdcc76c4619a0a60419978179e1ab6b6d7cf6`
- Bundle tree: `caf451410a2b1dda1c8b4d51a03f324186ff915b`
- Date: `2026-08-15`
- Routing: `READY_FOR_LO`

## AP decision

**PASS: READY_FOR_LO.** The provenance-v2 repair and the changed launch surface
pass one AP acceptance review. AP created a successor pushed-HEAD bundle,
fresh provider observation/admission, isolated staging/adoption, hash-bound
Owner-local manifest and remote transport, then issued authority v2 and the
current LO goal. This AP session started no measured A2, candidate evaluation,
REP-DEV measurement, A3, Selection, Final, or GPU scientific worker.

## Acceptance criteria

- Authority v1 remains historical and cannot authorize execution: **PASS**.
- Canonical false commitment remains unchanged and false; file SHA-256
  `cb3d6a15b1e62342a72d3f9a03e5fbf0a2e6f33c776b1baa1e5c2c88ee6131d5`:
  **PASS**.
- One attempt ID across manifest, transport, observation, binding, admission,
  stage, adoption, genesis, and transport receipt: **PASS**.
- Bundle/adoption/transport equality on bundle SHA, bundle receipt SHA, Git
  commit/tree, and remote root: **PASS**.
- Bundle commit is an ancestor of the authority route, and the complete
  execution-bundle closure is unchanged after the bundle commit: **PASS**.
- Durable interruption, cancellation, process identity, reaping, duplicate-safe
  resume, and recovery behavior: **PASS**.
- Provider observation/admission uses total TTL 84h, initial floor 40h,
  reserve floor `53848s`, USD 50 hard stop, and process-zero: **PASS**.
- Protected boundary excludes qrels, membership, evaluator, query identifiers,
  per-query outcomes, credentials, and raw provider payloads from remote
  transport and tracked projections: **PASS**.

## Successor evidence

Owner-local root:
`../04_Owner_Stores/armindex/a2/a2-ap-audit009-provenance-v2-20260815/`

- Bundle SHA-256: `510171e1e4eace309eae866de4ead9312f1f11c6b380d8fe40d3d59501c11511`.
- Bundle receipt self-hash:
  `25c4920d0c2ca421ab459c1f09b148fbfeee744ea5277cb397817ba63e11ba9f`.
- Owner manifest file/self hashes:
  `432af7aa7bbfa0e52c98c51b19ef15757d8e220f6c875415566d0c657e6188a2` /
  `38a8107d8dc986653e9f7cd36c16e7106439865e17d6f90744b41b758da8bd06`.
- Remote input file/self hashes:
  `8ebb03410f1b4776dc10609a19ba064f45aa05cb1363436bc2838e7daf9c568d` /
  `64da5d94c20ce67fe1e9a89fc508d93cd5225c138da6e395b068c250f5562ff1`.
- Remote transport request SHA-256:
  `8d9ca4f2cc6d9aed1fdaa319aa4f364d5a39e329515068a397dffe199a547d4b`.
- Provider observation/admission self-hashes:
  `a499b36c07888d8d11a6aef5ebafc30da1d9c0b17f4aa16f26a8bca6971466de` /
  `41c4057d1a3aa055698814cf13023de5db7b12dbf9dc994cda42c5d8d375b3d9`.
- Execution adoption self-hash:
  `0581bf85207391b4ebd191d463f98265c0d1587597614079bd94ced745b46eb6`.
- Transport check self-hash:
  `7d258c85a91bdc19c6c66d69fc9fdaeb1fa12c1b87488478212d9f2451a64573`.
- Isolated remote root: `/opt/myis/a2-im-audit008-provenance-v2`.
- Stage and transport GPU/A2 process counts: `0/0`; measured-boundary flags:
  all `false`.

The fresh complete all-fee quote is USD `48.668694688222227816`, within the
Owner-approved USD 50 Task/Run hard stop. Admission recorded `221578` seconds
remaining against deadline `2026-08-17T22:35:12.980077Z`. The instance is Vast
`47700074`, verified as 4x RTX 3090 with 24576 MiB each.

## Focused validation

- Readiness tests: `22 passed`.
- Execution contract tests: `4 passed`.
- Admission/reserve/provenance subset: `8 passed`.
- Remote transport and durable recovery changed surface: `20 passed`.
- Delegated focused checks: `26 + 4 + 1 passed`.
- Ruff, JSON/YAML parsing, budget self-hash, and `git diff --check`: **PASS**.
- Full operational suite exceeded the two-minute command window without an
  assertion failure; the changed launch-critical partitions passed.

## Projection status

- Obsidian/read-model sync: `PASS`, revision
  `c61573b0252186c784df9858380d459f91b828f8a99af3990a38582ff71496f8`.
- Report drift check: `PASS`; quick asset validation: `PASS`.
- The current MLflow generated archive index was refreshed. MLflow doctor is
  `PENDING` because one historical 2026-08-13 archive key
  `20a3f523644ba34a627bea37a3c5ce351a692d769da356428c9d65f782802298`
  points to a mirror receipt that records an earlier deferred sync rather than
  its later run ID. This pre-existing projection lineage mismatch is outside
  the A2 execution closure and does not alter canonical authority, measured
  counters, or launch evidence. Preserve it for a bounded projection repair;
  do not rewrite or delete historical archive evidence during LO.

## Authority and LO handoff

Authority v2 is
`control/armindex/a2/measured-authority/a2-im-audit008-provenance-v2.authority.v2.json`
with self-hash
`5fcd91014acd2a510bec8571815846861598a613eef33a2aa3fb29142e486e41`.
It binds goal `docs/goal/A2_PER_ARM_AUTOINDEX_goal_002.md` with file SHA-256
`25673ad3ae8377f7a075743aad5242674de185f554bc001d8b015a1fd44612dd`.

LO must obtain a fresh authenticated observation/admission immediately before
worker launch, preserve the same successor attempt/adoption/transport equality,
and follow the exact goal. Candidate evaluation and REP-DEV measurement remain
closed even while frozen A2 retrieval execution is authorized.

```text
/goal อ่าน docs/goal/A2_PER_ARM_AUTOINDEX_goal_002.md แล้วทำงานตามขั้นตอนทั้งหมด
```
