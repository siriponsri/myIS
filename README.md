# myIS Research

Publication-oriented research repository for the myIS program. This repository
is independent from the product application and from the shared project brain.

## Current state

- Restructure and tool bootstrap only.
- Papers A-D and the PDF corpus remain canonical in the App repository.
- Literature digests U001-U040 are preserved under `research/literature/`.
- U041 and later papers are closed until the Owner explicitly authorizes them.
- No research query, scientific MLflow run, API/GPU/Vast execution, held-out
  access, or Experience Brain write is authorized during restructuring.

## Research sequence

1. Track C: candidate exposure.
2. Track R: ranking and evidence, after the Track C candidate pool is frozen.
3. Track S: reusable skill evolution, initially S-on-C.

For each track, Claude runs HyperResearch and Open Deep Research to produce a
ranked Top-3 path knowledge graph. The Owner selects exactly one path before any
implementation. Codex and Claude may then implement only that selected path.

Start with [AGENTS.md](AGENTS.md), then read the governance documents in
`docs/governance/`.

## Repositories

| System | Local target | Remote |
|---|---|---|
| Research | `Projects/myIS/Research` | `https://github.com/siriponsri/myIS.git` |
| App | `Projects/myIS/App` | existing `siriponsri/thaipha-lex` remote |
| Brain | `Projects/myIS/Brain` | local Git repository |

The current App and Brain paths may temporarily retain one wrapper level until
the Owner closes programs holding directory handles. See
`docs/governance/RESTRUCTURE_STATUS.md`.

