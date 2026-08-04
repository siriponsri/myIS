# Contributing

ArmIndex changes must preserve the canonical control plane, protected-data
boundary, historical evidence, deterministic output, and append-only receipts.

1. Read `AGENTS.md`, `HANDOFF.md`, and `PLAN.md`.
2. Keep changes scoped and add synthetic tests for new contracts.
3. Do not download model weights or access protected data in repository tests.
4. Run focused tests, the full suite, report drift checks, layout validation,
   protected/unsafe-path scans, scoped lint, and `git diff --check`.
5. Never rewrite historical receipts, model results, or Git history.

External contributions cannot open Selection, Final, or release gates.
