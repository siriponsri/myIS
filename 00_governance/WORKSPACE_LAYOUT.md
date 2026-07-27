# myIS workspace layout

The workspace has four clear ownership domains and one shared persistence
boundary:

```text
myis-workspace/
  app/       # production application (thaipha-lex)
  research/  # this private repository: evidence, tracks, experiments, outputs, code
  brain/      # local-only Obsidian Mind/QMD curated knowledge and pointers
  tools/      # pinned utilities and adapters
  stores/     # local MLflow, evidence, datasets, model cache, backups
  workspaces/ # disposable runtime sandboxes
  archive/   # preserved legacy paths pending Owner approval
```

The current numbered folders are a migration checkpoint. They remain in place
until handles are closed and the Owner approves each exact move. This document
is the stable vocabulary for new code and documentation; historical path names
are retained only in provenance fields.

Ownership rules:

- App owns production code and raw application evidence.
- Research owns methods, manifests, experiments, and publication outputs.
- Brain owns curated synthesis and navigation pointers, never raw PDFs or web caches.
- Stores owns persistent MLflow and immutable source payloads.
