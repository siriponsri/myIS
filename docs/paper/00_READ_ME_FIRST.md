# Prism Evidence Pack — iSAI-NLP 2026

## Purpose
This is a deliberately lean writing pack for a new 6-page iSAI-NLP 2026 conference manuscript derived from the myIS/ArmIndex research program.

**Repository snapshot:** `siriponsri/myIS` @ commit `d0d6039a04eda97d7696a1b86ab4b1adf94d6595` (main, 2026-08-25).

## Authority order
1. `evidence/CORE_EVIDENCE_A1_A7.md` — numeric/claim authority for the conference story.
2. `evidence/RESEARCH_PROTOCOL.md` — protocol and claim-discipline guardrail.
3. `01_STORY_ARC_BEYOND_THE_RETRIEVER.md` — narrative authority.
4. `venue/ISAINLP_2026_SUBMISSION_GUIDELINES.md` and `venue/RULES_AND_TEMPLATE.md` — venue/format authority.
5. `references/references.bib` and `evidence/RELATED_WORK_POSITIONING.md` — literature starting point; verify metadata before final submission.

## Non-negotiable scientific boundaries
- Do not invent experiments, metrics, uncertainty estimates, datasets, ablations, or comparisons.
- Keep A1-A3 as development evidence; do not call them final generalization.
- A5 confirms the **complete frozen configuration**, not the isolated causal effect of representation.
- A5 and A6 use different cross-domain population definitions. Never present their metric values as a before/after trend.
- A7 oracle is an analytical within-pool upper bound, not an implemented reranker.
- Do not claim universal superiority, legal validity, infringement/FTO conclusions, or commercial deployability.
- Do not claim that every retriever requires a unique representation. The defensible finding is heterogeneous behavior and inconsistent transfer advantage.

## Writing objective
Produce a compelling empirical NLP/IR conference paper, **not** a chronological A0-A8 project report. Use figures and data storytelling. Minimize equations unless required for metric definitions or protocol clarity.

## Deliberately excluded
- Existing manuscript/PDF: excluded to avoid anchoring a fresh story to the old draft.
- A0 engineering details: not central to the 6-page scientific narrative.
- A8 publication workflow: not scientific evidence.
- Raw/protected query IDs, qrels, rankings, split membership, and private artifacts.

## Suggested working title
**Beyond the Retriever: Rethinking Representation for Cross-Domain Patent Retrieval**

