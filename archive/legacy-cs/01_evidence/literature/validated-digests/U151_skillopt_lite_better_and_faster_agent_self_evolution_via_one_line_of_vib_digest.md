---
paper_id: U151
title: "SkillOpt-Lite: Better and Faster Agent Self-Evolution via One Line of Vibe"
pdf_sha256: "4e7d36b233673a3793b95e7834e588acf19bcea3b292c7168781a95df792797d"
object_path: "01_evidence/A-tier/U151_skillopt_lite_better_and_faster_agent_self_evolution_via_one_line_of_vib.pdf"
legacy_primary_alias: "research/ref-paper/is1/pdfs/85_skillopt_lite_better_and_faster_agent.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: "2607.03451"
arxiv_source: "pdf_front_matter"
arxiv_confidence: "medium"
page_count: 16
record_type: "paper"
tier: "A"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U151: SkillOpt-Lite: Better and Faster Agent Self-Evolution via One Line of Vibe

## Bibliographic Identity

- Verified title source: `pdfinfo`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: 2607.03451 (source: pdf_front_matter; confidence: medium)
- Pages: 16
- Source collection: `is1`
- Legacy primary alias: `research/ref-paper/is1/pdfs/85_skillopt_lite_better_and_faster_agent.pdf`
- Identity result: `verified` (filename/title token overlap 1.00)

## Classification

**Tier A.** Direct HarnessOpt/skill/prompt optimization method evidence. Relevant surface: H/S.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, benchmark, contrastive, prompt optimization, skill optimization, agent.

Abstract/summary section scan:

> July, 2026 SkillOpt-Lite: Better and Faster Agent Self-evolution via One Line of Vibe Yifei Shen1 Bo Li1,2 Xinjie Zhang3 1 LMMs-Lab 2 NTU MMLab 3 Microsoft While skill optimization for autonomous agents has gained traction, existing methods rely on arXiv:2607.03451v1 [cs.SE] 3 Jul 2026 complex pipelines. This leaves a fundamental question unaddressed: What constitutes a minimal viable pipeline for skill optimization, where every component is justified by theory or empirical necessity? We formalize skill optimization via Zeroth-Order (ZO) optimization, mapping classical counterparts (central difference, trust regions) to recent literature. Noting that unlike blind nu- merical perturbations in classical ZO, skill trajectories serve as interpretable debugging feedback. Grounded in Claude Code philosophy and PAC learning, we establish three principles for conver- gence and generalization: file-system-based trajectory exploration, consensus attribute mining, and independent validation gating. Eliminating redundancies, we propose SkillOpt-Lite. It accelerates convergence and outperforms full SkillOpt: improving LiveMath by +8.8 points on GPT-5.5 and +25.4 points on GPT-5.4-nano, allowing

Conclusion/discussion section scan:

> In this report, we formalize agentic skill training through the lens of zeroth-order optimization and statistical learning theory. We show that complex multi-agent pooling and text update- damping mechanisms are largely redundant as base models scale. Guided by “everything is file” philosophy, we propose SkillOpt-Lite, a minimal viable pipeline that treats rollout trajectories as independent flat files and leverages autonomous coding agents for targeted, semantic-driven debugging. Empirically, SkillOpt-Lite accelerates optimization convergence and consistently matches or outperforms heavily engineered baselines across multiple benchmarks. Finally, we encapsulate this workflow into a native IDE extension, demonstrating that file-centric skill editing can naturally generalize to full harness optimization HarnessOpt. 6.2 Future Work To move toward fully autonomous agent self-evolution, we outline four practical directions for future research: • Skill Optimization for Frontier Model Distillation: While distilling proprietary frontier models into open-weight equivalents is a standard industrial practice, active anti-distillation defenses and sub-optimal generation boundaries often hinder data quality. Utilizing skill optimization to refine teacher agents across granular capabilities provides a structured framework for generating high-quality distillation corpora. However, because th

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
