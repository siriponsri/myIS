---
unique_id: U022
priority_tier: B
sha256: c309ccb34e8c36b529c40b702a622900ef2042f1a6e092e33b1defad8adb2ddb
canonical_path: research/ref-paper/is1/pdfs/22_enhancing_patent_retrieval_using_automated_patent_2022.pdf
size_bytes: 1994369
title: "Enhancing patent retrieval using automated patent summarization"
authors: "Eleni Kamateri, Renukswamy Chikkamath, Michail Salampasis, Linda Andersson, Markus Endres"
year: 2022
venue: "PatentSemTech 2025 (6th Workshop on Patent Text Mining and Semantic Technologies)"
doi: null
arxiv: null
extraction_cache: extraction-cache/U022.md
experience_brain_match: no
matched_knowledge_id: null
recommended_ingestion_action: ingest_new
digest_status: completed
digest_prepared: 2026-07-24
pass_type: Batch_2A
authority: External Knowledge
---

# U022 — Enhancing Patent Retrieval Using Automated Patent Summarization

## Bibliographic Identity

**Title:** Enhancing patent retrieval using automated patent summarization  
**Authors:** Eleni Kamateri¹, Renukswamy Chikkamath², Michail Salampasis¹, Linda Andersson³, Markus Endres² (¹International Hellenic University, ²Hochschule München, ³Artificial Researcher IT GmbH)  
**Venue:** 6th Workshop on Patent Text Mining and Semantic Technologies (PatentSemTech) 2025  
**DOI:** null (workshop paper)  
**arXiv ID:** null  
**Publication Date:** 2025 (presented at PatentSemTech workshop)  
**Document Type:** Workshop paper — query formulation via summarization for prior-art retrieval  
**Note:** Selected as one of top six finalists at EPO CodeFest 2024 competition  
**Field:** Patent information retrieval, query formulation, document summarization

## Research Problem

Effective query formulation is a core challenge in patent prior-art search. Patent documents are lengthy (description sections often >6,000 words), linguistically complex, and cover multiple interrelated technical topics. Human-authored patent abstracts often fail to summarize inventions effectively due to urgency, regulatory length constraints, limited inventor attention, and intentional vagueness to avoid narrowing legal protection scope. Relying directly on patent abstracts for query generation is therefore ineffective. Patent professionals typically use entire patent sections (abstract, claims, description) or manually selected keywords for query formulation, but these approaches are inefficient — full sections are too long for modern LLM token limits, while keyword extraction requires manual effort and domain expertise.

## Method

**Five-stage pipeline for automated patent summarization and retrieval evaluation:**

**Stage 1 — Patent part extraction:**
- Extract description, claims, abstract, and when identifiable: brief description, summary segment (from description), first claim
- Use HUPD dataset annotations to construct dictionary of summary headings; apply heuristic detection to unannotated patents
- Brief description = text from start of description to end of summary segment
- First claim = first non-dependent claim (identified by heuristic rules)

**Stage 2 — Patent summarization (three methods):**

*Extractive summarization:*
- **BERT** — sentence-level embeddings, cluster, select sentences nearest to centroids (default config)
- **SBERT** — "paraphrase-MiniLM-L6-v2" model for sentence embeddings

*Abstractive summarization:*
- **BigBird-Pegasus** (pre-trained on BIGPATENT) — two configurations: default (50–100 words), adjusted (250–300 words via modified length penalty/min-max length)
- **Fine-tuned BigBird (BigBirdFT)** — trained on custom 48,322-patent HUPD subset where brief description + first claim (700–800 words) → summary segment (150–250 words); training params: max_source_length 1024, learning_rate 2e-5, num_beams 4, length_penalty 0.8, num_train_epochs 2

**Stage 3 — Patent retrieval:**
- Embedding model: **GTE-large-en-v1.5** (409M params, 1024-dim, 8192 token limit, MTEB SOTA in size category)
- Vector database: FAISS
- Corpus embeddings: claims text (limited to 3000 tokens to capture independent + dependent claims)
- Query embeddings: summaries or full sections as alternatives
- Index: 200,000 patents from CLEF-IP + USPTO datasets
- Retrieval method: cosine similarity (embedding-based only, no lexical/keyword methods)

**Stage 4 — Evaluation datasets:**
- **HUPD** [2004–2018 USPTO] — for segment extraction (background, summary annotations)
- **BIGPATENT** [1.3M USPTO] — for intrinsic summary quality evaluation (1000-patent test sample); pairs description → abstract as ground truth
- **CLEF-IP 2013** [EPO/WIPO] — 24 English-language patents (reduced from 50 topics due to missing docs), 2–8 manually identified relevant docs per topic via expert-curated citation links
- **USPTO-Explainable AI** [Kaggle competition] — 3,343 topic patents with 50 similar patents each via content similarity (not citation-based), semantically coherent segments auto-detected

**Stage 5 — Evaluation metrics:**
- **Intrinsic:** ROUGE-1, ROUGE-L (vs reference summaries); semantic similarity (cosine between BERT-for-Patents embeddings of generated vs reference)
- **Extrinsic (retrieval):** MAP@100 (CLEF-IP), MAP@50 (USPTO); Precision/Recall @5, @10, @30

## Main Findings

**Intrinsic evaluation (BIGPATENT, n=1000):**
- BigBird pre-trained (description input, 118 words) vs abstract: ROUGE-1 0.51, ROUGE-L 0.42, semantic sim 0.81
- Fine-tuned BigBird (brief description input, 122 words) vs abstract: ROUGE-1 0.47, ROUGE-L 0.35, semantic sim 0.81 — similar quality with less input content
- Fine-tuned BigBird (brief description input) vs summary segment: ROUGE-1 **0.56**, ROUGE-L **0.53**, semantic sim 0.74 — best performance targeting the extended author-crafted summary segment

**Extrinsic evaluation — CLEF-IP 2013 (24 topics, citation-based relevance):**

*Baseline (full sections as queries):*
- Abstract (109 words): MAP@100 26.31%, P@10 14.58%, R@30 50.27%
- Claims (982 words): MAP@100 **27.72%**, P@10 **15.83%**, R@30 47.17%
- Description (6,962 words): MAP@100 23.89%, P@10 12.50%, R@30 35.87%

*Automated summaries as queries (best per method):*
- **Adjusted BigBird** (claims input, 224 words): MAP@100 **35.40%** (+7.68pp vs claims baseline), P@10 **18.33%**, R@30 **53.07%**
- SBERT (description input, 1,276 words): MAP@100 30.89%, P@10 15.42%, R@30 51.33%
- Default BigBird (claims input, 62 words): MAP@100 31.60%, P@10 15.83%, R@30 49.94%
- Fine-tuned BigBird (description input, 154 words): MAP@100 25.13% — underperforms, possibly because training target (summary segment) differs from retrieval relevance

**Extrinsic evaluation — USPTO (3,343 topics, similarity-based relevance):**

*Baseline (full sections/segments as queries):*
- Abstract (139 words): MAP@50 16.60%, P@10 44.77%, R@30 19.70%
- Claims (832 words): MAP@50 20.17%, P@10 52.82%, R@30 22.73%
- Description (4,200 words): MAP@50 21.19%, P@10 55.16%, R@30 24.04%
- **Brief description** (1,096 words): MAP@50 **22.40%**, P@10 **56.42%**, R@30 **24.98%** — best single-segment baseline
- Summary segment (524 words): MAP@50 21.08%, P@10 53.52%, R@30 23.71%
- Brief desc + first claim (1,267 words): MAP@50 **22.64%**, P@10 **56.91%**, R@30 **25.13%** — best baseline overall

*Automated summaries as queries (best per method):*
- **SBERT** (description input, 807 words): MAP@50 **23.95%** (+2.76pp vs description baseline), P@10 **58.78%**, R@30 **26.21%** — best overall
- BERT (description input, 695 words): MAP@50 23.40%, P@10 57.71%, R@30 25.74%
- Adjusted BigBird (claims input, 227 words): MAP@50 19.72%, P@10 51.10%, R@30 22.59%
- Adjusted BigBird (description input, 242 words): MAP@50 21.89%, P@10 55.39%, R@30 24.49%

**Cross-dataset patterns:**
- Automated summaries consistently outperform traditional full-section queries (abstract, claims, description used verbatim)
- Adjusted BigBird (longer summaries, 250–300 words) outperforms default BigBird (50–100 words) — longer summaries capture more patent content breadth
- SBERT extractive summaries achieve strong retrieval but retain much original text (avg 807–1,276 words), not addressing token-limit reduction goal
- Best configuration varies by dataset: adjusted BigBird from claims (CLEF-IP), SBERT from description (USPTO)
- High-value segments (brief description, summary segment + first claim) outperform conventional sections when detectable

## Limitations and Observations

**Acknowledged limitations:**
- **Token reduction vs performance tradeoff** — SBERT achieves best USPTO retrieval but generates long summaries (807 words from description), not addressing LLM token-limit challenge; BigBird addresses length but with lower absolute retrieval performance
- **Corpus representation fixed** — all experiments use claims text (3000 tokens) as corpus embeddings via GTE; alternative strategies (using abstracts, descriptions, or generated summaries as corpus representations) not explored
- **Single retrieval method** — only embedding-based cosine similarity tested; no lexical/BM25 or hybrid retrieval baseline
- **Limited datasets** — CLEF-IP reduced to 24 topics (from 50) due to missing docs; USPTO uses similarity-based (not citation-based) relevance
- **Segment detection inconsistency** — brief description and summary segments not consistently identifiable across all patents, especially non-US documents (EPO lacks standardized headings)
- **Fine-tuning target mismatch** — BigBirdFT trained to replicate author-crafted summary segments underperforms on retrieval; summary segments may not align with retrieval-optimal query characteristics
- **No abstractive model exploration beyond BigBird** — PEGASUS, T5, BART, GPT-4, Llama-3 not extensively evaluated (GPT-based models noted as limited by closed-source nature and token-based pricing)

**Visual verification note:** Tables 2–6 lost grid structure in PDF→text extraction (columns/rows stacked or shifted). Prose-quoted headline figures confirmed reliable:
- CLEF-IP: adjusted BigBird claims → MAP@100 35.40% vs claims baseline 27.72%
- USPTO: SBERT description → MAP@50 23.95% vs brief desc+first claim baseline 22.64%
- BIGPATENT: fine-tuned BigBird brief desc vs summary segment → ROUGE-1 0.56, ROUGE-L 0.53

For precise table-cell values beyond these prose-quoted numbers (e.g., individual cut-off precision/recall per method, per-input-source breakdowns), visually inspect source PDF pages 7–10. Non-blocking caution — main claims are verified reliable.

## Track C Relevance (proposed, NOT AUTHORIZED)

**Moderate relevance as query-formulation / query-representation method.** U022 directly addresses patent prior-art retrieval, using automated summarization to generate concise query representations that outperform full-section verbatim queries (abstract, claims, description). This is a query-side intervention in the candidate generation stage — the summaries serve as embedding inputs to dense retrieval (GTE + FAISS cosine similarity).

**Potential Track C applications:**
1. **Query compression for token-limited dense retrievers** — BigBird-generated 250-word summaries from claims achieve MAP@100 35.40% (CLEF-IP), outperforming 982-word claims verbatim (27.72%), addressing practical token limits
2. **Segment-based query construction** — brief description (1,096 words) + first claim outperforms full description (4,200 words) on USPTO; automated segment extraction + summarization could replace manual query formulation
3. **Hybrid query ensemble candidate** — combine lexical (BM25 on full claims), dense (GTE on summarized claims), and segment-based (brief desc + first claim) channels for multi-view candidate generation (cf. IS1 H1 hypothesis)

**Limitations for IS1 Track C:**
- Single retrieval method (dense-only, no BM25/lexical baseline or RRF fusion)
- No family-level aggregation or domain-split evaluation (CLEF-IP is EPO/WIPO mixed, USPTO is single-jurisdiction)
- No cross-domain generalization test (IN vs OUT domains as in DAPFAM)
- Evaluation is document-level retrieval (no passage/chunk retrieval as in IS1 H3)
- No reranking stage — summaries replace query, not candidate set

**Actionable insight:** The finding that high-value segments (brief description, summary segment + first claim when detectable) outperform full sections suggests segment-aware query construction could improve Track C candidate generation. However, segment detection is USPTO-specific; EPO patents lack standardized structure.

## Track R Relevance (proposed, NOT AUTHORIZED)

**No reranking component.** U022 is a single-stage dense retrieval pipeline (query embedding → FAISS cosine search → top-k results). Summaries replace the query representation, not a second-stage reranker. No retrieve-then-rerank architecture, no listwise/pointwise reranker, no instruction-aware reranking.

**Potential Track R connection (indirect):** If IS1 Track R uses a fixed candidate set (e.g., BM25 top-1000), then applying summarization to candidate documents (not queries) could generate enriched pseudo-documents for reranker input. U022 does not explore this direction.

## Track S Relevance (revision-stage, EXECUTION CLOSED)

**No prompt optimization or skill evolution.** Summarization models (BERT, SBERT, BigBird) are fixed pre-trained or fine-tuned transformers, not LLM-based prompt-engineering systems. No meta-learning, self-improvement, or prompt evolution mechanism. The fine-tuning of BigBird on HUPD (brief desc + first claim → summary segment) is supervised training, not SkillOpt-style prompt evolution.

## Relationship to Papers A, B, C, D

**Moderate connection to query formulation / candidate generation, no connection to reranking (Paper A/D focus).**

**Paper A (instruction-tuned reranking):** U022 generates queries via summarization; Paper A reranks fixed candidate sets using instruction-aware models. Orthogonal stages — U022 could provide query inputs for Paper A's retrieval stage, but U022 does not address reranking.

**Paper D (DAPFAM family-level retrieval):** U022 evaluates document-level retrieval on CLEF-IP (EPO/WIPO, citation-based) and USPTO (similarity-based), not family-level retrieval with domain-aware splits. DAPFAM uses IPC3 IN/OUT splits; U022 has no cross-domain evaluation. DAPFAM measures family-level Recall@100/NDCG@100; U022 measures document-level MAP@50/@100. Different granularity, different relevance definition, different evaluation protocol.

**Potential integration point:** If Paper D or IS1 Track C were extended to test segment-based or summarization-based query construction (e.g., brief description + first claim as query input instead of full claims), U022's findings provide empirical evidence that such segment-aware queries outperform full sections. However, U022's segment extraction relies on USPTO-specific structure annotations (HUPD), which are not available for EPO/WIPO/Asian patents in DAPFAM.

**Papers B/C:** No direct connection (Papers B/C are pilot provenance only, not cited in U022 or vice versa).

**Do not cross-compare:** U022's MAP@100 35.40% (CLEF-IP, 24 topics, citation-based relevance, adjusted BigBird from claims) is document-level retrieval performance, not family-level Recall@100 as in DAPFAM. The tasks, datasets, and metrics are different despite both being called "patent retrieval."

## Experience Brain Cross-Check

**Query:** "patent retrieval summarization BigBird query formulation"  
**Top 3 results:** KNO-20DDBF1D30A0 (IS1 candidate exposure synthesis), KNO-5449A7642CF9 (IS1 literature matrix), KNO-9F9F212D663E (IS1 project plan)  
**Match found:** No — no Knowledge record with SHA `c309ccb34e8c36b529c40b702a622900ef2042f1a6e092e33b1defad8adb2ddb` or title "Enhancing patent retrieval using automated patent summarization" in top 3 results.  
**Recommended action:** ingest_new

## Verification Warnings

Tables 2 (intrinsic evaluation ROUGE scores), 3 (CLEF-IP baseline sections), 4 (CLEF-IP automated summaries), 5 (USPTO baseline sections/segments), 6 (USPTO automated summaries) lost grid structure during PDF→text extraction — rows and columns became vertically stacked or shifted. The prose-quoted headline figures are confirmed reliable from discussion section (page 10) and results narrative (pages 7–9):
- CLEF-IP adjusted BigBird claims: MAP@100 35.40%, baseline claims 27.72%
- USPTO SBERT description: MAP@50 23.95%, best baseline (brief desc + first claim) 22.64%
- BIGPATENT fine-tuned BigBird: ROUGE-1 0.56, ROUGE-L 0.53 vs summary segment

For precise table-cell values beyond these prose-quoted numbers (e.g., individual P@5/R@10 per method/input combination, semantic similarity scores per configuration), visually inspect source PDF pages 7–10 before citation. This is a **non-blocking** visual-check caution — the paper's main claims are verified reliable.

---

**Tier B classification rationale:** U022 is a patent prior-art retrieval paper with quantitative retrieval metrics (MAP@50/@100, Precision, Recall) evaluated on established patent benchmarks (CLEF-IP 2013, USPTO Kaggle). It addresses query formulation via automated summarization — a candidate-generation-stage intervention relevant to IS1 Track C. However, it lacks the core characteristics for Tier A: (1) no family-level aggregation (document-level only), (2) no domain-aware splits or cross-domain evaluation (no IN/OUT generalization test), (3) single retrieval method (dense-only, no lexical/BM25 baseline or RRF fusion), (4) no reranking stage. The paper contributes a query-side method (summarization as query compression) with retrieval evaluation, but the evaluation scope is narrower than Tier A benchmarks like DAPFAM. Tier B: adjacent method with retrieval-relevant findings, but not a primary benchmark contribution or comprehensive retrieval architecture.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
