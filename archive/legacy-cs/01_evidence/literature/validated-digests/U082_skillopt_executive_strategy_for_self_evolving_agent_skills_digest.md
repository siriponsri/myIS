---
paper_id: U082
title: "SkillOpt: Executive Strategy for Self-Evolving Agent Skills"
pdf_sha256: "87f7f0f323b1671e9202b3ebb1596e909e507c71ecd1b360b0075a5ee1727fe3"
object_path: "01_evidence/A-tier/U082_skillopt_executive_strategy_for_self_evolving_agent_skills.pdf"
legacy_primary_alias: "research/ref-paper/is1/pdfs/84_skillopt_executive_strategy_for_self_evolving_agent_skills.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: "2605.23904"
arxiv_source: "pdf_front_matter"
arxiv_confidence: "medium"
page_count: 27
record_type: "paper"
tier: "A"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U082: SkillOpt: Executive Strategy for Self-Evolving Agent Skills

## Bibliographic Identity

- Verified title source: `pdfinfo`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: 2605.23904 (source: pdf_front_matter; confidence: medium)
- Pages: 27
- Source collection: `is1`
- Legacy primary alias: `research/ref-paper/is1/pdfs/84_skillopt_executive_strategy_for_self_evolving_agent_skills.pdf`
- Identity result: `verified` (filename/title token overlap 1.00)

## Classification

**Tier A.** Direct HarnessOpt/skill/prompt optimization method evidence. Relevant surface: H/S.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, ranking, benchmark, prompt optimization, skill optimization, agent, thai.

Abstract/summary section scan:

> May 2026 SkillOpt: Executive Strategy for Self-Evolving Agent Skills Yifan Yang1,∗,‡ Ziyang Gong2,∗ Weiquan Huang3,∗ Qihao Yang2,∗ Ziwei Zhou4,∗ Zisu Huang4,∗ Yan Li2 Xuemei Gao1 Qi Dai1 Bei Liu1 Kai Qiu1 Yuqing Yang1 Dongdong Chen1 Xue Yang2,‡ Chong Luo1 1 2 3 4 Microsoft Shanghai Jiao Tong University Tongji University Fudan University arXiv:2605.23904v2 [cs.AI] 25 May 2026 Agent skills today are hand-crafted, generated one-shot, or evolved through loosely controlled self-revision—none of which behaves like a deep-learning optimizer for the skill, and none of which reliably improves over its starting point under feedback. We argue the skill should instead be trained as the external state of a frozen agent, with the same discipline that makes weight-space optimization reproducible. SkillOpt is, to our knowledge, the first systematic controllable text-space optimizer for agent skills: a separate optimizer model turns scored rollouts into bounded add/delete/replace edits on a single skill document, and an edit is accepted only when it strictly improves a held-out validation score. A textual learning-rate budget, rejected-edit buffer, and epoch-wise slow/meta update make skill trainin

Conclusion/discussion section scan:

> We presented SkillOpt, a text-space optimizer that treats an external skill document as the trainable state for frozen LLM agents. By separating the target model that executes tasks from the optimizer that edits skills, and by using bounded edit budgets, minibatch reflection, held-out validation gates, rejected-edit buffers, and epoch-wise slow/meta update, SkillOpt turns skill improvement into a controlled learning process rather than ad hoc prompt revision. Across six benchmarks, seven target models, and three execution modes, SkillOpt is best or tied-best on 52 of 52 evaluated cells, lifts GPT–5.5 by +23.5 points on average over no skill in direct chat and by +24.8/ + 19.1 points under Codex and Claude Code harnesses, and beats the strongest per-cell baseline from human, LLM, Trace2Skill, TextGrad, GEPA, and EvoSkill skills by +5.4 points on average. Per-benchmark case studies show that these gains arise from compact (< 2,000 token), interpretable skill artifacts assembled from only 1–4 accepted edits, and that the deployed skills transfer across model scales, harnesses, and nearby benchmarks. These results suggest that compact natural-language skills can serve as a practical domain-adaptation layer for frontier agents, enabling reusable improvement without modifying model weights. 16 Outlook. SkillOpt optimizes a single skill artifact for a single target domain; natural ext

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
