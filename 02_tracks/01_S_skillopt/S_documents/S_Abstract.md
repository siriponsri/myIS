# Abstract

Family-level patent retrieval depends not only on a fixed candidate-recovery
harness but also on the instructions and bounded policy surfaces that govern its
use. This manuscript specifies a controlled study of whether typed HarnessOpt
improves retrieval relevance over full SkillOpt after Track C freezes one C1
harness. Five arms separate the frozen harness, a human-authored seed skill,
SkillOpt, SkillOpt-Lite, and a typed HarnessOpt surface. The three optimized arms
start independently from the same A1 state and match model, provider, effort,
data access, evaluator, tools, seeds, rollout ceilings, cost limits, retry
policy, and stopping rules. Provider preflight is a hard gate: routing,
fallback, or parameter dropping invalidates measured execution, and only one
identical retry is permitted for a transport error. Selection accepts only a
strictly greater development score and rejects ties. The primary untouched-test
comparison is A3 minus A2 on family-level OUT Recall@100; preregistered
additional comparisons use Holm correction, while A3 minus A2L remains
exploratory. External confirmation returns aggregates only, including exact n,
point estimates, paired delta, paired-bootstrap uncertainty, rank-biserial
effect, and win/loss/tie counts. The design isolates optimization lineage,
retrieval quality, cost, latency, and failure behavior without treating DAPFAM
relevance as novelty, infringement, validity, freedom to operate, or other
legal truth. No empirical result is available at this protocol stage.

Results: n/a

**wating for results**
