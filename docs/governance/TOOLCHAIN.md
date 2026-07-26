# Toolchain Contract

Exact source pins are recorded in `config/tools.lock.yaml`.

## HyperResearch

Claude-only execution. It may digest approved PDFs, conduct approved web search,
and call approved deep-research tooling. Its required deliverable is a Top-3
path knowledge graph, not an automatic implementation decision.

## Open Deep Research

Use as a source-gathering and synthesis component inside an approved research
run. Preserve query, source URL, retrieval time, model/provider configuration,
and claim-to-source mapping.

## Obsidian Mind and Experience Brain

Obsidian Mind is the shared human-readable Brain for Codex and Claude. Use one
serial writer at a time. Experience Brain stores only approved external
knowledge or grounded experience with provenance; never ingest raw PDFs or
extraction-cache text.

## MLflow

Git is canonical for prompt and skill source. MLflow records immutable prompt
versions, run and trace lineage, metrics, artifacts, cost, latency, batch
settings, optimizer lineage and API-to-local comparisons. Bootstrap tests use a
dedicated `stage=bootstrap` tag and contain no scientific data.

