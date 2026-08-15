# A2 LO 001-001: pre-launch provenance hard stop

- Session mode: `LO`
- Phase/Task: `A2_PER_ARM_AUTOINDEX / A2.1 FROZEN_FIVE_ARM_EXECUTION`
- Source goal: `docs/goal/A2_PER_ARM_AUTOINDEX_goal_001.md`
- Measured authority: `control/armindex/a2/measured-authority/a2-im-audit007-final-r3.authority.v1.json`
- Attempt: `a2-im-audit007-final-r3`
- Date: `2026-08-15`
- Outcome: `STOPPED_PRELAUNCH_BUNDLE_GIT_DRIFT`
- Routing: `NEEDS_IM`

## Result

LO stopped before fresh provider admission, worker launch, candidate execution,
or protected-input use. No A2 measured result, candidate evaluation, REP-DEV
measurement, Selection exposure, Final exposure, or canonical metric was
created by this session.

The final-r3 verifier failed its required equality assertion:

```text
HEAD == origin/main == execution bundle git_commit
```

At verifier invocation, the tracked clean worktree was at `8f983d7c`, while
the frozen final-r3 bundle and execution-adoption receipt bind commit
`765074a0f3fc1f607b5ba98e4713d9ceeffd2c6f` and tree
`13095f78a9465bb79400e94c7eab8b5caf178c7f`. The authority still correctly
binds the final-r3 adoption receipt SHA-256
`ce15cb10fe71244dae73df71e04221761493ce14cae63a7f92de9babc78866f1`, but it
cannot override the required Git equality chain.

The intervening commits introduced the measured authority, goal, and their
projection refresh after the final-r3 bundle was built. This is provenance
drift, not a dirty worktree or a candidate/input mutation. It is an explicit
hard stop under the goal and runbook.

## Contract conflict evidence

The conflict is enforced by the production code rather than only by the
standalone verifier. `_validate_measurement_authority_provenance` in
`src/myis_research/armindex/a2_operational_executor.py` requires the separate
measured authority to be a tracked file on a clean `main` exactly equal to
`origin/main`. The final-r3 verifier requires that same repository `HEAD` to
equal the immutable bundle's commit. The measured authority and goal were
committed only after that bundle/adoption commit, so no repository revision can
satisfy both predicates for the current final-r3 chain.

## Operational evidence

The local final-r3 verifier reached the Git equality check and stopped before
writing a passing closeout receipt. A subsequent read-only pinned-SSH probe of
instance `47700074` reported:

```text
gpu_processes=0
a2_processes=0
r3_root_exists=true
```

No remote file was changed by the probe, and no provider admission, staging,
execution adoption, safe return, or measured worker was launched during this
LO session.

## Required recovery

An IM repair must produce a non-cyclic provenance path in which the tracked
measured authority, goal, immutable bundle, execution adoption, and the
repository identity that the executor verifies can all be equal without
changing frozen candidate, metric, protected-boundary, budget, TTL, or model
semantics. AP must then audit the successor artifacts and issue a new LO goal
before measured execution resumes. Do not reuse the current final-r3 authority
or adoption receipt for a launch at `8f983d7c`.

## Provider disposition

`OWNER_ACTION_DESTROY`: no immediate authorized reuse remains after this hard
stop, and the executor must not destroy the instance. In the Vast dashboard,
open instance `47700074` and select **Destroy** after confirming no Owner-local
safe-return activity is running. A replacement instance is not authorized by
this LO result.
