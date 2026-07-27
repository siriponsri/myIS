# Publication Roadmap

## Frozen prior work

Paper D remains a frozen boundary study: a fixed candidate pool and tested 0.6B
scalar reranker/instruction surface did not show a measurable held-out OUT
unlock. It does not establish that all reranking or prompt optimization fails.

## Track C: Candidate Exposure

Question: which retrieval strategy increases OUT-domain relevant-family
exposure under a controlled budget?

Primary outcomes: Recall@K, relevant-family exposure, unique relevant-family
contribution, cost and latency. Gate 0 compares current recall with an exposure
oracle. Gate 1 tests manual route variants. Only then may a bounded optimizer
pilot run.

## Track R: Ranking and Evidence

Question: after freezing a candidate pool containing relevant families, which
small-model ranking/evidence surface best orders and supports them?

Candidate surfaces may include claim elements, evidence passages, pairwise or
listwise ranking, structured rubrics and citations. Gate 0 compares observed
ranking with an oracle over the frozen pool.

## Track S: Skill Evolution

Question: can an agent learn a reusable patent-search procedure that transfers
to a small local model?

Start with S-on-C. Compare no skill, human skill, GEPA and SkillOpt; add SPEAR
only when diagnostic evidence supports it. Gate 0 compares no-skill with a
strong human-authored skill. Track S must measure both quality and transfer.

## Candidate publications

- Paper E: Track C plus Track R, separating candidate exposure loss from ranking
  loss.
- Paper F: Track S, validation-gated skill optimization and API-to-local
  transfer.

Titles and claims remain provisional until results support them.

