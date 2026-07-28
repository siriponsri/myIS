# myIS Research Track S v0.1: SkillOpt and HarnessOpt Protocol

**Status:** planning and configuration contract only; no experiment is authorized
by this document.
**Program:** `myIS Research` (`myis-research`), protocol `1.0`.
**Track:** `S`, version `0.1`.
**Dependency:** Track C must first deliver the G3-approved frozen C1 harness.

## Purpose and causal claim

Track S is a required, separately governed adaptation-surface study after the
frozen Track C1 harness. It asks what additional candidate-recovery value comes
from optimizing a procedural skill or a narrowly typed harness. It is decision
support for patent-family retrieval, never a novelty, validity, infringement, or
FTO determination.

The primary comparison is **A3 - A2** on the untouched joint test: paired
family-level `OUT Recall@100`. It has no multiplicity correction. A positive
point delta is an observed improvement; paired bootstrap uncertainty determines
the strength of any superiority wording. No result is currently available.

## Shared membership, separate boundaries

Tracks C and S share one frozen query-ID commitment: seed `42`, with roles
`C_TRAIN=250`, `C_SELECTION=125`, and joint test `872`. These are membership
counts, not a license to expose qrels, IDs, outcomes, or per-query data.

Track S owns an independent evaluator, optimizer, budget ledger, manifests,
artifacts, and data firewall. The optimizer sees only its authorized adaptation
surface; selection is bounded and does not reveal raw protected labels. The
joint-test membership, qrels, protected payloads, and per-query outcomes stay
outside the workspace. The protected process must calculate and freeze actual
OUT-positive counts and hashes; the provisional `181/91/633` figures are not
protocol facts.

## Frozen arms

| Arm | Starting state | Editable surface | Status |
|---|---|---|---|
| A0 | frozen C1 harness | none | required control |
| A1 | human-authored seed skill | seed skill only | required control |
| A2 | identical frozen A1 | SkillOpt skill text only | required |
| A2L | identical frozen A1 | SkillOpt-Lite skill text only | required |
| A3 | identical frozen A1 | declared typed HarnessOpt allowlist | required |
| A2L-P | future exploratory | larger Lite schedule | deferred |
| A3X | future exploratory | broad harness surface | deferred |

Arms A2, A2L, and A3 are required matched parallel campaigns from the same
frozen A1 state. They may not inherit a selected artifact from another arm. A2L-P (`400` rollouts/seed)
and A3X are not part of Track S v0.1 and require new approval.

## Provider and optimization lock

Target execution is `qwen/qwen3-30b-a3b-instruct-2507`, non-thinking, through
the provisional OpenRouter CoreWeave BF16 endpoint. There is no routing,
fallback, or parameter dropping. The endpoint becomes final only after the
`COREWEAVE_FINAL_FREEZE_TBD_BLOCKING` preflight succeeds. One identical retry is
permitted only for a transport error; any hard preflight failure stops and
requires an Owner decision.

- A2 uses SkillOpt `v0.2.0`, commit
  `51d0a4d96e88558c84dee637f98e24e3fb2d1547`.
- A2L uses the adapted SkillOpt-Lite commit
  `4cb4eeef1f95375a9179737ab94cf5e64b9647c6`.
- A3 changes only the typed allowlist: route enablement, quotas/depths inside
  the fixed candidate budget, deterministic fusion parameters, pool/rerank
  depths, and validated context/control fields. It cannot change query views,
  prompts, encoder, reranker instructions, corpus, evaluator, split, qrels,
  family map, model/provider, or budget.

The CoreWeave preflight checks requested and resolved identity, seed, tool
availability, strict response schema, context capacity, latency/error behavior,
and repeated-fixture stability. Every measured record binds requested/resolved
provider identity, retry state, token/cost/latency fields, model parameters,
and fallback state.

## Budget and selection

Each of A2, A2L, and A3 receives seeds `11`, `23`, and `47`, at no more than
`160` rollouts per seed (`480` per arm) and USD `20` per arm. Shared services
are capped at USD `30`; the project target is USD `90` and the hard stop is USD
`100`. The deterministic kernel stops before a ceiling is crossed and preserves
invalid, rejected, and failed attempts.

Selection accepts a candidate only when the preregistered primary selection
score is strictly greater than its incumbent; ties and losses are rejected.
This rule applies within each arm and cannot be replaced by cost, secondary
metrics, or post-hoc judgment. A separate three-seed A1 S-MARGIN audit selects
`S_MARGIN_VALUES_TBD_BLOCKING` before A2/A2L/A3. It is not an optimization or
joint-test run.

## Comparisons and reporting

The primary joint-test comparison is A3-A2. The preregistered secondary Holm
family is A1-A0, A2-A1, A2L-A1, A3-A1, and A2L-A2. A3-A2L is exploratory.
For each registered comparison, the external aggregate package reports paired
delta, exact eligible `n`, 95% paired-bootstrap CI, rank-biserial effect, and
win/loss/tie counts. Results over all 1,247 queries are descriptive only if
DAPFAM qrels informed development.

## Phase contract

| Phase | Task | Required acceptance and gate |
|---|---|---|
| S0 | S0.1 provider/A0/A1 lock; S0.2 S-MARGIN audit | frozen identity, firewall, A1 state, and Owner G4 |
| S1 | S1.1 A2; S1.2 A2L; S1.3 A3 | required matched parallel three-seed campaigns from A1 under G5 |
| SF | nine seed-finalist submission and arm freeze | one immutable artifact per arm; G5 |
| Q | joint test | Owner-run aggregate-only evaluation under G6 |
| PS | Track S manuscript | evidence-bound publication decision G8 |

No Track S step can edit or rerun Track C. Track C's C1 harness is an immutable
input, and Track S does not create an independent ranking claim or ranking gate.

## Blocking Owner decisions

- `S_MARGIN_VALUES_TBD_BLOCKING`: choose the S-MARGIN rule after the isolated
  A1 three-seed audit.
- `COREWEAVE_FINAL_FREEZE_TBD_BLOCKING`: approve the endpoint only after all
  preflight conditions pass.
- `CT_BUDGET_LICENSE_TBD_BLOCKING`: applies only to deferred transfer work and
  is outside the Track S primary claim.

Before measured work, freeze code/config/prompt/skill/model/environment and
pool hashes, then emit only a hash-only confirmation request. Confirmation is
run by the Owner outside this repository; the repository may ingest only a
schema-validated aggregate package.

## Artifacts and publication

Canonical Track S materials live under `02_tracks/01_S_skillopt/`. Every
duplicate records its source path and SHA-256; symlinks are prohibited. The
IEEE draft has no figures and no results until validated aggregate evidence
exists. It retains null, boundary, invalid, and cost outcomes rather than
selecting favorable seeds.
