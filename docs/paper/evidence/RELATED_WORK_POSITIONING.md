# Related-Work Positioning Notes

Use this only as a starting map. Verify bibliographic metadata and claims against primary sources before final submission.

## DAPFAM
Family-level cross-domain patent-retrieval benchmark with explicit in-domain/out-of-domain relations; studies lexical/dense retrieval, document/passage granularity, aggregation and fusion. It establishes that cross-domain retrieval is difficult and that representation/granularity choices matter.

**Position this paper beyond:** “representation matters.”
**Our angle:** heterogeneous representation behavior across multiple frozen retrievers, cross-retriever transfer behavior, protected confirmation, and post-confirmatory candidate-exposure diagnosis.

## Recent patent embedding benchmarks
Recent work evaluates many embedding models and multiple patent text views, showing that quality depends on model family, scale, text view and configuration, with persistent out-of-domain degradation.

**Do not claim:** this is the first paper to compare patent representations or embeddings.

## AutoIndex / representation-program search
Representation-search work treats document construction as an explicit search variable around a frozen retrieval backend.

**Position carefully:** the present paper is not simply “representation search improves retrieval.” Its strongest empirical story is that representation advantages were heterogeneous and did not transfer consistently across frozen retrievers, followed by protected system-level confirmation.

## Fusion / multi-retriever work
Fusion and expert routing motivate complementarity, but ArmIndex development controls showed that adding systems did not monotonically improve quality. This is secondary context, not the headline contribution.

## Core novelty sentence to aim for
> Rather than treating document construction as a model-independent constant, we empirically examine how representation choices behave across heterogeneous frozen retrievers, then separate development observations from protected system-level confirmation and full-scale failure diagnosis.

Primary source starting points from the repository research notes:
- DAPFAM: Ayaou et al., arXiv:2506.22141 / Array 31 (2026) 100720.
- Benchmarking Patent Embeddings: Yousefiramandi and Cooney, arXiv:2605.24297.
- AutoIndex representation-search work: verify the correct AutoIndex paper/citation before submission; do not confuse it with database “AutoIndexer” work.
- BM25, RRF, nDCG, and bootstrap references are already seeded in `references/references.bib`.
