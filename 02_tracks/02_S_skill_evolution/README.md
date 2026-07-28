# Track S - Optional Adaptation Surface

Track S is optional A0-A3 methods work and does not block Gate C or Gate R.

| Arm | Editable surface |
|---|---|
| A0 | frozen baseline |
| A1 | human seed skill, frozen harness |
| A2 | optimized skill, frozen harness |
| A3 | optimized skill plus declared typed policy fields |

Measured optimizer calibration starts GPT-5.6 Sol Medium and escalates to High
only after qrels-blind validity failure. A2/A3 then freeze identical model,
provider, effort, budget, initial state, data access, evaluator, module pool,
repeats, and stopping. Luna is support-only or a separate cost ablation; no
silent fallback. Expose only adaptation/selection qrels and report every repeat.

See `PLAN.md` Phase S and `FULL_RESEARCH_TRACK_PLAN.md`.
