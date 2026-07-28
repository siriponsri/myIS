# myIS Research 1.0 repository structure decisions

The design follows common research-repository guidance: separate importable
source from tests, keep experiments/notebooks first-class but isolated, keep
large or sensitive data outside Git, and make generated artifacts disposable.
The workspace additionally separates product, research, knowledge, tools, and
persistent stores because they have different owners and release policies.

## Applied decisions

- One repository has one purpose. App, Research, and Brain remain separate Git
  histories rather than nested copies of `myIS` or `Projects`.
- Research has six stable concerns: governance, evidence, tracks, experiments,
  outputs, and code. Internal numbering is a temporary navigation checkpoint,
  not part of Python imports or public APIs.
- Importable Python lives only in `05_code/src/myis_research`; tests live only
  in `05_code/tests`; notebooks and their configs live by experiment version.
- Persistent MLflow, datasets, model cache, backups, and raw source payloads
  live under workspace Stores, not inside a repository.
- Brain contains curated notes, reports, knowledge-graph links, and source
  pointers. It does not duplicate PDFs, web caches, or experiment artifacts.
- Archive-first cleanup preserves provenance. Exact deletion groups require an
  Owner decision recorded in `CLEANUP_APPROVALS.md`.
- Active research tracks are `02_tracks/00_C_crossroute/` and
  `02_tracks/01_S_skillopt/`. Historical ranking/evidence material remains
  read-only under `02_tracks/99_legacy/01_R_ranking_evidence/` and is excluded
  from active navigation and emitters.
- Track C and Track S may duplicate approved documents or artifacts only with a
  source path and SHA-256 recorded next to each duplicate. Symlinks are not an
  allowed substitute for an auditable duplicate.

## Final naming vocabulary

Use `app`, `research`, `brain`, `tools`, `stores`, `workspaces`, and `archive`
in new documentation and interfaces. Retain older paths only in source
manifests, migration maps, and historical records. A physical outer-folder
rename is deferred until process handles are closed and the Owner approves the
exact move set.
