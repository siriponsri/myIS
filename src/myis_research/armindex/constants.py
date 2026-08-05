"""Canonical ArmIndex handoff text shared by controls and projections."""

A0_8_NEXT_AUTHORIZED_ACTION = (
    "/goal Execute A0.8_COMPUTE_AND_STORAGE_FEASIBILITY_FIXTURES from the canonical PLAN and "
    "control/campaigns/armindex-multiretriever-v2.yaml. Use synthetic fixtures only; do not "
    "access protected data, start measured retrieval, download model weights, use GPU or paid "
    "APIs, open Selection, or open Final."
)

A0_9_NEXT_AUTHORIZED_ACTION = (
    "/goal Execute A0.9_VALIDATION_SAFETY_AND_CLOSEOUT from the canonical PLAN and "
    "control/campaigns/armindex-multiretriever-v2.yaml. Validate the synthetic-only A0 "
    "migration, close A0 if all gates pass, and keep A1 locked until that closeout receipt "
    "is complete. Do not access protected data, start measured retrieval, download model "
    "weights, use GPU or paid APIs, open Selection, or open Final."
)

A1_1_NEXT_AUTHORIZED_ACTION = (
    "/goal Execute A1.1_ADAPTER_FIXTURE_VALIDATION from the canonical PLAN and "
    "control/campaigns/armindex-multiretriever-v2.yaml. Build and validate only "
    "synthetic/offline adapter fixtures on CPU. Do not access protected data, start "
    "measured retrieval, download model weights, use GPU or paid APIs, switch providers, "
    "open Selection, or open Final. Keep A1 measured screening closed until a separate "
    "execution contract authorizes it."
)

A1_2_NEXT_AUTHORIZED_ACTION = (
    "/goal Prepare and validate the versioned A1.2_COMMON_MULTI_ARM_SCREENING "
    "execution contract, hash-bound budget profile, frozen offline model and adapter "
    "locks, Owner-local launch checklist, and automatic shutdown plan from the validated "
    "A1.1 engineering receipt. Complete this scaffold before reserving GPU capacity. Do "
    "not launch measured retrieval, access protected payloads from the agent workspace, "
    "download model weights during measured runtime, use paid APIs, switch providers, "
    "open Selection, or open Final until the separate contract is adopted and validated."
)
