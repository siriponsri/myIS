# myIS SCOPE Inbox Handoff

## 1. Codex entry point

This directory is a staging package, not the repository.

Codex must:

1. read this file;
2. read `INSTRUCTION.md`;
3. locate and inspect the actual myIS Git repository;
4. inventory and hash all inbox files;
5. compare proposed contracts with current repository state;
6. present a concise migration diff;
7. implement reversible, local, no-cost migration work;
8. stop before measured or paid execution unless `D1 START_CAMPAIGN` is approved.

Do not copy the entire inbox over the repository.

## 2. Proposed active contracts

These files are proposed replacements or additions:

```text
README.md
PLAN.md
INSTRUCTION.md
NAMING.md
AGENTS.md
config/project.yaml
docs/ARCHITECTURE.md
docs/PATENT_STRUCTURE.md
docs/OPTIMIZER_DECISION.md
docs/PAPER_STRATEGY.md
docs/ISAI_NLP_2026.md
docs/RULES.md
docs/RUBRIC.md
schemas/scope-dsl.schema.json
schemas/patent-representation.schema.json
schemas/run-manifest.schema.json
schemas/examples/scope-dsl.example.json
schemas/examples/patent-representation.example.json
schemas/examples/run-manifest.example.json
```

Install them only after:

- inspecting existing counterparts;
- preserving user changes and historical evidence;
- recording superseded active documents in the archive index;
- validating links, config, schemas, and repository instructions.

`INBOX_MANIFEST.md` is a delivery note and does not need to become an active repository file.

## 3. Expected research sources

The inbox may also contain these user-provided sources:

| Source | Initial classification |
|---|---|
| `report-patent-databases.md` | Literature/evidence digest |
| `report-paper-c-p1.md` | Paper C evidence |
| `report-paper-a.md` | Paper A evidence |
| `report-paper-b.md` | Paper B evidence |
| `79_is_it_novel_and_why_fine_grained_patent_novelty_prediction.pdf` | Literature source |
| `11_dapfam_domain_aware_family_level_dataset_2025.pdf` | Primary DAPFAM source |
| `71_prompt_optimization_is_a_coin_flip.pdf` | Prompt-search evidence |
| `82_automatic_instruction_prompt_optimization_by_model_itself.pdf` | Prompt-optimization evidence |
| `83_a_benchmark_of_prompts_and_rubrics_for_evaluating_deep_research_agents.pdf` | Auditor/rubric evidence |
| `81_prompt_engineering_evaluation_metrics_for_interpretable_joint.pdf` | Prompt-evaluation evidence |
| `80_benchmarking_patent_embeddings.pdf` | Retrieval baseline evidence |
| `54_gepa_reflective_prompt_evolution_can_outperform_rl_2026.pdf` | Optimization evidence |
| `12_patenteb_a_comprehensive_benchmark_and_model_2025.pdf` | Patent embedding benchmark source |
| `paper-d-plan.md` | Historical or superseded plan until verified |
| `PROMPT_DECISION_REPORT.md` | Decision evidence |
| `MU_F_SPEC.md` | Method/specification evidence |
| `easychair.pdf` | User-captured iSAI-NLP EasyChair submission-form snapshot |
| `isaiNLP2026.pdf` | User-captured official venue-page snapshot |

Locate these recursively by filename; do not assume they are in a particular inbox subdirectory.

Use the public [conference site](https://isai-nlp2026.aiat.or.th/) and [submission page](https://isai-nlp2026.aiat.or.th/submission) as the current venue authority. Preserve the two PDF snapshots as dated evidence and recheck the public pages before submission.

## 4. Source handling

- Read source Markdown and relevant PDF sections before relying on their claims.
- Preserve filename, checksum, title, authors, year, URL/DOI, and role in the evidence catalog.
- Do not commit large PDFs merely because they were delivered in the inbox.
- Store large permissible source files under the external evidence store and commit a citation manifest or digest.
- Preserve Paper A-D identity and frozen claims.
- Treat older plans as historical evidence unless the migration explicitly promotes a section.
- Treat `docs/OPTIMIZER_DECISION.md` as the active AutoIndex/agent/SkillOpt boundary unless newer measured evidence is recorded.
- Treat `docs/ISAI_NLP_2026.md` as the submission-priority and anonymous-review contract.
- Do not ingest qrels or protected result files found in the inbox without checking split role and authorization.
- Do not infer a license from file availability.

## 5. Expected disposition

| Class | Target |
|---|---|
| Proposed active root contract | Repository root after conflict-aware replacement |
| Proposed config/schema | `config/` or `schemas/` after validation |
| Research digest | `evidence/literature/` |
| Source metadata | `evidence/catalog/` |
| Large PDF | External evidence store plus a Git-tracked manifest |
| Historical plan/decision | `archive/` with an index |
| Dataset/qrels/index/model | `MYIS_STORE`, never Git |
| Generated report | `reports/` from canonical run records |

## 6. Handoff success

The inbox handoff is complete when:

- every file has a recorded classification and destination;
- no existing repository evidence was overwritten silently;
- active root contracts are English and internally consistent;
- JSON Schemas and project YAML validate;
- MLflow, dashboard, Obsidian reports, and presentations remain supported;
- only the three documented Owner decisions remain;
- no measured or paid work was started without `D1`.
