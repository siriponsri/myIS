# Prism Master Brief

Create a **new anonymous IEEE conference manuscript** for iSAI-NLP 2026 from this pack.

## Goal
Write the strongest scientifically defensible 6-page paper around the story in `01_STORY_ARC_BEYOND_THE_RETRIEVER.md`.

## Working title
**Beyond the Retriever: Rethinking Representation for Cross-Domain Patent Retrieval**

You may improve the title if it becomes clearer and less generic, but do not make it sensational or claim a new SOTA retriever.

## Editorial priorities
1. One central question, not an A0-A8 chronology.
2. Figure-led data storytelling; equations only where indispensable.
3. Every strong sentence must map to evidence in `evidence/CORE_EVIDENCE_A1_A7.md`.
4. Preserve the evidence hierarchy: development → protected confirmation → scale → diagnosis.
5. Make A3 the conceptual reveal, A5 the scientific climax, A6 the scale bridge, and A7 the memorable aftershock.
6. Keep related work concise and position the paper against DAPFAM, recent patent embedding benchmarks, and representation-search work without claiming that “representation matters” is novel.
7. Keep methodology sufficient for reproducibility but compress operational/governance details that do not change scientific interpretation.
8. Use an academic, restrained tone. Let numbers create the surprise.

## Must not do
- Do not invent new CPU/GPU experiments.
- Do not describe A5 as causal proof of representation.
- Do not merge A5 and A6 cross-domain metrics into a trend.
- Do not call the A7 oracle an implemented reranker.
- Do not expose author identities, repository URLs, organization names, private paths, raw IDs, or protected data in the review manuscript.
- Do not add acknowledgements that break double-anonymous review.

## Preferred section structure
- Abstract
- I. Introduction
- II. Related Work
- III. Study Design
- IV. Representation Behavior Across Frozen Retrievers
- V. Protected Confirmation and Full-Scale Diagnosis
- VI. Discussion and Conclusion
- References

This is guidance, not a requirement; optimize for a clean 6-page IEEE paper.

## Output
Create/overwrite `main.tex`, use `references/references.bib`, and compile to PDF. Use `latex/IEEEtran.cls` or `\documentclass[conference]{IEEEtran}`. Keep the review version anonymous.
