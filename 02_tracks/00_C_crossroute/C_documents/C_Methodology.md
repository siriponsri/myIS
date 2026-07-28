# Methodology

Results: n/a

**wating for results**

## Protocol

Track C evaluates family-level candidate recovery on DAPFAM. It uses the
shared seed-42 membership commitment of 250/125/872 query IDs while retaining
an independent Track C evaluator, optimizer, budget, manifests, artifacts, and
firewall. The joint 872-query test membership, qrels, per-query outcomes, and
actual OUT-positive counts remain outside the agent workspace.

The controls are B0, Llama-Embed-Nemotron-8B TAC dense top-400 at revision
`aa3b43a495a9b280d1bdb716da37c54bb495d630`; B1, that encoder plus BM25
min-max fusion at weights 0.7/0.3; and B2, naive TAC/Abstract/Claim1 RRF.
Pure BM25 and `patembed-base` are secondary controls.

## CrossRoute arms

C0 is the zero-tuned arm. It uses TAC BM25/dense, independent-claim BM25/dense,
and grounded-mechanism BM25/dense routes. Their quotas are
100/100/50/50/50/50, raw candidate budget is 400, RRF uses k=60, and the final
ranking contains 100 families.

C1 is the metric-tuned arm. It may vary only route enablement, quotas, fusion,
RRF, and pool/rerank depths under raw budget 400. Prompts, query views, encoder,
and reranker instructions are frozen. At most 100 valid configurations are
evaluated on C_TRAIN. At most five Pareto finalists are evaluated on C_SELECTION
once. A candidate is kept only when the preregistered primary score is strictly
greater than the incumbent; ties are rejected.

## Analysis

The primary comparison is C1 minus C0 on OUT Recall@100. C0 minus B1 and C1
minus B1 are the additional confirmatory Holm family. After all arms freeze, a
full 1,247-query evaluation is descriptive only. MDE and C-SOEI are prospective
interpretation inputs, not observed-result gates; their Owner values remain
`TBD_BLOCKING`.

The C_DIAGNOSTIC runs only on the identical frozen candidate pool. It records
the pool hash, no-rerank order, frozen-reranker behavior, oracle/reachable nDCG,
promotion/demotion, and failure layer. It does not create an independent
ranking claim.
