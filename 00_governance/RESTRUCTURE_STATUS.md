# Restructure Status

Updated: 2026-07-29 Asia/Bangkok

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
  `01_Stores/00_myIS/mlflow/`. Internal experiment/run artifact URIs now use
  the numbered store, SQLite integrity is `ok`, and an upload/download
  round-trip returned matching SHA-256 hashes. A byte-identical pre-migration
  database backup is retained under `01_Stores/00_myIS/backups/`.
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
- The canonical literature corpus now contains 153 unique tier-organized PDFs
  with 169 legacy aliases and 16 duplicate groups preserved as metadata. Final
  validation reports A/B/C/N counts of 55/64/28/6 and no App or legacy PDFs.
- Brain literature ingestion covers U001-U153 with unique SHA-256 identities,
  a complete literature index, topic maps and resolvable canonical PDF paths.
  QMD sparse retrieval is operational; live index/vector counts remain runtime
  state rather than governance facts.

## Current implementation state

- The PDF corpus migration and U001-U153 Brain ingestion are complete.
- The offline HarnessOpt foundation, structured runtime logging, MLflow mirror,
  canonical manifest and notebook demo are implemented and locally validated.
- The active program identity is `myIS Research` (`myis-research`), protocol
  `1.0`; Track C and Track S use research version `0.1` while package and
  dependency-lock versions remain independent.
- The active scientific path is Track C -> frozen C1 harness -> Track S. The
  shared split commitment is seed `42`, 250/125/872 query membership; each track
  has a separate evaluator, optimizer, budget, manifest, artifacts, and firewall.
- Independent ranking/evidence work is retired from active navigation. Ranking/headroom is a
  Track C diagnostic, and evidence R2 remains a deferred separately gated lane.
- Scientific development runs, paid/API/GPU/Vast execution and prospective
  confirmation remain closed until their separate Owner gates are recorded.

## Immutable boundaries

- No project file or historical artifact has been deleted.
- Papers A-D and frozen historical evidence remain canonical in App. The
  literature/PDF corpus, new digests and HarnessOpt artifacts belong to Research.
- Historical evidence may retain retired tool names as provenance.
- Full U041-U153 triage is authorized; frozen U001-U040 bytes remain unchanged.
- Paid jobs, API/GPU/Vast execution and the prospectively isolated confirmation
  cohort remain separately gated.

## Cleanup evidence

See `ARCHIVE_CUTOVER_20260727.md`, `CLEANUP_APPROVALS.md`, and
`PDF_DUPLICATE_MANIFEST.csv` for exact sources, destinations, decisions, and
retention reasons.
