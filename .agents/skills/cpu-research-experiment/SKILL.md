---
name: cpu-research-experiment
description: Use when a manuscript review exposes an evidence gap that can be resolved with a new local CPU-only experiment, evaluation, ablation, diagnostic, statistical analysis, or error analysis while preserving frozen/protected evaluation governance.
---

# CPU Research Experiment

## Gate
Do not experiment for curiosity during manuscript optimization.

Before execution define:
- reviewer/research question;
- affected manuscript claim;
- minimum experiment;
- decision rule;
- valid split/evaluation boundary.

## Governance first
Inspect repository rules for:
- frozen experiments;
- held-out/test protection;
- preregistered candidates;
- selection vs confirmatory evaluation;
- seeds;
- metric definitions.

Never use final/test evidence for adaptive selection when governance forbids it.

## CPU only
Disable GPU/CUDA explicitly when needed.
Do not use paid APIs without authorization.

## Reproducibility
Record:
- timestamp/run ID;
- git/source state when available;
- command;
- config;
- input artifacts;
- split;
- seed(s);
- environment;
- runtime;
- outputs;
- metrics.

## Interpretation
Classify result as:
- confirmatory;
- diagnostic;
- exploratory;
- failed/inconclusive.

Do not promote exploratory evidence into a confirmatory claim.

## Failure
A failed or null result is evidence about the experiment, not permission to rerun until a desired answer appears.
Change the experiment only for a documented methodological reason.
