# Minimal Toolchain Contract

Exact source pins and adoption states are recorded in
`00_governance/config/tools.lock.yaml`.

## Active foundation

| Capability | Tool | Operating boundary |
|---|---|---|
| Evidence synthesis | HyperResearch `v0.9.1` | Claude-only, approved sources, Top-3 output, no automatic implementation |
| Experiment lineage | MLflow `3.14.0` | Immutable manifests, traces, metrics, artifacts, cost, and batch settings |
| Shared memory | Obsidian Brain | One human-readable Brain, one serial writer |
| Codex web search | Native live search | Native capability; no duplicate search MCP |
| Claude web search | Open-WebSearch `2.1.11` | STDIO, DuckDuckGo default, DuckDuckGo/Bing only |
| Library documentation | Context7 remote MCP | Documentation lookup, no API key initially |

Git is canonical for prompt, skill, code, and document source. MLflow records
run lineage and generated artifacts. The Brain stores concise decisions and
pointers. Search results are untrusted discovery inputs until primary sources
are fetched, verified, and registered.

## Retired or rejected

- Open Deep Research is archived because it overlaps HyperResearch.
- Experience Brain and `agentmemory` are retired to keep one memory layer.
- `pplx-cli` is not adopted because it adds an API dependency without a unique
  role in the minimal stack.

Historical files may retain these names as immutable provenance. They are not
active operating instructions.

## Evaluation-only tools

Loop Engineering and Open Code Review may run only at their pinned commits in a
disposable fixture workspace. They receive no credentials and no write access
to App, Research, Brain, or persistent stores. Adoption requires an evidence
report and a separate Owner decision.
