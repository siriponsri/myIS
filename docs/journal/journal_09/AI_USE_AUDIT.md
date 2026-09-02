# AI-use audit

Date: 2026-09-02  
Scope: `docs/journal/journal_09/` and its repository provenance

Publisher policy verified at
`https://www.elsevier.com/about/policies-and-standards/generative-ai-policies-for-journals`
on 2026-09-02; see `ELSEVIER_AI_POLICY_NOTE.md`.

## Evidence reviewed

- `main.tex` and the journal package's declared AI use.
- `WORDING_REPORT.md`, `LITREVIEW_REPORT.md`, and `DATA_PACK/G_manifest.md`.
- Repository history for journal drafting, figure production, and validation
  (`git log -- docs/journal/journal_09 docs/figures scripts docs/paper`).
- Project Codex bridge and execution records, including
  `control/armindex/a2/official-codex-bridge.v1.json`,
  `campaigns/armindex-multiretriever-v2/evidence/a2-five-arm-candidate-freeze.receipt.v1.json`,
  and
  `campaigns/armindex-multiretriever-v2/evidence/a2-official-codex-final-credit-check.receipt.v1.json`.
- The 2026-08-26 Codex session record
  `rollout-2026-08-26T19-28-11-01a03e0a-d18d-77e2-a255-8035a3283212.jsonl`,
  including direct tool calls that created the Altair and Matplotlib figure
  scripts and validated the aggregate publication evidence.

## Findings

Owner attestation received on 2026-09-02:
`AI_RESEARCH_CODE_ASSISTANCE = YES`.

| Activity | Repository evidence | Disclosure status |
|---|---|---|
| Manuscript language editing | `main.tex`, `WORDING_REPORT.md`, journal commit history | Disclosed |
| Manuscript/document organization | journal package structure and commit history | Disclosed |
| Literature/citation organization | `LITREVIEW_REPORT.md`, bibliography correction commits | Disclosed |
| Research-process candidate design and review | Official Codex bridge receipts and the frozen A2 candidate-freeze contract identify a pre-measurement proposer/reviewer role using aggregate-safe inputs | Disclosed in Methods |
| Research/analysis code assistance beyond the bounded bridge | The Owner attests that Codex assisted research/code work. Direct session evidence establishes publication-figure code generation and aggregate evidence validation, but does not establish retrieval/ranking/embedding experiment-code authorship | Disclosed in Methods at the verified level of specificity |
| Data analysis execution | Codex directly checked and reconciled the aggregate publication projection against canonical A1/A2/A3/A5/A7 evidence; the record does not show Codex executing retrieval or generating underlying experimental results | Disclosed in Methods at the verified level of specificity |
| Figure/data-visualization code authorship or editing | Direct `apply_patch` calls created `docs/paper/figures/build_altair_figures.py` and `docs/paper/figures/rebuilt/source/generate_rebuilt.py`, followed by generation, rendering, and value checks | Disclosed in Methods as OpenAI Codex `gpt-5.6-sol`, CLI `0.149.1` |
| `docs/journal/journal_09/figures/redraw.py` authorship | Session evidence verifies only its later deletion, not its original creation or editing | No file-specific authorship or model/version claim made; not needed for the bounded disclosure |
| Scientific experiment/model/dataset/metric changes | No evidence of such a change in this gate; explicitly prohibited by the gate scope | No change found |

## Tool identity boundary

The A2 research-process evidence identifies OpenAI Codex model `gpt-5.6-sol`
and SDK/CLI version `0.144.4`; those details are disclosed in Methods for the
bounded candidate proposer/reviewer role. A separate, direct 2026-08-26 session
record identifies OpenAI Codex model `gpt-5.6-sol` and CLI `0.149.1` for the
publication-figure scripts and aggregate evidence validation; those details
are also disclosed in Methods. The evidence does not verify a single Codex
model or version for the later manuscript-preparation pass or the original
authorship of `journal_09/figures/redraw.py`. The final AI declaration therefore
makes no model/version claim for those uses rather than guessing.

## Human verification

The manuscript states that the authors reviewed and edited generated material,
checked reported results against canonical research artifacts, and retain full
responsibility for the publication.

## Audit result

**PASS - OWNER ATTESTATION RECORDED**

The Owner attests that Codex assisted research/code work. The manuscript
discloses the directly evidenced candidate-program, publication-figure-code,
and aggregate-validation roles with verified tool identity and versions. It
does not over-attribute `journal_09/figures/redraw.py`, retrieval execution, or
the generation or alteration of underlying experimental data.
