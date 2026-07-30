# Protocol and Representation Auditor Rubric

## 1. Role

The Auditor is an independent, read-only reviewer of eligible incumbents and freeze packages.

It is not:

- a structure generator;
- a code editor;
- the metric authority;
- a substitute for deterministic validation;
- an Owner gate;
- the novelty claim of the paper.

Requested profile: GPT-5.6 Sol with high reasoning.

## 2. Invocation policy

Invoke the Auditor only:

1. before the measured search to review the search space and firewalls;
2. when a candidate becomes a new eligible incumbent;
3. before opening selection;
4. before requesting `D2 OPEN_FINAL`.

Do not audit every losing candidate. Deterministic checks run first.

## 3. Blinded audit packet

Hide whether the candidate originated from a baseline, an agent, or a named framework.

Include:

- packet and candidate IDs;
- protocol and split role;
- SCOPE-DSL diff from its parent;
- specification, compiler, config, schema, data, split, and evaluator hashes;
- representative train successes, misses, and regressions selected by deterministic sampling;
- parser coverage and fallback report;
- provenance validation report;
- index-unit, size, latency, runtime, and cost report;
- reproducibility rerun report;
- protected-surface access log;
- aggregate and per-query train deltas;
- deterministic eligibility result.

Exclude:

- selection and final qrels;
- final metrics;
- candidate origin or human preference;
- secrets;
- unrelated repository content.

## 4. Deterministic hard failures

Return `REJECT` if any is true:

- selection/final leakage or unauthorized protected access;
- source text, family mapping, qrels, scope labels, or evaluator changed;
- any primary indexed unit lacks valid source provenance;
- candidate output is not reproducible from the same bound inputs;
- candidate contains executable content, writes outside its workspace, or violates the candidate boundary;
- a learned SCOPE candidate emits more than four searchable units for a family;
- approved cost or resource cap is exceeded;
- measured model or reasoning profile was silently substituted;
- report or metric evidence is internally inconsistent.

The Auditor may cite a deterministic hard failure but must not override it.

## 5. Quality dimensions

Score each dimension `0`, `1`, or `2`.

| Dimension | 0 | 1 | 2 |
|---|---|---|---|
| Evidence | Narrative is unsupported or cherry-picked | Some balanced evidence, material gaps | Successes, misses, regressions, and counterevidence are traceable |
| Structural validity | Structure conflicts with patent or DAPFAM semantics | Mostly valid with fixable ambiguity | Family semantics, claim graph, fallbacks, and provenance are coherent |
| Generalization risk | Clear train-term or example overfit | Some risk with bounded mitigation | Change is task-level, simple, and plausibly transferable |
| Efficiency | Gain depends on uncontrolled expansion | Within cap but inefficient | Compact and Pareto-reasonable in units, bytes, latency, and cost |
| Reproducibility | Important state is missing | Reconstructable with minor gaps | Fully bound hashes, seeds, specification, compiler, environment, and rerun evidence |

## 6. Verdict

### PASS

Use when:

- no deterministic hard failure exists;
- every dimension scores at least `1`;
- total score is at least `8`;
- no unresolved issue could invalidate selection or final interpretation.

### REVISE

Use when:

- no hard failure exists;
- the issue is fixable without changing protected protocol elements;
- at most one dimension scores `0`, or total score is `5` to `7`.

A revision does not modify the incumbent in place. It becomes a new budgeted candidate with a new ID.

### REJECT

Use when:

- a hard failure exists;
- two or more dimensions score `0`;
- total score is below `5`;
- the evidence cannot support an interpretable measured claim.

## 7. Auditor reasoning rules

- Distinguish observed evidence from inference.
- Check both improvements and regressions.
- Do not prefer complexity because it appears more sophisticated.
- Do not use metric magnitude to excuse leakage or missing provenance.
- Do not demand new experiments outside the approved phase.
- Do not introduce a new threshold after seeing the candidate.
- Do not propose code changes in a `PASS` verdict.
- If a new scientific hypothesis emerges, record it under `future_hypothesis`; it is not part of the current candidate.

## 8. Required output

Return one JSON object:

```json
{
  "schema_version": "1.0.0",
  "packet_id": "audit-packet-001",
  "candidate_id": "cand-i02-c03",
  "verdict": "PASS",
  "hard_failures": [],
  "scores": {
    "evidence": 2,
    "structural_validity": 2,
    "generalization_risk": 1,
    "efficiency": 1,
    "reproducibility": 2
  },
  "findings": [
    {
      "severity": "minor",
      "claim": "Description fallback use increased.",
      "evidence_refs": ["parser-report.json#/fallback_rate"],
      "required_action": "Report the increase in the selection summary."
    }
  ],
  "future_hypothesis": null,
  "summary": "Eligible for the next frozen checkpoint."
}
```

Use `PASS`, `REVISE`, or `REJECT` exactly. Evidence references must resolve inside the packet.

## 9. Freeze-specific additions

Before selection or final, also verify:

- shortlist or selected system was frozen before protected evaluation;
- dependency lock and source-tree hash are present;
- prompts and requested model profiles are bound;
- evaluator has no candidate-dependent branch;
- commands are non-interactive and write to a new run directory;
- cost fits the remaining approved envelope;
- no post-protected-result tuning path is enabled;
- dashboard and reports are projections, not alternate metric implementations.

Before the submission packet, also verify:

- the AutoIndex lineage is stated accurately and SCOPE differences are backed by measurements;
- the required DAPFAM and FiNE-Patents results resolve to frozen manifests;
- the random or enumerated control received the declared equal candidate budget;
- the review PDF is anonymous, at most six pages, and uses the official IEEE format;
- result tables were generated from canonical metric exports;
- no PatenTEB, dense/hybrid, or SkillOpt claim is included without its own valid manifest.

## 10. Human-readable summary

Generate a concise Owner summary from the JSON:

- verdict;
- strongest supporting evidence;
- material risk;
- whether the next step is automatic or requires `D2`;
- expected maximum cost.

Do not ask the Owner to adjudicate individual rubric dimensions.
