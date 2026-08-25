# Literature Audit

The related-work section was checked against the requested sources and the local literature map before drafting.

| Source | Verified use in paper | Boundary |
| --- | --- | --- |
| [DAPFAM](https://arxiv.org/abs/2506.22141) | Family-level, domain-aware patent retrieval benchmark; 1,247 queries and explicit IN/OUT partitions | Benchmark context, not a new dataset contribution |
| [Benchmarking Patent Embeddings](https://arxiv.org/abs/2605.24297v2) | Multi-task evidence that patent embedding quality varies by task and domain | Current arXiv metadata verified as v2 on 2026-08-23 |
| [AutoIndexer](https://arxiv.org/abs/2507.23084v1) | Adjacent motivation for treating search/index configuration as an operating variable | Not patent-retrieval evidence and not used for performance comparison |
| [Reciprocal Rank Fusion](https://doi.org/10.1145/1571941.1572114) | Original source for the RRF control | Crossref metadata verified 2026-08-23 |
| [Cumulated Gain-Based Evaluation](https://doi.org/10.1145/582415.582418) | Original source for DCG/nDCG evaluation | Crossref metadata verified 2026-08-23 |
| [Bootstrap Methods and Their Application](https://doi.org/10.1017/CBO9780511802843) | Method source for percentile bootstrap intervals | Crossref metadata verified 2026-08-23 |

Local literature-map entries U001--U014 were used to cross-check the framing around patent retrieval, prior-art search, family-level evaluation, domain shift, and dense/sparse baselines. The manuscript explicitly narrows its novelty: Recall@k, candidate-depth diagnosis, and the reranker pool bound are prior art. The contribution is the receipt-bound DAPFAM case study and its separation of raw incidence composition from the macro-Recall oracle. Internal project identifiers and control vocabulary are excluded from the manuscript.
