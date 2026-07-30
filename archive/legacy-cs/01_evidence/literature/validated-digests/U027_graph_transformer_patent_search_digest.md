---
paper_id: U027
title: "Efficient Patent Searching Using Graph Transformers"
authors: "Krzysztof Daniell, Igor Buzhinsky, Sebastian Björkqvist"
year: 2025
venue: "PatentSemTech'25: 6th Workshop on Patent Text Mining and Semantic Technologies"
affiliation: "IPRally Technologies Oy, Helsinki, Finland"
pdf_sha256: "5924910b08d56a638904285d6ec44a2f2490c0704ed57bfd694e086863ef893e"
eb_status: "ingest_new"
tier: "B"
extraction_cache: "extraction-cache/U027.md"
digest_created: "2026-07-24"
schema_version: "PDF_DIGEST_SCHEMA_V1"
---

# U027: Efficient Patent Searching Using Graph Transformers

## Bibliographic Identity

**Title:** Efficient Patent Searching Using Graph Transformers

**Authors:** Krzysztof Daniell¹, Igor Buzhinsky¹, Sebastian Björkqvist¹  
¹IPRally Technologies Oy, Helsinki, Finland

**Venue:** PatentSemTech'25: 6th Workshop on Patent Text Mining and Semantic Technologies

**Year:** 2025

**DOI/URL:** Not provided in paper

**PDF SHA-256:** `5924910b08d56a638904285d6ec44a2f2490c0704ed57bfd694e086863ef893e`

**Page Count:** 11 pages (including references)

---

## Research Problem

### Problem Statement
Finding relevant prior art is crucial for deciding whether to file a new patent application or invalidate an existing patent. Traditional Boolean search requires substantial domain expertise and multiple iterations. Machine learning approaches (TF-IDF, word embeddings, BERT, GPT-2) have been explored, but processing full patent texts with Transformer models is computationally expensive due to long document lengths.

### Motivation
Patent documents are lengthy (often exceeding typical Transformer context windows), but the core inventive concept can be represented more compactly as a **graph of features and their relationships**. By converting patents to invention graphs, the authors aim to:
1. **Reduce computational overhead** compared to full-text Transformer processing
2. **Capture domain-specific similarity** beyond text-based matching using examiner citations as training signals
3. **Emulate professional patent examiner workflows** who identify core features and their interrelationships

### Proposed Solution
**Graph Transformer-based dense retrieval** where each invention is represented as a graph:
- **Nodes:** Key features of the invention (e.g., "snowthrower", "motor", "auger") or relationship descriptions (e.g., "frame for connecting handle device and auger housing")
- **Edges:** Hierarchical relationships (part-of/meronym, example-of/hyponym) and functional relationships (how features interoperate)
- **Model:** Graph Transformer with sparse attention (only on graph edges), trained using patent examiner citations (X/Y/A categories) as relevance signals

---

## Method

### 1. Graph Construction (Section 3.1)

**Input:** Patent document (claims and/or description)

**Process:**
1. **Linguistic analysis** using NLP to detect features of the invention
2. **Hand-crafted rules** to identify relationships (e.g., terms like "comprising", "connecting", "containing")
3. **Graph generation:** Three graph types per document:
   - **First claim graph:** Only the first independent claim
   - **All claims graph:** All claims
   - **Description graph:** Claims + full description

**Example graph** (from US20170152638A1):
```
A snowthrower, comprising:
  ├─ a motor
  ├─ an auger driven by the motor to rotate
  ├─ a handle device for a user to operate
  ├─ an auger housing for containing the auger
  └─ a frame for connecting the handle device and the auger housing
     wherein the auger housing is made of at least two different materials
```

Each node captures a feature or relationship phrase; edges encode hierarchical and functional dependencies.

### 2. Model Architecture (Section 3.2)

**Stage 1: Node Embedding Initialization (3.2.1)**
- Tokenize each node's text sequence using BPE tokenizer trained on patent documents
- Pre-train token embeddings with FastText for faster convergence
- Apply **SWEM (Simple Word-Embedding-based Model):** mean-pooling + max-pooling + linear projection to create node embeddings

**Stage 2: Graph Transformer Layers (3.2.2)**
- **Sparse attention:** Attention only over edges in the invention graph (not full pairwise attention)
- **Query-Key normalization** for training stability
- **Pre-Layer Norm** architecture for consistent gradient flow
- **GEGLU (Gated Linear Units with GELU)** in feed-forward sublayers
- Multiple layers refine node representations while preserving computational efficiency

**Stage 3: Pooling (3.2.3)**
- Assign each node a learned importance weight
- Graph embedding = weighted sum of all node embeddings (emphasizes most relevant nodes)

**Stage 4: Dimensionality Reduction (3.2.4)**
- **Densely-gated Mixture of Experts (MoE)** layer projects graph embedding to lower dimension (2048 → 150)

**Final output:** 
- **Base stage:** 2048-dim vector (156M params)
- **Dimensionality reduction stage:** 150-dim vector (161M params total)

### 3. Training Data (Section 3.3)

**Source:** Patent examiner citations from >40 jurisdictions (90% from US/EP/WO/JP/CN)
- **Total:** ~31.7M citations from ~8.7M applications and ~14.2M cited documents
- **Citation categories:**
  - **X:** Novelty-destroying prior art
  - **A:** Relevant but does not destroy novelty
  - **Y:** Obviousness (invention follows in obvious way from combination)

**Citation pairs:**
- **Citing graph:** Typically first claim graph
- **Cited graph:** Typically description graph

**Data augmentation / regularization:**
1. **Trivial citations:** Artificial citations from first claim graph → description graph of same patent (for training stability)
2. **Graph type augmentation:** With prob=0.4, randomly replace citing or cited graph (not both) with all-claims graph
3. **Node dropout:** Randomly drop nodes with probability dependent on graph size
4. **Embedding dropout:** Regular dropout on token embeddings

**Family-level exclusion:** Training/validation/test sets are split at document level with no citation crossing sets; all documents of same patent family excluded together.

### 4. Training Procedure (Section 3.4)

**Framework:** PyTorch + DGL (Deep Graph Library)

**Loss function:** Triplet loss with different margins for different citation categories

**Optimizer:** AdamW with learning rate reduction on plateaus

**Negative mining:** Online hard negative mining over current batch

**Batch creation:**
- Dynamic batch size accounting for graph sizes: 2100–2260 anchors, 900–960 positives on average
- Samples grouped by IPC class to create harder batches

**Two training stages:**
1. **Base stage:** Output dim=2048, trained for ~185k updates (12 epochs) over 4.6 days on 8× L4 GPUs
2. **Dimensionality reduction stage:** Fine-tune base + add MoE layer → output dim=150

**Stopping criterion:** Training stops when top-3 X-citation Recall@3 does not improve for 3 consecutive evaluation runs (evaluated 3× per epoch)

---

## Dataset / Evaluation Protocol

### Test Set (Section 4.1)
- **Search candidate documents:** ~161,000 documents
- **Queries:** ~96,000 queries (first independent claim of application)
- Each query cites one candidate document as **X citation** (novelty-destroying)
- **Retrieval task:** Document-level dense retrieval (not passage retrieval)
- Non-English documents machine-translated to English before processing

### Evaluation Metrics
1. **Recall@3:** How often the X-cited document appears in top-3 results (primary metric)
2. **nDCG@150:** Normalized Discounted Cumulative Gain over top-150 results (auxiliary metric)

### Compared Baselines (Section 4.2–4.4)
1. **Patent-specific dense retrievers:**
   - PaECTER (mpi-inno-comp/paecter): 345M params, 1024-dim, trained on patent titles+abstracts, X/Y/I/A citations
2. **General-purpose text embedding models:**
   - Stella (NovaSearch/stella_en_400M_v5): 435M params, 1024-dim
   - KaLM (HIT-TMG/KaLM-embedding-multilingual-mini-v1): 494M params, 896-dim
   - GTE-ModernBert (Alibaba-NLP/gte-modernbert-base): 149M params, 768-dim
3. **Sparse retriever:**
   - Okapi BM25 (k₁=2.7, b=1.15, tuned on 1,000 validation citations)
4. **Previous Tree-LSTM approach:**
   - Tree-LSTM base stage: 20M params, 600-dim (same training data, re-trained for fair comparison)

**Sequence length tuning:** Text embedding models' sequence lengths tuned on validation set for best Recall@3; PaECTER and Stella applied on multiple chunks and averaged embeddings.

---

## Main Findings

### Retrieval Performance (Table 1)

| Approach | Seq. len. | Output dim | Model size | Recall@3 | nDCG@150 |
|----------|-----------|------------|------------|----------|----------|
| **Our, base stage** | N/A | 2048 | 156M | **0.4046** | **0.5564** |
| **Our, dim. reduction** | N/A | 150 | 161M | **0.3861** | **0.5372** |
| Tree-LSTM, base stage | N/A | 600 | 20M | 0.3151 | 0.4685 |
| PaECTER | 4×512 | 1024 | 345M | 0.2798 | 0.4341 |
| Stella | 3×2048 | 1024 | 435M | 0.2734 | 0.4134 |
| KaLM | 1×4096 | 896 | 494M | 0.2211 | 0.3527 |
| GTE-ModernBert | 1×4096 | 768 | 149M | 0.2003 | 0.3231 |
| Okapi BM25 | N/A | N/A | N/A | 0.1866 | 0.2874 |

**Key results:**
1. **Graph Transformer base stage** achieves Recall@3=0.4046, **+44.6% relative improvement** over PaECTER (0.2798) and **+117% over BM25** (0.1866)
2. **Dimensionality reduction stage** (150-dim) achieves Recall@3=0.3861, still **+38.0% over PaECTER** with much smaller vector storage (150-dim vs 1024-dim = 85% reduction)
3. **Tree-LSTM baseline** (authors' previous work, 20M params) achieves 0.3151 Recall@3, showing Graph Transformer improves over Tree-LSTM by **+28.4% relative**
4. **All text embedding models** (including patent-specific PaECTER) substantially underperform Graph Transformer, despite similar or larger model sizes
5. **BM25** performs worst, showing deep learning methods significantly outperform lexical matching for this task

### Computational Efficiency
- **Graph representation** drastically reduces input size vs. full text (graphs are much smaller than raw text while preserving core features)
- **Sparse attention** (only on graph edges) avoids O(n²) full attention overhead
- Text embedding models with seq_len=512 can fit only **45-65 positives per batch** (GPU memory constraint), vs. **900-960 positives for Graph Transformer** (**13× larger batch size** critical for online hard negative mining)
- Training time: ~4.6 days on 8× L4 GPUs for both stages combined (~185k updates, 12 epochs)

---

## Technical Contributions

### Novel Elements
1. **Graph-based patent representation for dense retrieval:** First work to systematically convert patent documents to invention graphs (features + relationships) and use Graph Transformers for prior art search
2. **Sparse attention on invention graphs:** Restricts attention to actual edges (not full node pairs), reducing computational cost while preserving long-range dependencies
3. **Integrated graph construction + dense retrieval pipeline:** Hand-crafted linguistic rules extract features/relationships → Graph Transformer embeds → triplet loss training on examiner citations
4. **Three graph granularities:** First claim, all claims, description—allows trading off coverage vs. computational cost
5. **Dimensionality reduction stage with MoE:** Fine-tuning base model + MoE layer achieves 85% smaller vectors (150-dim vs 2048-dim) with only 4.6% relative Recall@3 loss (0.3861 vs 0.4046)

### Algorithmic Insights
- **Concept-level representation** (nodes as key features, not tokens) parallels Large Concept Models, reducing overhead while preserving essential relationships
- **Examiner citations as training signal** teach the model domain-specific similarity beyond surface text matching (e.g., different terminology for same inventive concept)
- **Large batch size with online hard negative mining** is critical for high recall—Graph Transformer's smaller input size (graphs vs. full text) enables 13× larger batches than text embedding models
- **Trivial citations** (first claim graph → description graph of same patent) stabilize training, likely by providing easy positives that anchor the embedding space

---

## Limitations and Future Work

### Acknowledged Limitations (Section 4.5)
1. **Comparison constraints:**
   - Text embedding models (except PaECTER) were not trained for patent retrieval, though Stella/KaLM are general-purpose SOTA models
   - Cannot fine-tune text embedding models with equally large batches due to memory constraints (45-65 vs 900-960 positives per batch)
   - Evaluation focuses on first-stage retrieval efficiency/effectiveness; **no comparison with re-ranking models** (cross-encoders) which are computationally intensive

2. **Graph construction:** 
   - Relies on **hand-crafted rules** to extract features and relationships (not end-to-end learned)
   - Rule quality depends on linguistic analysis accuracy and coverage of relationship patterns
   - No details provided on rule robustness across different patent domains or languages

3. **Language limitations:**
   - Non-English documents machine-translated to English before processing
   - No evaluation of multilingual retrieval quality or translation impact

### Additional Limitations (Not Discussed in Paper)
1. **No family-level aggregation:** Retrieves individual documents, not patent families (multiple applications for same invention)
2. **Single-jurisdiction evaluation:** Test set composition (US/EP/WO/JP/CN mix) not detailed; may not generalize to underrepresented jurisdictions
3. **Citation category weighting:** Paper mentions "different margins for different citation categories" but does not specify margin values or ablation study on this design choice
4. **Graph size impact:** No analysis of how graph size (number of nodes/edges) correlates with retrieval performance or computational cost
5. **Domain coverage:** No breakdown of Recall@3 by IPC class/technology domain; may perform unevenly across domains

---

## Relevance to Track C/R/S (ThaiPhaLex Candidate Generation, Reranking, Synthesis)

### Track C: Candidate Generation — HIGH Relevance

**Direct applicability:**
- **Graph-based representation** offers a **structured intermediate representation** between raw text and dense vectors, potentially useful for **claim-feature-based candidate expansion** in ThaiPhaLex Track C
- **Sparse attention on graphs** (not full text) provides computational efficiency for processing long patent documents, which is a key Track C constraint
- **Examiner citation training** demonstrates that **expert curation signals** (X/A/Y categories) can train models to capture domain-specific relevance—analogous to ThaiPhaLex using pharmaceutical domain expertise for candidate generation

**Transferability concerns:**
1. **Graph construction pipeline is proprietary:** Hand-crafted rules and NLP pipeline details are not open-sourced; cannot directly reproduce without reimplementation
2. **No passage-level retrieval:** Graph Transformer retrieves whole documents, not passages/claims; ThaiPhaLex Track C may benefit from finer-grained claim-level candidate generation
3. **No multi-view fusion:** Graph Transformer is a single-channel dense retriever; Track C hypothesis prioritizes **multi-view candidate generation** (lexical claim elements + dense semantic + structured query expansion)—Graph Transformer does not address hybrid/fusion approaches

### Track R: Reranking — LOW Relevance

**Not applicable:**
- Graph Transformer is a **first-stage dense retriever**, not a reranker
- Paper explicitly states evaluation focuses on first-stage retrieval; **no comparison with re-ranking models** like cross-encoders
- Track R focuses on instruction-aware reranking of fixed candidate sets; Graph Transformer does not address this

### Track S: Synthesis — MEDIUM Relevance

**Methodological insights:**
1. **Concept-level representation** (graph nodes as features/phrases, not tokens) aligns with Track S goal of **synthesizing multi-source signals** into coherent candidate sets
2. **Hierarchical + functional relationships** in graphs mirror Track S's need to **aggregate across patent families** and **relate claims to descriptions**
3. **Dimensionality reduction with MoE** (150-dim vectors) suggests a path for **efficient vector storage** in Track S's multi-view candidate aggregation pipeline

**Limitations:**
- No explicit family-level aggregation or synthesis across multiple retrieved documents
- No fusion of graph-based retrieval with other modalities (lexical, structured queries, citation networks)

---

## Connection to Papers A-D (Frozen Evidence Foundation)

### Relationship to Paper A (BM25 Baseline)
**Direct comparison:** Graph Transformer base stage (Recall@3=0.4046) outperforms BM25 (0.1866) by **+117% relative** on the authors' test set. However, this comparison is on **prior art retrieval task with examiner X citations**, not ThaiPhaLex's pharmaceutical patent search task. **Domain, corpus, and evaluation protocol differ**, so absolute numbers cannot be transferred to ThaiPhaLex. The comparison validates that **dense retrieval can substantially beat lexical baselines** in patent domain, supporting Paper A's findings.

### Relationship to Paper B
**No direct connection:** Paper B's specific research problem is not specified in this digest context. If Paper B addresses passage-level retrieval or claim-level ranking, Graph Transformer's document-level approach does not directly intersect.

### Relationship to Paper C
**No direct connection:** Paper C's focus is not specified. If Paper C addresses query expansion or structured retrieval, Graph Transformer's graph construction (feature extraction via hand-crafted rules) offers a complementary structured representation approach, but no explicit connection exists.

### Relationship to Paper D (Instruction-Aware Reranking)
**Orthogonal:** Paper D (if it addresses reranking) operates on fixed candidate sets, while Graph Transformer is a first-stage retriever that generates candidate sets. The two are complementary in a multi-stage pipeline (Graph Transformer retrieves, Paper D's reranker reorders), but Graph Transformer does not test reranking hypotheses.

**Governance note:** Papers A-D relationships are observational only. No claims are made about metric transferability, reproducibility on ThaiPhaLex corpus, or authorization to integrate Graph Transformer into ThaiPhaLex system without explicit Owner approval.

---

## Verification Warnings

### Reproducibility Concerns
1. **Graph construction pipeline not open-sourced:** Hand-crafted rules, NLP models, and graph generation code are proprietary to IPRally Technologies Oy. Cannot reproduce without substantial reimplementation effort.
2. **Training data not publicly available:** 31.7M examiner citations from 40+ jurisdictions are not released; cannot retrain or validate model on custom patent corpus.
3. **No public model release:** Unlike PaECTER or text embedding models, Graph Transformer model weights are not publicly available (as of paper publication).
4. **Hyperparameters partially specified:** Some details missing (e.g., triplet loss margin values per citation category, exact MoE architecture, node dropout probabilities as function of graph size).

### Evaluation Limitations
1. **Single test set:** Evaluation on authors' proprietary test set (~161k documents, ~96k queries); no BEIR benchmark or CLEF-IP comparison to enable cross-study comparisons.
2. **No domain-stratified evaluation:** No breakdown of Recall@3 by IPC class or technology domain; cannot assess cross-domain generalization or identify domain-specific weaknesses.
3. **No ablation studies:** Paper does not ablate graph types (first claim vs. all claims vs. description), node dropout rates, graph augmentation strategies, or citation category weighting—cannot isolate which design choices drive performance gains.
4. **Baseline fairness concerns:** Text embedding models were not trained with equally large batches (45-65 vs 900-960 positives) due to memory constraints; this may understate their potential performance if trained with hard negative mining at scale.

### Generalization Risks
1. **Examiner citation bias:** Model trained on examiner citations may not generalize to **user search intent** (what practitioners actually search for vs. what examiners cite in office actions).
2. **Jurisdiction imbalance:** 90% of training citations from US/EP/WO/JP/CN; may not generalize to patents from other jurisdictions (e.g., TH, IN, BR, RU) with different citation practices.
3. **Temporal drift:** Training data span not specified; if citations are from older patents, model may not capture recent technological terminology or domains (e.g., AI/ML patents filed post-2020).
4. **Language model dependence:** Machine translation quality impacts non-English patents; no evaluation of translation-induced errors or multilingual embedding quality.

---

## EB Cross-Check

**EB Query:** "Graph Transformer patent search invention graphs features relationships IPRally examiner citations dense retrieval"

**Match Result:** ❌ NO_MATCH (EB returned general patent retrieval knowledge synthesis and PatenTEB/DAPFAM references, but no IPRally Graph Transformer-specific entry)

**Ingestion Recommendation:** ✅ INGEST_NEW

**Rationale:** No existing ThaiPhaLex IS1 knowledge entry documents IPRally's Graph Transformer approach. Returned EB results include:
- KNO-20DDBF1D30A0: IS1 RUN-003 candidate exposure synthesis (multi-view retrieval hypothesis, not Graph Transformer)
- KNO-528A290EA2E4: PatenTEB benchmark (embedding evaluation, not invention graphs)
- KNO-5449A7642CF9: IS1 literature matrix (general references, no IPRally entry)

This paper offers a **novel graph-based dense retrieval architecture** not previously documented in ThaiPhaLex knowledge base. The approach is **transferable as a candidate generation method** (Track C), though **proprietary graph construction pipeline** limits direct reproducibility. Ingestion as new knowledge is recommended to inform Track C multi-view candidate generation design.

---

## Tier Classification Rationale

**Tier: B**

**Justification:**
This paper presents a complete patent prior art retrieval system with quantitative evaluation on a large test set (~161k documents, ~96k queries), achieving Recall@3=0.4046 on novelty-destroying (X) citation retrieval. The evaluation uses examiner citations as ground truth and compares against multiple baselines (PaECTER, Stella, KaLM, GTE-ModernBert, BM25, Tree-LSTM). Metrics are standard retrieval metrics (Recall@K, nDCG@K).

**However, it is classified as Tier B (not Tier A) due to:**
1. **Proprietary evaluation corpus:** Test set is not publicly available; cannot reproduce or validate on standard benchmarks (BEIR, CLEF-IP, DAPFAM)
2. **No family-level aggregation:** Retrieves individual documents, not patent families—ThaiPhaLex Tier A criterion requires family-level evaluation
3. **No domain-stratified evaluation:** Does not report cross-domain IN/OUT splits or per-IPC performance—cannot assess cross-domain generalization gap, a key ThaiPhaLex concern
4. **Single retrieval method:** Graph Transformer is evaluated in isolation; no hybrid/multi-view fusion experiments (e.g., combining graph-based + lexical + dense text retrieval)
5. **Graph construction not reproducible:** Hand-crafted rules and NLP pipeline are proprietary; cannot independently validate graph quality or transfer to Thai pharmaceutical patents

**Tier B characteristics met:**
- Quantitative retrieval metrics (Recall@3, nDCG@150) on large-scale task
- Substantial baseline comparisons (6 models + BM25 + Tree-LSTM)
- Novel architecture (Graph Transformer on invention graphs) with demonstrated improvements (+44.6% over PaECTER, +117% over BM25)
- Transferable methodology (concept-level representation, sparse attention, examiner citation training)

**Why not Tier A:**
- Lacks public benchmark evaluation (DAPFAM, CLEF-IP with domain splits)
- No family-level retrieval or aggregation
- Proprietary test set prevents cross-study validation
- Missing ablation studies and domain-stratified analysis

**Why not Tier C:**
- Not a classification, clustering, or summarization task—this is core patent retrieval
- Comprehensive quantitative evaluation (not qualitative case studies)
- Multiple strong baselines compared

**Conclusion:** Tier B—strong retrieval methodology with quantitative evidence, but missing family-level evaluation, domain-split analysis, and public benchmark validation required for Tier A in ThaiPhaLex context.

---

## Digest Metadata

**Digest Created:** 2026-07-24  
**Digest Author:** Batch 2A Processing Agent  
**Schema Version:** PDF_DIGEST_SCHEMA_V1  
**Batch ID:** BATCH_2A  
**Paper ID:** U027  
**Processing Status:** ✅ COMPLETED  
**EB Cross-Check:** ✅ PERFORMED (NO_MATCH → INGEST_NEW)

---

**END OF DIGEST**
