# A2 Official Codex Bridge and Candidate Freeze Preparation

## Identity

- Campaign: `armindex-multiretriever-v2`
- Phase: `A2_PER_ARM_AUTOINDEX`
- Task: `OFFICIAL_CODEX_BRIDGE_AND_CANDIDATE_FREEZE`
- Attempt: `a2-prep-20260812-official-codex-freeze-v1`
- Evidence class: `engineering_preparation`
- Scientific authority: `false`
- Goal: `docs/goal/A2_official_codex_bridge_goal.md`

## Assumptions and Direct Change

1. `openai-codex==0.144.4` is the stable Python SDK release used by the bridge;
   its bundled `openai-codex-cli-bin` runtime is authoritative for this attempt.
2. The current MaxPlus process remains rooted at `%USERPROFILE%/.codex`;
   Official subprocesses receive only the allowlisted environment and
   `CODEX_HOME=%USERPROFILE%/.codex-official`.
3. A2 preparation is distinct from measured AutoIndex. The preparation code
   creates, reviews, compiles, verifies, and freezes candidates without calling
   measured evaluation or `advance_autoindex()`.
4. The frozen universe is exactly 40 matched candidates plus 12 dormant
   conditional reserves. `ARM-01` and `ARM-02` are diagnostic non-advancing.

The smallest direct implementation adds one bridge module, one preparation
contract/freezer module, their schemas/templates/tests, additive A2 controls,
and aggregate-safe receipts. Historical A1 and P2 bytes remain unchanged.

## Numbered Execution

1. Confirm A1 terminal lineage with the existing A2 entry preflight and keep
   every measured/provider authorization flag false.
2. Add the A2 five-arm contract, envelope, budget, schemas, and tests. Verify
   `40 + 12`, role symmetry, reserve dormancy, and diagnostic non-advancement.
3. Implement the local-only Official Codex Python bridge with three allowlisted
   operations, explicit child environment, versioned prompts/schemas, model and
   effort observation, Owner-local append-only events, bounded retry, and a
   machine-enforced freeze lock.
4. Run mocked and WhatIf bridge tests, then one synthetic Official smoke call.
   Store raw prompts/responses/events only under the Owner-local event root.
5. Generate all 52 candidates with Official proposer calls and review them in
   independent Official requests. Repair schema/integration failures and retry;
   never synthesize scientific fallback candidates locally.
6. Compile every accepted program twice against a synthetic fixture, run the
   independent deterministic verifier, write the canonical manifest, receipt,
   and freeze lock, then replay validation.
7. Update the single read model and generated A2 Phase/Task report, create the
   pointer-only session capsule under the Brain writer lease, and run the
   focused governance checks.
8. Request one-pass auditor review limited to identity/isolation, protected
   boundary, five-arm counts/roles, freeze hashes, and zero measured work.
9. Repair any bounded auditor findings, commit aggregate-safe files, push, and
   verify `main == origin/main`. Stop before measured A2.

## Checkpoints

- CP0: A1 r15 is `25/25`; A2 authorization false; no candidate manifest.
- CP1: additive controls and focused contract tests prove `40 + 12` and
  non-advancement.
- CP2: mocked, WhatIf, and synthetic Official smoke pass without parent
  environment mutation or protected/measured access.
- CP3: proposer/reviewer receipts cover `52/52` accepted candidates.
- CP4: compile-twice, verifier, manifest self-hash, freeze receipt, and lock
  replay pass with all measured/resource counters zero.
- CP5: report/session/governance checks and one-pass auditor review pass.

## Recovery

- Dependency, SDK compatibility, schema, prompt, bridge, compile, verifier, or
  test failures are repairable before freeze. Record every retry in the ledger.
- A changed prompt/input creates a new request hash and event; it does not alter
  the scientific design or reinterpret a prior receipt.
- After freeze, proposer/reviewer operations remain locked. Only a new campaign
  revision may change candidate/spec/rule bytes.

## Hard Stops

- Protected data, credentials, raw provider payloads, or full inherited
  environments cross the bridge boundary.
- Measured A2, REP-DEV measurement, GPU work, provider admission/adoption,
  HARNESS-DEV, Selection, or Final begins.
- Official model `gpt-5.6-sol`, reasoning `high`, SDK/runtime identity, or
  Official profile isolation cannot be observed after compatibility repair.
- The 52-candidate universe is incomplete, unstable, duplicated, mutated after
  freeze, or violates diagnostic non-advancement.

## Required Artifacts

- Versioned bridge, launcher/config, operation registry, templates, schemas,
  Owner-local event pointer policy, tests, and aggregate-safe smoke receipt.
- A2 campaign/envelope/budget/contract revisions and focused tests.
- Canonical 52-candidate manifest, verification receipt, freeze receipt/lock,
  tracked ledger, generated report update, and pointer-only session capsule.
- Auditor handoff stating `A2_NOT_STARTED` and
  `BLOCKED_PENDING_AUDITOR_REVIEW`.

## Verification Commands

```powershell
uv run --no-sync python -m myis_research.armindex.a2_entry_preflight_v16 --repository-root .
uv run --no-sync pytest -q tests/test_armindex_a2_contract.py tests/test_armindex_official_codex_bridge.py tests/test_armindex_a2_candidate_freeze.py
uv run --no-sync ruff check src/myis_research/armindex tests/test_armindex_a2_contract.py tests/test_armindex_official_codex_bridge.py tests/test_armindex_a2_candidate_freeze.py
uv run --no-sync myis-report sync --repository-root .
uv run --no-sync myis-report check --repository-root .
git diff --check
```

## Terminal Report

Report the exact phase/task/status, Official SDK/runtime/model/effort and smoke
receipt, control and freeze hashes, `matched=40`, `conditional_dormant=12`,
untouched protected surfaces, zero measured/provider counters, exact changed
files/checks, auditor result, commit/push state, and
`next_action=AUDITOR_REVIEW_ONLY` or the auditor-approved A2 handoff state.
