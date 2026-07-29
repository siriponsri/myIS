# Methodology

The required arms are A0 frozen baseline, A1 curated seed skill, A2 SkillOpt,
A2L SkillOpt-Lite, and A3 typed HarnessOpt. A2, A2L, and A3 independently start
from frozen A1 and use seeds 11, 23, and 47, at 160 rollouts per seed. The
target model is `qwen/qwen3-30b-a3b-instruct-2507` in non-thinking mode through
the provisional OpenRouter CoreWeave BF16 endpoint. The budget is USD 20 per
optimized arm, USD 30 shared services, USD 90 target, and USD 100 hard stop.
A2 uses SkillOpt `v0.2.0` at commit
`51d0a4d96e88558c84dee637f98e24e3fb2d1547`; A2L derives from the adapted
SkillOpt-Lite commit `4cb4eeef1f95375a9179737ab94cf5e64b9647c6`.

CoreWeave preflight is a hard gate. Measured execution stops if the requested
and resolved model or provider differ, if routing or fallback occurs, if any
parameter is dropped, or if the endpoint contract fails. Exactly one identical
retry is allowed only for a transport error. A2, A2L, and A3 match model,
provider, effort, budget, data, evaluator, tools, repeats, retry policy, initial
A1 state, and stopping rules. A3 may change only the declared typed allowlist;
A2L-P and broad A3X remain deferred exploratory lanes.

The shared query-ID commitment is 250/125/872 with seed 42. Track S retains an
independent evaluator, optimizer, artifacts, budget ledger, and firewall. The
primary test is A3-A2 paired OUT Recall@100 on the untouched Owner-run joint
test without multiplicity correction. The preregistered Holm family is A1-A0,
A2-A1, A2L-A1, A3-A1, and A2L-A2; A3-A2L is exploratory only. Each external
confirmation comparison reports exact eligible n, both point estimates, paired
delta, a deterministic 10,000-resample paired-bootstrap 95% CI, rank-biserial
effect, win/loss/tie counts, comparison-family metadata, and input/output
hashes. The repository emits only a hash-only request and ingests only the
schema-validated aggregate response.
