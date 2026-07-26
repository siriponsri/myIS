# Owner Gates

## Default rule

If an agent is uncertain, detects drift, sees conflicting evidence, or lacks a
required fact, it must stop and ask the Owner. Silence is not approval.

## Destructive actions

Every delete or removal requires a separate YES/NO question that identifies the
exact file or directory. Moving an item to `Archive` is preferred and is not a
delete, but the move still requires scope to be clear.

## Research gates

| Gate | Required evidence | Owner action |
|---|---|---|
| R0 restructure | Three repos, validated imports, pinned tools, cutover report | Approve research readiness |
| R1 track start | Scope, approved inputs, budget ceiling, protected split declaration | Open one track |
| R2 Top-3 review | Path KM graph, evidence table, cost/risk/falsification for all three | Select exactly one path |
| R3 measured run | Gate 0/1 evidence, manifest, model/provider pin, batch benchmark plan | Approve API/GPU/Vast budget |
| R4 held-out | Frozen method, code, prompt/skill, candidate pool where applicable | Approve one confirmatory pass |
| R5 publication | Claim-evidence audit, limitations, provenance and artifact inventory | Approve submission package |

Track order is C, R, S. Opening a later track does not implicitly reopen an
earlier track or Paper D.

## Tool-specific boundaries

- Claude alone executes HyperResearch.
- A HyperResearch recommendation never authorizes implementation.
- Experience Brain writes need a separate Owner gate.
- A bootstrap-only MLflow smoke must be tagged `stage=bootstrap`; it may not log
  scientific metrics or touch a research dataset.
- No provider fallback is allowed in confirmatory API runs unless it is pinned
  and declared in advance.

