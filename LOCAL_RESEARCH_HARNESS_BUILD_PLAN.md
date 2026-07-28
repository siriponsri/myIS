# myIS Research 1.0 Local Harness Build Contract

This contract defines deterministic implementation boundaries for Track C and
Track S. It authorizes offline schemas, fixtures, validators, dashboard, and
projection code only. Scientific execution requires the applicable Owner Gate.

## Identity and compatibility

Active emitters require `program_id=myis-research`, display name `myIS Research`,
protocol version `1.0`, and Track C/S version `0.1`. Package version remains
`0.1.0`. Historical schema readers may load predecessor bundles in an explicit
read-only legacy mode. Active creation, mutation, confirmation request, or
measured execution with the predecessor identity or independent ranking phase
must fail.

## Deterministic kernel

The kernel owns typed identity, lifecycle, approvals, split commitments, hash
closure, budgets, family deduplication, tie-breaking, metrics/statistics,
manifest validation, redaction, protected-path checks, and immutable writes.
Policy code may propose only grounded query views, allowlisted routes, route
depth/quota, fixed budgets, declared fusion, frozen-pool diagnostic depth, and
bounded stopping. Probabilistic output is never authoritative before validation.

## Required schemas

- `ResearchVersionSpec`: program, protocol, track, track version, package version.
- `SharedSplitCommitment`: seed, counts, opaque membership hashes, qrels hash,
  and separate C/S firewall identifiers; never raw protected IDs.
- `TrackCManifest`: arms B0/B1/B2/C0/C1/CF/C_DIAGNOSTIC/Q/PC/CT.
- `TrackSManifest`: arms A0/A1/A2/A2L/A3/SF/Q/PS/CT.
- `TrackCRankingDiagnostic`: identical pool hash, no-rerank/rerank identities,
  oracle/reachable nDCG, promotion/demotion counts, and failure layer.
- `AggregateComparison`: required `track_id`, comparison family, exact n,
  estimates, paired delta/CI/effect/W-L-T, multiplicity role, and hash closure.
- `ProviderExecution`: requested/resolved model/provider/effort, endpoint class,
  fallback/routing/parameter-drop flags, repeat, cost/latency/tokens.

## Track C policy

C0 validates six named routes, quotas `100/100/50/50/50/50`, raw budget 400,
RRF 60, and final K 100. C1 patch validation permits only route enablement,
quotas, fusion, RRF, and pool/rerank depth. It rejects changes to query views,
prompts, encoder revision, reranker instructions, evaluator, split, budget,
protected surfaces, or executable tools. Search and one-batch selection ceilings
are kernel-enforced.

Candidate ledgers retain query/view/source-span, route, publication/family,
component rank/score, fused rank/score, dedup decisions, and deterministic
tie-break fields. Final family count never exceeds 100 and raw unique families
never exceed 400.

## Track S optimizer adapter

Lifecycle is `preflight -> dry_run -> execute -> collect -> validate -> freeze`.
Preflight validates the Qwen/CoreWeave identity and rejects routing, fallback,
parameter dropping, tool drift, weak schema mode, or unstable fixtures. Only one
identical transport retry is legal.

A2/A2L/A3 share A1, seeds, model/provider/effort, dataset access, evaluator,
tools, 160-rollout seed cap, USD 20 arm cap, retry and stopping rules. A3 patch
validation uses an exact typed allowlist and denies executable expansion.
Every repeat, failure, invalid trial, and cost event is retained.

## Confirmation and statistics

The local command creates a hash-only request; external Owner infrastructure
returns only aggregate packages. Validators reject raw IDs, qrels, membership,
per-query outcomes, credentials, or unknown fields that can carry protected
payloads. Track C primary and Track S primary remain distinct. Holm is applied
only to each preregistered additional family, never the single primary.

## Manifest and artifact layout

Track C writes only below `02_tracks/00_C_crossroute/C_artifacts/`; Track S only
below `02_tracks/01_S_skillopt/S_artifacts/`. Cross-track duplicates require an
Owner-approved source path plus SHA-256 record; symlinks are forbidden. Manifests
record exact Python patch, uv version, OS/architecture, accelerator/CUDA,
selected groups/extras, `uv.lock` hash, Git SHA, config/code/prompt/skill/model/
provider/evaluator/split/pool hashes, costs, and artifact hashes.

MLflow is a rebuildable allowlisted mirror with additive experiments
`myis-research-{bootstrap,catalog,track-c,track-s,joint,publication}` and required
tags for track, arm, phase, data role, protocol/track version, and source hashes.
It rejects protected data and cannot validate or invalidate a canonical bundle.

## Dashboard boundary

The UI binds only `127.0.0.1`, validates Host/Origin/session/CSRF, disables
cache/CDN/CORS, and exposes counts, hashes, aggregate state, phase dependencies,
deferred lanes, and projection links only. Owner Gate decisions are immutable
hash-chained records. PDF streaming remains exact allowlist/hash controlled with
append-only local receipts.

## Test obligations

Tests cover active/legacy identity separation; shared split commitments and dual
firewalls; C0 recipe and C1 edit denial; strict tie rejection; one-batch limits;
provider/fallback/parameter drift; A2/A2L/A3 matching; budget hard stops;
diagnostic pool equality; aggregate track IDs; confirmation redaction; immutable
manifests; dashboard security; MLflow rejection; and deterministic replay.
