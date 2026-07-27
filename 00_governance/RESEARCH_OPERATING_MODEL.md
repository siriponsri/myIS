# Research Operating Model

## System boundaries

```text
App canonical evidence and datasets
              |
              v
Research repo: methods, manifests, experiments, papers
       |                         |
       v                         v
Brain: status/decisions     MLflow: run lineage
       |
       v
Experience Brain: approved cross-session knowledge only
```

The Research repo owns scientific truth for new work. Brain is a readable
control plane, not a replacement for manifests or results. Experience Brain is
append-only long-term memory, not a PDF cache. HyperResearch workspaces are
staging areas, not canonical repositories.

## Evidence workflow

```text
approved PDF/web/deep-research inputs
  -> Claude HyperResearch evidence synthesis
  -> Top-3 path KM graph for one track
  -> Owner selects Top-1
  -> DEV implementation and leverage gates
  -> frozen method and manifest
  -> Owner-held-out gate
  -> publication artifact package
```

## Optimizer policy

- GEPA is a shared optimizer/comparator, not a fourth track.
- SkillOpt is the primary Track S hypothesis, not a foregone conclusion.
- SPEAR may be a diagnostic comparator when per-example errors justify it.
- Track C optimizes exposure; Track R freezes the candidate pool before ranking;
  Track S optimizes a reusable procedural skill and initially uses C as its
  environment.

## Positive publication policy

Each track must define a useful positive contribution that remains valid even
when the primary method does not win: a benchmark, diagnostic taxonomy,
validated boundary, transfer finding, or reproducible efficiency result. Claims
must follow measured evidence; the publication narrative cannot redefine a
failed primary endpoint after seeing held-out results.

