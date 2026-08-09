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

A1_2_SCAFFOLD_NEXT_AUTHORIZED_ACTION = (
    "/goal Run only the Owner-local SSH/Vast A1.2 preflight from "
    "docs/operations/A1_2_VAST_4X3090_OWNER_RUNBOOK_V3.md on one disposable four-RTX3090 "
    "instance. Validate the clean pushed v3 correction, preserve the unchanged v2 bytes, "
    "and verify the frozen bundle commit, tree, image digest, four GPU UUIDs, locked "
    "runtime and model bytes, adapter parity, Qwen maximum length, local protected-root "
    "boundary, live USD quote, heartbeat/resume, safe return path, and provider destroy/TTL "
    "path. Keep launch_allowed=false and adopted_for_execution=false; do not start measured "
    "retrieval, optimization, Selection, Final, paid API work, or weight changes."
)

A1_LONG_RUN_NEXT_AUTHORIZED_ACTION = (
    "/goal Execute one governed long-running A1 closeout from the validated v15 local "
    "adoption inputs. In one continuous workflow, create or validate the tracked runbook "
    "and append-only execution ledger, complete fresh Vast identity, all-fee quote, "
    "whole-workload budget admission, provider admission, and execution-adoption receipts, "
    "then run the frozen A1.2 five-arm common screen end to end. Require all 25 program-arm "
    "results, collect and validate aggregate-safe receipts, deterministically promote at "
    "most three arms, close A1, safely collect artifacts, and destroy the Vast instance. "
    "Keep the same instance throughout A1 only while its identity, hashes, watchdog, "
    "protected scan, TTL, and all hard stops remain valid; otherwise checkpoint, collect "
    "safely, and destroy. Stop before A2, HARNESS-DEV, Selection, and Final. Do not change "
    "the frozen v11-v15 scientific semantics, model weights, evaluator, split, metrics, or "
    "candidate rules, and do not use paid APIs, provider fallback, or runtime model downloads."
)
