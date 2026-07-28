# Minimal Toolchain Contract

Exact source pins and adoption states are recorded in
`00_governance/config/tools.lock.yaml`.

## Active foundation

| Capability | Tool | Operating boundary |
|---|---|---|
| Research orchestration | myIS HarnessOpt kernel | Immutable evaluator/split/approval/budget/logging; typed policy is the only optimization surface |
| Harness baseline | SkillOpt `v0.2.0` | Matched four-arm baseline; no model-weight optimization in HarnessOpt v1 |
| Runtime events | structlog `26.1.0` | One redacted event to console, runtime JSONL and milestone projection |
| Experiment lineage | MLflow `3.14.0` | Searchable mirror; validated manifests and metric artifacts remain paper truth |
| Evidence synthesis | HyperResearch `v0.9.1` | Optional Claude-only staging flow; approved sources, no automatic implementation |
| Shared memory | Obsidian Brain | One human-readable Brain, one serial writer |
| Codex web search | Native live search | Native capability; no duplicate search MCP |
| Claude web search | Open-WebSearch `2.1.11` | STDIO, DuckDuckGo default, DuckDuckGo/Bing only |
| Library documentation | Context7 remote MCP | Documentation lookup, no API key initially |

Git is canonical for prompt, skill, code, and document source. MLflow records
run lineage and generated artifacts. The Brain stores concise decisions and
pointers. Search results are untrusted discovery inputs until primary sources
are fetched, verified, and registered.

Project research skills are canonical under `.agents/skills/` and linked into
Codex/Claude with `05_code/scripts/sync_project_skills.ps1`. Upstream skills are
never bulk-installed or auto-updated.

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
