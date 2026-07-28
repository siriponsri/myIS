# Claude Instructions for IS1 Research V0.1

Read `AGENTS.md`, `PLAN.md`, `FULL_RESEARCH_TRACK_PLAN.md`, and the applicable
Owner Gate before acting. `Paper E` is a historical alias only; preserve it in
provenance but use `IS1 Research V0.1` on active artifacts.

Treat Paper D as frozen. Do not expose confirmation membership, qrels, payloads,
or per-query outcomes. Confirmation is Owner-run outside the agent workspace;
this repo emits only a hash-only request and accepts only aggregate results.

Use GPT-5.6 Sol High for implementation. Measured optimizer calibration starts
Sol Medium and escalates to High only after a documented qrels-blind validity
failure; freeze model/provider/effort/budget identically in A2/A3. Never permit
silent fallback.

The dashboard is loopback-only and read-only for experiment artifacts. Brain and
MLflow are projections, not paper truth. Any Brain/MCP write requires its typed,
serial-writer, provenance, and Owner boundary.

If using HyperResearch or another evidence synthesis procedure, use only
approved inputs, preserve source/license/hash provenance, and stop for the Owner
before implementation or external action. A recommendation is not approval.
