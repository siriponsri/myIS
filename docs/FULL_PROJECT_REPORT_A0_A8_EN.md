# Full Project Report: Retriever-Conditioned Document Representation for Cross-Domain Patent-Family Retrieval

**Coverage:** Complete research program from A0 through A8

**Evidence cutoff:** 24 August 2026

**Document type:** Full technical research report based on verified aggregate evidence

**Project status:** Scientific execution, post-confirmatory analysis, and publication-package quality control complete; submission authorized but not yet performed

> This report is self-contained. It does not cite local file locations, execution identifiers, integrity hashes, protected query membership, relevance judgments, rankings, or per-query outcomes. The labels A0-A8 are retained only to preserve the requested chronological structure. Internal workflow terminology is replaced with ordinary research language wherever possible.

---

## Abstract

Cross-domain prior-art retrieval is difficult because patent documents are long, structurally heterogeneous, duplicated across family members, and written in both technical and legal language. Relevant inventions in different technical domains may also describe similar mechanisms using dissimilar terminology. A retrieval system therefore does not score an invention in the abstract; it scores a particular representation of that invention. Field selection, field order, segmentation, overlap, truncation, view construction, and family-level aggregation determine what evidence the retriever can access.

This study investigates whether the document representation should be selected conditional on the frozen retrieval system rather than treated as universal preprocessing. Five retrieval systems were examined: BM25, BGE-M3, PatEmbed-large, Arctic Embed M v2.0, and Qwen3 Embedding 0.6B. Model weights, tokenizer behavior, pooling, normalization, similarity, prompts, evaluation code, data partitions, and decision rules were fixed before measurement. Only deterministic document construction was varied. The evaluation used a family-level patent benchmark with 1,247 query families, 45,336 target families, and 49,869 judged relations. The protocol separated engineering readiness, development, one-time selection, one-time confirmation, full-benchmark characterization, and post-confirmatory diagnosis.

Development results were heterogeneous. The best document representation differed by retriever; transferred representations did not retain a consistent source advantage; and adding more retrieval systems did not monotonically improve quality. A constrained adaptive composition procedure generated 12 proposals but only one distinct executable behavior, revealing a flat optimization surface rather than a hidden multi-system gain.

One sealed 125-query selection exposure fixed two systems for an 872-query confirmation. Both completed all 872 queries with deterministic output and zero failures. The selected research system achieved cross-domain Recall@100 of 0.442476 versus 0.331097 for the frozen static comparator. The paired difference was 0.111379 with a 95% bootstrap confidence interval of 0.102294-0.120438. It recorded 619 wins, 158 ties, and 95 losses. Cross-domain nDCG@100 increased from 0.279253 to 0.365595, a paired difference of 0.086342 with a 95% confidence interval of 0.078673-0.094077. Median latency and throughput favored the research system, while p99 latency favored the comparator, preventing an unqualified efficiency claim.

The confirmed system was then applied unchanged to the complete benchmark. It processed all 45,336 target families and all 1,247 queries to depth 200 with no failures. In the strict cross-domain population, only 796 of 5,193 relevant family pairs appeared in ranks 1-100, another 332 appeared only in ranks 101-200, and 4,065 were absent from the Top-200 pool. Perfect ordering of the existing pool would raise cross-domain Recall@100 from 0.188450 to at most 0.260167, an analytical within-pool headroom of 0.071717. The remaining error is therefore not only an ordering problem; most relevant cross-domain pairs were never exposed to a downstream ranker.

The study supports a bounded conclusion: document representation is part of the retrieval configuration, and a complete system selected through retriever-conditioned representation research can yield a confirmed improvement under a frozen protocol. Because the two confirmed systems differed in multiple frozen bindings, the result does not isolate representation as the sole cause. It also does not establish universal superiority, legal validity, infringement, freedom-to-operate, commercial deployability, or the effectiveness of an unimplemented reranker. The strongest confirmed model is subject to a research/non-commercial license boundary. The resulting manuscript and reproducibility package passed internal quality checks and received submission authorization, but no journal upload or submission had occurred by the evidence cutoff.

**Keywords:** patent retrieval; patent families; cross-domain retrieval; document representation; passage segmentation; rank fusion; Recall; nDCG; candidate exposure; reproducible evaluation

---

## 1. Introduction

### 1.1 Research Context

Patent retrieval supports prior-art search, technology landscaping, competitive intelligence, and examination workflows. Unlike short web documents, patents distribute meaning across titles, abstracts, descriptions, and claims. Titles may be too brief to discriminate inventions. Abstracts summarize but omit details. Descriptions contain broad technical context, repeated embodiments, and extensive procedural language. Claims compress legal scope into highly structured sentences. Multiple publications may also belong to the same patent family and describe substantially the same invention.

These properties make retrieval quality sensitive to document construction. A system may index the complete title-abstract-claims text as one unit, omit claims to reduce noise and computation, use the first independent claim as a concise technical-legal anchor, split long text into overlapping passages, or score multiple section-specific views and aggregate them at family level. Each choice changes the evidence presented to the retriever.

Cross-domain retrieval creates an additional challenge. A query and its relevant target may arise in different technical fields and therefore use different vocabularies for related mechanisms. Lexical systems can recover exact technical terms but may miss semantic equivalence. Dense systems can bridge vocabulary variation but depend on their training domain, input conventions, context length, pooling, and representation geometry. A representation that works well for one retrieval system may therefore fail for another.

### 1.2 Core Problem

Many retrieval evaluations choose a single document representation before comparing retrievers. This practice treats preprocessing as neutral. The present study challenges that assumption. Its core proposition is that a retrieval result is produced jointly by:

1. the frozen retrieval system;
2. the deterministic document representation;
3. the family-level aggregation rule;
4. the evaluation population and metric.

If this proposition is correct, model comparisons that omit representation details may conflate model quality with document construction. Conversely, optimizing a representation without a protected confirmation protocol may create another route for development-set overfitting.

### 1.3 Research Questions

The study addresses six questions.

1. Does changing the deterministic representation improve a fixed retriever over its static reference representation?
2. Are useful representations retriever-specific, or does one representation transfer reliably across retrieval systems?
3. Do different retrieval systems recover complementary relevant patent families under domain shift?
4. Can a constrained combination of systems improve the quality-latency-cost trade-off over the strongest single system?
5. Does the selected configuration retain its advantage on a sealed confirmatory population that was not used for development?
6. After confirmation, is remaining error primarily caused by ordering within the candidate pool or by failure to retrieve relevant candidates at all?

### 1.4 Objectives

The research objectives were to:

- establish a reproducible and protected experimental foundation before scientific measurement;
- compare five frozen retrieval systems under five shared deterministic document representations;
- search for retriever-specific representations without changing model weights;
- evaluate representation transfer and fixed multi-system combinations;
- select one operating point using a single protected selection exposure;
- confirm one frozen comparison on 872 held-out queries;
- characterize the confirmed winner on the complete benchmark; and
- diagnose candidate exposure and within-pool ordering headroom without modifying the winner.

### 1.5 Contributions

The study makes five contributions.

First, it treats document representation as an explicit scientific variable coupled to the retriever. Second, it evaluates this interaction across lexical, general dense, patent-specialized, long-context, and instruction-aware systems while keeping weights fixed. Third, it reports positive, tied, negative, and flat-search outcomes rather than selecting only favorable cells. Fourth, it separates iterative development, one-time selection, one-time confirmation, and post-confirmatory analysis. Fifth, it decomposes remaining cross-domain error into relevant families found by rank 100, found only between ranks 101 and 200, and absent from the Top-200 pool.

### 1.6 Scope

The study evaluates citation-derived family-level retrieval relevance under one benchmark protocol. It does not train a new embedding model, fine-tune existing weights, learn adapters, perform query rewriting, implement a reranker, expand the confirmed candidate pool, or make legal conclusions about novelty, validity, infringement, or freedom to operate. The confirmed comparison contains exactly two frozen systems and is not a universal leaderboard.

---

## 2. Literature Review

### 2.1 Patent-Family Retrieval

Patent retrieval differs from general information retrieval because the same invention can be represented by multiple national or procedural publications. Family-level evaluation reduces duplicate credit and aligns the retrieval unit more closely with the invention. DAPFAM provides a domain-aware family-level benchmark for cross-domain patent retrieval and explicitly separates in-domain and out-of-domain relations [1]. Its citation-derived relevance structure is useful for controlled retrieval evaluation, but citation evidence is not equivalent to a legal determination.

The benchmark contains 1,247 query families, 45,336 target families, and 49,869 judged relations. The present work uses these dimensions as the fixed study population. Detailed external benchmark cells are not reused as comparative results because exact corpus revision, preprocessing, family normalization, and denominator parity must be established before numerical comparison.

### 2.2 Lexical Retrieval

BM25 remains a strong and interpretable lexical reference. Its probabilistic term-weighting framework rewards discriminative query terms while controlling for document length [2]. In patent search, lexical retrieval can be particularly valuable for rare materials, component names, formulas, and claim terminology. Its limitation is that semantically related inventions may share few words, especially across technical domains or drafting conventions.

Including BM25 serves two purposes. It anchors the study against a transparent non-neural method, and it tests whether representation design benefits a system whose scoring mechanism differs fundamentally from dense embedding retrieval.

### 2.3 Dense and Domain-Specific Embeddings

Dense retrievers map queries and documents into vector spaces. BGE-M3 was designed for multilingual, multi-functional, and multi-granular text representation [3]. Arctic Embed focuses on scalable and accurate embedding retrieval [4]. Qwen3 Embedding provides an instruction-aware embedding family with long-context capability [5]. Patent-specific embeddings seek to model the specialized technical and legal language found in patent documents.

Recent patent embedding benchmarks reinforce the need to evaluate multiple models and tasks rather than infer quality from architecture or model scale alone [6], [7]. In the present report, these sources motivate model diversity but are not used to import external numerical rankings. The study measures every reported system under one internal evaluator and one family-level population.

### 2.4 Executable Document Representations

AutoIndex frames document representation as an executable search variable while holding the retrieval backend fixed [8]. A representation can select fields, segment text, add contextual structure, or aggregate evidence. The important conceptual shift is that representation construction is no longer invisible preprocessing; it becomes a versioned and testable component.

Patent records require additional controls. The representation must preserve family identity, handle repeated publications, respect field structure, prevent silent truncation, and map passage-level scores back to one family-level score. This study therefore constrains representation search to deterministic, serializable operations. It does not generate free-form document summaries or modify the retriever.

### 2.5 Passage Retrieval and Long Documents

Long patent documents often exceed model input limits. Passage segmentation can preserve local evidence that would otherwise be truncated. Fine-grained patent novelty work has demonstrated the importance of passage retrieval for locating specific supporting evidence [9]. Segmentation, however, introduces trade-offs. Short passages can lose context, long passages can exceed input limits, overlap increases storage and compute, and family-level aggregation may overemphasize one high-scoring fragment.

The present design therefore tests complete documents, reduced documents, first-claim views, fixed overlapping passages, and section-specific multi-view representations. Passage length, overlap, boundary handling, and aggregation are treated as controlled configuration rather than incidental implementation detail.

### 2.6 Rank Fusion and Complementarity

Reciprocal Rank Fusion combines ranked lists without requiring comparable raw scores [10]. It can benefit systems that recover different relevant documents, but an additional list can also introduce noise. Complementarity must therefore be measured rather than assumed. The study compares the strongest single system, two-system fusion, three-system fusion, all-primary fusion, and a commercial-only combination under fixed candidate-depth rules.

### 2.7 Evaluation Metrics

Recall@k measures the fraction of relevant families found within the first k results. It is appropriate when missed prior art is costly. Discounted cumulative gain and its normalized form reward placing relevant results earlier [11]. Reporting both measures separates candidate recovery from ordering quality.

For confirmation, the two systems answer the same queries. Paired analysis therefore preserves query-level dependence. Paired bootstrap resampling estimates uncertainty without assuming normally distributed query-level differences [12]. The study uses 10,000 paired resamples and 95% percentile intervals for the primary confirmatory effects.

### 2.8 Research Gap

Prior work provides benchmarks, retrievers, representation search, passage retrieval, and fusion methods, but a gap remains in evaluating them under one governed sequence that:

- holds multiple retrievers fixed;
- searches document representations independently by retriever;
- tests transfer and combination without opening confirmation data;
- performs one protected selection;
- confirms exactly one frozen comparison; and
- diagnoses whether remaining error lies inside or outside the candidate pool.

This study addresses that gap while keeping inference and deployment boundaries explicit.

---

## 3. Conceptual Framework

### 3.1 Retriever-Conditioned Representation

Let \(q\) be a query patent family, \(d\) a target patent family, \(a\) a frozen retriever, and \(p\) a deterministic representation. The representation produces one or more views:

\[
\mathcal{V}_{p}(d)=\{v_1,\ldots,v_m\}.
\]

The retriever scores each view, and the representation defines a family-level aggregation rule:

\[
S_{a,p}(q,d)=G_p\left(s_a(q,v_1),\ldots,s_a(q,v_m)\right).
\]

Development seeks a representation for each retriever:

\[
p_a^*=\arg\max_{p\in\mathcal{P}}J_a(p),
\]

where \(J_a\) is the predeclared development objective. The subscript \(a\) is substantive: the optimum is not assumed to be shared across retrievers.

### 3.2 Family-Level Recall

For query \(q\), let \(R_q\) be the set of relevant patent families and \(L_q^k\) the first k retrieved families:

\[
\mathrm{Recall@}k(q)=\frac{|R_q\cap L_q^k|}{|R_q|}.
\]

Reported Recall is the macro-average over judged queries in the specified population. It must not be reconstructed from raw pair counts because macro-averaging weights queries equally rather than weighting every relation equally.

### 3.3 Ranking Quality

Normalized discounted cumulative gain is defined as:

\[
\mathrm{nDCG@}k(q)=\frac{\mathrm{DCG@}k(q)}{\mathrm{IDCG@}k(q)}.
\]

It measures whether relevant results are placed near the top of the list. Recall and nDCG answer complementary questions: whether evidence entered the result set and whether it was ordered effectively.

### 3.4 Evidence Classes

The report distinguishes three types of statement.

- **Measured result:** directly produced by a completed and audited experiment.
- **Diagnostic inference:** an interpretation consistent with measured aggregates but not a component-level causal proof.
- **Not tested:** unsupported because no compatible experiment, comparator, or authority exists.

This distinction prevents engineering tests, development results, confirmation, and analytical upper bounds from being presented as interchangeable evidence.

---

## 4. Study Design

### 4.1 Dataset and Partitions

The evaluation unit is the patent family. The fixed benchmark contains 1,247 query families, 45,336 candidate families, and 49,869 judged relations. The experimental sequence used:

| Partition | Queries | Purpose | Access rule |
|---|---:|---|---|
| Representation development | 150 | Shared screening and per-system representation search | Reusable only within development rules |
| System-composition development | 100 | Transfer, fusion, and constrained orchestration | Reserved from representation search |
| Selection | 125 | Choose the configuration entering confirmation | One exposure only |
| Final confirmation | 872 | Compare two frozen systems | One exposure only; no feedback into design |

The first two partitions form a 250-query development pool. Selection and confirmation membership, query identifiers, relevance judgments, rankings, and per-query outcomes remain protected.

### 4.2 Relation-Scoped In-Domain and Cross-Domain Evaluation

An in-domain relation indicates that the query and relevant target share the required technical classification level. A cross-domain relation does not. These are relation-scoped populations, not disjoint query sets. One query may have both in-domain and cross-domain relevant families. Query and relation denominators are therefore reported explicitly.

### 4.3 Frozen Retrieval Systems

| Retrieval system | Type | Principal role | License boundary |
|---|---|---|---|
| BM25 | Lexical | Transparent CPU reference | Commercial-capable implementation |
| BGE-M3 | Multilingual dense | General dense reference | MIT |
| PatEmbed-large | Patent-specific dense | Research-quality candidate | Research/non-commercial boundary |
| Arctic Embed M v2.0 | Long-context multilingual dense | Commercial-capable candidate | Apache 2.0 |
| Qwen3 Embedding 0.6B | Instruction-aware dense | Commercial-capable candidate | Apache 2.0 |

Before measurement, each system fixed its model revision, tokenizer, query and document prefixes, pooling, normalization, dimension, context limit, precision behavior, similarity, and tie handling. No fine-tuning, adapters, distillation, continued pretraining, or weight changes were permitted.

### 4.4 Shared Document Representations

Five deterministic views were used in common screening.

1. Title, abstract, and claims concatenated as one family document.
2. Title and abstract only.
3. The first structured independent claim.
4. Fixed 384-token passages with 64-token overlap and family-level maximum-score aggregation.
5. Separate labeled title, abstract, and claims views combined at family level by rank fusion.

All representations used canonical field ordering, Unicode normalization, deterministic whitespace handling, explicit final-fragment handling, and fail-closed protection against silent truncation.

### 4.5 Outcomes

The primary development and confirmation outcome was cross-domain Recall@100. Secondary outcomes were cross-domain nDCG@100 and nDCG@10. All-population and in-domain scores were guardrails and diagnostic outcomes. Operational measurements included p50, p95, and p99 latency, throughput, total wall time, charged cost, index size, peak RAM, peak VRAM, failure count, and determinism.

### 4.6 Statistical Analysis

The confirmatory comparison used eligible paired queries and 10,000 paired bootstrap resamples. It reported mean difference, two-sided 95% percentile confidence intervals, and win/tie/loss counts. A superiority claim required the lower confidence bound to exceed zero. Predeclared additional selection comparisons used Holm-Bonferroni correction. Metrics without a canonical interval were reported descriptively rather than assigned an inferred interval.

### 4.7 Governance and Protected Data

Raw queries, partition membership, patent identifiers, family identifiers, relevance judgments, rankings, provider payloads, credentials, and per-query outcomes remained in the protected evaluation environment. Only aggregate metrics, counts, failure categories, manifests, and integrity evidence were returned. Failed or incompatible attempts were kept separate. Engineering repair could change operational parameters such as batching or process supervision only when scientific semantics remained unchanged.

---

## 5. A0: Research Foundation and Experimental Governance

### 5.1 Purpose

A0 established the conditions required for interpretable measurement. It did not evaluate retrieval quality. Its purpose was to define authority, preserve evidence, formalize schemas, register models and licenses, establish protected-data rules, test feasibility, and create a reproducible execution scaffold.

### 5.2 Work Completed

Ten tasks covered evidence migration, scientific authority, reporting projections, experiment tracking, phase and decision structure, scientific contracts, retrieval-system declarations, license registration, compute and storage feasibility, validation, safety, and reusable implementation scaffolding.

Feasibility tests used synthetic data on CPU. They exercised representation compilation, index construction, search, aggregation, deterministic replay, memory observation, and scaling behavior. They did not access protected benchmark content, perform measured retrieval, download production model weights, use scientific GPU compute, or incur paid API use.

### 5.3 Validation

The closeout recorded all ten tasks complete. Engineering validation included 44 targeted checks, 387 broader tests, and 66 interface and policy checks. These counts support software readiness and evidence integrity only. Measured retrieval runs in A0 were zero.

### 5.4 Interpretation

A0 established a reproducible control environment. It cannot be used as evidence that any representation or retriever is effective. This distinction is essential because synthetic correctness can show that a pipeline runs deterministically without demonstrating performance on real relevance judgments.

---

## 6. A1: Common Multi-System Screening

### 6.1 Protocol

A1 crossed five retrieval systems with five shared document representations, producing 25 logical evaluation cells on the fixed 150-query representation-development population. Every cell used the same family-level evaluator and metric definitions. The objective was to characterize the initial frontier and identify systems warranting per-system search.

### 6.2 Aggregate Results

| Retrieval system | Recall@100 | nDCG@100 | nDCG@10 | p95 latency (ms) | Development disposition |
|---|---:|---:|---:|---:|---|
| BM25 | 0.191200 | 0.172717 | 0.160011 | 441.520 | Diagnostic; did not advance |
| BGE-M3 | 0.269933 | 0.231377 | 0.198497 | 235.203 | Diagnostic; did not advance |
| PatEmbed-large | 0.413400 | 0.347812 | 0.289856 | 212.062 | Advanced |
| Arctic Embed M v2.0 | 0.340667 | 0.284546 | 0.235538 | 214.207 | Advanced |
| Qwen3 Embedding 0.6B | 0.363733 | 0.307930 | 0.256706 | 217.099 | Advanced |

All 25 cells completed in the terminal attempt. The measured charge was USD 11.161632, and verified artifact return and worker cleanup passed. The patent-specific dense system had the highest mean Recall@100 across the five shared views. Arctic and Qwen3 also met the predeclared advancement rule.

### 6.3 Interpretation

A1 shows substantial differences among retrieval systems under common representations. It does not identify a universal winner because the results are development aggregates and the protected selection and confirmation populations were not accessed. "Advanced" means eligible for deeper study, not confirmed superiority.

---

## 7. A2: Per-System Representation Search

### 7.1 Search Universe

A2 evaluated a frozen universe of 52 trial configurations: 40 matched primary configurations and 12 conditional reserves. Forty-four configurations were measured, including four activated reserves; eight reserves remained dormant because their activation conditions were not met. No configuration failed.

### 7.2 Results

| Retrieval system | Recall@100 | nDCG@100 | nDCG@10 | p95 latency (ms) | Predeclared decision |
|---|---:|---:|---:|---:|---|
| BM25 | 0.234667 | 0.210784 | 0.195024 | 1,387.940 | Diagnostic tie; no per-system winner |
| BGE-M3 | 0.290000 | 0.249919 | 0.220057 | 1,139.045 | Diagnostic tie; no per-system winner |
| PatEmbed-large | 0.423000 | 0.357636 | 0.299444 | 1,686.804 | Unique within-search winner; tied with its A1 incumbent at displayed precision |
| Arctic Embed M v2.0 | 0.358667 | 0.301868 | 0.253229 | 1,115.052 | Strict improvement; retained for transfer |
| Qwen3 Embedding 0.6B | 0.373667 | 0.321262 | 0.273664 | 816.055 | No strict improvement; retained as transfer control |

The full measured workload cost USD 54.526667, below the USD 60 hard ceiling. Integrity checks, verified aggregate return, and worker termination passed.

### 7.3 Interpretation

Only Arctic met its strict improvement-over-incumbent rule. PatEmbed had a unique winning configuration within its A2 search while tying its frozen A1 incumbent at the displayed precision; these are different comparison statements and are both retained. Qwen3 remained valuable for transfer analysis despite not meeting the primary improvement rule. BM25 and BGE-M3 remained diagnostic ties. Latency, cost, or secondary metrics were not used after the fact to manufacture winners among tied systems.

A1 and A2 use different summaries: A1 reports common-screen aggregates across shared representations, whereas A2 reports the configurations selected or classified under frozen per-system rules. Informal subtraction between the displayed tables is not a valid causal or statistical effect estimate.

---

## 8. A3: Representation Transfer, Complementarity, and Constrained System Composition

### 8.1 Design

A3 tested the three retained dense systems. It completed a 3-by-3 representation-transfer matrix and five fixed composition controls, for 14 audited operations. Every operation covered all 250 development queries. This phase tested compatibility and complementarity; it was not a second protected selection.

### 8.2 Transfer Matrix

| Representation source | Target system | Recall@100 | nDCG@100 | nDCG@10 | p95 (s) |
|---|---|---:|---:|---:|---:|
| PatEmbed | PatEmbed | 0.418436 | 0.347098 | 0.290589 | 1.712 |
| PatEmbed | Arctic | 0.337430 | 0.288876 | 0.248091 | 1.715 |
| PatEmbed | Qwen3 | 0.362570 | 0.306168 | 0.259749 | 1.445 |
| Arctic | PatEmbed | 0.418715 | 0.352416 | 0.295553 | 1.493 |
| Arctic | Arctic | 0.341341 | 0.286975 | 0.239140 | 1.462 |
| Arctic | Qwen3 | 0.359497 | 0.305476 | 0.258884 | 1.411 |
| Qwen3 | PatEmbed | 0.419274 | 0.351428 | 0.296279 | 0.976 |
| Qwen3 | Arctic | 0.338268 | 0.280557 | 0.229009 | 0.892 |
| Qwen3 | Qwen3 | 0.360615 | 0.306579 | 0.261546 | 0.872 |

The Qwen3-derived representation applied to PatEmbed produced the highest Recall@100, 0.419274. The Arctic-derived representation applied to PatEmbed produced the highest nDCG@100, 0.352416. No source representation retained a consistent diagonal or universal advantage. Target-system identity remained strongly associated with the resulting quality.

### 8.3 Fixed Composition Controls

| Configuration | Recall@100 | nDCG@100 | nDCG@10 | p95 (s) |
|---|---:|---:|---:|---:|
| Strongest single system | 0.418436 | 0.347098 | 0.290589 | 1.692 |
| Two-system fusion | 0.418715 | 0.352747 | 0.293716 | 1.345 |
| Three-system fusion | 0.415084 | 0.346250 | 0.284772 | 1.443 |
| All-primary fusion | 0.415084 | 0.346250 | 0.284772 | 1.436 |
| Commercial-only fusion | 0.369274 | 0.308967 | 0.258116 | 1.165 |

Two-system fusion slightly improved nDCG@100 and reduced p95 latency relative to the strongest single control. Three-system and all-primary fusion produced identical aggregate quality and underperformed the two-system configuration. Commercial-only fusion was faster but lower in quality. More systems therefore did not imply better retrieval.

### 8.4 Flat Adaptive Search Surface

The constrained composition procedure generated 12 proposals across three batches. All proposals resolved to one distinct executable action and reproduced the same result:

- Recall@100: 0.415084
- nDCG@100: 0.346250
- nDCG@10: 0.284772
- p95 latency: 1.436 s
- coverage: 250 of 250 queries

This is a useful negative result. Under the frozen action space and label-free constraints, adaptive proposal generation did not create a new behavior or measurable gain. Counting proposal texts without resolving their executable identity would have overstated search diversity.

### 8.5 Interpretation

A3 supports retriever-conditioned compatibility and rejects monotonic fusion gains. It does not provide a formal paired-bootstrap superiority claim for the transfer matrix. The aggregate values describe development behavior and boundaries.

---

## 9. A4: Operating Profiles and One-Time Selection

### 9.1 Development Profiles

Four frozen profiles were evaluated on the reserved 100-query system-composition population: a speed-oriented profile, a balanced profile, a quality-oriented profile, and a research reference. Each completed all 100 queries with deterministic output and zero failures.

| Profile | Recall@100 | nDCG@100 | nDCG@10 | p50 (ms) | p95 (ms) | QPS | Reported cost (USD) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Speed-oriented | 0.345833 | 0.292764 | 0.249337 | 487.241 | 1,524.230 | 0.02831 | 0.63345 |
| Balanced | 0.382639 | 0.328777 | 0.278442 | 732.509 | 1,771.497 | 0.01134 | 1.58184 |
| Quality-oriented | 0.382639 | 0.328777 | 0.278442 | 314.432 | 1,637.748 | 0.01518 | 1.18153 |
| Research reference | 0.463194 | 0.372934 | 0.305775 | 327.714 | 1,742.994 | 0.01452 | 1.23489 |

The balanced and quality-oriented profiles tied on all reported quality metrics, while the quality-oriented profile had lower median latency and reported cost. The research reference had the highest quality but remained separate from commercial deployment because of its model license.

### 9.2 Selection Population Accounting

The sealed selection set was opened once. All four profiles produced rankings for all 125 scoped queries with no failures. Cross-domain metrics and paired statistics used the 90 queries with positive cross-domain relations. The remaining 35 queries still counted toward selection coverage and access control but were excluded only from the cross-domain denominator.

### 9.3 Selection Results

| Recall@100 comparison | Left | Right | Difference | 95% CI | Win/Tie/Loss |
|---|---:|---:|---:|---:|---:|
| Research vs balanced | 0.416111 | 0.360556 | 0.055556 | 0.029986-0.081667 | 49/20/21 |
| Research vs quality-oriented | 0.416111 | 0.360556 | 0.055556 | 0.029986-0.081667 | 49/20/21 |
| Research vs speed-oriented | 0.416111 | 0.308333 | 0.107778 | 0.081111-0.135000 | 69/9/12 |
| Balanced vs quality-oriented | 0.360556 | 0.360556 | 0.000000 | 0.000000-0.000000 | 0/90/0 |
| Balanced vs speed-oriented | 0.360556 | 0.308333 | 0.052222 | 0.038889-0.065556 | 55/29/6 |
| Quality-oriented vs speed-oriented | 0.360556 | 0.308333 | 0.052222 | 0.038889-0.065556 | 55/29/6 |

Only verified Recall@100 paired results are reported for selection. No paired nDCG results are inferred. The research configuration and a static representation comparator were frozen after this exposure. An isolated legal-transfer experiment was unsupported and did not influence the selected systems.

### 9.4 Interpretation

A4 selected the configuration to be confirmed; it did not itself establish a final effect. Its scientific value lies in the single-exposure decision process and explicit accounting of all 125 queries versus the 90-query cross-domain-positive denominator.

---

## 10. A5: Final Confirmation

### 10.1 Confirmatory Protocol

A5 compared exactly two complete frozen systems: the selected research configuration and the frozen static/common comparator. Their system-level bindings, including model, program, representation, prompt, and runtime choices, were fixed before access; the evaluator, metric definitions, output depth, and tie policy were also frozen. Because multiple bindings differed between systems, the comparison estimates the effect of choosing the complete research configuration rather than the isolated causal effect of representation alone. Both systems processed all 872 final queries. There were zero failures, no missing outputs, and deterministic replay.

### 10.2 Confirmatory Quality Results

| Cross-domain outcome | Static comparator | Research system | Difference |
|---|---:|---:|---:|
| Recall@100 | 0.331097 | 0.442476 | 0.111379 |
| nDCG@100 | 0.279253 | 0.365595 | 0.086342 |
| nDCG@10 | 0.233666 | 0.297459 | 0.063794 |

The paired Recall@100 difference had a 95% bootstrap confidence interval of 0.102294-0.120438. The research system recorded 619 wins, 158 ties, and 95 losses. The paired nDCG@100 difference had a 95% confidence interval of 0.078673-0.094077. Both intervals exclude zero. nDCG@10 is descriptive because the frozen evidence does not contain a canonical confidence interval for that endpoint.

### 10.3 Operational Results

| Outcome | Static comparator | Research system | Interpretation |
|---|---:|---:|---|
| p50 latency (ms) | 315.862 | 237.547 | Lower for research system |
| p95 latency (ms) | 735.171 | 732.218 | Similar |
| p99 latency (ms) | 804.002 | 1,044.613 | Worse for research system |
| Throughput (queries/s) | 2.6659 | 3.3193 | Higher for research system |
| Peak RAM (GiB) | 16.358 | 16.358 | Equal |
| Peak VRAM (GiB) | 0.845 | 0.845 | Equal |
| Index size (bytes) | 2,961,523,444 | 2,961,523,444 | Equal |
| Reported cost (USD) | 1.45682 | 1.45682 | Equal |

The operational result is mixed. Median latency and throughput favor the research configuration, while tail latency at p99 favors the static comparator. A claim that the research system is faster in every operational sense would therefore be incorrect.

### 10.4 Confirmatory Conclusion

Under the frozen family-level protocol, the complete research configuration selected through retriever-conditioned representation research improved cross-domain Recall@100 and nDCG@100 over the frozen static/common comparator. This conclusion applies to the exact two-system comparison and should not be interpreted as a component-level causal estimate for representation alone. It does not establish superiority over every retriever, every patent benchmark, or every deployment environment. It also does not remove the research/non-commercial license boundary of the selected model.

---

## 11. A6: Full-Benchmark Depth and Scalability Evaluation

### 11.1 Purpose

After confirmation, the selected system was fixed permanently and applied alone to the complete benchmark. A6 measured full-corpus coverage, candidate-depth behavior, resources, and determinism. It did not compare systems or select a new winner.

### 11.2 Coverage and Materialization

- Source families: 45,336
- Materialized families: 45,336
- Query families: 1,247
- Text chunks or representations: 188,944
- Candidate depth: 200 per query
- Ranked rows: 249,400
- Coverage: 100%
- Failures: 0
- Duplicate-family errors: 0
- Checkpoint recoveries required: 0

### 11.3 Depth Results

| Population | Recall@10 | Recall@20 | Recall@50 | Recall@100 | Recall@200 | nDCG@10 | nDCG@100 |
|---|---:|---:|---:|---:|---:|---:|---:|
| All relations | 0.136795 | 0.214697 | 0.336358 | 0.438965 | 0.546832 | 0.295725 | 0.362497 |
| In-domain relations | 0.187048 | 0.277872 | 0.413145 | 0.528164 | 0.645077 | 0.307483 | 0.406513 |
| Strict cross-domain relations | 0.034023 | 0.070933 | 0.133994 | 0.188450 | 0.260167 | 0.025697 | 0.070644 |

The all-relations population contains 1,247 judged queries. The in-domain relation scope contains 1,217 judged queries, and the strict cross-domain scope contains 905. These populations may overlap at query level.

### 11.4 Operational Results

| Measure | Result |
|---|---:|
| Materialization throughput | 14.349 documents/s |
| Recorded p50 latency | 50 ms |
| Recorded p95 latency | 50 ms |
| Recorded p99 latency | 50 ms |
| Index size | 773,914,624 bytes, approximately 738 MiB |
| Peak RAM | 2,154,569,728 bytes, approximately 2.01 GiB |
| Peak VRAM | 1,773,727,744 bytes, approximately 1.65 GiB |
| Reported cost | USD 0.300323 |

### 11.5 Interpretation

Recall increased with candidate depth in every population, but strict cross-domain performance remained substantially below in-domain performance. A6 demonstrates complete processing and deterministic full-benchmark characterization of the confirmed system. It does not re-estimate the A5 comparative effect.

The cross-domain values in A5 and A6 use different population definitions. A5 aggregates its eligible final cohort, whereas A6 uses strict relation-scoped cross-domain judgments. They must not be shown as a before-and-after trend.

---

## 12. A7: Post-Confirmatory Candidate-Exposure Diagnosis

### 12.1 Diagnostic Scope

A7 analyzed the immutable A6 Top-200 pool on CPU. It did not retrieve new candidates, change the winner, select a reranker, or access selection or confirmation data again. The analysis covered score identity, family integrity, protocol comparability, representation attribution, query rescue, candidate-exposure anatomy, and an analytical ordering bound.

### 12.2 Score and Family Integrity

Recalculation reproduced A6 Recall@100 and nDCG@100 exactly for all, in-domain, and cross-domain populations. There were zero family collisions, zero denominator discrepancies, and zero mapping-scope leakage events.

Forty raw self-relations were examined in a sensitivity analysis. Removing them changed all-relations Recall@100 by -0.000777 and nDCG@100 by -0.004146. In-domain changes were -0.000908 and -0.005136. Strict cross-domain metrics were unchanged. This is a sensitivity result, not evidence of cross-partition leakage.

### 12.3 Candidate-Exposure Anatomy

| Population | Relevant family pairs | Found at ranks 1-100 | Found only at ranks 101-200 | Absent from Top-200 |
|---|---:|---:|---:|---:|
| All relations | 24,929 | 10,938 | 2,689 | 11,302 |
| In-domain relations | 19,736 | 10,142 | 2,357 | 7,237 |
| Strict cross-domain relations | 5,193 | 796 | 332 | 4,065 |

Among the 905 judged cross-domain queries:

- 67 had all relevant evidence exposed by rank 200;
- 297 had partial relevant evidence exposed;
- 86 had relevant evidence only at ranks 101-200; and
- 455 had no relevant candidate in the Top-200 pool.

The dominant cross-domain finding is the absence of 4,065 relevant pairs from the fixed candidate pool. A downstream ranker cannot recover a family that first-stage retrieval never supplies.

### 12.4 Analytical Within-Pool Bound

The analytical oracle moves every relevant family already present in Top-200 into the first 100 positions. It adds no candidate and is not an implemented reranker.

| Population | Observed Recall@100 | Perfect-ordering bound within Top-200 | Within-pool headroom |
|---|---:|---:|---:|
| All relations | 0.438965 | 0.546832 | 0.107868 |
| In-domain relations | 0.528164 | 0.645077 | 0.116913 |
| Strict cross-domain relations | 0.188450 | 0.260167 | 0.071717 |

The cross-domain ordering headroom is real but limited. Even perfect ordering cannot address the 4,065 relevant pairs that are not present in the pool.

### 12.5 Diagnostic Boundaries

Several questions remain explicitly unanswered.

- A fixed-reference GPU reproduction was not run because no fresh GPU authorization existed.
- Numerical parity with external protocols was not established because their exact dataset revision, representation, aggregation, and evaluator settings were not fully verified.
- Representation attribution is descriptive because no hash-bound component ablation was performed.
- Query-rescue comparison is unavailable because no compatible frozen comparator ranking was supplied to this diagnostic stage.
- Oracle values are analytical bounds, not achieved system or reranker results.

These boundaries strengthen rather than weaken the interpretation by distinguishing measured evidence from unavailable evidence.

---

## 13. A8: Manuscript Synthesis and Publication Preparation

### 13.1 Purpose

A8 converted the validated A0-A7 evidence into a journal manuscript, figures, tables, bibliography, claim-to-evidence mapping, and release materials. It was a synthesis phase, not a retrieval experiment. No new model, candidate pool, reranker, winner, or quality claim was introduced.

### 13.2 Quality-Control Scope

Internal checks covered:

- separation of development, selection, confirmation, scalability, and diagnostic claims;
- consistency of all reported aggregate numbers;
- citation and bibliography structure;
- model-license boundaries;
- protected-data and double-anonymization checks;
- figure and table readability;
- document compilation and layout; and
- absence of query identifiers, relevance judgments, raw rankings, and per-query outputs.

### 13.3 Current Status

The publication package passed its internal scientific and quality-control checks, completing A8. Submission authorization was approved after the preceding diagnostic phase. No manuscript had yet been uploaded or submitted externally by the evidence cutoff.

The remaining work consists of external submission-administration tasks rather than an unresolved scientific or project gate:

1. add author names, affiliations, corresponding-author information, funding, contribution roles, and competing-interest declarations;
2. finalize repository, archive, and data-availability wording for the selected venue;
3. recheck the journal's current formatting, submission, and AI-disclosure policies; and
4. perform the journal upload and submission procedure.

A8 is therefore scientifically and operationally complete as a research synthesis package. External journal submission remains an administrative action that had not yet occurred.

---

## 14. Integrated Evaluation

### 14.1 Answers to the Research Questions

**RQ1: Does representation search improve a fixed retriever?**

It can, but not uniformly. Arctic met its strict development improvement rule. PatEmbed produced a unique within-search winner that tied its A1 incumbent at displayed precision, Qwen3 did not meet the strict rule, and BM25 and BGE-M3 produced diagnostic ties. The method is conditional rather than universally positive.

**RQ2: Are representations retriever-specific?**

The evidence supports retriever dependence. Per-system outcomes differed, and no source representation retained a consistent advantage across the transfer matrix. The target retriever remained a major determinant of quality.

**RQ3: Does multi-system fusion improve quality?**

Only selectively. Two-system fusion slightly improved nDCG@100, but three-system and all-primary fusion did not improve the strongest controls. The adaptive composition search collapsed to one action. Additional systems must contribute unique relevant evidence; architectural diversity alone is insufficient.

**RQ4: Which operating point should be selected?**

The research reference had the strongest development and one-time selection quality. Commercial profiles exposed a quality-license-cost trade-off. The research configuration was selected for confirmation, but that choice is not a commercial deployment recommendation.

**RQ5: Did the effect confirm on held-out data?**

Yes, for the exact two complete frozen systems. The research configuration exceeded the static/common comparator by 0.111379 in cross-domain Recall@100 and by 0.086342 in nDCG@100 on 872 queries, with both paired confidence intervals excluding zero and no failures. The design supports a system-level comparison, not attribution of the entire effect to representation alone.

**RQ6: Is remaining error ordering or candidate exposure?**

Both contribute, but missing candidates dominate the strict cross-domain diagnosis. Of 5,193 relevant pairs, 4,065 were absent from Top-200. Perfect ordering within the pool could add only 0.071717 macro-Recall@100.

### 14.2 Evidence Hierarchy

| Stage | Evidence class | Supported use | Unsupported use |
|---|---|---|---|
| A0 | Synthetic engineering validation | Readiness, safety, reproducibility | Retrieval effectiveness |
| A1-A3 | Measured development evidence | Interaction, transfer, fusion, negative findings | Final generalization |
| A4 | Development plus one-time selection | Selection rationale | Confirmatory effect |
| A5 | Paired final confirmation | Effect between two frozen systems | Universal or commercial superiority |
| A6 | Single-system post-confirmatory measurement | Full-scale depth and resources | New comparative winner |
| A7 | Post-confirmatory diagnosis | Candidate exposure and analytical bounds | Achieved reranker performance |
| A8 | Publication synthesis | Prepared internal package | Journal submission or acceptance |

### 14.3 Quality, Latency, Cost, and Licensing

No single configuration dominates every axis. The confirmed research system improved quality, median latency, and throughput but had worse p99 latency. Commercial-capable profiles avoided the selected model's license restriction but had lower development quality. Operational selection must therefore consider the full quality-latency-cost-license surface rather than rank systems by one headline metric.

### 14.4 Negative and Boundary Findings

The program preserved several findings that a winner-only narrative would hide:

- two retrieval systems had no per-system development winner;
- one retained dense system did not meet its strict improvement rule;
- transferred representations had no universal source advantage;
- adding a third system did not improve fusion;
- 12 adaptive proposals yielded only one executable behavior;
- external numerical parity was not established;
- component-level causality was not tested; and
- no reranker or candidate-rescue system was evaluated.

These results define where the method does not yet work and improve the scientific value of the study.

---

## 15. Discussion

### 15.1 Representation Is Part of the Retrieval System

The results reject a model-independent account of preprocessing. A lexical retriever, a general dense encoder, a patent-specialized encoder, a long-context encoder, and an instruction-aware encoder do not consume evidence in the same way. Field selection, truncation, passage construction, and aggregation interact with their scoring behavior.

Retrieval reports should therefore version the representation with the retriever. At minimum, they should disclose selected fields, field order, section labels, passage length, overlap, boundary policy, truncation behavior, family aggregation, query/document prefixes, pooling, normalization, and model revision.

### 15.2 Confirmation Under a Freeze

The A5 result is strong because the systems were fixed after a single selection exposure, both covered the same 872 queries, the analysis was paired, and confidence intervals were reported. The lower confidence bounds remain above zero for Recall@100 and nDCG@100.

The conclusion must nevertheless remain narrow. The confirmed systems differed in multiple frozen system bindings, and the winning configuration also changed several representation components together. Without a controlled component ablation under otherwise identical system bindings, the study cannot attribute the gain causally to representation as a whole or to claims, passages, field order, or aggregation in isolation. The defensible statement is that the selected complete research configuration outperformed the frozen static/common comparator, not that one component caused the improvement.

### 15.3 Why More Retrieval Systems Did Not Necessarily Help

Fusion benefits from complementary evidence, not simply from model diversity. If additional systems retrieve similar families or introduce lower-quality candidates, fusion can dilute strong rankings. The equality of three-system and all-primary aggregate scores, together with the stronger two-system nDCG@100, illustrates this boundary.

The flat adaptive search surface adds a methodological lesson. Proposal diversity must be measured after compilation into executable actions. Multiple natural-language proposals can describe the same behavior. Optimization systems should track distinct action signatures and stop when nominal exploration no longer creates operational diversity.

### 15.4 Candidate Exposure as the Next Engineering Target

The A7 decomposition changes the next research question. A reranker can improve ordering among the 1,128 cross-domain relevant pairs that appear within Top-200, including the 332 found only at ranks 101-200. It cannot recover the 4,065 pairs absent from the pool.

Future work should therefore prioritize first-stage exposure: controlled query expansion, complementary indexes, section-aware candidate generation, graph signals, or multi-stage retrieval designed explicitly for recall. Reranking remains useful, but its potential is bounded by the pool it receives.

### 15.5 Research and Commercial Tracks

The confirmed research system uses a patent-specialized model with a non-commercial license boundary. Scientific effectiveness does not imply deployability. A commercial study must preregister a new comparison among suitably licensed models and use fresh development and confirmation data. It should not retrospectively select a commercial substitute from the already exposed final population.

### 15.6 Implications for Patent Retrieval Evaluation

Six reporting practices follow from the evidence.

1. State whether the evaluation unit is a publication or a patent family.
2. Report document construction and family aggregation as part of the model configuration.
3. State the query and relation denominators for in-domain and cross-domain metrics.
4. Separate iterative development, protected selection, confirmation, and post-confirmatory analysis.
5. Report candidate exposure separately from ranking quality.
6. Refuse external score comparisons unless corpus, population, representation, and evaluator parity are verified.

---

## 16. Validity Threats and Limitations

### 16.1 Internal Validity

The strongest controls are frozen bindings, protected partitions, deterministic execution, paired confirmation, and separation of incompatible attempts. The main internal limitation is that winning representations combine several operations. The design confirms the complete configuration but does not identify a causal component.

### 16.2 Construct Validity

Recall and nDCG measure retrieval relative to the benchmark's citation-derived judgments. They do not measure legal novelty, inventive step, validity, infringement, or freedom to operate. In-domain and cross-domain labels describe relations and can overlap at query level.

### 16.3 External Validity

The evidence comes from one English family-level benchmark. It may not generalize to other languages, patent offices, corpora, legal tasks, classification tasks, or production systems using metadata and citation graphs. External numerical protocols were not verified sufficiently for a defensible common ranking.

### 16.4 Statistical Conclusion Validity

The primary confirmation and nDCG@100 effect have paired bootstrap intervals. Several development, transfer, and operational values are descriptive aggregates without formal intervals. nDCG@10 in confirmation is also descriptive. These results should not be upgraded to confirmatory superiority claims.

### 16.5 Operational Limitations

Resource measurements depend on the recorded hardware and runtime. The research configuration's p99 latency is worse than the comparator's. No new GPU reference run, learned reranker, or candidate-pool expansion was performed during diagnosis.

### 16.6 Data and Reproducibility Limitations

Protected identifiers, judgments, rankings, and per-query outcomes cannot be redistributed. This preserves the evaluation boundary but prevents external readers from conducting case-level error analysis from this report alone. Reproduction requires authorized access to the benchmark and its source terms.

### 16.7 License Limitation

The strongest confirmed model is not available for unrestricted commercial use under the recorded license. The research champion and any commercial-capable recommendation must remain separate.

---

## 17. Recommended Future Work

1. **Component ablation:** vary one representation component at a time while holding all others fixed.
2. **Candidate-generation research:** evaluate complementary lexical, dense, section-aware, and graph-based first-stage retrieval.
3. **Frozen-pool reranking:** test whether a real reranker converts part of the analytical headroom into achieved gains.
4. **Commercial-only confirmation:** preregister and evaluate licensed systems on fresh protected data.
5. **Independent benchmark replication:** repeat the study across languages, offices, and family-normalization schemes.
6. **External protocol parity audit:** align dataset revision, query population, family mapping, representation, cutoffs, and metric implementation before numerical comparison.
7. **Operational robustness:** repeat latency, memory, energy, and cost measurement on multiple hardware classes.
8. **Expert-user evaluation:** determine whether increased candidate recall improves real prior-art workflow completeness or time.
9. **Action-space diagnostics:** measure distinct executable behaviors during automated configuration search and stop flat searches early.
10. **Data-efficient validation:** develop methods that preserve a protected final set while enabling broader model and representation comparisons.

All future adaptive work should use new development, selection, and confirmation partitions. The 872-query final population should not be reopened for further design decisions.

---

## 18. Conclusion

The project progressed from engineering foundation through common screening, per-system representation search, transfer and fusion analysis, one-time selection, paired final confirmation, complete-benchmark characterization, candidate-exposure diagnosis, and publication synthesis.

The primary confirmatory result is clear and bounded. On 872 held-out queries, the complete research configuration selected through retriever-conditioned representation research achieved cross-domain Recall@100 of 0.442476 compared with 0.331097 for the frozen static/common comparator. The paired difference of 0.111379 had a 95% confidence interval of 0.102294-0.120438. Cross-domain nDCG@100 improved by 0.086342 with a 95% interval of 0.078673-0.094077. These results confirm the advantage of the selected complete configuration in this comparison; because several frozen system bindings differed, they do not isolate document construction as the sole causal factor.

The post-confirmatory result is equally important. In the strict cross-domain population, only 1,128 of 5,193 relevant family pairs were present in Top-200, and 4,065 were absent. Perfect within-pool ordering could raise macro Recall@100 only from 0.188450 to 0.260167. Candidate generation, not ranking alone, is therefore the central remaining retrieval problem under this protocol.

The conclusion does not extend to universal model superiority, legal decisions, or commercial deployment. The study used one family-level benchmark, one frozen final comparator, and a research-licensed winning model. No component ablation, external protocol parity, implemented reranker, or candidate-rescue study was completed. The publication package passed internal review and received submission authorization; venue-specific administration and the external journal submission itself had not yet been completed.

---

## 19. A0-A8 Chronology at a Glance

| Stage | Plain-language role | Completed work | Principal result |
|---|---|---|---|
| A0 | Research foundation | Governance, schemas, license registry, synthetic feasibility, safety | Ready for governed measurement; no retrieval result |
| A1 | Common screening | Five systems by five shared representations | 25/25 cells complete; three systems advanced |
| A2 | Per-system search | Frozen universe of 52 configurations | 44 measured, 8 dormant, 0 failures; heterogeneous outcomes |
| A3 | Transfer and composition | Nine transfer cells and five fixed controls | No universal transfer; more fusion was not always better; adaptive surface flat |
| A4 | Operating profiles and selection | Four profiles and one 125-query selection exposure | Research and comparator systems fixed for confirmation |
| A5 | Final confirmation | Two frozen systems on 872 queries | Confirmed Recall@100 and nDCG@100 gains |
| A6 | Full-benchmark evaluation | 45,336 families, 1,247 queries, depth 200 | 100% coverage, 0 failures; large cross-domain gap remained |
| A7 | Candidate-exposure diagnosis | Integrity replay, exposure decomposition, analytical bound | 4,065 of 5,193 cross-domain relevant pairs absent from Top-200 |
| A8 | Publication synthesis | Manuscript, figures, tables, evidence mapping, internal QA | Package complete and submission authorized; not externally submitted |

---

## 20. Glossary

| Term | Definition |
|---|---|
| Patent family | Publications representing the same invention or linked priority lineage |
| Retrieval system | The fixed method that scores and ranks patent families for a query |
| Document representation | Deterministic rules for selecting, ordering, segmenting, labeling, and aggregating patent text |
| In-domain relation | Query-target relation sharing the required technical classification level |
| Cross-domain relation | Query-target relation without that shared classification under the benchmark definition |
| Recall@100 | Fraction of relevant families appearing in the first 100 results |
| nDCG@100 | Rank-sensitive quality through position 100, normalized by ideal ordering |
| p50/p95/p99 | Latency thresholds within which 50%, 95%, or 99% of observations complete |
| Throughput | Number of queries or documents processed per second |
| Paired bootstrap | Resampling paired query outcomes to estimate uncertainty in a system difference |
| Candidate pool | Families supplied by first-stage retrieval for possible downstream ranking |
| Analytical upper bound | Best value allowed by a stated hypothetical constraint, not an achieved model result |
| Frozen configuration | Data, model, representation, evaluator, and decision rules fixed before protected evaluation |
| Development evidence | Results used to explore and choose configurations, not final confirmation |
| Confirmatory evidence | Results from the sealed final comparison after all systems were fixed |

---

## References

[1] I. Ayaou, D. Cavallucci, and H. Chibane, “DAPFAM: A Domain-Aware Family-level Dataset to Benchmark Cross-Domain Patent Retrieval,” *Array*, vol. 29, article 100720, 2026. doi: 10.1016/j.array.2026.100720.

[2] S. Robertson and H. Zaragoza, “The Probabilistic Relevance Framework: BM25 and Beyond,” *Foundations and Trends in Information Retrieval*, vol. 3, no. 4, pp. 333-389, 2009. doi: 10.1561/1500000019.

[3] J. Chen, S. Xiao, P. Zhang, K. Luo, D. Lian, and Z. Liu, “BGE M3-Embedding: Multi-Lingual, Multi-Functionality, Multi-Granularity Text Embeddings Through Self-Knowledge Distillation,” arXiv:2402.03216, 2024.

[4] L. Merrick, D. Xu, G. Nuti, and D. Campos, “Arctic-Embed: Scalable, Efficient, and Accurate Text Embedding Models,” arXiv:2405.05374, 2024.

[5] Y. Zhang et al., “Qwen3 Embedding: Advancing Text Embedding and Reranking Through Foundation Models,” arXiv:2506.05176, 2025.

[6] I. Ayaou and D. Cavallucci, “PatenTEB: A Comprehensive Benchmark and Model Family for Patent Text Embedding,” arXiv:2510.22264, 2025.

[7] A. Yousefiramandi and C. Cooney, “Benchmarking Patent Embeddings: A Multi-Task Evaluation of 22 Models Across Retrieval, Classification, and Clustering,” arXiv:2605.24297, 2026.

[8] S. O'Nuallain, N. Rajkumar, R. Narayanasamy, H. Jiang, S. Chaudhari, and A. Drozdov, “AutoIndex: Learning Representation Programs for Retrieval,” arXiv:2607.18603, 2026.

[9] V. Knappich, A. Hatty, S. Razniewski, and A. Friedrich, “Is It Novel and Why? Fine-Grained Patent Novelty Prediction Based on Passage Retrieval,” in *Proceedings of the 49th International ACM SIGIR Conference on Research and Development in Information Retrieval*, 2026. doi: 10.1145/3805712.3809576.

[10] G. V. Cormack, C. L. A. Clarke, and S. Buettcher, “Reciprocal Rank Fusion Outperforms Condorcet and Individual Rank Learning Methods,” in *Proceedings of the 32nd Annual International ACM SIGIR Conference*, pp. 758-759, 2009. doi: 10.1145/1571941.1572114.

[11] K. Jaervelin and J. Kekaelaeinen, “Cumulated Gain-Based Evaluation of IR Techniques,” *ACM Transactions on Information Systems*, vol. 20, no. 4, pp. 422-446, 2002. doi: 10.1145/582415.582418.

[12] A. C. Davison and D. V. Hinkley, *Bootstrap Methods and Their Application*. Cambridge University Press, 1997. doi: 10.1017/CBO9780511802843.

---

## Report Use Note

This document is intended for full-project review, advisor discussion, manuscript preparation, and planning of follow-up experiments. Its numerical results are verified aggregate evidence within the stated stage boundaries. It should not be used as a substitute for protected source data, as legal advice, or as a commercial deployment recommendation without a separately designed and authorized study.
