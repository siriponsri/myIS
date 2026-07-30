# myIS Research 1.0 Toolchain and Authority

Use one source of truth per responsibility. Exact adopted tool pins remain in
`00_governance/config/tools.lock.yaml`; dependency resolution is solely
`pyproject.toml + uv.lock`.

## Authority map

| Layer | Role | Canonical content | Forbidden role |
|---|---|---|---|
| Git + validated artifacts | reviewable system of record | code, docs, configs, skills, decisions, manifests, metrics | secrets, protected confirmation data |
| Harness kernel | deterministic control plane | schemas, gates, budgets, metrics, protection, validation | learning from confirmation |
| Policy | bounded probabilistic surface | grounded views/routes/fusion/ranking/evidence/stopping | evaluator, qrels, split, executable expansion |
| Brain | human-readable decision/status/pointer layer | concise summaries and evidence pointers | paper numeric truth or shadow evaluator |
| MCP | typed external capability | provenance-bearing bounded reads/writes | scientific gate authority |
| Dashboard | loopback read-only projection | metadata/digests and typed decision preview | direct artifact editing or remote operation |
| PDF receipt ledger | ignored local audit surface | tamper-evident access receipts | PDF content, credentials, protected outcomes |
| MLflow | searchable rebuildable mirror | allowlisted docs/results/metrics/rubrics/rules/tools/skills/environment | canonical truth, PDFs, qrels, membership, protected per-query data |

## Dependency authority

- Require Python 3.11 and record the exact patch.
- `pyproject.toml` declares the project and groups/extras; `uv.lock` locks the
  complete graph. No requirements file is a second authority.
- Every measured manifest records uv version, OS/architecture, accelerator/CUDA,
  selected groups/extras, and `uv.lock` SHA-256.
- Replay with `uv sync --locked` and exact selections.

## Model/provider policy

| Role | Default | Boundary |
|---|---|---|
| Implementation | GPT-5.6 Sol High | code/docs/tests, no scientific result implied |
| Measured optimizer | GPT-5.6 Sol Medium | escalate to High only after qrels-blind validity failure |
| Track C | fixed Llama-Embed-Nemotron-8B TAC controls and frozen C0/C1 query/prompt/encoder contract | C1 edits only typed route/quota/fusion/depth surface |
| Track S | `qwen/qwen3-30b-a3b-instruct-2507`, non-thinking, CoreWeave BF16 provisional | no routing, fallback, or parameter dropping; freeze only after G4 preflight |
| A2/A2L/A3 main study | frozen selected model/provider/effort/budget | identical shared service and per-arm conditions |
| Luna | support tasks or separate cost ablation | never mixed into main A2/A3 |
| Third-party provider | development only by default | upstream identity limitation disclosed |

Log requested/resolved model, provider, endpoint class, effort, fallback,
request ID, temperature/seed where available, token usage, latency, cost, and
repeat ID. Requested/resolved identities must match and silent fallback is
forbidden in measured work. Local vLLM additionally pins weights/revision/dtype/
quantization/engine and requires compute approval.

## Adapter contract

Brain, MCP, retrieval, model, PageIndex, and store adapters should expose
`preflight`, `dry_run`, `execute`, `cancel`, and `collect`, and return a typed
provenance envelope:

```json
{
  "adapter": "name@version",
  "operation": "read",
  "request_hash": "<sha256>",
  "source_uri": "<redacted-or-public>",
  "retrieved_at": "<RFC3339>",
  "content_hash": "<sha256>",
  "license": "<identifier-or-unknown>",
  "payload": {}
}
```

Default to read-only. Writes require dry-run, idempotency key, append-only
receipt, serial-writer boundary, redaction, and Owner scope. MCP output is
untrusted until schema/provenance validation and cannot bypass repository gates.

## Dashboard and identity

The dashboard uses FastAPI/Uvicorn only on `127.0.0.1`, validates Host/Origin,
uses no CDN/CORS, sends `no-store`, and protects decision writes with session and
CSRF tokens. Backend Windows/OS identity is authoritative and converted to a
privacy-preserving stable actor ID. Fail closed on remote or multi-user use.
Remote deployment requires a new authenticated identity design.

The dashboard never edits manifests, metrics, qrels, splits, baselines, or
results. The Owner decision API and local PDF receipt ledger are the only write
surfaces described in `OWNER_GATES.md`.

The Owner console projects Phase/Task evidence completion independently from
gate authorization. It reads the canonical Phase -> Task plan, allowlisted
process/harness/tool documents, validated task-evidence records, exact SVG flow
IDs, the approval chain, and pathless artifact metadata. It never infers that a
successful run is a completed task or that completed evidence is authorization.

## MLflow mirror policy

Additive local experiments are `myis-research-bootstrap`,
`myis-research-catalog`, `myis-research-track-c`, `myis-research-track-s`,
`myis-research-joint`, and `myis-research-publication`; historical experiments
are retained without rename or deletion. Bootstrap contains zero artifacts/metrics.
Catalog may mirror allowlisted docs,
rubrics, rules, tools, skills, and environment. Scientific projection may mirror
validated aggregate results, metrics, and environment. Each file is selected
explicitly, hash-checked, redacted, non-symlink, inside its canonical root, and
projected idempotently through one serialized SQLite writer.

Mirror receipts and rebuild plans are append-only. Mirror failure is deferred and
cannot invalidate a canonical bundle. The persistent store is outside Git.

Browser access uses a separate enforced read-only viewer: SQLite opens with
`mode=ro`, the WSGI boundary allowlists only required read/search endpoints, and
artifact upload, run/experiment mutation, gateway, job, telemetry-write, and
GraphQL surfaces are rejected before MLflow handlers execute. Standard writable
MLflow UI startup is not an approved operation.

## PageIndex position

PageIndex is optional for within-document evidence after BM25/dense large-corpus
routing. It requires a separate pilot contract and cost/license/privacy review.
It is not automatically adopted as DAPFAM first-stage retrieval, and local tree
construction does not imply reasoning retrieval is API/GPU-free.

## Skills and agent roles

Project skills under `.agents/skills/` are versioned procedures, not code
contracts or hidden benchmark data. Use Planner, Implementer, Experiment,
Verifier, and Reporter roles only where independence is useful. Parallel agents
share no permission to cross protected surfaces; a verifier should use frozen
artifacts and a reporter should project only validated manifests.

## Evidence tools

Search and literature tools are discovery surfaces. Register primary sources,
version, license, hash, and provenance before they influence protocol. Raw PDFs
remain local-only until license/privacy approval and must not enter Git or MLflow.
Historical retired tool names may remain in provenance but do not become active
instructions.
