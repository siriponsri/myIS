# Track S: SkillOpt and HarnessOpt

Track S is the required adaptation-surface study in `myIS Research` protocol
`1.0`, Track version `0.1`. Its sequence is frozen Track C1 harness -> S0 -> S1
-> SF -> joint test. It is not an independent ranking track and does not alter
Track C candidate exposure.

The study compares required arms A0, A1, A2, A2L, and A3. A2, A2L, and A3 each
start from the same frozen A1 artifact and run seeds `11`, `23`, and `47` with a
maximum of `160` rollouts per seed. The primary comparison is A3-A2 on paired
`OUT Recall@100` at the Owner-run joint test. See the authoritative protocol at
[`IS_RESEARCH_TRACK_S_V0.1_SKILLOPT_HARNESSOPT_PLAN.md`](../../00_governance/IS_RESEARCH_TRACK_S_V0.1_SKILLOPT_HARNESSOPT_PLAN.md).

`S_artifacts/` is reserved for immutable configs, manifests, optimization
lineage, aggregate results, and receipts. `S_documents/` contains the
result-free IEEE manuscript skeleton. No qrels, split membership, per-query
outcomes, credentials, or confirmation payload belongs in this tree.

## Operating boundary

The target is `qwen/qwen3-30b-a3b-instruct-2507` non-thinking through the
provisional OpenRouter CoreWeave BF16 endpoint, with no fallback. A2 uses
SkillOpt `v0.2.0` at commit `51d0a4d96e88558c84dee637f98e24e3fb2d1547`; A2L
uses adapted SkillOpt-Lite at commit
`4cb4eeef1f95375a9179737ab94cf5e64b9647c6`. A3 is limited to the typed
allowlist documented in the protocol. Experiments remain gated.
