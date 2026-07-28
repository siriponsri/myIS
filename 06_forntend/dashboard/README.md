# Owner Research Dashboard Frontend

This is the build-free, same-origin frontend for the IS1 Research V0.1 Owner
Dashboard. It presents the canonical plan, process, flows, harness rules, tools,
Owner Gate ledger, and allowlisted artifact metadata without becoming a second
source of truth.

## Runtime contract

- Serve this directory only through the repository dashboard backend.
- Bind the backend to `127.0.0.1`; remote and multi-user operation must fail
  closed.
- Load all data from same-origin `/api/v1/*` endpoints.
- Create a local session through `GET /api/v1/session` before reading protected
  projections or previewing an Owner decision.
- Permit no direct browser edit of plans, manifests, metrics, qrels, splits,
  baselines, results, or artifact files.
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
| `GET /api/v1/session` | Establish the loopback browser session and CSRF token |
| `GET /api/v1/dashboard-snapshot` | Phase, Task, evidence, dependency, and gate projection |
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

## Verification

Run static checks for remote URLs, inline script/style, and unsafe DOM APIs,
then exercise the page through the loopback backend at desktop and mobile
viewports. Owner Gate tests must use fixture ledgers and must never append a
canonical decision under `00_governance/approvals/`.
