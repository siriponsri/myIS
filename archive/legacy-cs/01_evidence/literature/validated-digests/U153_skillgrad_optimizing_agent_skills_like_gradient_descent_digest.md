---
paper_id: U153
title: "SkillGrad: Optimizing Agent Skills Like Gradient Descent"
pdf_sha256: "ac08480ae67c537dcfdc7ddb9dd1938adde2330943c09b3682a8f8e7383b1cfe"
object_path: "01_evidence/A-tier/U153_skillgrad_optimizing_agent_skills_like_gradient_descent.pdf"
legacy_primary_alias: "research/ref-paper/is1/pdfs/87_skillgrad_optimizing_agent_skills_like_gradient_descent.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: "2605.27760"
arxiv_source: "pdf_front_matter"
arxiv_confidence: "medium"
page_count: 26
record_type: "paper"
tier: "A"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U153: SkillGrad: Optimizing Agent Skills Like Gradient Descent

## Bibliographic Identity

- Verified title source: `pdfinfo`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: 2605.27760 (source: pdf_front_matter; confidence: medium)
- Pages: 26
- Source collection: `is1`
- Legacy primary alias: `research/ref-paper/is1/pdfs/87_skillgrad_optimizing_agent_skills_like_gradient_descent.pdf`
- Identity result: `verified` (filename/title token overlap 1.00)

## Classification

**Tier A.** Direct HarnessOpt/skill/prompt optimization method evidence. Relevant surface: C, R, H/S.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, benchmark, contrastive, knowledge graph, prompt optimization, skill optimization, agent, legal, classification, calibration.

Abstract/summary section scan:

> applications require more than general problem- solving ability. In specialized, procedure-heavy arXiv:2605.27760v1 [cs.AI] 26 May 2026 Agent skills provide a lightweight way to adapt domains, such as spreadsheet manipulation (Chen LLM agents to specialized domains by storing et al., 2024), document editing (Li et al., 2025), reusable procedural knowledge in structured and codebase maintenance (Li et al., 2026a), agents files. However, whether downloaded from third must repeatedly follow domain-specific workflows, parties or self-generated, these skills are of- ten unreliable, incomplete, or outdated. Exist- use specialized tools correctly, and handle recurring ing skill-evolution methods often address these edge cases. Adapting agents to various domains deficiencies through heuristic reflections with- through fine-tuning (Liu et al., 2024; Chang et al., out an explicit optimization formulation. In 2026a), retrieval pipelines (Zhao et al., 2025), or this paper, we propose SkillGrad, a gradient- repeated web searches (Shao et al., 2024) can be descent-inspired framework for optimizing costly or cumbersome, especially when the needed agent skills. SkillGrad treats the skill package knowledge is procedural rather than purely factual. as a structured parameter to optimize in a gra- dient descent fashion: task executions provide To bridge this gap, Agent Skills offer a lightweight trajectory-level loss evidence, automatic diag- alternative. They are persistent file packages that noses then provide text-based gradients that an agent can load progressively when solving tasks. indicate the correction directions. To stabilize Unlike a flat prompt, a skill is a structured artifact. optimization across iterations, a momentum Its metadata determines when it is activated, its agent

Conclusion/discussion section scan:

> under the fixed update budget. Larger batches pro- vide more evidence per update, but they also re- We present SkillGrad, an optimization-inspired quire one textual patch to compress a wider set framework for agent skill improvement. Skill- of diagnoses into a single skill edit. In this set- Grad casts a structured skill package as the op- ting, batch size 4 gives the best observed balance timizable artifact and maps execution evidence, di- between evidence per update and update frequency. agnosis, momentum, and layer-aware patching to Iteration budget. Figure 2(b) evaluates check- the main stages of an optimization loop. Across points from the same training trajectory. Accuracy SpreadsheetBench Verified and WikiTableQues- rises from 63.3% at iteration 1 to 65.8% at iter- tions, SkillGrad improves skills initialized from ation 4, 67.5% at iteration 7, and 72.5% at the both LLM-generated and third-party sources. Em- default iteration 10. Continuing training for three pirical results suggest a practical path for improv- additional iterations gives 70.0% at iteration 13. ing agent skills through structured optimization. 8 Limitations Proceedings of the 62nd Annual Meeting of the As- sociation for Computational Linguistics (Volume 1: SkillGrad is evaluated primarily on spreadsheet- Long Papers), pages 6864–6890. centered tasks, with WikiTableQuestions used as Yifan Lan, Yuanpu Cao,

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
