# Track R - Ranking and Evidence

Track R receives the exact CF candidate-pool SHA-256 and may not expand, remove,
or substitute candidate families.

Primary claim: a selected reranker increases family-level `OUT nDCG@100` over
the preregistered no-rerank baseline on the identical frozen pool. Gate R is
independent of Gate C. Selection requires a strictly greater primary score and
rejects ties.

R0 measures oracle/reachable headroom. R1 develops practical, passage-aware, and
claim-limitation ranking with controls. R2 produces publication-level verbatim
evidence and an error taxonomy without making novelty/FTO legal conclusions.
PageIndex is optional only as a BM25/dense-routed within-document evidence pilot.

See `PLAN.md` Phases R0-R2 and `FULL_RESEARCH_TRACK_PLAN.md`.
