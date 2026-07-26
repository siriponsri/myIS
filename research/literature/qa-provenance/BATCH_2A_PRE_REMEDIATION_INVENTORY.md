# Batch 2A Pre-Remediation Inventory

**Purpose:** Freeze the actual filesystem state for U021-U040 as observed at the start of the Batch 2A remediation pass, before any cache-repair action (Task 2) was taken. Captured from live filesystem checks (`ls -la`, `grep`, digest frontmatter reads) performed in this session prior to any write.

**Captured:** 2026-07-25, start of remediation session.

---

## Filesystem snapshot at session start

`extraction-cache/` directory listing before remediation contained exactly 23 files: `U001.md` through `U023.md`. **No file `U024.md` through `U040.md` existed.**

## Per-paper inventory (U021-U040)

| ID | Canonical PDF path (relative to canonical repo) | Expected SHA-256 (manifest) | Persistent cache exists (pre-remediation) | Cache metadata value (digest/index/checkpoint/CSV) | Digest exists | digest frontmatter present |
|----|---|---|---|---|---|---|
| U021 | research/ref-paper/is1/pdfs/21_patcid_chemical_structure_database_from_patent_2024.pdf | 4e90f27e...48ddbe5a7 | ✅ yes — `extraction-cache/U021.md` (62,194 B pre-existing, 11 page markers) | `extraction_cache: source-packet/03-priority-papers/extraction-cache/U021.md` | ✅ yes | ✅ yes (full schema) |
| U022 | .../22_enhancing_patent_retrieval_using_automated_patent_2022.pdf | c309ccb3...1defad8adb2ddb | ✅ yes — `extraction-cache/U022.md` (44,579 B pre-existing, 12 page markers) | `extraction_cache: source-packet/03-priority-papers/extraction-cache/U022.md` | ✅ yes | ✅ yes |
| U023 | .../23_llm_powered_real_time_patent_citation_2026.pdf | 16fb7f9b...86eb933d768 | ✅ yes — `extraction-cache/U023.md` (72,757 B pre-existing, 40 page markers) | `extraction_cache: source-packet/03-priority-papers/extraction-cache/U023.md` | ✅ yes | ✅ yes |
| U024 | .../24_evopat_multi_llm_based_patent_summarization_2024.pdf | 2594f2d8...91b556c736 | ❌ **missing** | `tool-results/toolu_ic57lpKiZt84i68vHpnSUG.json` (temporary tool-result, not persistent) | ✅ yes | ✅ yes |
| U025 | .../25_deep_learning_for_patent_landscaping_using_2022.pdf | 77887357...7db09b241e7ad540 | ❌ **missing** | `tool-results/toolu_UphhE53I7cbFzJfBMdyncs.json` (temporary tool-result) | ✅ yes | ✅ yes |
| U026 | .../26_biocpt_contrastive_pre_trained_transformers_for_2023.pdf | 36375d53...ed8b662b02f | ❌ **missing** | `tool-results/toolu_FutqxPu4aXKHpL0z7FeF5v.json` (temporary tool-result) | ✅ yes | ❌ **no YAML frontmatter at all** — SHA field in body literally reads `[To be computed from cache file]`; schema-non-compliant |
| U027 | .../27_graph_transformer_for_efficient_patent_search_2025.pdf | 5924910b...f694e086863ef893e | ❌ **missing** | frontmatter literally `extraction_cache: "tool-results/[to_be_filled]"` (unresolved placeholder, never filled in) | ✅ yes | ✅ yes but value is a placeholder |
| U028 | .../28_contrastive_learning_enhanced_retrieval_augmented_few_2026.pdf | db1eb590...25fd267a138d | ❌ **missing** | `tool-results/mcp-markdownify-pdf-to-markdown-1784933543013.txt` (temporary Markdownify output) | ✅ yes | ✅ yes |
| U029 | .../29_clef_ip_2011_retrieval_in_the_2011.pdf | c2e600a8...66e17f50d74b662 | ❌ **missing** | `"[extraction_output, inline, ~13 pages]"` (inline extraction, no file) | ✅ yes | ✅ yes |
| U030 | .../30_clef_ip_2012_retrieval_experiments_in_2012.pdf | 43f35981...8876f5d6550e5d0c07 | ❌ **missing** | `"inline extraction, ~12 pages"` | ✅ yes | ✅ yes |
| U031 | .../31_report_on_clef_ip_2011_exploring_2011.pdf | 801f9f44...a42ac81f0abb25394a | ❌ **missing** | `"inline extraction, ~10 pages"` | ✅ yes | ✅ yes |
| U032 | .../32_a_comparative_analysis_of_embedding_models_2024.pdf | 83e960fe...a886170654d602915f | ❌ **missing** | `"inline extraction, ~8 pages"` | ✅ yes | ✅ yes |
| U033 | .../33_a_survey_on_automated_and_ai_2026.pdf | ee11448b...15164e5e40e3d620aead | ❌ **missing** | `"inline extraction (~26 pages, ~7,388 lines...)"` | ✅ yes | ✅ yes |
| U034 | .../34_a_survey_on_patent_analysis_from_2024.pdf | 94b2ef78...68723f9841f1676f17 | ❌ **missing** | `"inline extraction (~1235 lines...)"` | ✅ yes | ✅ yes |
| U035 | .../36_beir_heterogeneous_benchmark_for_zero_shot_2021.pdf | 682da185...812d1f522756c1bc | ❌ **missing** | `"inline extraction, ~10 pages..."` | ✅ yes | ✅ yes |
| U036 | .../37_patexpert_ai_orchestrated_multi_agent_patent_2024.pdf | 6840dc1e...a713d93c94ee2b48bf2 | ❌ **missing** | `"inline extraction, ~16 pages..."` | ✅ yes | ✅ yes |
| U037 | .../38_colbertv2_effective_and_efficient_retrieval_via_2022.pdf | 62d6558f...74d048804e17a6de93 | ❌ **missing** | `"inline extraction, ~1788 lines..."` | ✅ yes | ✅ yes |
| U038 | .../39_h_protorag_hierarchical_prototype_based_retrieval_2026.pdf | ab0a4341...5da20bb10edb434f2 | ❌ **missing** | `"inline extraction, ~1366 lines..."` | ✅ yes | ✅ yes |
| U039 | .../40_full_recall_semantic_search_based_ranking_2025.pdf | 1a744181...9726e2dc263ef60b8c7 | ❌ **missing** | `"inline extraction, ~1612 lines..."` | ✅ yes | ✅ yes |
| U040 | .../41_mining_patents_with_llms_chemical_function_2024.pdf | df93f5d3...f840e4d54b20796 | ❌ **missing** | `"inline extraction, full paper..."` | ✅ yes | ✅ yes |

---

## Summary counts (pre-remediation)

- **IDs with valid persistent cache:** 3 — U021, U022, U023
- **IDs with missing cache:** 17 — U024, U025, U026, U027, U028, U029, U030, U031, U032, U033, U034, U035, U036, U037, U038, U039, U040
- **IDs with cache existing but invalid/mismatched:** 0 (none of the 3 existing caches were mismatched — SHA/page-marker checks passed on all 3)
- **IDs whose metadata points to tool-results (temp JSON/TXT):** U024, U025, U026, U027 (placeholder), U028
- **IDs whose metadata points to "inline extraction" (no file at all):** U029, U030, U031, U032, U033, U034, U035, U036, U037, U038, U039, U040
- **Digest files present for all 20 IDs:** yes, confirmed via directory listing
- **Digest schema/frontmatter anomaly found:** U026 digest has **no YAML frontmatter block at all** (starts directly with an `## Paper Metadata` H1, not a `---` YAML block); its embedded SHA field literally reads `[To be computed from cache file]` — never resolved. This is a distinct defect from the missing-cache issue and is addressed in Task 4/9.
- **U027 frontmatter placeholder anomaly:** `extraction_cache: "tool-results/[to_be_filled]"` — a literal unresolved template placeholder, confirming the extraction step was never actually completed to a tool-result file either.

**Correct pre-remediation status, consistent with the owner's stated problem:** content digestion completed (20/20 digest files exist and are schema-plausible except U026's frontmatter); persistent artifact protocol incomplete (only 3/20 caches persistent); overall **PARTIAL-PASS, remediation required.**
