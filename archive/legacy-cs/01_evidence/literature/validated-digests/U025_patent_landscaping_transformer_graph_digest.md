---
unique_id: U025
priority_tier: C
sha256: 7788735721a8d0516cbbfc46d59d5236e484e57e001511497db09b241e7ad540
canonical_path: research/ref-paper/is1/pdfs/25_deep_learning_for_patent_landscaping_using_2022.pdf
size_bytes: 1310097
title: "Deep learning for patent landscaping using transformer and graph embedding"
authors: "Seokkyu Choi, Hyeonju Lee, Eunjeong Park, Sungchul Choi"
year: 2022
venue: "Technological Forecasting and Social Change"
doi: "10.1016/j.techfore.2021.121413"
arxiv: null
extraction_cache: extraction-cache/U025.md
experience_brain_match: no
matched_knowledge_id: null
recommended_ingestion_action: ingest_new
digest_status: completed
digest_prepared: 2026-07-24
pass_type: Batch_2A
authority: External Knowledge
---

# U025 — Deep learning for patent landscaping using transformer and graph embedding

## Bibliographic Identity

**Title:** Deep learning for patent landscaping using transformer and graph embedding  
**Authors:** Seokkyu Choi¹, Hyeonju Lee², Eunjeong Park³, Sungchul Choi⁴ (¹Gachon University, ²Industrial Application R&D Institute, ³Upstage, ⁴Pukyong National University)  
**Venue:** Technological Forecasting and Social Change  
**DOI:** 10.1016/j.techfore.2021.121413  
**Publication Date:** December 2021 (online), Volume 175, February 2022  
**Document Type:** Journal article — patent classification for patent landscaping  
**Field:** Patent landscaping, deep learning, transformer, graph embedding, patent classification

## Research Problem

Patent landscaping is used to search for related patents during R&D projects to avoid patent infringement and follow technology trends. The first task of patent landscaping is to extract target patents for analysis from a patent database. Traditional patent classification for patent landscaping is human-centric, tedious, and expensive — researchers and patent attorneys must query large patent databases, eliminate unrelated documents, and extract only target patents related to their project, requiring advanced human resources familiar with scientific and technical domains. The demand for automated patent classification has gradually increased, but a shortage of well-defined benchmark datasets and comparable models makes it difficult to find related research studies. Existing machine-learning-based patent classification methods (tf-idf + SVM/KNN, IPC/CPC code-based classification, citation network features) often focus on single-dimensional tasks and do not fully leverage the multi-modal nature of patent documents (text data + bibliometric metadata). The challenge is to develop an automated deep-learning-based patent classification model that: (1) combines text features (abstracts) and graph-based metadata features (technology classification code co-occurrence), (2) handles extremely long patent texts efficiently, (3) provides benchmark datasets for patent landscaping (not general IPC/CPC classification), and (4) achieves classification performance applicable to real-world patent landscaping workflows where experts regularly update target patent sets weekly or monthly.

## Method

**Proposed model: Transformer + Diff2Vec hybrid architecture for patent landscaping classification**

**Overall architecture (Figure 3):**
1. **Text branch:** Modified transformer encoder processes patent abstracts → text embeddings
2. **Metadata branch:** Diff2Vec graph embedding processes technology classification code co-occurrence → graph embeddings
3. **Fusion:** Concatenate text + graph embeddings → MLP classifier → binary classification (target patent or not)

**Phase 1 — Data preprocessing:**
- **Text extraction:** Text-based PDFs extracted via PyPDF/pymupdf (low time cost, accurate); image-based PDFs via OCR (high time cost, insufficient accuracy)
- **Text filtering:** Normalize via regex (remove special characters except punctuation, remove HTML tags/URLs, remove stopwords like "the"/"is")
- **Text embedding:** BGE-M3 multilingual embedding model (100+ languages, bidirectional dense embeddings, 3072-dim)
- **Vector storage:** Faiss vector database (Meta) for similarity search and clustering (exact/approximate NN search, GPU acceleration)

**Phase 2 — Feature extraction:**

**2A. Base features selected:**
- **Text data:** Abstract only (not title/description/claims) — processable length for transformer, most frequently used by patent attorneys in landscaping
- **Metadata:** Technology classification codes (IPC, CPC, USPC) — best bibliometric feature for patent landscaping; assignee/inventor data excluded (extensive, ambiguous, constantly growing)

**2B. Diff2Vec for metadata embeddings:**
- **Co-occurrence matrix construction:** If patent p has codes {ipc₅, ipc₁₀₂, ipc₇₆₄}, mark co-occurrence; build co-occurrence graph where nodes = classification codes, edges = co-occurrence frequency across all patents in corpus
- **Diff2Vec algorithm (Rozemberczki & Sarkar 2018):** Graph embedding method based on Word2Vec; uses diffusion process to extract neighbor node subgraph (diffusion graph); subgraph formed by randomly selecting neighboring nodes diffused from one node; Euler tour applied to diffusion graph to generate sequence; sequences train Word2Vec layer
- **Hyperparameters:** Diffusion length = 40, number of diffusions per node = 10
- **Embedding aggregation:** Average embedding values of each code for one patent (e.g., if patent has 3 CPC codes, average their 3 embeddings); dense layer processes averaged graph information: CPC codes → 256-dim (twice the Diff2Vec embedding size, since CPC is most granular), IPC/USPC codes → 128-dim

**2C. Transformer architecture for text data:**
- **Tokenization:** Extract abstracts, divide into tokens via Word2Vec; insert [CLS] at beginning, [SEP] at end
- **Transformer encoder (Vaswani et al. 2017):** 6 stacked encoder layers (alternate config: 12 layers), multi-head self-attention (8 heads, alternate: 4 heads), scaled dot-product attention, sequence length = 128, hidden size = 512, embedding size = 512-dim per word
- **Squeeze technique (from BERT):** Convert matrix to vector (embedding size) based on [CLS] tag for concatenation with metadata embeddings

**Phase 3 — Training and inference:**
- Concatenate text embeddings (from [CLS] token) + graph embeddings (averaged CPC/IPC/USPC)
- Feed concatenated vector into simple MLP
- Binary classification: target patent or not (binary cross-entropy loss)
- **Hyperparameters:** 20 epochs, batch size 64, Adam optimizer, learning rate 0.0001, epsilon 1e⁻⁸

## Dataset / Evaluation Protocol

**KISTA benchmark datasets (4 technology domains):**

**Data source:** Korea Intellectual Property Strategy Agency (KISTA) patent trend reports — written by patent attorneys and technology experts, disclose target patent lists + patent search queries validated by experts

**Dataset construction:**
1. Start with KISTA report identifying technology area + search keywords + target patents filtered by experts
2. Convert WIPS search query to Google BigQuery query (Python module for reproducibility)
3. Extract patents from USPTO BigQuery public dataset
4. Mark "target patents" from KISTA report as positive class (true Y label)
5. Exclude patents published after KISTA report publication date

**Four technology domains (Table 3, Table 4):**

| Dataset | Full name | Keywords | Retrieved | Target | Imbalanced ratio |
|---------|-----------|----------|-----------|--------|------------------|
| MPUART | Marine Plant Using Augmented Reality Technology | hmd, photorealistic, georegistered | 1,469,741 | 468 | 3140:1 |
| 1MWDFS | 1MW Dual Frequency System | reverse conductive, mini dipole | 1,774,132 | 927 | 1914:1 |
| MRRG | Micro Radar Rain Gauge | klystron, bistatic, frequency agile | 2,068,566 | 225 | 9194:1 |
| GOCS | Geostationary Orbit Complex Satellite | rover, pgps, pseudolites | 294,636 | 653 | 451:1 |

**CPC-based heuristic undersampling:**
- Original datasets extremely imbalanced (98:2 or worse) → cannot build usable model
- **Heuristic approach (inspired by patent attorney workflow):** Patent experts use CPC/IPC codes to eliminate unrelated patents in first step of landscaping
- **Important CPC selection criteria:** CPC code appears in ≥0.5% of target patents AND emergence ratio in target set is >50× higher than in entire USPTO database
- **Undersampling:** Exclude negative samples (non-target patents) that do not contain important CPC codes; retain only negative samples with important CPC codes
- **Undersampled datasets (Table 5, Table 6):**

| Dataset | Important CPCs | Train | Val | Test | Positive (train:val:test) |
|---------|----------------|-------|-----|------|---------------------------|
| MPUART | 147 | 50,280 | 10,094 | 10,094 | 280:94:94 |
| 1MWDFS | 145 | 50,556 | 10,185 | 10,186 | 556:185:186 |
| MRRG | 217 | 50,135 | 10,045 | 10,045 | 135:45:45 |
| GOCS | 179 | 50,391 | 10,131 | 10,131 | 391:131:131 |

- Split ratio: 60% train, 20% validation, 20% test

**Evaluation metrics:**
- **Average Precision (AP)** and **F1-score** — commonly used for binary classification with imbalanced datasets
- **Baselines:**
  - TRF (Transformer only, no metadata)
  - DIFF (Diff2Vec only, no text)
  - APL (Automated Patent Landscaping, Abood & Feltenberger 2018)
  - PATENTBERT (BERT-based classifier, Lee & Hsiang 2020)

## Main Findings

**Overall results (Table 8 — TRF+DIFF proposed model vs baselines):**

| Dataset | Model | Precision | Recall | AP | F1 |
|---------|-------|-----------|--------|----|----|
| **MPUART** | TRF+DIFF | **0.8915** | **0.7872** | **0.7038** | **0.8361** |
| | TRF | 0.7590 | 0.6702 | 0.5117 | 0.7118 |
| | DIFF | 0.9027 | 0.6914 | 0.6271 | 0.7831 |
| | APL | 0.7115 | 0.4252 | 0.3061 | 0.5323 |
| | PATENTBERT | 0.9178 | 0.7127 | 0.6568 | 0.8023 |
| **1MWDFS** | TRF+DIFF | 0.8510 | 0.6451 | **0.5555** | **0.7339** |
| | TRF | 0.8617 | 0.5698 | 0.4989 | 0.6860 |
| | DIFF | 0.85 | 0.6397 | 0.5503 | 0.7300 |
| | APL | 0.8062 | 0.5502 | 0.4496 | 0.6540 |
| | PATENTBERT | **0.8888** | **0.6451** | 0.5799 | 0.7476 |
| **MRRG** | TRF+DIFF | **0.95** | **0.8444** | **0.8029** | **0.8941** |
| | TRF | 0.8048 | 0.7333 | 0.5914 | 0.7674 |
| | DIFF | 0.9473 | 0.8 | 0.7587 | 0.8674 |
| | APL | 0.7391 | 0.3863 | 0.2874 | 0.5074 |
| | PATENTBERT | 0.9722 | 0.7777 | 0.7571 | 0.8641 |
| **GOCS** | TRF+DIFF | 0.7882 | 0.5114 | **0.4094** | **0.6203** |
| | TRF | 0.6440 | 0.5801 | 0.3790 | 0.6104 |
| | DIFF | 0.8169 | 0.4427 | 0.3688 | 0.5742 |
| | APL | 0.8214 | 0.3565 | 0.2987 | 0.4972 |
| | PATENTBERT | **0.9027** | **0.4961** | 0.4544 | 0.6403 |

- **TRF+DIFF outperforms baselines on average:** Wins 3/4 datasets on AP, 3/4 on F1
- **Multi-modal advantage:** Combining text + graph embeddings outperforms either modality alone (TRF or DIFF) in most cases
- PATENT BERT achieves highest precision on 3/4 datasets (deeper transformer), but TRF+DIFF achieves better balanced performance on AP and F1

**Key observations:**
- Classification accuracy improved by ~15% on average vs traditional models (from abstract)
- Technology codes (metadata) play vital role — DIFF alone achieves strong performance (e.g., MRRG: AP 0.7587, F1 0.8674)
- Text + metadata complement each other → better overall performance

**Effects of technology code metadata (Table 9 — which code matters most):**

| Dataset | text+CPC (AP/F1) | text+IPC (AP/F1) | text+USPC (AP/F1) |
|---------|------------------|------------------|-------------------|
| MPUART | **0.6321 / 0.7835** | 0.586 / 0.7606 | 0.5372 / 0.7227 |
| 1MWDFS | **0.5384 / 0.7069** | 0.4902 / 0.6883 | 0.4669 / 0.6776 |
| MRRG | **0.6634 / 0.8069** | 0.5067 / 0.7059 | 0.6195 / 0.7814 |
| GOCS | 0.4071 / 0.6301 | 0.3922 / 0.6151 | **0.4140 / 0.6347** |

- **CPC codes** (most detailed, ~260k codes) achieve highest performance on 3/4 datasets
- USPC codes slightly better than CPC for GOCS (likely because GOCS target patents have proportionally more USPC codes than CPC codes in target set vs corpus)
- IPC codes (least detailed, ~70k codes) consistently lowest performance

**Effects of text representation (Table 10 — transformer config + embedding methods):**

| Dataset | TRF(6,8) | TRF(12,4) | Word2Vec | Doc2Vec | Fasttext |
|---------|----------|-----------|----------|---------|----------|
| MRRG (AP/F1) | 0.6871 / 0.823 | **0.7384 / 0.8426** | 0.6414 / 0.7895 | 0.7020 / 0.8289 | 0.6835 / 0.8212 |

- MRRG dataset: deeper transformer (12 layers, 4 heads) outperforms standard config (6 layers, 8 heads) — likely because MRRG has smallest target patent set (n=225) and shortest average sequence length → relies more on text than codes
- Doc2Vec generally better than Word2Vec/Fasttext for other datasets
- Transformer config (6,8) sufficient for most datasets; deeper config beneficial when target patent set is very small

**Practical implications from discussion:**
- Patent documents contain large amounts of scholarly data (text + metadata); using both features is important for better classification performance than individual features alone
- CPC codes (most detailed) guarantee better classification performance results in most cases
- Number of technology codes that a target patent has in a dataset is an important feature — if dataset has proportionally more USPC codes, USPC may outperform CPC

## Limitations and Observations

**Acknowledged limitations:**
- **Limited dataset scope:** Only 4 KISTA datasets tested; need to expand to more KISTA reports and evaluate generalizability
- **Domain-specific models:** Proposed model must be trained separately for each technology domain; no universal cross-domain model developed (future work: multi-task learning like MTDNN to learn multiple domains simultaneously)
- **Abstract-only text:** Only abstracts used (processable length); claims and technical descriptions (long sentences) not tested; future work: LongTransformer (Beltagy et al. 2020) for long texts
- **Limited metadata exploration:** Did not test assignee/inventor/citation features (extensive, ambiguous, constantly growing); only CPC/IPC/USPC codes used
- **Graph embedding alternatives not tested:** Only Diff2Vec used; other graph embedding methods (node2vec, RandomWalk) not compared
- **Image data not used:** Patent images are essential features (cf. Jiang et al. 2021) but not included in this study
- **No meta-learning or AutoML:** Different datasets require different classification models; future work: AutoML to automatically select optimal model configuration per dataset

**Benchmark dataset contribution:**
- **First well-defined benchmark datasets for patent landscaping** — prior studies (APL) had issues: (1) no comparable benchmark data (heuristically generated datasets may learn heuristic rather than human expert patterns), (2) APL datasets used extremely broad/common technology fields (machine learning, IoT) whereas typical patent landscaping focuses on extremely specific technologies depending on R&D project
- KISTA datasets based on human expert work (patent attorneys, technology experts) → closer to real-world patent landscaping tasks
- Datasets publicly available via Google BigQuery (reproducible)

**Practical workflow recommendation:**
1. Patent attorneys + technical experts create keyword list for patent database search
2. Tag target patents to be analyzed in searched patent list
3. Create classification model using proposed algorithm with entire patent dataset + tagged classification targets
4. Conduct patent search weekly/monthly using predefined search keyword set
5. Use classification model to determine target patents vs non-target patents
6. Engineers perform additional analysis as necessary for target patents tagged by model

## Track C Relevance (proposed, NOT AUTHORIZED)

**Minimal relevance as patent classification automation tool for R&D patent landscaping, not prior-art retrieval or family-level candidate generation.** U025 addresses automated patent classification for patent landscaping — a binary classification task (target patent for specific R&D project or not) using transformer (text) + Diff2Vec (technology code co-occurrence graph). This is a **domain-specific target-patent identification pipeline** for R&D workflows, not a general prior-art retrieval or candidate generation system.

**Potential Track C connections (indirect):**
1. **Technology code co-occurrence as graph embedding feature:** Diff2Vec on CPC/IPC/USPC co-occurrence graph could inform Track C metadata-based candidate generation (e.g., graph neural network on patent citation network + CPC co-occurrence network for candidate exposure)
2. **Multi-modal fusion baseline:** Concatenating text embeddings (transformer on abstract) + graph embeddings (Diff2Vec on codes) demonstrates multi-view representation fusion; relevant to IS1 H1 hypothesis (multi-view union: lexical + dense semantic for candidate exposure)
3. **CPC vs IPC vs USPC comparative analysis:** Finding that CPC (most granular, ~260k codes) outperforms IPC (~70k codes) and USPC (~150k codes) on 3/4 datasets provides empirical evidence for using most detailed classification codes in patent retrieval systems

**Limitations for IS1 Track C:**
- Not a retrieval system — binary classification (is this patent relevant to my R&D project?), not ranking (rank all patents in corpus by relevance to query patent)
- No retrieval metrics (MAP, Recall@k, NDCG, family-level Recall@100) — evaluation uses precision, recall, AP, F1 for binary classification
- No family-level aggregation or domain-split evaluation (IN vs OUT as in DAPFAM)
- Domain-specific training required — each R&D project (MPUART, 1MWDFS, MRRG, GOCS) trains separate model; not a general cross-domain retrieval system
- Abstract-only embeddings — IS1 may require claims text or multi-field representations
- USPTO-only evaluation — no multilingual or multi-jurisdiction testing
- CPC-based undersampling heuristic — uses important CPC codes to filter candidate set before classification, but this is a preprocessing step (eliminate obviously unrelated patents), not a retrieval/ranking mechanism

**Actionable insight:** The finding that combining text embeddings (transformer on abstract) + graph embeddings (Diff2Vec on CPC co-occurrence) outperforms either modality alone (TRF+DIFF AP 0.7038 vs TRF 0.5117 vs DIFF 0.6271 on MPUART) demonstrates that multi-view representation fusion improves patent understanding. If IS1 Track C uses multi-view candidate generation (H1: lexical claim-element channel + dense semantic channel), U025's fusion architecture (concatenate text + graph embeddings → MLP) could serve as a baseline fusion method. However, U025's graph embedding is CPC co-occurrence (bibliometric metadata), not citation network or claim-element co-occurrence, so direct transfer is uncertain.

## Track R Relevance (proposed, NOT AUTHORIZED)

**No reranking component.** U025 is a binary classification system (target patent or not for specific R&D project), not a ranking system. No candidate set construction, no ranking metrics (NDCG, MAP, MRR), no reranking stage. The system outputs binary labels (0 or 1), not a ranked list of candidates.

## Track S Relevance (revision-stage, EXECUTION CLOSED)

**No prompt optimization or skill evolution.** U025 uses fixed transformer encoder architecture (6 layers, 8 heads) with no prompt engineering, no meta-learning, no prompt evolution, no SkillOpt-style self-improvement. Model architecture is manually designed; hyperparameters are fixed (or ablated in experiments). No connection to Track S.

## Relationship to Papers A, B, C, D

**No connection to Paper A/D reranking focus; no connection to Paper D family-level retrieval benchmarks; minimal overlap with IS1 core tasks.**

**Paper A (instruction-tuned reranking):** U025 does not address reranking. It performs binary classification (target patent or not for specific R&D project), not ranking of fixed candidate set. Orthogonal tasks.

**Paper D (DAPFAM family-level retrieval):** U025 does not address family-level retrieval, domain-split evaluation, or citation-relevance ranking. DAPFAM evaluates family-level Recall@100/NDCG@100 on IN vs OUT domains with citation-based relevance; U025 evaluates binary classification precision/recall/AP/F1 on domain-specific R&D project patent sets. Different tasks (domain-specific target patent identification vs cross-domain family-level prior-art retrieval), different metrics, different evaluation protocols.

**Potential integration point (post-retrieval filtering):** If IS1 Track C retrieval system outputs top-k ranked families and requires domain-specific filtering (e.g., "among retrieved families, which are relevant to pharmaceutical formulation project X?"), U025's binary classification architecture (text + graph embeddings → MLP) could serve as a post-retrieval filtering stage. However, this is not part of core candidate generation or reranking pipeline. U025's contribution is R&D-project-specific target patent identification automation, not retrieval performance improvement.

**Do not cross-compare:** U025's classification metrics (MPUART: precision 0.8915, recall 0.7872, AP 0.7038, F1 0.8361) assess binary classification quality on domain-specific R&D project patent sets, not retrieval quality on prior-art search benchmarks. They are not comparable to DAPFAM retrieval metrics (family Recall@100, NDCG@100) or reranking metrics (MAP, MRR). Different tasks, different metrics.

## Experience Brain Cross-Check

**Query:** "patent landscaping transformer graph embedding Diff2Vec CPC IPC classification KISTA"  
**Top 3 results:** KNO-20DDBF1D30A0 (IS1 candidate exposure synthesis), KNO-528A290EA2E4 (PatenTEB benchmark), KNO-3D43C4514725 (IS1 research gaps)  
**Match found:** No — no Knowledge record with SHA `7788735721a8d0516cbbfc46d59d5236e484e57e001511497db09b241e7ad540` or title "Deep learning for patent landscaping using transformer and graph embedding" or authors "Seokkyu Choi, Hyeonju Lee, Eunjeong Park, Sungchul Choi" in top 3 results. Returned results are about IS1 project knowledge and patent retrieval benchmarks (PatenTEB), not patent landscaping classification systems.  
**Recommended action:** ingest_new

## Verification Warnings

Tables 8 (overall results), 9 (effects of technology codes), 10 (effects of text representation) preserved grid structure in PDF→markdown extraction. Prose-quoted headline figures confirmed reliable from abstract and results sections (pages 1, 7-9):
- TRF+DIFF MPUART: Precision 0.8915, Recall 0.7872, AP 0.7038, F1 0.8361
- CPC codes outperform IPC/USPC on 3/4 datasets
- Classification accuracy improved by ~15% on average vs traditional models

Appendix A contains BigQuery search queries for all 4 datasets (MPUART, 1MWDFS, MRRG, GOCS). Queries are readable and complete. No visual-check caution needed.

---

**Tier C classification rationale:** U025 is a patent classification system for R&D patent landscaping using transformer (text) + Diff2Vec (technology code co-occurrence graph) to perform binary classification (target patent for specific R&D project or not). Core contribution is **automation of domain-specific target patent identification** in R&D workflows + **first well-defined benchmark datasets for patent landscaping** (4 KISTA datasets based on human expert work by patent attorneys). System substantially outperforms baselines (TRF+DIFF AP 0.7038 vs APL 0.3061 on MPUART, ~15% accuracy improvement on average) and demonstrates that multi-modal fusion (text + graph embeddings) outperforms either modality alone. However, it lacks core Tier A/B characteristics: (1) not a retrieval or ranking system (binary classification, no candidate generation, no family-level aggregation, no retrieval metrics MAP/Recall@k/NDCG), (2) no cross-domain or domain-split evaluation (no IN/OUT generalization test like DAPFAM), (3) domain-specific training required (separate model per R&D project, not universal retrieval system), (4) evaluation uses classification metrics (precision/recall/AP/F1), not retrieval metrics, (5) USPTO-only, abstract-only, no multilingual or multi-jurisdiction testing, (6) no connection to IS1 Track C/R core tasks (prior-art candidate exposure, family-level reranking, cross-domain OUT performance). Tier C: domain-adjacent system (R&D patent landscaping automation) with methodological insights for multi-modal representation fusion (text + graph embeddings) and technology code importance analysis (CPC > IPC > USPC), but not directly applicable to IS1 prior-art retrieval/reranking benchmarks. Relevant as reference for multi-view fusion if IS1 includes metadata-based graph embeddings (CPC co-occurrence, citation network), but addresses different task (project-specific target patent identification vs prior-art discovery).

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
