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

1. `PLAN.md` is canonical execution authority; the Full Research and Local
   Harness plans define program strategy and implementation detail.
2. Full U041-U153 triage is Owner-authorized. Preserve frozen U001-U040 bytes,
   corpus identity, legacy aliases, tier metadata and QA provenance.
3. HarnessOpt is the active governed optimization program and SkillOpt v0.2.0
   is its pinned baseline. Use equal evaluator, split hashes, tools and budget.
4. HyperResearch is an optional staged flow. Open Deep Research, Experience
   Brain and `agentmemory` are retired and must not be reactivated.
5. Never use the prospectively isolated confirmation cohort for design, tuning,
   prompt optimization or path selection.

## Experiment gates

Run Gate 0 headroom, Gate 1 manual responsiveness, Gate 2 bounded optimizer
pilot, and Gate 3 API-to-local transfer in that order. Failure at a gate stops
the track until the Owner approves a redesign.

Every execution must have an immutable manifest, pinned model/provider or model
revision, prompt/skill version, dataset split, seed, batch settings, cost and
latency fields, and MLflow lineage. One GPU starts with one vLLM engine and many
concurrent client requests; do not load one model per worker.

Every run also follows `00_governance/OBSERVABILITY_AND_RUN_LOGGING.md`.
Structured runtime logs, progress, metrics, MLflow and the canonical manifest
have distinct authority; paper generators read only validated manifests and
metric artifacts.

## Brain use

The shared Brain repository is the human-readable project control plane.
Codex and Claude are serial writers: only one may write to Brain at a time.
Research facts remain canonical here or in immutable App evidence; Brain holds
summaries, decisions, status, and pointers. It is the only active memory layer.
Historical Experience Brain and `agentmemory` records remain provenance only;
neither system is an active memory layer.

## Frozen boundaries

- Paper D is a frozen boundary study and must not be reopened implicitly.
- Historical names and provenance remain unchanged even when they reference a
  retired tool or earlier project name.
- Paid/API/GPU/Vast runs and confirmation-cohort access require explicit Owner
  approval. Offline fixtures, tests and governed local bootstrap checks are open.
