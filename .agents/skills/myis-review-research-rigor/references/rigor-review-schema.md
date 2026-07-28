# Rigor review schema

## Scoring anchors

Apply these anchors to every dimension:

| Score | Meaning |
|---:|---|
| 5 | Complete, precise, independently reproducible, and free of material gaps |
| 4 | Strong with minor gaps that do not change the conclusion |
| 3 | Adequate but missing meaningful evidence or methodological detail |
| 2 | Major weaknesses undermine one or more central claims |
| 1 | Fundamental contradiction, invalid method, or unusable evidence |

Map the mean only after checking critical findings:

- Strong Accept: mean at least 4.5 and no dimension below 3.
- Accept: mean at least 3.8 and no dimension below 2.
- Weak Accept: mean at least 3.0 and no dimension below 2.
- Weak Reject: mean at least 2.0 but below 3.0, or any dimension below 2.
- Reject: mean below 2.0, any dimension equals 1, or a critical governance violation invalidates the package.

## Minimum JSON shape

```json
{
  "schema_version": "myis.rigor-review.v1",
  "review_id": "<unique-id>",
  "artifact": "<name>",
  "artifact_path": "<repository-relative-path>",
  "artifact_sha256": "<hash-or-null>",
  "review_status": "complete",
  "governance": {
    "approval_valid": true,
    "split_isolation_valid": true,
    "gate_order_valid": true,
    "budget_valid": true,
    "manifest_integrity_valid": true,
    "blocking_findings": []
  },
  "overall": {
    "grade": "Accept",
    "mean_score": 4.0,
    "one_line_summary": "<summary>",
    "strengths": [],
    "weaknesses": []
  },
  "dimensions": {
    "D1_evidence_relevance": {"score": 4, "strengths": [], "weaknesses": [], "suggestions": []},
    "D2_falsifiability": {"score": 4, "strengths": [], "weaknesses": [], "suggestions": []},
    "D3_scope_calibration": {"score": 4, "strengths": [], "weaknesses": [], "suggestions": []},
    "D4_argument_coherence": {"score": 4, "strengths": [], "weaknesses": [], "suggestions": []},
    "D5_exploration_integrity": {"score": 4, "strengths": [], "weaknesses": [], "suggestions": []},
    "D6_methodological_rigor": {"score": 4, "strengths": [], "weaknesses": [], "suggestions": []}
  },
  "findings": [
    {
      "finding_id": "F001",
      "dimension": "D6_methodological_rigor",
      "severity": "major",
      "target_artifact": "metrics.json",
      "target_entity": "out.ndcg_at_100",
      "evidence_locator": "JSON pointer or exact quote",
      "observation": "<fact>",
      "reasoning": "<impact>",
      "suggestion": "<action>"
    }
  ],
  "questions_for_owner": [],
  "read_order": []
}
```

Use `blocked_structural`, `blocked_authorization`, or `not_assessable` for `review_status` when a complete semantic review is not legitimate. Do not emit a numeric grade in those states.
