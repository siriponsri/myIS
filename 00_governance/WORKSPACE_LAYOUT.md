# myIS workspace layout

The workspace has four clear ownership domains and one shared persistence
boundary:

```text
My_Research/
  00_Projects/00_myIS/
    00_App/      # product repository
    01_Research/ # evidence, tracks, experiments, outputs and code
    02_Brain/    # local-only Obsidian/QMD knowledge and pointers
  01_Stores/00_myIS/ # MLflow, datasets, models and backups
  02_Tools/          # pinned dependencies and environments
  03_Workspaces/     # disposable execution and source staging
  99_Archive/00_myIS/# preserved legacy material
```

The numbered layout is the active final navigation vocabulary. Historical path
names remain only in provenance fields; do not recreate parallel `Projects`,
`Tools`, `Stores` or `ResearchWorkspaces` roots.

Ownership rules:

- App owns production code and frozen historical application evidence.
- Research owns the literature corpus, methods, manifests, experiments and publication outputs.
- Brain owns curated synthesis and navigation pointers, never raw PDFs or web caches.
- Stores owns persistent MLflow, datasets, model cache and backups.
