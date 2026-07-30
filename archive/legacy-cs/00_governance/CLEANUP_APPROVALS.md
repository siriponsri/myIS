# Cleanup approval register

Owner decision: **YES**, recorded 2026-07-27 Asia/Bangkok in the current
session. Approval authorizes archive-first cleanup after safety checks; it does
not override immutable evidence or permit breaking live references.

No exact path is deleted by the restructure. Each candidate below requires a
separate Owner YES/NO decision before move or removal.

| Group | Evidence | Default action | Owner decision |
|---|---|---|---|
| Research legacy shells: `artifacts`, `config`, `docs`, `mlartifacts`, `mlruns`, `research`, `runtime`, `templates`, `tracks` | Confirmed empty | Removed 2026-07-27 | YES / COMPLETE |
| Root `Projects` legacy wrapper | Confirmed empty `Projects/myIS/App` | Archived to `99_Archive/00_myIS/navigation-shells/legacy-Projects-shell-20260727` | YES / COMPLETE |
| Root `Tools/experience-brain-is1-runtime` | No external process referenced the path at cutover | Archived to `99_Archive/00_myIS/experience-brain-is1/runtime-20260727` | YES / COMPLETE |
| Duplicate PDF groups | Current scan: 16 SHA-256 groups / 32 files | Retain referenced aliases; canonical mapping recorded | YES / REVIEW COMPLETE |

Every PDF alias is still referenced by track inventories, KM notes, citation
audits, or immutable result manifests. Removing those aliases would break
provenance, so no PDF was moved or deleted. See `PDF_DUPLICATE_MANIFEST.csv`.
