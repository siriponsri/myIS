# Tool Bootstrap Status

Updated: 2026-07-26 Asia/Bangkok

| Tool | Pin | State | Validation |
|---|---|---|---|
| HyperResearch | `v0.9.1`, commit `183443aefec8d0444f4b53095cee17bf77ad5fb2` | Active | Import, CLI version, dependency check, empty-workspace lint |
| MLflow | `3.14.0`, commit `86cd7f5a1dc25a1387ad07c87811bbc30f62951c` | Active | Import, dependency check, bootstrap-only local store smoke |
| Obsidian Mind | `v7.0.0`, commit `dde3710fcdc71fcc10578e4a58cbc3014211ddbb` | Active baseline | Shared-agent contract and Windows hook smoke |
| Codex native search | top-level `web_search = "live"` | Configured; restart validation pending | Official Codex config surface; no duplicate search MCP |
| Open-WebSearch | `2.1.11`, commit `3094fa558fce35a8373e45ed5a6c43362e206906` | Configured; restart validation pending | Claude STDIO; DuckDuckGo/Bing; request-only; no daemon |
| Context7 | remote MCP; source `3.2.5`, commit `b250c2515694eee4b6df4db82fa056df9ed3e306` | Codex OAuth complete; Claude connection verified | Remote endpoint, no API key initially |
| Open Deep Research | commit `d337ae32ed4ff8f4c6fbe192ba3bf1b2d6610799` | Retired/archive pending | Earlier import and dependency check preserved as history |
| Loop Engineering | `v1.6.0`, commit `548ad72faca686766c23fcb88b3bccf643bd3b2d` | Pilot complete; not adopted | Audit tests 20/20; fixture score 19/L0; excessive overlap |
| Open Code Review | `v1.7.17`, tag object `b2038ceaa6ee7c676b91c6e6371a36c9cddd3e14`, commit `0ced7165718725e15223c3e5a506df7b7e9de51f` | Pilot complete; not adopted | Deterministic delegation preview only |

The existing MLflow bootstrap run contains only bootstrap tags and tool-purpose
parameters; metrics are empty and dataset access is `none`. No research query,
web/PDF acquisition, model/provider call, paid operation, scientific metric, or
dataset access was performed during bootstrap.

HyperResearch's annotated tag object is
`1af2f89bf19dd677fa0be0a1b2f83c939ec1d502`; it peels to the commit shown above.
