# Methodology

The required arms are A0 frozen baseline, A1 curated seed skill, A2 SkillOpt,
A2L SkillOpt-Lite, and A3 typed HarnessOpt. A2, A2L, and A3 independently start
from frozen A1 and use seeds 11, 23, and 47, at 160 rollouts per seed. The
target model is `qwen/qwen3-30b-a3b-instruct-2507` in non-thinking mode through
the provisional OpenRouter CoreWeave BF16 endpoint. The budget is USD 20 per
optimized arm, USD 30 shared services, USD 90 target, and USD 100 hard stop.

The shared query-ID commitment is 250/125/872 with seed 42. Track S retains an
independent evaluator, optimizer, artifacts, budget ledger, and firewall. The
primary test is A3-A2 paired OUT Recall@100 on the untouched Owner-run joint
test. See the Track S protocol for the typed A3 allowlist and confirmation
boundary.
