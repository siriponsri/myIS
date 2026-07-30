---
paper_id: U067
title: "Prompt Optimization is a Coin Flip"
pdf_sha256: "726bf5b639910e69991fe4d9ded654cca700ebbe40f79d37b10eed71ee6a3638"
object_path: "01_evidence/A-tier/U067_prompt_optimization_is_a_coin_flip.pdf"
legacy_primary_alias: "research/ref-paper/is1/pdfs/68__prompt_optimization_is_a_coin_flip_2026.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: "2604.14585"
arxiv_source: "acquisition_url"
arxiv_confidence: "high"
page_count: 9
record_type: "paper"
tier: "A"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U067: Prompt Optimization is a Coin Flip

## Bibliographic Identity

- Verified title source: `acquisition_metadata_verified_in_pdf`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: 2604.14585 (source: acquisition_url; confidence: high)
- Pages: 9
- Source collection: `is1`
- Legacy primary alias: `research/ref-paper/is1/pdfs/68__prompt_optimization_is_a_coin_flip_2026.pdf`
- Identity result: `verified` (filename/title token overlap 1.00)

## Classification

**Tier A.** Direct HarnessOpt/skill/prompt optimization method evidence. Relevant surface: H/S.

## Content Triage

Controlled content signals found in the full-text extraction: benchmark, prompt optimization, agent, summarization.

Abstract/summary section scan:

> how should we optimize the prompts in these systems? Prompt optimization in compound AI systems Recent work strongly favors end-to-end joint optimization. arXiv:2604.14585v2 [cs.AI] 27 May 2026 is statistically indistinguishable from a coin flip: TextGrad (Yuksekgonul et al., 2025) propagates textual gra- across 72 optimization runs on Claude Haiku 4.5 dients through multi-component systems. DSPy (Khattab (6 methods × 4 tasks × 3 repeats), 49% score et al., 2023) compiles LLM programs with end-to-end op- below zero-shot; on Amazon Nova Lite, the fail- timization. GPTSwarm (Zhuge et al., 2024) treats agent ure rate is even higher. Yet on one task, all six graphs as optimizable structures. These methods implicitly methods improve over zero-shot by up to +6.8 rely on two assumptions: points. What distinguishes success from failure? We investigate with 18,000 grid evaluations and • Assumption A (coupling): Agent prompts interact, 144 optimization runs, testing two assumptions be- so the optimal prompt for one agent depends on the hind end-to-end optimization tools like TextGrad prompt of another, requiring joint rather than indepen- and DSPy, in the order they must be answered: dent optimization. (A) agent prompts interact, requiring joint rather than independent optimization, and (B) individ- • Assumption B (worth optimizing): Individual agent ual prompts are worth optimizing at all. Interac- prompts are worth optimizing, in that changing a tion effects are never significant (p > 0.52, all prompt meaningfully affects system output, even at F < 1.0), and optimization helps only when the realistic training budgets. task has exploitable output structure: a format the model can produce but does not default to. We If Assumption A fails, independent per-agent optimization furthe

Conclusion/discussion section scan:

> No reliable conclusion section was extracted.

## Evidence Use

This record is indexed for source discovery and method/background triage. Any
numeric or comparative claim used in a paper, thesis, slide, or experiment
protocol must be checked against the canonical PDF object and cited to the
relevant page; this digest is not a substitute for claim-level verification.

## Limitations And Verification

- Review depth is metadata verification plus a full-text scan for abstract,
  conclusion, and controlled topic signals. Identifiers are recorded only from
  acquisition URLs, PDF metadata, or explicitly labeled first-page front
  matter; bibliographies are excluded from identifier discovery.
- Tables, figures, equations, appendices, and numeric results were not
  independently transcribed in this corpus migration pass.
- Legacy aliases remain in `catalog/legacy_aliases.csv`; misleading aliases do
  not create a second paper identity.
