# Codex Provider Switching

This guide separates user-level Codex state from the myIS Research control
plane. Provider switching is an engineering-assistant operation; it is not
scientific evidence and it must not change campaign, schema, evaluator, or
protected-store configuration.

## Profiles

The intended user-level layout is:

```text
$HOME\.codex-official
$HOME\.codex-maxplus
```

The installed CLI is `codex-cli 0.146.0`. The CLI supports process-scoped
`CODEX_HOME` and `--profile`. The current `$HOME\.codex` state is preserved
until the Owner manually verifies a replacement profile. Do not copy
`auth.json`, session files, or provider credentials between profiles.

Project `.codex/config.toml` may contain only shared, non-secret behavior. It
is not allowed to select authentication, copy credentials, or silently change
the provider used by a scientific run.

## Manual switching workflow

1. Start a new PowerShell session.
2. Choose one profile directory outside the Git worktree.
3. Run the matching `scripts/dev/start-codex-*.ps1 -WhatIf` check.
4. Create or configure the profile manually if the launcher reports it missing.
5. Run the official CLI login command yourself, only when you intend to log in.
6. Start a new Codex session and verify `/status`.
7. Perform a read-only repository survey before editing.
8. Do not expose `MYIS_STORE`, `MYIS_MLFLOW_STORE`, qrels, query IDs, or other
   protected data to the assistant by default.

The launchers never login, logout, copy credentials, edit keyrings, or run a
network/authentication smoke test. They fail closed when the executable,
profile, or config is missing. `-WhatIf` never starts Codex.

## Rollback

Close the current session and start a new PowerShell process with the previous
`CODEX_HOME` value, or use the preserved current `$HOME\.codex` state. No
repository edit is required to return to MaxPlus. The OS keyring may still be
shared by the CLI; that behavior is not assumed to be isolated by this guide.

## Scientific provenance boundary

For engineering sessions, a sanitized provider label may be recorded in a
session capsule. It is not model lineage. A future LLM-in-the-loop experiment
must freeze provider, model ID and revision, reasoning effort, instruction and
skill hashes, prompt hash, budget profile, seed/determinism controls, Git
commit, and request hash, with provider fallback disabled. That experiment is
not activated by P2 readiness.

MaxPlus endpoint names and environment-variable names remain Owner-verification
items. This repository contains no provider key, bearer token, endpoint with an
embedded credential, or credential-process output.

## Relationship to repository rules

`AGENTS.md` contains only provider-neutral safety rules. There is no active
`CLAUDE.md`; the historical archive copy is not authority. Canonical research
facts remain in `control/`, schemas, manifests, receipts, and validated P2
packages. Dashboard, MLflow, Obsidian, and this document are projections or
operating guidance only.
