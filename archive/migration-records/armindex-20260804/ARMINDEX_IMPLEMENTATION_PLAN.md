# ArmIndex Migration Implementation Plan

This checkpoint was produced after read-only inspection of the existing myIS
repository and all six inbox inputs. It records implementation choices; it does
not authorize measured execution.

## Reuse without changing scientific meaning

- `myis_research` package namespace, deterministic canonical JSON and SHA-256 helpers;
- P1 evaluator, family mapping, manifests, receipts, and validation reports;
- protected-data and unsafe-path scanners;
- serialized writer, journal, checkpoint, resume, and process-identity logic;
- shared read-model fan-out, generated Obsidian reports, Dashboard security, and MLflow read-only viewer;
- historical SCOPE compiler/schema readers for compatibility only.

## Refactor

- root authority and public documentation to ArmIndex;
- shared read model with one versioned `armindex` fragment;
- Dashboard navigation, labels, phase spine, arms, profiles, and historical separation;
- MLflow active experiment registry while retaining legacy runs;
- Brain and Obsidian navigation around the active A0-A6 campaign;
- report records so every active Phase and Task has a generated machine and Markdown report.

## Archive or supersede

- `scope-autoindex-v1` is superseded as the active direction but remains at its
  original paths as `historical_read_only`;
- P2 readiness, fixture, and runtime-resilience records remain engineering history;
- inbox sources are adopted byte-identically, hash-verified, then archived;
- CrossFAM material remains historical proposed direction.

## Create

- `control/campaigns/armindex-multiretriever-v2.yaml` and migration budget;
- versioned ArmIndex adapter, representation, harness, Research Flow, Brain,
  latency/cost, and read-model schemas;
- `src/myis_research/armindex/` for new semantics inside the stable package;
- ArmIndex campaign index, migration manifest/receipt, professional docs, and tests;
- MLflow ArmIndex experiment and safe migration receipt.

## Superseded control authority

`control/campaigns/scope-autoindex-v1.yaml` no longer determines current phase
or active research direction. It remains authoritative only for its historical
campaign. `control/program.yaml`, `control/source-of-truth.yaml`, and the new
ArmIndex campaign record determine current state.

## New schema versions

Historical SCOPE and P2 schemas remain unchanged. New ArmIndex objects use the
schemas under `schemas/armindex/`. The shared read-model v2 container is extended
with a versioned `myis.armindex-read-model.v1` fragment so existing consumers
remain readable while new consumers can validate ArmIndex independently.

## Backward-compatible names

Keep `myis_research`, `scope`, P1/P2 CLI names, historical campaign paths,
manifest IDs, receipt IDs, experiment IDs, and schema IDs. New behavior is
introduced under `myis_research.armindex` and new versioned IDs.

## Names that must not be changed

Do not rename historical P0-P4 IDs, R0/R0-W/R1, request/run IDs, manifest and
receipt filenames, evidence paths, content hashes, old MLflow experiment IDs,
or external Brain/Paper source pointers. Renaming would break lineage or imply
scientific reinterpretation.

## Migration order and rollback

1. Verify clean synchronized main and push the immutable safety branch.
2. Record input hashes and adopt canonical documents.
3. Add ArmIndex control, schemas, package subsystem, tests, and migration records.
4. Extend the shared read model and projections without creating a second pipeline.
5. Register the MLflow experiment append-only and regenerate projections.
6. Run focused, full, drift, layout, safety, store, link, and clean-checkout checks.
7. Commit coherently, pull `--ff-only`, push main, and verify origin SHA.

Rollback uses `archive/pre-armindex-migration-20260804` as a pointer for a new
review branch. It never force-pushes or rewrites main.

## Public documentation

Rewrite README and create architecture, research protocol, productization, use
cases, production profiles, operations, data boundary, model/license policy,
roadmap, contributing, security, changelog, citation, and pending-license docs.
All current-status language must state that measured ArmIndex work has not
started and that production validation is pending.
