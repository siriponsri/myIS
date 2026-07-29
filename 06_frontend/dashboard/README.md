# Owner Research Dashboard Frontend

This is the build-free, same-origin frontend for the myIS Research protocol 1.0 Owner
Dashboard. It presents an English-first Owner workbench with Thai detail help, the canonical PLAN flow as
`Phase -> Task`, plain-language Gate guidance, process, harness rules, tools,
the Owner Gate ledger, and allowlisted artifact metadata without becoming a
second source of truth.

## Current readiness projection

The verified current view is `F0 = closed`, `G0 = approved`,
`F1 = waiting_gate`, `G1 = pending`, and `F1/G1 preparation only`. This is a
read-only projection of validated canonical Task evidence and immutable Gate
records; it does not authorize reproduction or change a Gate. MLflow remains a
separate rebuildable mirror and is not a source of dashboard authorization.

## Runtime contract

- Serve this directory only through the repository dashboard backend.
- Bind the backend to `127.0.0.1`; remote and multi-user operation must fail
  closed.
- Load all data from same-origin `/api/v1/*` endpoints.
- Create a local session through `GET /api/v1/session` before reading protected
  projections or previewing an Owner decision.
- Permit no direct browser edit of plans, manifests, metrics, qrels, splits,
  baselines, results, or artifact files.
- Build Gate scope from typed PLAN Tasks, not free-form Phase/Task fields.
- Require a cataloged, path/hash-verified evidence package for approval.
- Write an Owner decision only through preview followed by explicit confirm.

The frontend contains no Node build, package manager, CDN, remote font, inline
script, inline style, or browser-supplied actor identity.

## Start

From the research repository root, install the locked dashboard environment and
launch the loopback-only service:

```powershell
uv sync --locked --extra dashboard
uv run --no-sync myis-dashboard --repository-root . --port 8765
```

Open `http://127.0.0.1:8765`. Browsing remains available while Git is dirty,
but the New decision control stays disabled until the backend verifies a clean
worktree. The service has no remote-bind option.

## Expected endpoints

| Endpoint | Purpose |
|---|---|
| `GET /assets/tokens.css` | Locked local design tokens; no remote fonts or CDN |
| `GET /api/v1/session` | Establish the loopback browser session and CSRF token |
| `GET /api/v1/dashboard-snapshot` | Phase, Task, evidence, dependency, and gate projection |
| `GET /api/v1/governance-catalog` | Friendly Gate/evidence names and validated PLAN/Linear/MLflow bindings |
| `GET /api/v1/f1-g1-readiness` | Validated hash/count-only Owner-local preparation projection |
| `GET /api/v1/presentation-topics` | Registry-driven Thai-first DAPFAM teaching content |
| `GET /api/v1/content/process` | Allowlisted process documentation |
| `GET /api/v1/content/harness` | Allowlisted harness rules |
| `GET /api/v1/flows` | Flow catalog |
| `GET /api/v1/flows/{flow_id}` | Flow metadata and a SHA-256-bound image URL |
| `GET /api/v1/flows/{flow_id}/image?sha256=...` | Exact validated SVG bytes for that digest |
| `GET /api/v1/tools` | Tool lock and bootstrap projection |
| `GET /api/v1/owner-gates` | Immutable decision records and chain state |
| `GET /api/v1/artifacts` | Allowlisted artifact metadata and approved PDFs |
| `POST /api/v1/owner-gates/preview` | Validate and preview one typed decision |
| `POST /api/v1/owner-gates/confirm` | Explicitly append the previewed decision |

## Accessibility and responsive behavior

The interface uses native landmarks, buttons, forms, tables, and dialogs. It
supports keyboard navigation, visible focus, reduced motion, and layouts for
wide desktop, compact desktop/tablet, and narrow mobile viewports. The Phase
evidence spine is a causal map; it never treats a successful run as an Owner
approval.

The detailed flow is parsed from `PLAN.md`, not maintained as a second task
list. Every Task exposes Goal, Inputs, Outputs, Tests, Acceptance, Gate,
Budget/stop, Rollback, Risk, Evidence, Dependencies, and its validated Linear
projection. Decision history resolves registered evidence hashes to friendly
Thai titles while retaining the exact SHA-256 in the detail view.

Flow controls let the Owner jump to a Phase, expand a Task, and filter active,
complete, waiting, or Gate-blocked work. The page refreshes the local projection
every 60 seconds while visible. `Complete` is derived only from validated
canonical Task evidence; Linear status cannot complete work or approve a Gate.
Any future DAPFAM reproduction control must remain a fail-closed
`waiting_gate` path until a valid G1 decision and frozen RunSpec are present.

The primary Presentation tab supports Beginner/Instructor and Learn/Present
modes. Its DAPFAM topic shows source counts, IN/OUT/NC distribution, the fresh
split, metric interpretation, commitments, and current readiness. Unrun
scientific charts are explicitly labeled as waiting for G1; no placeholder
measurement is rendered.

## Verification

Run static checks for remote URLs, inline script/style, and unsafe DOM APIs,
then exercise the page through the loopback backend at desktop and mobile
viewports. Owner Gate tests must use fixture ledgers and must never append a
canonical decision under `00_governance/approvals/`.
