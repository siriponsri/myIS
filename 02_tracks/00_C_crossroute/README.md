# Track C - CrossRoute Candidate Recovery

Track C is the active candidate-recovery track in `myIS Research` protocol
`1.0`, track version `0.1`. Its active sequence is:

```text
F1 -> D0 -> C0 -> C1 -> CF -> S0/S1/SF -> Q
```

Track C owns candidate exposure. The frozen C1 harness is the only retrieval
harness handed to Track S. Ranking is a diagnostic performed on an identical
frozen pool; it is not an independent scientific track or a separate gate.

## Current gate state

Foundation migration is closed: `F0 = closed` and `G0 = approved`. Track C
baseline reproduction remains `F1 = waiting_gate` because `G1 = pending`.
Current work is F1/G1 preparation only. Draft schemas, documentation, fixtures,
and fail-closed adapter checks may be prepared, but no DAPFAM reproduction,
dataset or qrels access, confirmation access, paid API, GPU use, measured
manifest, or scientific metric is authorized.

Any future `myis-harness reproduce dapfam` path must refuse before protected or
scientific access unless a valid G1 decision and a frozen, resolved RunSpec are
available. A draft is not executable and cannot stand in for that authorization.

## Locked comparison

The primary comparison is `C1 - C0` on family-level `OUT Recall@100` over the
shared held-out joint test. `C0 - B1` and `C1 - B1` form the preregistered
additional Holm family. A full 1,247-query report is descriptive only after all
arms are frozen.

- `B0`: Llama-Embed-Nemotron-8B TAC dense top-400 at revision
  `aa3b43a495a9b280d1bdb716da37c54bb495d630`.
- `B1`: the same encoder plus BM25 min-max fusion at `0.7/0.3`.
- `B2`: naive TAC/Abstract/Claim1 RRF. Pure BM25 and `patembed-base` are
  secondary controls.
- `C0`: zero-tuned CrossRoute, six atomic routes: TAC BM25/dense,
  independent-claim BM25/dense, and grounded-mechanism BM25/dense. Quotas are
  `100/100/50/50/50/50`, raw budget `400`, RRF `k=60`, final top-100.
- `C1`: metric-tuned CrossRoute. Only route enablement, quotas, fusion, RRF,
  and pool/rerank depths may change; raw budget remains at most `400`. Prompts,
  query views, encoder, and reranker instructions are frozen.

`C1` considers at most 100 valid configurations on `C_TRAIN`, then sends at
most five Pareto finalists to `C_SELECTION` once. Acceptance requires a
strictly greater preregistered primary score; ties are rejected.

## Firewall and freeze

Tracks C and S share a seed-42 commitment of `250/125/872` query IDs but keep
independent evaluators, optimizers, budgets, manifests, artifacts, and data
firewalls. The held-out 872-query joint test and its qrels remain protected.
The actual OUT-positive counts and hashes are Owner-run protected outputs, not
values to infer here.

`CF` freezes C0/C1 code, configuration, prompts, model revisions, environment,
pool hashes, and the C1 harness. The `C_DIAGNOSTIC` reports pool equality,
no-rerank ordering, frozen-reranker behavior, reachable/oracle nDCG,
promotion/demotion, and failure layer. It cannot create an independent ranking
claim.

No experiment, qrels evaluation, paid API, GPU, or confirmation action is
authorized by this directory. This is decision support, not legal advice.

## F1/G1 preparation

The F1.1 DAPFAM material is a non-executable preparation scaffold only. Its
draft templates live in `03_experiments/templates/`; they do not belong in
`C_artifacts/manifests/`, which is reserved for immutable measured outputs.
`myis-harness reproduce dapfam` can validate the draft only in explicit dry-run
mode and otherwise fails closed with `WAITING_GATE`. G1 must approve the corpus,
query, qrels, family, evaluator, field protocol, published targets, compute
budget, and reproduction authorization before any F1 execution work begins.

See [the Track C source plan](../../00_governance/IS_RESEARCH_TRACK_C_V0.1_CROSSROUTE_PLAN.md)
and the canonical execution plan.
