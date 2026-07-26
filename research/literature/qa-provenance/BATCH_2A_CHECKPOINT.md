# Batch 2A Checkpoint

**Authorized range:** U021–U040  
**Session started:** 2026-07-24  
**Schema:** PDF_DIGEST_SCHEMA_V1.md (frozen)  
**Stop condition triggered:** no — batch completed normally at U040 (20/20). Hard stop boundary at U041 (unauthorized) respected; U041 not started.  

---

## Current state

| Field | Value |
|---|---|
| Last completed ID | U040 |
| Exact next ID | U041 (NOT AUTHORIZED — batch complete, do not start) |
| Completed count | 20 / 20 |
| Failed or held IDs | none |

---

## Artifact tracking

**Historical Remediation Note (2026-07-25):** The cache-path column below originally recorded transient references (tool-results/*.json temp files, "inline extraction" with no persistent file) for 17 of 20 papers (U024-U040). Only U021-U023 had real persistent files in `extraction-cache/`. A remediation pass regenerated all 17 missing persistent caches via `_extract_cache.py`, verified each against the manifest SHA-256, and normalized every `extraction_cache:` reference (in digests, this checkpoint, the index, and the CSV) to point exclusively at `extraction-cache/U0XX.md`. See `BATCH_2A_REMEDIATION_REPORT.md` for full detail. The table below reflects current, post-remediation state — persistent files, not the original transient references.

| ID | Cache path | Digest path | Index updated | EB lookup | Status |
|----|-----------|-------------|---------------|-----------|--------|
| U021 | extraction-cache/U021.md | digests/U021_patcid_chemical_structure_database_digest.md | ✅ | no/ingest_new | ✅ completed |
| U022 | extraction-cache/U022.md | digests/U022_patent_retrieval_summarization_digest.md | ✅ | no/ingest_new | ✅ completed |
| U023 | extraction-cache/U023.md | digests/U023_llm_patent_citation_recommendation_digest.md | ✅ | no/ingest_new | ✅ completed |
| U024 | extraction-cache/U024.md | digests/U024_evopat_multi_llm_patent_summarization_digest.md | ✅ | no/ingest_new | ✅ completed |
| U025 | extraction-cache/U025.md | digests/U025_patent_landscaping_transformer_graph_digest.md | ✅ | no/ingest_new | ✅ completed |
| U026 | extraction-cache/U026.md | digests/U026_medcpt_biomedical_ir_pubmed_logs_digest.md | ✅ | no/ingest_new | ✅ completed |
| U027 | extraction-cache/U027.md | digests/U027_graph_transformer_patent_search_digest.md | ✅ | no/ingest_new | ✅ completed |
| U028 | extraction-cache/U028.md | digests/U028_contrastive_rag_fewshot_patent_classification_digest.md | ✅ | no/ingest_new | ✅ completed |
| U029 | extraction-cache/U029.md | digests/U029_clef_ip_2011_retrieval_digest.md | ✅ | no/ingest_new | ✅ completed |
| U030 | extraction-cache/U030.md | digests/U030_clef_ip_2012_retrieval_digest.md | ✅ | no/ingest_new | ✅ completed |
| U031 | extraction-cache/U031.md | digests/U031_clef_ip_2011_pattextiling_digest.md | ✅ | no/ingest_new | ✅ completed |
| U032 | extraction-cache/U032.md | digests/U032_embedding_models_patent_similarity_digest.md | ✅ | no/ingest_new | ✅ completed |
| U033 | extraction-cache/U033.md | digests/U033_survey_automated_ai_patent_retrieval_digest.md | ✅ | no/ingest_new | ✅ completed |
| U034 | extraction-cache/U034.md | digests/U034_survey_patent_analysis_nlp_multimodal_digest.md | ✅ | no/ingest_new | ✅ completed |
| U035 | extraction-cache/U035.md | digests/U035_beir_heterogeneous_benchmark_digest.md | ✅ | no/ingest_new | ✅ completed |
| U036 | extraction-cache/U036.md | digests/U036_patexpert_multiagent_patent_digest.md | ✅ | no/ingest_new | ✅ completed |
| U037 | extraction-cache/U037.md | digests/U037_colbertv2_late_interaction_digest.md | ✅ | no/ingest_new | ✅ completed |
| U038 | extraction-cache/U038.md | digests/U038_h_protorag_hierarchical_prototype_digest.md | ✅ | no/ingest_new | ✅ completed |
| U039 | extraction-cache/U039.md | digests/U039_fullrecall_semantic_search_ranking_digest.md | ✅ | no/ingest_new | ✅ completed |
| U040 | extraction-cache/U040.md | digests/U040_mining_patents_llms_chemical_function_digest.md | ✅ | no/ingest_new | ✅ completed |

---

## Manifest resolution (U021–U040)

All 20 IDs confirmed canonical, no duplicate-of rows within range.

| ID | SHA256 | Canonical path | Size |
|----|--------|----------------|------|
| U021 | 4e90f27e6d8b72449c3a96b219ddf5efd743db5f0879c25907f379648ddbe5a7 | research/ref-paper/is1/pdfs/21_patcid_chemical_structure_database_from_patent_2024.pdf | 1505975 |
| U022 | c309ccb34e8c36b529c40b702a622900ef2042f1a6e092e33b1defad8adb2ddb | research/ref-paper/is1/pdfs/22_enhancing_patent_retrieval_using_automated_patent_2022.pdf | 1994369 |
| U023 | 16fb7f9b2d7b8601931847b3d7683c4e4ab9f354d563014586e99b9eb933d768 | research/ref-paper/is1/pdfs/23_llm_powered_real_time_patent_citation_2026.pdf | 3717890 |
| U024 | 2594f2d877a4b65e08c6e2eb10612094ecff83a51a63696bc50a7e91b556c736 | research/ref-paper/is1/pdfs/24_evopat_multi_llm_based_patent_summarization_2024.pdf | 1227477 |
| U025 | 7788735721a8d0516cbbfc46d59d5236e484e57e001511497db09b241e7ad540 | research/ref-paper/is1/pdfs/25_deep_learning_for_patent_landscaping_using_2022.pdf | 1310097 |
| U026 | 36375d5310c4ebee73a73453aba880a5babdedfe7ec2ca40c83ffed8f662b02f | research/ref-paper/is1/pdfs/26_biocpt_contrastive_pre_trained_transformers_for_2023.pdf | 990380 |
| U027 | 5924910b08d56a638904285d6ec44a2f2490c0704ed57bfd694e086863ef893e | research/ref-paper/is1/pdfs/27_graph_transformer_for_efficient_patent_search_2025.pdf | 814033 |
| U028 | db1eb5909cf96c601252d732e7b95bd57556c48e1f0c0288cf25a4fd267a138d | research/ref-paper/is1/pdfs/28_contrastive_learning_enhanced_retrieval_augmented_few_2026.pdf | 5172601 |
| U029 | c2e600a8d73153f81716fceabe391739444a32cc156379dbe66e17f50d74b662 | research/ref-paper/is1/pdfs/29_clef_ip_2011_retrieval_in_the_2011.pdf | 254838 |
| U030 | 43f35981d827f6c1118c11fc8f4aa97f964e40c8df223b8876f5d6550e5d0c07 | research/ref-paper/is1/pdfs/30_clef_ip_2012_retrieval_experiments_in_2012.pdf | 1112195 |
| U031 | 801f9f44e5e6a3f97f63a9dc2e7f74650250ee68ca6a51a42ac81f0abb25394a | research/ref-paper/is1/pdfs/31_report_on_clef_ip_2011_exploring_2011.pdf | 248923 |
| U032 | 83e960fef77fcdbff639a21a425095f0f99b6620b48fa7a886170654d602915f | research/ref-paper/is1/pdfs/32_a_comparative_analysis_of_embedding_models_2024.pdf | 156335 |
| U033 | ee11448b455dc4fdac09e95d6f476472ef8ad067318715164e5e40e3d620aead | research/ref-paper/is1/pdfs/33_a_survey_on_automated_and_ai_2026.pdf | 2987221 |
| U034 | 94b2ef789464ff2c35599f0cc8399d4710dc8697317fc068723f9841f1676f17 | research/ref-paper/is1/pdfs/34_a_survey_on_patent_analysis_from_2024.pdf | 1023191 |
| U035 | 682da185b92b4d04f906de2a59f4b5152c1a1f15433cc7da812d1f522756c1bc | research/ref-paper/is1/pdfs/36_beir_heterogeneous_benchmark_for_zero_shot_2021.pdf | 1214175 |
| U036 | 6840dc1ed45a2865c72748a1779ecc427178acc4ff1a7a713d93c94ee2b48bf2 | research/ref-paper/is1/pdfs/37_patexpert_ai_orchestrated_multi_agent_patent_2024.pdf | 746290 |
| U037 | 62d6558f515ef6a62dfb3047f8d79262613c7f13503cdf74d048804e17a6de93 | research/ref-paper/is1/pdfs/38_colbertv2_effective_and_efficient_retrieval_via_2022.pdf | 916038 |
| U038 | ab0a43419308ca9b3b4400888c56daaa81b3c5b9e459af35da20bb10edb434f2 | research/ref-paper/is1/pdfs/39_h_protorag_hierarchical_prototype_based_retrieval_2026.pdf | 2757044 |
| U039 | 1a7441812abe43487ecc4b5995dc998c4d97aa3ed39ea9726e2dc263ef60b8c7 | research/ref-paper/is1/pdfs/40_full_recall_semantic_search_based_ranking_2025.pdf | 2282222 |
| U040 | df93f5d3e50e9c77a91cca80d62dc5e7c3c5488b9756d9441f840e4d54b20796 | research/ref-paper/is1/pdfs/41_mining_patents_with_llms_chemical_function_2024.pdf | 1184030 |

---

## Five-paper consistency checks

*(appended after each group)*

### U021-U025 Consistency Check (2026-07-24)

**Tier distribution:**
- Tier A: 0
- Tier B: 2 (U022, U023)
- Tier C: 3 (U021, U024, U025)

**EB match distribution:**
- No match (ingest_new): 5/5 (100%)
- Existing match: 0/5

**Schema compliance:**
- All 5 digests include complete YAML frontmatter with required fields
- All 5 digests include required sections: Bibliographic Identity, Research Problem, Method, Dataset/Evaluation Protocol, Main Findings, Limitations, Track C/R/S Relevance, Relationship to Papers A-D, EB Cross-Check, Verification Warnings
- All 5 digests end with Tier classification rationale paragraph

**Tier B rationale consistency (U022, U023):**
- U022: Retrieval metrics (CLEF-IP MAP@100 35.40%, USPTO MAP@50 23.95%) but narrower scope (query formulation via summarization, single retrieval method, no family-level, no domain splits) → Tier B
- U023: Retrieval metrics (MRR 0.1782, Rec@200 44.43%) on large-scale corpus (428k CNIPA financial patents) with incremental updating, but single-domain (G06Q financial only), Chinese-language only, citation-based relevance (not family-level), no cross-domain splits → Tier B
- Both have quantitative retrieval metrics but lack Tier A characteristics (family-level aggregation, domain-split IN/OUT evaluation, multi-method comparison)

**Tier C rationale consistency (U021, U024, U025):**
- U021: Image-based chemical structure retrieval (80.7M patent images → 13.8M SMILES), molecule retrieval 56.0% D2C-RND, but NOT text-based prior-art retrieval → Tier C (domain-adjacent, image retrieval)
- U024: Multi-agent patent analysis/summarization system (ROUGE-1 0.2164 vs GPT-4o 0.0745), human eval (Informative 4.82, Rich 4.85), but NOT retrieval/ranking system (no MAP/Recall@k/NDCG, no candidate generation, no family-level) → Tier C (domain-adjacent, summarization automation)
- U025: Binary classification for R&D patent landscaping (TRF+DIFF AP 0.7038 vs APL 0.3061), 4 KISTA benchmark datasets, but NOT retrieval system (binary target/non-target classification, no ranking, no family-level, domain-specific training per project) → Tier C (domain-adjacent, project-specific target identification)
- All three address patent understanding/processing but not core prior-art retrieval/reranking tasks

**Track C/R/S relevance assessment consistency:**
- All 5 digests correctly identify minimal/no Track R relevance (none are reranking systems)
- All 5 digests correctly identify no Track S relevance (no prompt evolution, no SkillOpt)
- Track C relevance assessment varies appropriately:
  - U021: Minimal (image-based, not text retrieval)
  - U022: Moderate (query formulation method applicable to Track C query-side candidate generation)
  - U023: Moderate (LLM-embedding + incremental HNSW candidate generation method)
  - U024: Minimal (post-retrieval analysis automation, not candidate generation)
  - U025: Minimal (multi-modal fusion insights, but addresses different task: project-specific classification)

**Papers A-D relationship assessment consistency:**
- All 5 digests correctly state "No connection to Paper A/D reranking focus"
- All 5 digests correctly avoid cross-comparing metrics (e.g., U023 MRR 0.1782 ≠ DAPFAM OUT Recall@100, U025 AP 0.7038 ≠ DAPFAM family-level metrics)
- All 5 digests correctly identify different tasks, metrics, evaluation protocols vs Papers A/D

**EB cross-check consistency:**
- All 5 digests performed EB query with appropriate keywords
- All 5 digests correctly interpreted "no match" results (returned IS1 project knowledge or other papers, not the target paper)
- All 5 digests correctly recommended `ingest_new` action

**Verification warnings consistency:**
- All 5 digests report table extraction status (preserved grid structure or prose-quoted figures)
- All 5 digests confirm headline figures match prose (no discrepancies flagged)
- No visual-check cautions needed for any of the 5 digests

**Quality observations:**
- All 5 digests provide detailed method descriptions with specific algorithmic steps
- All 5 digests report complete quantitative results with specific metrics and baselines
- All 5 digests correctly distinguish between what papers claim vs what they demonstrate
- All 5 digests correctly apply IS1 governance boundaries (Track C/R/S proposed/unauthorized, Papers A-D frozen evidence, no cross-task metric comparisons)

**Issues identified:** None

**Recommendation:** Proceed to U026. Schema compliance is consistent, tier classification rationale is appropriately differentiated (Tier B: retrieval metrics but narrower scope; Tier C: domain-adjacent non-retrieval tasks), and governance boundaries are correctly applied across all 5 digests.

---

### U026-U030 Consistency Check (2026-07-25)

**Unique IDs / source hashes / canonical paths:** All 5 (U026 36375d53, U027 5924910b, U028 db1eb590, U029 c2e600a8, U030 43f35981) verified against manifest; U030 SHA independently recomputed via sha256sum and matched exactly. No duplicate-of rows in range.

**Tier distribution:**
- Tier A: 0
- Tier B: 4 (U026, U027, U029, U030)
- Tier C: 1 (U028)

**EB match distribution:** No match (ingest_new): 5/5 (100%). Existing match: 0/5.

**Schema compliance:** All 5 digests carry YAML frontmatter with required fields (unique_id/paper_id, sha256, tier, eb_status, etc.); all include Bibliographic Identity, Research Problem/Method, Findings, Limitations, Track C/R/S Relevance, Relationship to Papers A-D, Verification Warnings, EB Cross-Check. U029/U030 (lab-overview reports) compress Track sections per §4 tier-length guidance — consistent with schema.

**Tier B rationale consistency (U026, U027, U029, U030):**
- U026: Biomedical (PubMed) retriever+reranker, NDCG@10 0.510 avg, SOTA on 3/5 BEIR biomedical tasks — real retrieval metrics, adjacent domain (not patent) → Tier B
- U027: Patent Graph Transformer, Recall@3 0.4046 on proprietary 161k-doc test set — real patent retrieval metric, but proprietary/non-reproducible construction, no domain-split → Tier B
- U029: CLEF-IP 2011 lab overview — real PAC retrieval task/metrics but non-extractable headline numbers (bar-chart only), multi-team survey not single method → Tier B
- U030: CLEF-IP 2012 lab overview, sequel to U029 — real Passage-Retrieval-from-Claims task defined, but headline metrics explicitly "not available at time of writing"; only the non-retrieval chemical-structure recognition sub-task has clean numbers → Tier B
- Consistent pattern: all 4 have a genuine retrieval task/metric definition but each has a distinct limiting factor (domain-adjacency, proprietary data, non-extractable figures, or unpublished results)

**Tier C rationale consistency (U028):**
- U028: Multi-label patent classification (Macro-F1 0.847), retrieval used only internally for few-shot demonstration selection, not as the end task → Tier C (domain-adjacent, classification not retrieval)

**Track C/R/S relevance assessment consistency:**
- All 5 digests correctly label Track sections "proposed, NOT AUTHORIZED" (C/R) — no exceptions
- Track R relevance uniformly LOW/NOT RELEVANT (none are dedicated rerankers over a fixed candidate list)
- Track S uniformly NOT RELEVANT across all 5
- Track C relevance appropriately varies: U026 minimal (biomedical, transferable architecture only), U027 moderate (graph-transformer candidate generation), U028 low (classification not retrieval), U029/U030 low-moderate (dataset/relevance-construction lineage feeding U014/U015)

**Papers A-D relationship consistency:** All 5 digests correctly state no direct connection to Papers A-D; no cross-task metric comparisons made (e.g., U026 BEIR NDCG@10 ≠ DAPFAM metrics, U027 proprietary Recall@3 ≠ DAPFAM Recall@100, U029/U030 CLEF-IP bar-chart/unavailable figures never compared to any paper's headline numbers).

**EB cross-check consistency:** All 5 performed narrow EB queries (SHA/title/DOI-scoped); all returned NO_MATCH (only unrelated IS1 synthesis/DAPFAM/PatenTEB records surfaced); all correctly recommended `ingest_new`.

**Verification warnings consistency:**
- U026/U027/U028: no blocking visual-check flags; tables read cleanly
- U029: non-blocking — bar-chart axis labels OCR-garbled, but only Table 2 (IMG-CLS) needed for headline claims and it was clean
- U030: non-blocking — passage-retrieval/flowchart results simply absent from source text (not an extraction-damage issue); chemical-structure Tables 2-3 read cleanly
- No paper in this group required blocking on a headline claim

**Quality observations:**
- All 5 digests correctly distinguish real retrieval metrics (U026, U027) from lab-overview benchmark definitions with unavailable/non-extractable metrics (U029, U030) from pure classification (U028)
- CLEF-IP 2011→2012 lineage (U029→U030) correctly identified and cross-referenced without conflating their distinct task sets
- All digests correctly apply the "no cross-comparing incompatible metrics" rule (§15) and the legal/FTO boundary (§10)

**Issues identified:** None. Path-confusion incident from this session (4 digest files briefly written to a non-canonical `My Project\thaipha-lex` location) was caught and reconciled before this checkpoint; canonical index/checkpoint state is verified consistent.

**Recommendation:** Proceed to U031. Schema compliance, tier rationale, and governance boundaries remain consistent across the batch; no stop condition triggered.

---

### U031-U035 Consistency Check (2026-07-25)

**Unique IDs / source hashes / canonical paths:** All 5 (U031 801f9f44, U032 83e960fe, U033 ee11448b, U034 94b2ef78, U035 682da185) verified against manifest; U032/U033/U034/U035 SHAs independently recomputed via sha256sum and matched exactly (U031 verified in prior segment). No duplicate-of rows in range.

**Tier distribution:**
- Tier A: 3 (U033, U034, U035)
- Tier B: 2 (U031, U032)
- Tier C: 0

**EB match distribution:** No match (ingest_new): 5/5 (100%). Existing match: 0/5.

**Schema compliance:** All 5 digests carry YAML frontmatter with required fields; all include Bibliographic Identity, Research Problem/Method, Findings, Limitations, Track C/R/S Relevance, Relationship to Papers A-D, Verification Warnings, EB Cross-Check. Tier A digests (U033/U034/U035) appropriately fuller (survey/benchmark scope); Tier B digests (U031/U032) appropriately compressed per §4.

**Tier A rationale consistency (U033, U034, U035):**
- U033: Comprehensive 2026 life-sciences-focused patent-retrieval survey, new taxonomy, formal metric definitions (incl. PRES), independently cross-references U021/PatCID figures → Tier A as connective/taxonomic infrastructure
- U034: Comprehensive 2024 patent-analysis survey (4-task taxonomy), independently cross-references U018 (Siddharth et al.) → Tier A as connective/taxonomic infrastructure
- U035 (BEIR): Canonical general-domain zero-shot IR benchmark, rigorous fully-extractable metrics, biomedical subset overlaps U026/MedCPT's eval tasks → Tier A as core retrieval-methodology reference
- All three placed Tier A not for patent-domain retrieval metrics directly, but for breadth/recency/taxonomic or methodological infrastructure value — consistent rationale applied across all three, distinct from the narrower Tier A criterion (quantitative patent retrieval metric) used for papers like U011/U012

**Tier B rationale consistency (U031, U032):**
- U031: CLEF-IP 2011 PAC-task participant report, real extractable MAP/NDCG/Recall metrics (best MAP 0.0896) but single-institution ablation, low absolute performance, no domain-split → Tier B
- U032: Patent-similarity embedding comparison, real quantitative results (% max/min-similarity correctness) but small eval set (133 pairs), not Recall@k/MAP-style retrieval metric → Tier B
- Consistent with established Tier B pattern (retrieval-adjacent quantitative findings, narrower scope than Tier A peers)

**Track C/R/S relevance assessment consistency:**
- All 5 digests correctly label Track sections "proposed, NOT AUTHORIZED" (C/R) or "NOT RELEVANT" (S) — no exceptions
- Track C relevance appropriately varies: U031 MODERATE (query-modeling/retrievability-bias), U032 MODERATE (embedding-model selection insight), U033 HIGH (retrieval-method taxonomy+pitfalls), U034 HIGH (retrieval taxonomy+multimodal fusion finding), U035 HIGH (OOD-generalization+annotation-bias methodology)
- Track R relevance appropriately varies: U031/U032/U033/U034 LOW-to-NOT-RELEVANT (no dedicated reranking focus), U035 MODERATE (cross-encoder re-ranking shown as best-generalizing architecture)
- Track S uniformly NOT RELEVANT across all 5

**Papers A-D relationship consistency:** All 5 digests correctly state no direct connection to Papers A-D; no cross-task metric comparisons made (U031's PAC MAP/Recall, U032's %max/min-similarity, U033/U034's secondary-source survey figures, and U035's nDCG@10 general-domain results are all explicitly flagged as non-comparable to DAPFAM/Papers A-D family-level metrics per schema §15).

**EB cross-check consistency:** All 5 performed narrow EB queries (SHA/title/DOI/arXiv-ID-scoped); all returned NO_MATCH (only unrelated IS1 literature-matrix/DAPFAM/PatenTEB/benchmarking-patent-embeddings records surfaced); all correctly recommended `ingest_new`.

**Verification warnings consistency:**
- U031/U032/U035: no blocking visual-check flags; all headline tables read cleanly with no OCR/grid-damage
- U033: non-blocking — appendix quantitative tables (1-3) confirmed present via targeted reads but not individually transcribed (large-cache §3 targeted-read policy applied); no headline claim depends on untranscribed cells
- U034: non-blocking — appendix quantitative tables (6-11) confirmed present via in-text citation but not independently re-transcribed; headline numeric claims sourced from main-body text, not appendix
- No paper in this group required blocking on a headline claim

**Quality observations:**
- U033 and U034 (both broad surveys) correctly cross-reference already-digested papers in this batch (U021/PatCID and U018/Siddharth-et-al respectively), providing useful independent corroboration of prior digests' figures/characterizations
- U035 (BEIR) provides a transferable evaluation-methodology lesson (annotation-selection-bias/Hole@10 correction) directly applicable to auditing this project's own candidate-exposure measurement protocols
- Large-extraction-cache handling (U033: 7388 lines; U034: 1235 lines) correctly used targeted/full-core-body reads per schema §3 rather than loading entire caches, with explicit Verification Warnings disclosure of what was/was not individually transcribed

**Issues identified:** None.

**Recommendation:** Proceed to U036. Schema compliance, tier rationale, and governance boundaries remain consistent across the batch; no stop condition triggered. 15/20 complete.

---

### U036-U040 Consistency Check (2026-07-25)

**Unique IDs / source hashes / canonical paths:** All 5 (U036 6840dc1e, U037 62d6558f, U038 ab0a4341, U039 1a744181, U040 df93f5d3) verified against manifest; U037/U038/U039/U040 SHAs independently recomputed via sha256sum and matched exactly (U036 verified in prior segment). No duplicate-of rows in range.

**Tier distribution:**
- Tier A: 2 (U037, U038)
- Tier B: 1 (U039)
- Tier C: 2 (U036, U040)

**EB match distribution:** No match (ingest_new): 5/5 (100%). Existing match: 0/5.

**Schema compliance:** All 5 digests carry YAML frontmatter with required fields (paper_id/title/authors/year/venue/affiliation/pdf_sha256/eb_status/tier/extraction_cache/digest_created/schema_version); all include Bibliographic Identity, Classification, Research Problem/Method, Main Findings, Limitations, Track C/R/S Relevance, Relationship to Papers A-D, Verification Warnings, EB Cross-Check, Digest Metadata footer. Tier A digests (U037/U038) appropriately fuller (canonical architecture/multi-task methodology scope); Tier B (U039) and Tier C (U036/U040) appropriately compressed per §4 length guidance.

**Tier A rationale consistency (U037, U038):**
- U037 (ColBERTv2): Canonical late-interaction retrieval architecture, fully extractable metrics across 28 datasets (BEIR/LoTTE/Open-QA), already a cited baseline elsewhere in this batch (U020, U035) → Tier A as core retrieval-architecture infrastructure
- U038 (H-ProtoRAG): Primarily a CPC classification paper, but contains a genuine prior-art retrieval component (CLEF-IP 2010, nDCG@10/P@1/Recall@50 vs BM25 baseline) with rigorous controlled ablations isolating hierarchy-only vs retrieval-only contributions → Tier A for methodological rigor despite retrieval being secondary to classification
- Both placed Tier A for methodological/architectural infrastructure value, consistent with the U033/U034/U035 precedent (Tier A can be earned via rigor/breadth, not only via a primary patent-retrieval task)

**Tier B rationale consistency (U039):**
- U039 (FullRecall): Real recall metric (100% claimed) vs 2 named baselines using examiner-citation ground truth, but only n=5 query patents, no Precision/MAP/NDCG, and an asymmetric baseline-comparison protocol (ReQ-ReC cutoff manually expanded to match FullRecall's retrieved-set size) → Tier B, consistent with other narrow-scope-retrieval-with-caveats papers in this batch (U022, U023, U027)

**Tier C rationale consistency (U036, U040):**
- U036 (PatExpert): Multi-agent patent analysis/summarization system, no retrieval/ranking metrics (MAP/Recall@k/NDCG absent), fine-tuned-vs-zero-shot baseline asymmetry flagged → Tier C (domain-adjacent, summarization automation)
- U040 (Mining Patents w/ LLMs): Chemistry/drug-discovery dataset-construction paper using patents purely as a text-mining source (ChatGPT summarization → CheF dataset), no retrieval task, no candidate generation over a document corpus → Tier C (domain-adjacent, not a retrieval system at all)
- Both correctly distinguished from retrieval/reranking tasks despite patent-adjacent framing

**Track C/R/S relevance assessment consistency:**
- All 5 digests correctly label Track sections "proposed, NOT AUTHORIZED" (C/R) or "NOT RELEVANT" (S) — no exceptions
- Track C relevance appropriately varies: U036 minimal (analysis automation not candidate generation), U037 HIGH (late-interaction architecture directly relevant to candidate-generation design space), U038 HIGH (hybrid dense+sparse fusion generator), U039 MODERATE (IPC-guided key-phrase query formulation), U040 MINIMAL (LLM summarization technique tangential, task unrelated)
- Track R relevance appropriately varies: U036 not relevant, U037 LOW-MODERATE (built-in approximate-then-exact retrieval pattern), U038 MODERATE (cross-encoder reranking + clean ablation-attribution template), U039 LOW (simple similarity rerank, not learned), U040 not relevant
- Track S uniformly NOT RELEVANT or MINIMAL across all 5

**Papers A-D relationship consistency:** All 5 digests correctly state no direct connection to Papers A-D; no cross-task metric comparisons made (U036's fine-tuned-vs-zero-shot summarization scores, U037's general-domain MRR@10/nDCG@10, U038's CPC classification F1 + CLEF-IP 2010 metrics, U039's n=5 binary recall, and U040's chemistry ROC-AUC/PR-AUC are all explicitly flagged as non-comparable to DAPFAM/Papers A-D family-level metrics per schema §15).

**EB cross-check consistency:** All 5 performed narrow EB queries (SHA/title/DOI-scoped); all returned NO_MATCH (only unrelated IS1 literature-matrix/DAPFAM/PatenTEB/plan records surfaced); all correctly recommended `ingest_new`.

**Verification warnings consistency:**
- U036/U037/U038/U039/U040: no blocking visual-check flags; all headline tables/figures read cleanly with no OCR/grid-damage affecting main claims
- U039: non-blocking caution flagged on the baseline-comparison protocol itself (asymmetric cutoff expansion), not an extraction-fidelity issue
- No paper in this group required blocking on a headline claim

**Quality observations:**
- U037 (ColBERTv2) and U035 (BEIR, prior group) cross-reference cleanly — ColBERTv2 is evaluated on several of the same BEIR datasets digested in U035, and both are cited as baselines/methodology in U020 (Batch 1), providing coherent cross-batch corroboration
- U038 correctly distinguishes its secondary retrieval contribution from its primary classification contribution while still meeting Tier A bar via methodological rigor (controlled ablations)
- U039's digest correctly flags a methodological caveat in the source paper's own baseline-comparison design, rather than silently repeating its headline superiority claim at face value
- U040 correctly identifies that "patent" in the title does not imply a patent-retrieval task, avoiding tier misclassification based on surface keyword matching alone

**Issues identified:** None.

**Recommendation:** Batch 2A COMPLETE at U040 (20/20). Schema compliance, tier rationale, and governance boundaries remain consistent across the full batch; no stop condition triggered at any point in U021-U040. Proceed to closing QA artifacts (BATCH_2A_QA_REPORT.md, BATCH_2A_INGESTION_CANDIDATES.csv). U041 NOT started, per hard stop boundary.

---

*Last updated: 2026-07-25 — 20/20 complete (U021-U040), U036-U040 consistency check appended. BATCH 2A COMPLETE.*
