# Bounded Official Codex Research Orchestrator

These PowerShell scripts let the MaxPlus main agent request a bounded,
read-only research review from the Official Codex profile. They are engineering
support only: an orchestrator round is not a P2 candidate iteration, measured
run, selection exposure, or publication decision.

## Safety contract

- The Official child receives `CODEX_HOME=C:\Users\Siripon Sri\.codex-official`
  in its own process environment. The caller's environment is not changed.
- `MYIS_STORE` and `MYIS_MLFLOW_STORE` are removed from the child environment.
- Every call uses `--ephemeral`, `--ignore-user-config`, `--sandbox read-only`,
  the explicit working directory, `gpt-5.6-sol` by default, and the checked-in
  output schema.
- The scripts never authenticate, inspect or copy credentials, change the
  active provider, add writable directories, or bypass the sandbox.
- Prompts, stdout/stderr logs, and raw responses stay under
  `orchestration/results/`, which is ignored except for `.gitkeep`.
- The worker must report both protected-data access and measured execution as
  `false`. Any other value fails local validation and stops the loop.

## Validate without invoking Codex

```powershell
scripts/orchestrator/invoke-official-research.ps1 `
  -PromptFile orchestration/prompts/review.txt `
  -WorkingDirectory . `
  -WhatIf
```

`-WhatIf` checks the executable, fixed Official profile and config, prompt,
working directory, output directory, and JSON schema. It creates no artifact
and does not start Codex.

## Run one Official review

```powershell
scripts/orchestrator/invoke-official-research.ps1 `
  -PromptFile orchestration/prompts/review.txt `
  -WorkingDirectory . `
  -TimeoutSeconds 1800
```

The command returns only invocation metadata. The raw final JSON and captured
stdout/stderr paths are in that metadata and remain untracked.

## Run the bounded loop

```powershell
scripts/orchestrator/run-research-loop.ps1 `
  -PromptFile orchestration/prompts/review.txt `
  -WorkingDirectory . `
  -MaxRounds 2
```

`MaxRounds` defaults to 2 and cannot exceed 3. Each round makes exactly one
Official call. A `revise` result can open the next round; only the prior
structured summary, required changes, evidence gaps, and next action are
carried forward. Full transcripts are never copied into a later prompt.

The loop stops on acceptance, a repeated prompt hash, timeout, nonzero child
exit, local schema failure, `blocked`, or the round limit. Its summary contains
only the round, SHA-256 prompt hash, raw output path, exit code, timeout flag,
verdict, provider label, and model label.

## Scientific boundary

Do not place protected DAPFAM inputs, query or family identifiers, qrels,
membership, per-query outcomes, final-split material, provider payloads, or
credentials in a prompt. These scripts do not run `myis-p2`, change the
`p2-r1-primary-v1` budget, open D2/D3, use GPU, download models, or create
scientific evidence. Raw responses must never be staged.
