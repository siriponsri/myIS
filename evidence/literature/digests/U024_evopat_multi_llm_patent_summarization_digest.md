---
unique_id: U024
priority_tier: C
sha256: 2594f2d877a4b65e08c6e2eb10612094ecff83a51a63696bc50a7e91b556c736
canonical_path: research/ref-paper/is1/pdfs/24_evopat_multi_llm_based_patent_summarization_2024.pdf
size_bytes: 1227477
title: "EvoPat: A Multi-LLM-Based Patents Summarization and Analysis Agent"
authors: "Suyuan Wang, Xueqian Yin, Menghao Wang, Ruofeng Guo, Kai Nan"
year: 2024
venue: "arXiv preprint"
doi: null
arxiv: null
extraction_cache: extraction-cache/U024.md
experience_brain_match: no
matched_knowledge_id: null
recommended_ingestion_action: ingest_new
digest_status: completed
digest_prepared: 2026-07-24
pass_type: Batch_2A
authority: External Knowledge
---

# U024 — EvoPat: A Multi-LLM-Based Patents Summarization and Analysis Agent

## Bibliographic Identity

**Title:** EvoPat: A Multi-LLM-Based Patents Summarization and Analysis Agent  
**Authors:** Suyuan Wang, Xueqian Yin, Menghao Wang, Ruofeng Guo, Kai Nan (SynMat AI Tech Inc)  
**Venue:** arXiv preprint  
**DOI:** null  
**arXiv ID:** Not provided (submitted December 25, 2024)  
**Publication Date:** December 25, 2024  
**Document Type:** Preprint — multi-agent LLM system for patent analysis  
**Field:** Patent analysis, NLP, multi-agent systems, retrieval-augmented generation

## Research Problem

The rapid growth of patent filings creates a significant burden for researchers and engineers navigating the patent landscape to identify trends, innovations, and breakthroughs. Existing LLM-based patent analysis systems focus on single-dimensional tasks (keyword extraction, text summarization) and fail to provide comprehensive, structured understanding of patent content and its relationship to other patents. Researchers need efficient tools to summarize, evaluate, and contextualize patents, revealing innovative contributions and underlying scientific principles. The challenge is to automate holistic patent analysis that extracts key innovations, identifies technical difficulties, performs horizontal comparisons with similar patents, and offers structured summaries tailored to various user needs—all while managing long patent texts that exceed LLM token limits and integrating external knowledge sources (related patents, academic papers) to reduce hallucination.

## Method

**EvoPat: Multi-LLM-based patent analysis agent with three-phase architecture**

**Phase 1 — Data Preprocessing:**
1. **Text extraction:** Text-based PDFs extracted via open-source tools (PyPDF); image-based PDFs processed via OCR (high time cost, lower accuracy)
2. **Text filtering:** Normalize via regex (remove special characters, HTML tags, URLs, stopwords)
3. **Text embedding:** BGE-M3 multilingual embedding model (supports 100+ languages, bidirectional dense embeddings, 3072-dim for text-embedding-3-large compatibility)
4. **Vector storage:** Faiss (Meta) vector database for similarity search and clustering (supports exact/approximate NN search, GPU acceleration, billions of vectors)

**Phase 2 — Patent Analysis (Multi-Agent System):**
- **Five specialized LLM agents** (all using GPT-4o via OpenAI API):
  1. **Innovation Points Scientist:** Identifies most valuable innovative methods within the patent (determines whether users explore further)
  2. **Implementation Method Scientist:** Presents implementation process and workflow (helps assess realization complexity)
  3. **Technical Detail Scientist:** Provides supplementary technical details (numerical values, environmental conditions, unique processes)
  4. **Horizontal Comparison Scientist:** Conducts internet searches for similar patents via Google Patents API, performs comparative analysis highlighting uniqueness
  5. **Academic Direction Scientist:** Conducts online searches for related papers via Semantic Scholar API, analyzes current research trends, broadens perspective

- **Agent collaboration:** Agents share all content generated during prior interactions (models negotiation/reasoning across multiple iterations); each agent analyzes from distinct perspective; contributions combined into detailed yet concise patent analysis

- **Long-context handling (two strategies):**
  - **TransformMessages (Autogen):** Segment text, treat prior segments as historical context (MessageHistoryLimitation + TokenLimitation); challenges: forgetting with excessively long text, high cost (many tokens per call)
  - **LLMLingua (default in EvoPat):** Compress prompts using small aligned LMs (GPT-2 Small, LLaMA-7B) to identify and remove unimportant tokens; constructs language exclusive to LLMs (hard for humans, easy for LLMs); achieves up to 20× reduction in prompt size while maintaining nearly identical performance on downstream tasks including in-context learning and reasoning; lower cost, better efficiency, minimal forgetting

**Phase 3 — Output Integration:**
- Convert agent responses to Markdown format (lightweight markup, easy-to-read plain text → valid HTML → PDF)
- Final document includes: abstract and innovations, implementation methods, technical details, comparative analysis, academic direction

## Dataset / Evaluation Protocol

**Patent corpus:**
- **Total:** 5,000 patents (past decade, science and engineering domains)
- **Source:** Google Patents
- **Languages:** Chinese, English, Japanese, Korean
- **Evaluation subset:** 100 patents randomly sampled in photoresist and nanoimprint lithography domains

**Evaluation setup:**
- **Baseline:** GPT-4o (single-agent, no multi-agent architecture, no external API retrieval)
- **Experts:** 4 domain experts in photoresist and nanoimprint lithography
- **Automatic metrics:** ROUGE-1, ROUGE-2, ROUGE-L, BERTScore (Precision, Recall, F1)
- **Human evaluation dimensions (max score 5):** Informative, Rich, Coherent, Attributable, Extensible

**Ablation study:**
- Compare TransformMessages vs LLMLingua for long-text processing
- Metrics: ROUGE-1/2/L, Informative, Rich, Attributable

## Main Findings

**EvoPat vs GPT-4o (automatic metrics, n=5000):**

| Model | ROUGE-1 | ROUGE-2 | ROUGE-L | BERTScore P | BERTScore R | BERTScore F1 |
|---|---|---|---|---|---|---|
| **EvoPat** | **0.2164** | **0.08152** | **0.2081** | **0.7856** | **0.7392** | **0.7616** |
| GPT-4o | 0.0745 | 0.0122 | 0.1079 | 0.7760 | 0.7332 | 0.7540 |

- EvoPat ROUGE-1: +190% vs GPT-4o (0.2164 vs 0.0745)
- EvoPat ROUGE-2: +568% vs GPT-4o (0.08152 vs 0.0122)
- EvoPat ROUGE-L: +93% vs GPT-4o (0.2081 vs 0.1079)
- BERTScore improvements: +0.0096 Precision, +0.0060 Recall, +0.0076 F1

**EvoPat vs GPT-4o (human evaluation by 4 experts, n=100, max=5):**

| Model | Informative | Rich | Coherent | Attributable | Extensible |
|---|---|---|---|---|---|
| **EvoPat** | **4.82** | **4.85** | **4.63** | **4.89** | **4.34** |
| GPT-4o | 4.13 | 3.95 | 4.55 | 4.72 | 2.79 |

- EvoPat clearly outperforms GPT-4o across all dimensions
- Largest gains: **Informative** (+0.69), **Rich** (+0.90), **Extensible** (+1.55)
- Multi-agent approach + external knowledge (Google Patents, Semantic Scholar) greatly enhances depth and quality
- Extensible score gap (4.34 vs 2.79) reflects EvoPat's ability to incorporate supplementary content from external sources

**Note on automatic metrics:** ROUGE/BERTScore primarily assess correlation between generated content and original text; they underestimate EvoPat's performance because EvoPat performs in-depth analysis and integrates online search/expansion (horizontal comparison, academic direction modules), which adds novel information not present in the original patent. Human evaluation better captures EvoPat's comprehensive analysis capabilities.

**Long-text processing ablation (TransformMessages vs LLMLingua):**

| Strategy | ROUGE-1 | ROUGE-2 | ROUGE-L | Informative | Rich | Attributable |
|---|---|---|---|---|---|---|
| TransformMessages | 0.1815 | 0.06576 | 0.1722 | 4.68 | 4.81 | 4.76 |
| **LLMLingua** | **0.2164** | **0.08152** | **0.2081** | **4.85** | **4.63** | **4.89** |

- LLMLingua outperforms TransformMessages on all ROUGE metrics and most human dimensions
- TransformMessages risk: excessively lengthy historical information causes LLMs to forget important context, leading to omission of critical details
- LLMLingua advantage: compresses text while preserving essential information LLMs can process; minimal forgetting risk; lower cost; better efficiency
- EvoPat supports both methods; LLMLingua is default

**Qualitative insight:** Breaking patent analysis into five adjustable sub-tasks (innovation points, implementation, technical details, horizontal comparison, academic direction) addresses inherent token limitations of LLMs and prevents incomplete responses. Multi-agent approach enables more effective exploration of vast knowledge landscape within patents compared to single-agent direct analysis.

## Limitations and Observations

**Acknowledged limitations:**
- **Data preprocessing challenges:** Extracting meaningful connections between figures and text content from PDFs remains a significant hurdle; figure recognition and content-text alignment need improvement; OCR for image-based PDFs has high time cost and insufficient accuracy
- **Patent-paper connection gaps:** Identifying and explaining scientific principles underlying patents requires robust knowledge graph construction and integration of specialized agent roles (current Academic Direction Scientist uses Semantic Scholar API for related papers but lacks deep principle extraction)
- **Temporal gap modeling:** Time lag between emerging scientific trends in publications and their subsequent appearance in patents necessitates advanced time-series algorithms to generate more precise and forward-looking reports
- **Hallucination mitigation:** While RAG and external APIs (Google Patents, Semantic Scholar) reduce hallucination, further mitigation needed through knowledge graph construction and time-series modeling
- **Evaluation scope:** Tested only in NLP domain patents (photoresist, nanoimprint lithography); generalization to other technical domains (mechanical, electrical, biomedical) not demonstrated
- **Single LLM architecture:** All five agents use GPT-4o; no exploration of heterogeneous LLM combinations (e.g., different models for different agent roles)
- **No retrieval metrics:** System evaluated on summarization quality (ROUGE, BERTScore, human dimensions) but not on retrieval accuracy (precision/recall of cited patents, citation-relevance of retrieved papers)
- **Computational cost not reported:** OpenAI API cost (tokens, latency, pricing) for processing 5,000 patents not disclosed; Faiss indexing and embedding time not measured

**Visual verification note:** Paper contains system architecture diagram (Figure 1), multi-agent workflow diagram (Figure 2 with US20170263445A1 example), and evaluation tables (Tables 1-3). No table extraction issues flagged. Headline figures from abstract/results match tabulated values.

## Track C Relevance (proposed, NOT AUTHORIZED)

**Minimal relevance as patent analysis automation / summarization tool, not candidate generation or retrieval system.** U024 addresses automated patent summarization and multi-dimensional analysis (innovation identification, horizontal comparison, academic trend contextualization) using multi-agent LLM orchestration and external knowledge retrieval (Google Patents API, Semantic Scholar API). This is a **post-retrieval analysis pipeline** — assumes input is a single target patent to analyze, not a retrieval task over a large corpus to find relevant prior art or candidate patents.

**Potential Track C connections (indirect):**
1. **Horizontal Comparison Scientist as retrieval baseline:** Uses Google Patents API to search for similar patents given target patent keywords; could serve as commercial API baseline for Track C candidate generation experiments (cf. U014's comparison of Google Patents similar-document API vs open-source embedding models)
2. **Multi-agent analysis for query formulation:** Innovation Points Scientist extracts key innovations from query patent; could inform query expansion or claim-element extraction for Track C candidate generation (cf. U022 query formulation via summarization)
3. **Academic Direction Scientist for literature grounding:** Uses Semantic Scholar API to retrieve related papers; demonstrates integration of patent corpus + academic literature for contextualization; relevant to IS1 Track C if pharmaceutical formulation patents require literature-grounded retrieval

**Limitations for IS1 Track C:**
- Not a retrieval system — no candidate generation, no ranking, no family-level aggregation, no retrieval metrics (MAP, Recall@k, NDCG)
- Horizontal Comparison Scientist retrieves "similar patents" via Google Patents API but does not evaluate retrieval quality (precision, recall, citation-relevance)
- Evaluated on summarization quality (ROUGE, BERTScore, human dimensions: Informative, Rich, Coherent), not retrieval performance
- Single-patent analysis workflow (processes one patent at a time); Track C requires corpus-scale retrieval (query patent → rank 45k+ candidate families)
- No domain-split evaluation (IN vs OUT as in DAPFAM); tested only in NLP domain (photoresist, nanoimprint)
- No pharmaceutical patent evaluation; relevance to IS1 pharmaceutical formulation corpus uncertain

**Actionable insight:** The finding that multi-agent specialization (five distinct analyst roles sharing context) outperforms single-agent GPT-4o substantially on Informative (+0.69), Rich (+0.90), and Extensible (+1.55) human dimensions demonstrates that task decomposition and agent collaboration improve patent understanding. If IS1 Track C includes a post-retrieval analysis stage (e.g., summarize top-k retrieved families for user review), EvoPat's multi-agent architecture could serve as a reference design. However, EvoPat does not address the core Track C retrieval challenge (candidate exposure, family-level ranking, cross-domain OUT performance).

## Track R Relevance (proposed, NOT AUTHORIZED)

**No reranking component.** U024 is a patent analysis and summarization system, not a retrieval or reranking system. Horizontal Comparison Scientist retrieves similar patents via Google Patents API and compares them qualitatively (innovation points, technical differences), but does not rerank a fixed candidate set or evaluate ranking metrics (NDCG, MAP, Recall@k). The system's output is a structured PDF report (abstract, innovations, implementation, technical details, comparative analysis, academic direction), not a ranked list of candidate patents.

**Potential Track R connection (indirect):** If Track R includes an instruction-aware analysis stage (e.g., "given query patent and top-k candidates, generate comparative analysis highlighting innovation gaps"), EvoPat's Horizontal Comparison Scientist (prompt-engineered GPT-4o agent with Google Patents API access) could serve as a baseline. However, U024 does not evaluate reranking performance or compare against ranking baselines.

## Track S Relevance (revision-stage, EXECUTION CLOSED)

**Minimal prompt engineering, no skill evolution.** U024 uses five specialized GPT-4o agents, each with a fixed system prompt defining its role and task (Tables 4-8 in Appendix list verbatim prompts: Innovation Points Scientist, Implementation Method Scientist, Technical Detail Scientist, Horizontal Comparison Scientist, Academic Direction Scientist). Prompts are manually designed via prompt engineering; no meta-learning, no prompt evolution, no SkillOpt-style self-improvement. Agents share historical context (multi-turn conversation memory) but prompts are static. LLMLingua compresses input text but does not modify agent prompts.

**No connection to Track S (SkillOpt-style prompt evolution).**

## Relationship to Papers A, B, C, D

**No connection to Paper A/D reranking focus; no connection to Paper D family-level retrieval benchmarks; minimal overlap with IS1 core tasks.**

**Paper A (instruction-tuned reranking):** U024 does not address reranking. Agents analyze a single target patent in isolation; no ranking of candidate patents, no instruction-aware ranking model. Orthogonal tasks.

**Paper D (DAPFAM family-level retrieval):** U024 does not address family-level retrieval, domain-split evaluation, or citation-relevance ranking. DAPFAM evaluates family-level Recall@100/NDCG@100 on IN vs OUT domains with citation-based relevance; U024 evaluates single-patent summarization quality via ROUGE/BERTScore/human dimensions. Different tasks (retrieval vs summarization), different metrics, different evaluation protocols.

**Potential integration point (post-retrieval analysis):** If IS1 Track C retrieval system outputs top-k ranked families and requires human-readable analysis for review, EvoPat's multi-agent architecture could generate structured summaries and comparative analyses for each retrieved family. However, this is a post-retrieval stage, not part of the core candidate generation or reranking pipeline. U024's contribution is analysis automation, not retrieval performance improvement.

**Do not cross-compare:** EvoPat's human evaluation scores (Informative 4.82, Rich 4.85, Extensible 4.34 on 5-point scale) assess summarization quality, not retrieval quality. They are not comparable to DAPFAM retrieval metrics (family Recall@100, NDCG@100) or reranking metrics (MAP, MRR, NDCG@10). Different tasks, different metrics.

## Experience Brain Cross-Check

**Query:** "EvoPat multi-LLM patent summarization analysis agent GPT-4 RAG multi-agent"  
**Top 3 results:** KNO-B9A6DB6B10C1 (QaECTER/Sophia-Bench citation-driven embeddings), KNO-20DDBF1D30A0 (IS1 candidate exposure synthesis), KNO-3D43C4514725 (IS1 research gaps and hypothesis context)  
**Match found:** No — no Knowledge record with SHA `2594f2d877a4b65e08c6e2eb10612094ecff83a51a63696bc50a7e91b556c736` or title "EvoPat: A Multi-LLM-Based Patents Summarization and Analysis Agent" or authors "Suyuan Wang, Xueqian Yin, Menghao Wang, Ruofeng Guo, Kai Nan" in top 3 results. Returned results are about IS1 project knowledge and patent retrieval/embedding benchmarks, not multi-agent patent analysis systems.  
**Recommended action:** ingest_new

## Verification Warnings

Tables 1 (EvoPat vs GPT-4o automatic metrics), 2 (human evaluation), 3 (TransformMessages vs LLMLingua ablation) preserved grid structure in PDF→markdown extraction. Prose-quoted headline figures confirmed reliable from abstract and results sections (pages 1, 7-8):
- EvoPat ROUGE-1: 0.2164 (vs GPT-4o 0.0745)
- EvoPat human Informative: 4.82 (vs GPT-4o 4.13)
- LLMLingua ROUGE-1: 0.2164 (vs TransformMessages 0.1815)

Appendix Tables 4-8 contain verbatim system prompts for five agents (Innovation Points Scientist, Implementation Method Scientist, Technical Detail Scientist, Horizontal Comparison Scientist, Academic Direction Scientist). Prompts are readable and complete. No visual-check caution needed.

---

**Tier C classification rationale:** U024 is a patent analysis and summarization system using multi-agent LLM orchestration, RAG (Faiss vector DB, BGE-M3 embeddings), and external knowledge APIs (Google Patents, Semantic Scholar). It does **not** address patent retrieval, reranking, or family-level prior-art search. Core contribution is **automation of multi-dimensional patent analysis** (innovation identification, implementation methods, technical details, horizontal comparison, academic contextualization) via task-specialized agents with shared context. Evaluation focuses on summarization quality (ROUGE, BERTScore, human dimensions: Informative, Rich, Coherent, Attributable, Extensible) on 100 sampled patents in photoresist/nanoimprint domains, not retrieval metrics (MAP, Recall@k, NDCG). The system substantially outperforms single-agent GPT-4o on all metrics (ROUGE-1 +190%, Rich +0.90, Extensible +1.55), demonstrating effectiveness of multi-agent specialization for patent understanding. However, it lacks core Tier A/B characteristics: (1) not a retrieval or ranking system (no candidate generation, no family-level aggregation, no retrieval metrics), (2) no domain-split evaluation (no IN/OUT generalization test), (3) single-patent analysis workflow (not corpus-scale retrieval), (4) evaluated only in NLP domain (photoresist/nanoimprint, not pharmaceutical or multi-domain), (5) no connection to IS1 Track C/R core tasks (candidate exposure, reranking). Tier C: domain-adjacent system (patent understanding automation) with methodological insights for post-retrieval analysis stage, but not directly applicable to IS1 retrieval/reranking benchmarks. Relevant as reference architecture if IS1 includes human-readable analysis generation for retrieved families, but does not address core retrieval performance challenge.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
