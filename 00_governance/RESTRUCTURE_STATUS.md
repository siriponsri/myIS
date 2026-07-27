# Restructure Status

Updated: 2026-07-26 Asia/Bangkok

## Target layout

```text
My_Research/
  00_Projects/00_myIS/
    00_App/                  independent product repository
    01_Research/             independent publication repository
    02_Brain/                shared Codex/Claude Obsidian repository
  01_Stores/00_myIS/         persistent stores and migration audits
  02_Tools/                  active pinned shared dependencies
  03_Workspaces/             disposable research and pilot workspaces
  99_Archive/00_myIS/        preserved legacy paths
```

## Completed without process cutover

- Research internals now use `00_governance` through `05_code` navigation.
- U001-U040 and all 64 imported artifacts validate through portable relative
  paths with unchanged source/target provenance values and matching hashes.
- Stores, Archive, Workspaces, HyperResearch, and the retired Open Deep
  Research source/environment were moved into numbered boundaries.
- The MLflow bootstrap database and report were moved to
  `01_Stores/00_myIS/mlflow/` with matching pre/post SHA-256 hashes.
- Root and Research README files, the all-track plan, operations guide, tool
  decisions, source staging contract, and disposable pilot report are present.
- Ten Mermaid diagrams render successfully with Mermaid CLI `11.16.0`.
- Codex app config has native live search and Context7 OAuth. Claude user config
  has pinned Open-WebSearch STDIO and a verified Context7 remote MCP connection.
- Loop Engineering and Open Code Review pilots completed without project data,
  credentials, model calls, commits, or global installation. Neither tool is
  recommended for active adoption now.

## Current blockers

- Research remains at `Projects/myIS/Research` because Windows denied its move
  while this active session held the repository path.
- App remains at `Projects/myIS/App/thaipha-lex`; its modified
  `.codex/config.toml` and untracked SkillOpt PDF remain untouched.
- Brain remains at `Projects/myIS-brain`.
- Experience Brain processes `26984` and `29404` still reference retired paths.
  Its runtime/store/config archival and removal of Experience Brain and
  `agentmemory` MCP entries require the Owner's explicit process-stop approval.
- Codex and Claude must restart after that cutover before final MCP and target
  path validation.

## Immutable boundaries

- No project file or historical artifact has been deleted.
- Papers A-D and PDFs remain canonical in App.
- Historical evidence may retain retired tool names as provenance.
- U041 is not started and not authorized.
- No research query, new PDF acquisition, model/provider call, paid job,
  API/GPU/Vast run, scientific MLflow run, or held-out access occurred.

## Required stop point

After the Owner authorizes stopping the two retired MCP processes, back up and
hash the remaining global configs/store, stop only those PIDs, complete the
App/Research/Brain moves, archive the retired runtime/store, detach Experience
Brain and `agentmemory`, and stop. The Owner must restart Codex and Claude before
read-only final validation.
