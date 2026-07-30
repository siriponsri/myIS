# Archive Index

Archived material is immutable historical context. It is not an active
execution source and must not be silently deleted.

## Migration Map

| Legacy material | Action | Active destination |
|---|---|---|
| `00_governance/` | archive | `control/` owns current identity/protocol; old approvals remain under `legacy-cs/` |
| `01_evidence/` | archive/reference | `evidence/` stores only index and hash pointers; protected bytes remain external |
| `02_tracks/` | merge/rewrite | `campaigns/scope-autoindex-v1/` with SkillOpt conditional |
| `03_experiments/` | rewrite | `campaigns/.../specs` and `manifests` |
| `04_outputs/` | archive | `projections/` and `03_Paper` are generated from run facts |
| `05_code/` | keep/restructure | `src/`, `tests/`, `scripts/` |
| `06_frontend/` | keep/restructure | `dashboard/` and `dashboard/mlflow/` |
| `07_obsidian_note/` | archive/merge | `02_Brain/reports/generated/` and `projections/obsidian/` |
| `inbox/` | archive/input | `archive/inbox/source/`; no file is active authority |
| generated caches | remove | exact-path cleanup only after hash/reference scan |

The full hash inventory is `migration-manifests/migration-manifest.v1.json`.
