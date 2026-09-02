# Elsevier AI-policy verification

Source: https://www.elsevier.com/about/policies-and-standards/generative-ai-policies-for-journals  
Accessed: 2026-09-02  
Publisher: Elsevier

## Verified requirements relevant to this manuscript

- Elsevier requires a separate AI declaration statement in the manuscript when
  AI tools are used for manuscript preparation beyond basic grammar, spelling,
  and punctuation checks.
- The recommended section title is exactly:
  `Declaration of generative AI and AI-assisted technologies in the manuscript preparation process`.
- The statement should identify the tool/service, purpose, and extent of
  human oversight. Authors remain responsible for accuracy, sources, and the
  final manuscript.
- When AI tools are used as part of the research process rather than only for
  manuscript preparation, that use belongs in the Methods section.
- For research/data visualizations, AI must not fabricate, invent, or alter
  underlying data. If AI is used in visualization generation, the Methods
  disclosure should identify the model/tool, version, and developer or
  manufacturer; the visualization must remain directly derived from the
  underlying data through reproducible methods.
- Elsevier states that AI tools must not be listed as authors or co-authors.

## Application to journal_09

The Owner attests `AI_RESEARCH_CODE_ASSISTANCE = YES`.

The manuscript uses the exact recommended title and states the tool/service,
purposes, human review, independent result checking, and author responsibility.
Repository evidence also establishes a bounded pre-measurement Official Codex
candidate proposer/reviewer role and a later publication-figure-code and
aggregate-validation role, each with a verified model and SDK/CLI version;
both are disclosed in Methods. The figure scripts read aggregate publication
CSVs and assert displayed values against canonical evidence. The authors
reviewed the code and outputs, and the record does not show Codex generating
underlying experimental data or executing retrieval. The audit does not verify
one model/version for the later manuscript-preparation pass or the original
authorship of `journal_09/figures/redraw.py`; no unsupported attribution has
been inserted.

The five result plots are reproducible data visualizations derived from the
aggregate publication data and are covered by the Methods disclosure. The
evidence map is an explanatory workflow image. The Owner attests that Codex
assisted code associated with the research/figure workflow, but provenance does
not bind the verified `gpt-5.6-sol` / CLI `0.149.1` session to the submitted
rendition of this diagram. Its caption therefore identifies OpenAI Codex,
OpenAI, the code-assistance role, human verification, and transparently states
that the exact model/version for this figure workflow was not retained.
