# Tool Bootstrap Status

Updated: 2026-07-26 Asia/Bangkok

| Tool | Source/runtime | Validation |
|---|---|---|
| HyperResearch | v0.9.1, peeled commit `183443aefec8d0444f4b53095cee17bf77ad5fb2` | import, CLI version, `uv pip check`, empty-workspace lint |
| Open Deep Research | commit `d337ae32ed4ff8f4c6fbe192ba3bf1b2d6610799` | import and `uv pip check` |
| MLflow | package 3.14.0 | import, `uv pip check`, bootstrap-only local store smoke |
| Obsidian Mind | v7.0.0 Brain baseline | shared agent contract, Codex adapters and Windows hook smoke |

MLflow bootstrap experiment ID: `1`; run ID:
`7900037bf1ba4a1b862891eb0c1dd07a`. The run contains only bootstrap tags and
tool-purpose parameters; metrics are empty and dataset access is `none`.

HyperResearch v0.9.1 uses annotated tag object
`1af2f89bf19dd677fa0be0a1b2f83c939ec1d502`; the tag peels to the commit shown
above. Both values are recorded to avoid conflating tag identity with commit
identity.

No API key was created, no research query was issued, no web/PDF source was
fetched, no model/provider was called, no server was started, and no scientific
metric or dataset was logged.
