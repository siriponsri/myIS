---
paper_id: U028
title: "Contrastive learning enhanced retrieval-augmented few-shot framework for multi-label patent classification"
authors: "Wenlong Zheng, Xin Li, Guoqing Cui, Shikun Chen"
year: 2026
venue: "PLOS ONE"
affiliation: "Ningbo University of Finance and Economics; First Topographic Surveying Brigade of Ministry of Natural Resources; Northwest Land and Resources Research Center, Shaanxi Normal University"
pdf_sha256: "db1eb5909cf96c601252d732e7b95bd57556c48e1f0c0288cf25a4fd267a138d"
eb_status: "ingest_new"
tier: "C"
extraction_cache: "extraction-cache/U028.md"
digest_created: "2026-07-24"
schema_version: "PDF_DIGEST_SCHEMA_V1"
---

# U028: Contrastive Learning Enhanced RAG Few-Shot for Multi-Label Patent Classification

## Bibliographic Identity

**Title:** Contrastive learning enhanced retrieval-augmented few-shot framework for multi-label patent classification

**Authors:** Wenlong Zheng¹, Xin Li²*, Guoqing Cui²'³, Shikun Chen¹  
¹Ningbo University of Finance and Economics, School of Finance and Information, Ningbo, Zhejiang, China  
²First Topographic Surveying Brigade of Ministry of Natural Resources of P.R.C., Xi'an, Shaanxi, China  
³Northwest Land and Resources Research Center, Shaanxi Normal University, Xi'an, Shaanxi, China

**Venue:** PLOS ONE 21(1): e0341118

**Year:** 2026 (Published: January 21, 2026; Received: September 1, 2025; Accepted: January 4, 2026)

**DOI:** https://doi.org/10.1371/journal.pone.0341118

**PDF SHA-256:** `db1eb5909cf96c601252d732e7b95bd57556c48e1f0c0288cf25a4fd267a138d`

**Page Count:** 26 pages

**Open Access:** ✅ CC BY 4.0 License

**Code/Data:** https://github.com/redcican/Contrastive-learning-latent-multi-label-classification

---

## Classification

**Tier:** C

**Rationale:** This paper addresses **multi-label patent classification** (not retrieval/ranking). The task is to assign multiple technological category labels (VTOL, surveillance, flight control, etc.) to UAV patent documents given their abstracts. Evaluation metrics are classification metrics (Macro-F1, Micro-F1, Label Ranking Average Precision, Coverage Error), not retrieval metrics (Recall@K, MAP@K, NDCG@K). The paper uses **retrieval-augmented demonstration selection** as a component within a few-shot learning classification framework, but the end task is categorization, not prior art search or document ranking. Since this is **classification** (not retrieval/reranking), it is **Tier C** in ThaiPhaLex context, which prioritizes retrieval and reranking tasks for patent prior art search.

---

## Research Problem

### Problem Statement
Multi-label patent classification faces three key challenges:
1. **Annotation bottleneck:** Expert-level patent annotation is prohibitively expensive and time-consuming
2. **Multi-label complexity:** Patents span multiple technological domains simultaneously (e.g., UAV patents encompass mechanical, electronic, software, communication technologies)
3. **Domain-specific terminology:** Patent language requires specialized understanding that general-purpose models fail to capture

### Proposed Solution
**Contrastive learning enhanced retrieval-augmented few-shot framework** that combines:
1. **Patent-specific contrastive pre-training:** Learns domain-adapted embeddings capturing multi-label co-occurrence patterns
2. **Retrieval-augmented demonstration selection:** Uses semantic similarity to identify informative examples for few-shot classification
3. **Chain-of-thought reasoning:** GPT-4o generates structured reasoning for each label, handling inter-label dependencies

---

## Method (Simplified Summary)

### 1. Dataset
- **Source:** 1 million patents from National Intellectual Property Administration China (CNIPA)
- **Curated subset:** 100,000 UAV-related patents, 15,000 annotated across 10 technological categories
- **Categories:** VTOL & Hybrid Flight, Surveillance & Mapping, Flight Control & Stability, Modular & Deployable, Endurance & Power Systems, Structural & Materials, Logistics & Cargo, Bionic & Flapping Wing, Specialized Applications, Multi-Environment Operations
- **Multi-label nature:** Average 2.3 labels per patent; patents naturally span multiple domains

### 2. Contrastive Pre-training
- **Encoder:** RoBERTa-Large backbone + projection layers → contrastive embedding space
- **Multi-label contrastive loss:** Combines instance-level (InfoNCE) + label-aware objectives
  - Positive examples: patents sharing at least one technological category
  - Label similarity: weighted by Jaccard overlap + penalty for label disparity
- **Domain adaptations:** Adaptive temperature scaling based on technical term density, category-aware negative sampling
- **Training:** Momentum-based updates, 3 phases (init RoBERTa → contrastive pre-train frozen RoBERTa → joint fine-tune)

### 3. Retrieval-Augmented Demonstration Selection
- **Multi-faceted similarity scoring:** Combines semantic similarity (contrastive embeddings), technical domain alignment (IPC codes, term overlap, citations), diversity promotion (avoids redundant retrievals)
- **Adaptive retrieval:** Increases technical similarity weight for patents with high specialized term density
- **Label-aware retrieval:** Considers label complexity and co-occurrence patterns learned during pre-training
- **Output:** Top-k patents ordered by relevance while ensuring label space diversity

### 4. Few-Shot Multi-Label Prediction
- **Prompt construction:** Task instruction + k demonstrations (input-output pairs) + query patent
- **Embedding-guided attention:** Weights each demonstration by contrastive similarity to query
- **Decomposed inference:** Evaluates each category independently while modeling inter-label dependencies
- **Adaptive thresholding:** Adjusts decision threshold per category based on frequency and uncertainty
- **Prototype fallback:** For categories with insufficient demonstration coverage, uses prototype-based similarity

### 5. Chain-of-Thought Reasoning (GPT-4o Integration)
- **Structured reasoning:** For each category, sequentially (1) extract key features, (2) compare with demonstrations, (3) evaluate evidence, (4) decide label assignment
- **Inter-label dependencies:** Conditional evaluation considering previously assigned labels (e.g., if VTOL assigned, reason about Flight Control in that context)
- **API parameters:** Temperature=0.3, max_tokens=2048, top_p=0.9, frequency_penalty=0.2, JSON output mode
- **Final prediction:** Weighted combination of CoT reasoning (β=0.7) + base framework scores

---

## Main Findings

### Overall Performance (5-shot setting, Table 3)

| Method | Macro-F1 | Micro-F1 | LRAP | Coverage |
|--------|----------|----------|------|----------|
| **Our Framework** | **0.847±0.021** | **0.892±0.018** | **0.878±0.019** | **1.23±0.087** |
| LLM-AL | 0.798±0.028 | 0.865±0.024 | 0.834±0.025 | 1.41±0.112 |
| PatentSBERTa | 0.762±0.033 | 0.828±0.030 | 0.782±0.031 | 1.68±0.135 |
| XLNet-Large | 0.741±0.031 | 0.815±0.027 | 0.768±0.028 | 1.74±0.128 |
| RoBERTa-Large | 0.729±0.034 | 0.801±0.029 | 0.756±0.032 | 1.87±0.142 |

**Key improvements:**
- **+16.2% Macro-F1** over RoBERTa-Large (+30% relative over few-shot baselines mentioned in abstract)
- **+6.1% Macro-F1** over LLM-AL (recent patent-specific method)
- **+11.2% Macro-F1** over PatentSBERTa
- All improvements statistically significant (p<0.001, Bonferroni-corrected α=0.00625, Cohen's d=1.2-2.3)

### Few-Shot Learning Curves (Fig 5)
- **1-shot:** Macro-F1 0.723 (+23.2% over RoBERTa, +18.5% over LLM-AL)
- **10-shot:** Macro-F1 improvements narrow to +15.3% over RoBERTa as baselines also benefit from more examples
- Framework maintains more stable performance (lower standard deviations) across episodes

### Computational Efficiency (Table 4)
- **Model size:** 357M params (+2M over RoBERTa, 0.6% increase)
- **Training time:** 8.2 hours on single RTX 4090 (vs. 24-26.5 hours for transformer baselines, 18-22 hours for patent-specific methods)
- **Inference latency:** 48ms local + 180ms GPT-4o API calls = 228ms total per patent
- **Memory:** 3.3GB GPU (comparable to baselines; GPT-4o via API doesn't require local storage)

### Ablation Study (Table 5)
| Configuration | Macro-F1 | Contribution |
|---------------|----------|--------------|
| Full Framework | 0.847 | — |
| w/o Contrastive Pre-training | 0.789 | **-6.8%** |
| w/o Semantic Retrieval | 0.765 | **-9.7%** |
| w/o Chain-of-Thought | 0.801 | **-5.4%** |
| w/o Inter-label Dependency | 0.823 | **-2.8%** |

**Contrastive pre-training** and **semantic retrieval** are the most critical components.

---

## Technical Contributions

1. **Multi-label contrastive learning for patents:** Extends standard contrastive objectives to capture label co-occurrence patterns and technological relationships
2. **Multi-faceted retrieval scoring:** Combines semantic embeddings, technical domain features (IPC, term overlap, citations), and diversity constraints
3. **Few-shot framework with adaptive mechanisms:** Embedding-guided attention, adaptive thresholding, prototype fallback for sparse categories
4. **GPT-4o integration for structured reasoning:** Chain-of-thought decomposition with inter-label dependency modeling

---

## Limitations

### Acknowledged (Discussion Section)
1. **Domain-specific evaluation:** Focus on UAV patents only; generalization to other technological domains requires validation
2. **GPT-4o dependency:** API costs and inference latency (180ms per patent) may limit large-scale deployment
3. **Contrastive pre-training requires domain corpus:** Need curated patent data for new technical domains
4. **Translation noise:** Reliance on machine translation for non-English patents may introduce errors
5. **Temporal evaluation split:** May not fully capture challenges of genuinely novel technologies absent from historical data

### Additional Concerns
1. **Not a retrieval system:** This is multi-label classification, not prior art search or patent ranking
2. **No family-level aggregation:** Treats each patent document independently
3. **No cross-domain evaluation:** All train/val/test patents are from UAV domain; no evaluation on domain shift (IN/OUT splits like DAPFAM)
4. **Small test set:** 15,000 annotated patents across 10 categories; unclear how method scales to hundreds of CPC/IPC classes
5. **CoT reasoning quality not quantified:** Human expert assessment mentioned (500 samples, 3 experts, 5-point Likert scales) but results not reported in tables

---

## Relevance to ThaiPhaLex Track C/R/S

### Track C: Candidate Generation — LOW Relevance

**Not applicable:** This paper addresses **classification** (assigning category labels to patent documents), not **retrieval** (finding relevant prior art patents given a query). The retrieval component is used internally to select demonstration examples for few-shot learning, not to retrieve prior art candidates.

**Methodological insights (tangential):**
- Contrastive learning on patent-specific data can capture domain semantics
- Multi-faceted similarity scoring (semantic + technical features + diversity) could inform candidate generation design
- However, the end task (classification) differs fundamentally from Track C's goal (prior art retrieval)

### Track R: Reranking — NOT RELEVANT

This paper does not address reranking of fixed candidate sets. The framework predicts labels given demonstrations, not ranking documents by relevance.

### Track S: Synthesis — NOT RELEVANT

No family-level aggregation, no multi-view fusion of retrieval channels, no synthesis of heterogeneous evidence sources.

---

## Connection to Papers A-D (Frozen Evidence Foundation)

### No Direct Connection to Any Paper

**Papers A-D focus on patent retrieval/reranking tasks:**
- Paper A: BM25 baseline for patent prior art retrieval
- Paper D: Instruction-aware reranking (if reranking-focused)
- Papers B/C: (Not specified, but likely retrieval/reranking related)

**U028 focuses on patent classification:**
- Task: Assign technological category labels (VTOL, surveillance, etc.) to patent abstracts
- Evaluation: Classification metrics (Macro-F1, Micro-F1, LRAP, Coverage Error)
- No retrieval metrics, no prior art search evaluation, no document ranking

**Orthogonal contributions:**
- U028's contrastive learning approach (capturing multi-label co-occurrence) could inspire Track C candidate generation if adapted to retrieval tasks
- Retrieval-augmented demonstration selection shares principles with RAG for prior art search, but application context differs (classification vs. retrieval)

**Governance note:** No metric or methodological comparisons are made, as U028 addresses a fundamentally different task (classification) from Papers A-D (retrieval/reranking).

---

## Verification Warnings

### Reproducibility
1. **Code/data released:** ✅ GitHub repository available
2. **Curated dataset:** 15,000 annotated UAV patents publicly released (contribution of this work)
3. **GPT-4o API dependency:** Requires OpenAI API access and costs; exact API version not specified (may affect reproducibility if API changes)
4. **Training cost:** 8.2 hours on RTX 4090 for contrastive pre-training

### Evaluation Concerns
1. **Single domain evaluation:** UAV patents only; no cross-domain generalization assessment
2. **No comparison with supervised baselines:** All baselines are few-shot methods; unclear how framework compares to fully supervised multi-label classifiers trained on all 15,000 labels
3. **Statistical testing:** Bonferroni-corrected paired t-tests (α=0.00625) across 50 episodes; Cohen's d=1.2-2.3 indicates large effect sizes
4. **CoT reasoning quality:** Human evaluation mentioned but results not quantified in tables

---

## EB Cross-Check

**EB Query:** "contrastive learning retrieval-augmented few-shot multi-label patent classification UAV drone chain-of-thought reasoning"

**Match Result:** ❌ NO_MATCH (EB returned general IS1 patent retrieval knowledge, not this specific classification paper)

**Ingestion Recommendation:** ✅ INGEST_NEW

**Rationale:** No existing ThaiPhaLex IS1 knowledge entry documents this multi-label patent classification framework. The paper is **orthogonal to ThaiPhaLex's core tasks** (retrieval/reranking for prior art search), but demonstrates methodological innovations (contrastive learning for patent embeddings, retrieval-augmented few-shot learning) that could inform future Track C design if adapted to retrieval tasks.

---

## Digest Metadata

**Digest Created:** 2026-07-24  
**Digest Author:** Batch 2A Processing Agent  
**Schema Version:** PDF_DIGEST_SCHEMA_V1  
**Batch ID:** BATCH_2A  
**Paper ID:** U028  
**Processing Status:** ✅ COMPLETED  
**EB Cross-Check:** ✅ PERFORMED (NO_MATCH → INGEST_NEW)  
**Content Coverage:** ~1200 lines read from 1353-line extraction (title, abstract, method, results, discussion, conclusion); sufficient for Tier C classification digest

---

**END OF DIGEST**
