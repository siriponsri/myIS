# Appendix A - Protocol and Leakage Controls

Results: n/a

**wating for results**

Candidate generation may use only query-derived TAC, deterministically parsed
independent claims, and grounded mechanism views. It must not use qrels, target
identifiers or text, direct or indirect citation paths to DAPFAM positives,
protected test information, or Track S selection information. Every generated
term requires a source span, route name, prompt/model hash, grounding status,
and any quarantine reason.

The Owner-run D0 process freezes seed, membership hashes, qrels snapshot, and
OUT-positive availability/count before development. C_MARGIN_VALUES_TBD_BLOCKING
requires an Owner choice of delta_IN and delta_ALL from 0, 0.0025, or 0.005,
with delta_ALL less than or equal to delta_IN. C_SOEI_VALUE_TBD_BLOCKING is
interpretive only.
