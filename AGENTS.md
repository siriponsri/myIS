# myIS Research Agent Operating Contract

This contract applies equally to Codex and Claude.

## Authority

1. The Owner is the final decision maker.
2. If facts are incomplete, instructions conflict, a source has drifted, or an
   action is not clearly authorized, stop and ask the Owner before proceeding.
3. Any delete or removal requires a separate YES/NO approval naming the exact
   target. Prefer move or archive.
4. Never push or publish unless the Owner explicitly authorizes it.
5. Do not modify the App or Brain from this repository unless the Owner's task
   explicitly includes that repository.

## Research gates

1. Execute tracks in order: C, then R, then S.
2. Before implementing a track, research must present three ranked paths as a
   knowledge graph with evidence, assumptions, cost, risk, falsification tests,
   and dependencies.
3. The Owner must select one Top-1 path. Ranking by an agent is a recommendation,
   not approval.
4. HyperResearch runs are Claude-only because the upstream workflow requires
   Claude. Codex may organize inputs, validate artifacts, and implement an
   Owner-selected path.
5. U041 and subsequent literature digestion require explicit Owner approval.
6. Never use a protected held-out set for design, tuning, performance tuning,
   prompt optimization, or path selection.

## Experiment gates

Run Gate 0 headroom, Gate 1 manual responsiveness, Gate 2 bounded optimizer
pilot, and Gate 3 API-to-local transfer in that order. Failure at a gate stops
the track until the Owner approves a redesign.

Every execution must have an immutable manifest, pinned model/provider or model
revision, prompt/skill version, dataset split, seed, batch settings, cost and
latency fields, and MLflow lineage. One GPU starts with one vLLM engine and many
concurrent client requests; do not load one model per worker.

## Brain use

The shared Brain repository is the human-readable project control plane.
Codex and Claude are serial writers: only one may write to Brain at a time.
Research facts remain canonical here or in immutable App evidence; Brain holds
summaries, decisions, status, and pointers. It is the only active memory layer.
Do not attach or write to Experience Brain or `agentmemory`; historical records
remain provenance only.

## Frozen boundaries

- Paper D is a frozen boundary study and must not be reopened implicitly.
- Historical names and provenance remain unchanged even when they reference a
  retired tool or earlier project name.
- During restructure: no scientific MLflow runs, research calls, memory writes,
  API/GPU/Vast jobs, or held-out access.
