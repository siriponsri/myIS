# A1.2 Whole-Workload Budget Admission v12

This additive local-only evaluator tests whether a sanitized, fresh, complete
quote can fund the entire frozen A1.2 common screen. It does not contact Vast
or another provider, reserve a GPU, open SSH, adopt execution, or start a
measured run.

The frozen contract is
`control/armindex/a1.2/whole-workload-budget-admission.v12.json`. It uses a
six-hour TTL and these hard stops: USD 18 common screen, USD 23 A1 total, and
USD 100 campaign total. It calculates the charge exactly as:

```text
ceil(ttl_seconds / billing_granularity_seconds) * billing_granularity_seconds
/ 3600 * compute_hourly_rate_usd + storage_fee_usd + network_fee_usd
+ platform_or_other_fee_usd + tax_or_surcharge_usd
```

Prepare a sanitized JSON input outside Git. It must contain every fee, the
quote and evaluation timestamps in UTC, prior aggregate spend for all three
hard-stop scopes, and the complete five-arm / 25-result workload declaration.
Do not include an instance ID, endpoint, credentials, qrels, membership, query
IDs, paths, or provider payloads.

```json
{
  "quote": {
    "quote_observed_at_utc": "2026-08-08T00:00:00Z",
    "compute_hourly_rate_usd": 0.60,
    "billing_granularity_seconds": 60,
    "minimum_billable_seconds": 60,
    "storage_fee_usd": 0.00,
    "network_fee_usd": 0.00,
    "platform_or_other_fee_usd": 0.00,
    "tax_or_surcharge_usd": 0.00
  },
  "prior_spend_usd": {"common_screen": 0.0, "a1_total": 0.0, "campaign": 0.0},
  "workload": {
    "arm_ids": ["ARM-01", "ARM-02", "ARM-03", "ARM-04", "ARM-05"],
    "expected_program_arm_runs": 25,
    "partial_arm_admission": false
  },
  "evaluated_at_utc": "2026-08-08T00:05:00Z"
}
```

Check the frozen local status:

```powershell
uv run --no-sync python -m myis_research.armindex.a1_2_whole_workload_budget_admission_v12 status --repository-root .
```

Evaluate the local input:

```powershell
uv run --no-sync python -m myis_research.armindex.a1_2_whole_workload_budget_admission_v12 evaluate --repository-root . --input <SAFE_OWNER_LOCAL_QUOTE_JSON> --receipt-id a1.2-whole-workload-budget-admission-<attempt>-v12
```

`PASS_BUDGET_ADMISSION_LOCKED` means only the quoted budget arithmetic passed.
It still has `provider_contact_allowed=false`, `launch_allowed=false`, and
`adopted_for_execution=false`. A quote older than 900 seconds, an incomplete or
partial workload, or a projected charge over any hard stop returns
`BLOCKED_BUDGET`. Missing, unknown, non-finite, or negative fees are rejected
without a receipt.
