---
unique_id: U023
priority_tier: B
sha256: 16fb7f9b2d7b8601931847b3d7683c4e4ab9f354d563014586e99b9eb933d768
canonical_path: research/ref-paper/is1/pdfs/23_llm_powered_real_time_patent_citation_2026.pdf
size_bytes: 3717890
title: "LLM-powered Real-time Patent Citation Recommendation for Financial Technologies"
authors: "Tianang Deng, Yu Deng, Tianchen Gao, Yonghong Hu, Rui Pan"
year: 2026
venue: "arXiv preprint"
doi: null
arxiv: "arXiv:2601.16775v1 [cs.IR] 23 Jan 2026"
extraction_cache: extraction-cache/U023.md
experience_brain_match: no
matched_knowledge_id: null
recommended_ingestion_action: ingest_new
digest_status: completed
digest_prepared: 2026-07-24
pass_type: Batch_2A
authority: External Knowledge
---

# U023 — LLM-powered Real-time Patent Citation Recommendation for Financial Technologies

## Bibliographic Identity

**Title:** LLM-powered Real-time Patent Citation Recommendation for Financial Technologies  
**Authors:** Tianang Deng¹, Yu Deng², Tianchen Gao³✉, Yonghong Hu¹, Rui Pan¹✉ (¹Central University of Finance and Economics, ²Harbin Huiwen JetCreate AI, ³Peking University BICMR)  
**Venue:** arXiv preprint  
**DOI:** null  
**arXiv ID:** arXiv:2601.16775v1 [cs.IR]  
**Publication Date:** 23 January 2026  
**Document Type:** Preprint — citation recommendation system with incremental updating  
**Field:** Patent information retrieval, citation recommendation, financial technology

## Research Problem

Financial innovation drives rapid patenting activity, creating a dynamic patent corpus where timely and comprehensive prior-art discovery is critical. Financial technologies (FinTech) patents grow continuously, citation recommendation systems must operate in real-time as new applications arrive, and delays of even months can lead to missed R&D opportunities, avoidable litigation risks, or incomplete prior-art search during examination. Existing patent citation recommendation methods rely on static indexes or periodic batch retraining, which cannot scale with explosive growth or incorporate newly filed patents without costly full-index reconstruction. The dual challenges are: (1) **large-scale retrieval** over 428,843 CNIPA financial patents (IPC G06Q 10/00–50/00, 2000–2024), and (2) **real-time incremental updating** to add newly issued patents without rebuilding the entire index, which traditional approximate nearest-neighbor (ANN) methods like ANNOY cannot support efficiently.

## Method

**Three-stage patent citation recommendation framework with incremental updating:**

**Stage 1 — Text embedding (LLM-based semantic representation):**
- Model: OpenAI **text-embedding-3-large** (3,072-dimensional vectors)
- Input: patent abstracts (Chinese language financial patents)
- Normalization: unit-length vectors for cosine similarity computation
- Semantic proximity: simcos(v(A), v(B)) = v(A)ᵀv(B) (since ||v|| = 1)

**Stage 2 — Candidate pool construction (HNSW K-ANNS):**
- Algorithm: **Hierarchical Navigable Small World (HNSW)** graph [Malkov & Yashunin 2018]
- Index structure: multi-layer navigable small-world graph; higher layers = sparse long-range connections, bottom layer = all data points with short-range connections
- Incremental insertion: new patents inserted without global rebuilding; assigned maximum layer via exponentially decaying distribution; greedy search from top layer down to find entry point, then establish connections at each layer
- Parameters: M (max connections per node), ef_construction (construction search), ef_search (query search)
- Retrieval: hierarchical SEARCH-LAYER algorithm from top to bottom, K = 1,000 nearest neighbors retrieved

**Stage 3 — Candidate ranking (cosine similarity reranking):**
- Compute cosine similarity between query patent and all K = 1,000 candidates
- Rank candidates in descending order
- Return top-k as citation recommendations (k ∈ {10, 50, 100, 200} evaluated)

**Incremental updating mechanism (rolling day-by-day):**
1. Build initial HNSW index from all patents filed ≤ 2023-12-31
2. For each application date t in 2024:
   - Retrieve K = 1,000 nearest neighbors for patents filed on date t
   - Rank and recommend top-k citations
   - Insert embeddings of patents filed on date t into HNSW index
   - Use updated index for date t+1
3. 341 distinct application dates in 2024 processed sequentially

## Dataset / Evaluation Protocol

**CNIPA financial patent corpus:**
- **Total:** 428,843 CNIPA patents (2000–2024)
- **IPC classification:** G06Q 10/00–50/00 (business methods, finance, e-commerce)
- **Language:** Chinese (abstracts embedded via text-embedding-3-large)
- **Test set:** 15,733 patents filed in 2024 with at least one comparison document (examiner-curated citation) in the corpus
- **Index:** All patents filed before 2023 used to build initial HNSW/ANNOY/baseline indexes
- **Ground truth:** Examiner-curated comparison documents (citations) from patent examination records

**Evaluation setting:**
- **Time-ordered evaluation:** Train on earlier-filed patents (≤2022), test on 2024-filed patents — mirrors real-world prior-art search where query patent is new and index is historical
- **Metrics:** Mean Reciprocal Rank (MRR), Normalized Discounted Cumulative Gain (nDCG), Recall@k (Rec@10, Rec@50, Rec@100, Rec@200)
- **Baselines:** TF-IDF (4096-dim sparse vectors), Doc2Vec (500-dim PV-DM, 50 epochs), BERT (bert-base-chinese, 768-dim [CLS] embeddings), ANNOY (100 trees, text-embedding-3-large), Google Patents similar-document API (up to 25 similar docs)

**Incremental updating experiment:**
- **Static HNSW/ANNOY:** Index built once from 2000–2023 patents, no updates
- **Incremental HNSW:** Rolling day-by-day insertion of 2024 patents (341 dates)
- **Reconstructed ANNOY:** Full forest rebuilt from scratch for each application date (341 rebuilds)
- **Time cost:** Measured in seconds for complete processing of 15,733 test patents

## Main Findings

**Baseline comparison (static index, 2024 test set, n=15,733):**

| Model | MRR | nDCG | Rec@10 | Rec@50 | Rec@100 | Rec@200 |
|-------|-----|------|--------|--------|---------|---------|
| **Exact-Large** (exhaustive cosine) | **0.1782** | **0.1831** | **0.1309** | **0.2512** | **0.3196** | **0.3914** |
| **HNSW-Large** (proposed) | **0.1782** | 0.1830 | **0.1309** | 0.2511 | 0.3194 | 0.3912 |
| ANNOY-Large | 0.1775 | 0.1814 | 0.1301 | 0.2489 | 0.3160 | 0.3860 |
| HNSW-TF-IDF | 0.0786 | 0.0806 | 0.0617 | 0.1430 | 0.1912 | 0.2507 |
| HNSW-Doc2Vec | 0.0397 | 0.0493 | 0.0275 | 0.0753 | 0.1172 | 0.1806 |
| HNSW-BERT | 0.0348 | 0.0404 | 0.0234 | 0.0622 | 0.0936 | 0.1455 |

- HNSW-Large matches exhaustive search (upper bound) on MRR/Rec@10, near-identical on other metrics
- ANNOY-Large marginally lower (-0.7pp MRR, -5.2pp Rec@200)
- TF-IDF achieves only 44% of HNSW-Large MRR (0.0786 vs 0.1782)
- Doc2Vec/BERT substantially worse than TF-IDF (BERT MRR 0.0348 = 19.5% of HNSW-Large)
- **LLM embeddings (text-embedding-3-large) vastly outperform traditional NLP representations**

**Google Patents comparison:**
- Google Patents similar-document API returns up to 25 docs per patent (fixed)
- Evaluated on overlap with examiner-curated comparison documents
- HNSW-Large Rec@25 performance compared against Google Patents (qualitative case study shows HNSW retrieves more technically relevant citations)

**Incremental updating results (rolling day-by-day, 341 dates, n=15,733):**

| Search Method | MRR | nDCG | Rec@10 | Rec@50 | Rec@100 | Rec@200 | Time Cost (s) |
|---------------|-----|------|--------|--------|---------|---------|---------------|
| Static HNSW | 0.1782 | 0.1830 | 0.1309 | 0.2511 | 0.3194 | 0.3912 | 859.6 |
| Static ANNOY | 0.1775 | 0.1814 | 0.1301 | 0.2489 | 0.3160 | 0.3860 | 1470.9 |
| Reconstructed ANNOY | 0.1928 | 0.2040 | 0.1425 | 0.2777 | 0.3555 | 0.4385 | **49146.4** |
| **Incremental HNSW** | 0.1926 | **0.2055** | **0.1433** | **0.2801** | **0.3590** | **0.4443** | **1147.3** |

- **Incremental HNSW achieves best performance** on nDCG and all Recall@k metrics (except MRR where reconstructed ANNOY is +0.2pp)
- Incremental HNSW Rec@200: **44.43%** vs static HNSW 39.12% (+5.31pp absolute gain from daily updates)
- **Time cost:** Incremental HNSW 1147.3s = only +288s vs static HNSW (859.6s) = ~5ms overhead per newly filed patent
- Reconstructed ANNOY: 49146.4s = **42.8× slower** than incremental HNSW, despite slightly lower performance on most metrics
- Static ANNOY: 1470.9s = 1.28× slower than incremental HNSW with worse performance

**Key insight:** Incremental updating improves recall substantially (newly filed patents become retrievable as candidates immediately), while HNSW's native incremental insertion support avoids costly full-index rebuilding that ANNOY requires (341 rebuilds = 49k seconds).

## Limitations and Observations

**Acknowledged limitations:**
- **Single-domain evaluation** — only CNIPA financial patents (IPC G06Q 10/00–50/00); no cross-domain or multi-jurisdiction evaluation (USPTO, EPO, JPO not tested)
- **Abstract-only input** — only patent abstracts embedded; claims text, full description, or multi-field representations not explored
- **Chinese language only** — CNIPA patents are Chinese; multilingual or English-language patent evaluation not conducted
- **Citation-based relevance only** — ground truth is examiner-curated comparison documents; no evaluation on technical similarity, family-level retrieval, or classification-based relevance
- **No reranking stage** — system is single-stage retrieve-then-rank by cosine similarity; no learned reranker, cross-encoder, or instruction-aware reranking
- **No hybrid retrieval** — dense-only (LLM embeddings + cosine similarity); no BM25/lexical baseline, no RRF fusion
- **HNSW parameter sensitivity not studied** — M, ef_construction, ef_search values not ablated; optimal hyperparameters not determined
- **Computational cost of LLM embeddings not reported** — OpenAI text-embedding-3-large API cost (tokens, latency, pricing) not disclosed; batch embedding time for 428k patents not measured

**Visual verification note:** Table 2 (baseline comparison), Table 5 (incremental updating) visible in extraction cache — prose-quoted headline figures (HNSW-Large MRR 0.1782, incremental HNSW Rec@200 44.43%, reconstructed ANNOY time 49146.4s) match table values exactly. Tables preserved grid structure in extraction. No visual-check caution needed.

**Qualitative observation (case study):** Paper presents example patent CN112651849A (blockchain parallel transaction execution) — HNSW-Large retrieves technically relevant prior art on DAG blockchain and parallel execution methods; TF-IDF retrieves textually similar but less technically relevant patents; Doc2Vec/BERT retrieve irrelevant or distantly related documents. Demonstrates LLM embeddings capture semantic/technical relevance beyond keyword overlap.

## Track C Relevance (proposed, NOT AUTHORIZED)

**Moderate relevance as LLM-embedding + incremental-index candidate generation method.** U023 addresses patent citation recommendation (prior-art discovery) using dense retrieval (LLM embeddings + HNSW K-ANNS + cosine ranking). This is a candidate generation pipeline — retrieve K=1000 nearest neighbors, rank by similarity, return top-k citations. The incremental updating mechanism (HNSW daily insertion) directly addresses real-time candidate exposure in dynamically growing corpora.

**Potential Track C applications:**
1. **LLM-embedding baseline for pharmaceutical patents** — text-embedding-3-large achieved MRR 0.1782 on CNIPA financial patents; could serve as dense-retrieval baseline for IS1 pharmaceutical formulation patents (though domain transfer and language shift would need evaluation)
2. **Incremental index updating for continuous corpus growth** — HNSW's native incremental insertion (+5ms per patent, +5.31pp Rec@200 gain) demonstrates feasibility of real-time candidate exposure without costly batch rebuilding; relevant if IS1 Track C corpus grows over time
3. **Hybrid candidate generation candidate** — combine lexical (BM25 on claims), dense (LLM embeddings on abstracts/claims), and HNSW K-ANNS for multi-view candidate pool (cf. IS1 H1 hypothesis on multi-view union for OUT-domain coverage)

**Limitations for IS1 Track C:**
- Single-stage dense retrieval only (no BM25/lexical baseline, no RRF fusion, no reranking)
- No family-level aggregation or domain-split evaluation (IN vs OUT as in DAPFAM)
- Citation-based relevance (examiner comparison documents) ≠ family-level citation-relevance as in DAPFAM
- CNIPA financial patents (Chinese, G06Q business methods) ≠ pharmaceutical formulation patents (multilingual, A61K/C07D)
- Abstract-only embeddings; IS1 may require claims text or multi-field representations
- OpenAI API dependency (not self-hosted open-weight model)

**Actionable insight:** The finding that incremental HNSW updating improves Rec@200 by +5.31pp (39.12% → 44.43%) while adding only +288s overhead (vs 42.8× slower for ANNOY full rebuilds) demonstrates that real-time candidate exposure is computationally feasible at scale. If IS1 Track C operates over a continuously updated patent corpus, HNSW incremental insertion could enable daily/weekly index updates without batch retraining.

## Track R Relevance (proposed, NOT AUTHORIZED)

**No reranking component.** U023 is a single-stage retrieval pipeline (embed → K-ANNS → cosine rank → top-k). Candidates are ranked solely by cosine similarity in the embedding space; no learned reranker, cross-encoder, listwise ranker, or instruction-aware reranking. The system retrieves K=1000 candidates via HNSW, then ranks them by similarity — this is candidate generation + simple scoring, not retrieve-then-rerank.

**Potential Track R connection (indirect):** If IS1 Track R uses a fixed BM25 candidate set (e.g., top-1000), then applying LLM embeddings + cosine reranking (as in U023 Stage 3) could serve as a dense reranker baseline. However, U023 does not evaluate reranking over a fixed diverse candidate set — it evaluates end-to-end retrieval where embedding similarity is both the retrieval and ranking signal.

## Track S Relevance (revision-stage, EXECUTION CLOSED)

**No prompt optimization or skill evolution.** U023 uses fixed pre-trained OpenAI text-embedding-3-large model for embedding, with no fine-tuning, prompt engineering, or meta-learning. HNSW is a deterministic graph-based K-ANNS algorithm with fixed hyperparameters (M, ef_construction, ef_search). No SkillOpt-style prompt evolution, no LLM-based reasoning, no self-improvement mechanism.

## Relationship to Papers A, B, C, D

**Minimal connection to Paper A/D reranking focus; potential connection to candidate generation (relevant to future IS1 Track C candidate-exposure experiments, but different domain/language/metric).**

**Paper A (instruction-tuned reranking):** U023 does not address reranking — it ranks candidates by cosine similarity only. Paper A reranks fixed candidate sets using instruction-aware models. Orthogonal stages.

**Paper D (DAPFAM family-level retrieval):** U023 evaluates document-level citation recommendation on CNIPA financial patents (Chinese, G06Q, citation-based relevance), not family-level retrieval with IPC3 domain splits. DAPFAM uses family-level Recall@100/NDCG@100 on IN vs OUT domains; U023 uses document-level MRR/Rec@k on single-domain (financial) with no IN/OUT split. Different granularity, different relevance definition, different evaluation protocol.

**Potential integration point:** If Paper D or IS1 Track C were extended to test LLM-embedding-based dense retrieval (vs PatentSBERTa/PAECTER/GTE), U023's finding that text-embedding-3-large vastly outperforms BERT/Doc2Vec/TF-IDF (MRR 0.1782 vs 0.0348–0.0786) provides empirical evidence for LLM embeddings' superiority. However, U023's CNIPA financial corpus (Chinese, business methods) differs substantially from DAPFAM pharmaceutical formulation corpus (multilingual, A61K/C07D), so domain transfer is uncertain.

**Do not cross-compare:** U023's MRR 0.1782 / Rec@200 44.43% (CNIPA financial, citation-based, incremental HNSW) is not comparable to DAPFAM OUT Recall@100 ≈0.1655 (family-level, IPC3 cross-domain, citation-relevance). Different tasks (document citation recommendation vs family-level prior-art retrieval), different metrics (MRR/Rec@k vs family Recall@100), different domains (G06Q financial vs pharmaceutical formulation).

## Experience Brain Cross-Check

**Query:** "LLM patent citation recommendation HNSW financial technology CNIPA"  
**Top 3 results:** KNO-3D43C4514725 (IS1 research gaps), KNO-528A290EA2E4 (PatenTEB), KNO-92F3E83D2CBF (PAECTER)  
**Match found:** No — no Knowledge record with SHA `16fb7f9b2d7b8601931847b3d7683c4e4ab9f354d563014586e99b9eb933d768` or title "LLM-powered Real-time Patent Citation Recommendation for Financial Technologies" or arXiv ID `2601.16775` in top 3 results.  
**Recommended action:** ingest_new

## Verification Warnings

Tables 2 (baseline comparison) and 5 (incremental updating) preserved grid structure in PDF→text extraction. Prose-quoted headline figures confirmed reliable from abstract and results sections (pages 22–31):
- HNSW-Large: MRR 0.1782, nDCG 0.1830, Rec@200 0.3912
- Incremental HNSW: MRR 0.1926, nDCG 0.2055, Rec@200 0.4443 (+5.31pp vs static), time 1147.3s
- Reconstructed ANNOY: time 49146.4s (42.8× slower than incremental HNSW)

No visual-check caution needed — tables are readable and values match prose.

---

**Tier B classification rationale:** U023 is a patent citation recommendation paper with quantitative retrieval metrics (MRR, nDCG, Recall@k) evaluated on a large-scale patent corpus (428k CNIPA financial patents). It addresses prior-art discovery using LLM embeddings + HNSW K-ANNS + incremental updating — a candidate-generation-stage method relevant to IS1 Track C. However, it lacks core Tier A characteristics: (1) no family-level aggregation (document-level citation only), (2) no cross-domain or domain-split evaluation (single-domain G06Q financial, no IN/OUT generalization test), (3) single retrieval method (dense-only, no BM25/lexical baseline or hybrid fusion), (4) no reranking stage, (5) Chinese-language CNIPA corpus (not multilingual or standard USPTO/EPO benchmarks). The paper contributes a real-time incremental-updating method with strong empirical results on financial patents, but the evaluation scope is narrower than Tier A benchmarks like DAPFAM or CLEF-IP. Tier B: adjacent method with retrieval-relevant findings and novel incremental-updating contribution, but domain-specific (FinTech), language-specific (Chinese), and single-stage retrieval architecture.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
