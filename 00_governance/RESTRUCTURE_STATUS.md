# Restructure Status

Updated: 2026-07-27 Asia/Bangkok

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

## Completed

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
- App, Research, and Brain are now at the numbered workspace paths shown above.
- The empty `Projects` wrapper and retired Experience Brain runtime were moved
  into dated archive locations after Owner YES and process/path checks.
- Nine empty Research navigation shells and the resulting empty root `Tools`
  shell were removed after zero-entry checks.
- The current PDF duplicate audit records 16 exact groups / 32 files. Every
  alias remains referenced, so the files were retained and canonical mappings
  were recorded instead of breaking provenance.

## Remaining gated work

- Two misleading PDF aliases require reference migration before they can be
  archived; see `PDF_DUPLICATE_MANIFEST.csv`.
- Global Experience Brain or `agentmemory` MCP configuration, if still present,
  requires a separate config backup and exact-entry review outside this repo.
- U041, research execution, protected data, and publication remain separately
  gated and were not opened by the cleanup approval.

## Immutable boundaries

- No project file or historical artifact has been deleted.
- Papers A-D and PDFs remain canonical in App.
- Historical evidence may retain retired tool names as provenance.
- U041 is not started and not authorized.
- No research query, new PDF acquisition, model/provider call, paid job,
  API/GPU/Vast run, scientific MLflow run, or held-out access occurred.

## Cleanup evidence

See `ARCHIVE_CUTOVER_20260727.md`, `CLEANUP_APPROVALS.md`, and
`PDF_DUPLICATE_MANIFEST.csv` for exact sources, destinations, decisions, and
retention reasons.
