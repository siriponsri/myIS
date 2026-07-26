# Restructure Status

Updated: 2026-07-26 Asia/Bangkok

## Target layout

```text
My_Research/
  Projects/myIS/App/       independent product repository
  Projects/myIS/Research/  independent publication repository
  Projects/myIS/Brain/     shared Codex/Claude Obsidian vault repository
  Stores/myIS/             persistent stores and migration audits
  Tools/                   pinned shared runtimes
  Workspaces/              disposable tool workspaces
  Archive/myIS/            preserved legacy paths
```

## Current blockers

- App still resides at `Projects/myIS/App/thaipha-lex` because Windows denied a
  metadata-only directory rename while a process held an open handle.
- Brain still resides at `Projects/myIS-brain` for the same reason. Its empty
  target wrapper was archived intact.
- Owner must close Obsidian and any IDE/Codex/Claude session using those paths
  before the moves are retried.
- Experience Brain store cutover has not occurred. Existing MCP processes still
  point to the old runtime and store.

## Immutable boundaries

- No files have been deleted.
- App dirty state is preserved: modified `.codex/config.toml` and the untracked
  SkillOpt PDF remain Owner data.
- Papers A-D and PDFs remain canonical in App.
- U001-U040 curated digests are imported to Research with a migration manifest;
  the old HyperResearch workspace remains unchanged until archived.
- U041 is not started and not authorized.

## Required stop point

After Experience Brain MCP configuration cutover, stop. The Owner must restart
Codex and Claude before read-only Phase 2C validation. Experience Brain writes
remain forbidden until Phase 2C passes and a later write gate is opened.

