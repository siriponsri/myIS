# DEEP RESEARCH EVIDENCE — ArmIndex V02 NEW

**Research date:** 2026-08-04

**Purpose:** summarize external evidence used to design `PLAN_V02_NEW.md`. This file distinguishes reported findings from project design inferences.

---

## 1. AutoIndex

**Source:** O'Nuallain et al., *AutoIndex: Learning Representation Programs for Retrieval*  
https://arxiv.org/abs/2607.18603

**Reported evidence**

- searches executable document transformations;
- holds BM25 fixed;
- agents diagnose failures and synthesize candidate updates;
- reports gains on all eight CRUMB tasks;
- average gains approximately `+8.4% Recall@100` and `+8.3% nDCG@10`.

**Design implication**

Retain representation programs, failure-driven proposals, deterministic execution, immutable lineage, and Recall@100. The new extension is multiple frozen backbones plus cross-backbone transfer.

---

## 2. DAPFAM

**Source:** Ayaou et al., *DAPFAM*  
https://arxiv.org/abs/2506.22141

**Reported evidence**

- family-level benchmark;
- explicit IN/OUT partitions;
- Recall@100 and nDCG@100;
- document/passage granularity, aggregation, lexical/dense retrieval, and RRF;
- severe OUT difficulty.

**Design implication**

Use OUT Recall@100 as primary because multi-arm retrieval/harness composition target relevant-family exposure. Keep nDCG@100 and nDCG@10 for ranking quality.

---

## 3. Patent embeddings and representation interaction

**Sources**

- PatenTEB: https://arxiv.org/abs/2510.22264
- Benchmarking Patent Embeddings: https://arxiv.org/abs/2605.24297

**Reported evidence**

- PatEmbed-large is a strong patent-specific external DAPFAM model.
- Performance depends on model family, scale, text view, and prompt/configuration.
- OUT degradation remains large.
- sparse–dense fusion does not automatically solve domain shift.
- weight adaptation may fail to transfer.

**Design implication**

Use frozen models, exact adapters, and per-retriever representation search. Do not assume a universal view or build around fine-tuning.

---

## 4. Multi-expert routing

**Source:** Lee et al., *RouterRetriever*  
https://arxiv.org/abs/2409.02685

**Reported evidence**

- routing over multiple expert embedding models can outperform a single general model;
- experts can be added/removed;
- routing is lightweight;
- some gains generalize without a dataset-specific expert.

**Design implication**

Retain arms by unique relevant contribution and frontier value, not model diversity alone.

---

## 5. Harness optimization

**Sources**

- Meta-Harness: https://arxiv.org/abs/2603.28052
- Retrospective Harness Optimization: https://arxiv.org/abs/2606.05922
- Direct Harness Optimizer Evaluation: https://arxiv.org/abs/2605.22505

**Reported evidence**

- performance depends on code, tools, context, and workflow;
- agentic outer loops can improve harnesses;
- direct evaluation of optimizer actions matters because trial-and-error can masquerade as informed optimization.

**Design implication**

HarnessOpt uses a constrained DSL, retrieval metrics, controls, matched ablations, immutable batches, and independent verification. The optimizer does not write arbitrary runtime code.

---

## 6. Automated RAG configuration

**Sources**

- AutoRAG: https://arxiv.org/abs/2410.20878
- AutoRAGTuner: https://arxiv.org/abs/2605.02967
- AutoRAG-HP: https://arxiv.org/abs/2406.19251

**Reported evidence**

- RAG module combinations are dataset-dependent;
- declarative configuration reduces engineering overhead;
- hierarchical search reduces evaluation cost.

**Design implication**

Use staged search:

1. common screen;
2. promote at most three arms;
3. per-arm AutoIndex;
4. transfer;
5. bounded HarnessOpt.

---

## 7. Production RAG caution

**Source:** Medrano et al., *Scaling RAG with Fusion*  
https://arxiv.org/abs/2603.02153

**Reported evidence**

- fusion can improve raw recall;
- gains may disappear after reranking/truncation;
- fusion adds latency;
- retrieval quality must be evaluated with production constraints.

**Design implication**

Report p95 latency, cost/query, arm calls, and context implications. Always-on fusion is a control, not the assumed champion.

---

## 8. Legal structured retrieval

**Source:** LegalBench-RAG  
https://arxiv.org/abs/2408.10343

**Reported evidence**

- benchmark focuses on legal retrieval;
- precise snippets are preferred over large imprecise chunks;
- large contexts increase cost, latency, and hallucination risk;
- annotations trace supporting context.

**Design implication**

LegalBench-RAG is a frozen zero-shot transfer diagnostic for commercial-capable arms and the representation grammar. It does not validate legal-decision claims and does not feed back into the patent campaign.

---

## 9. Official model sources

- BGE-M3: https://huggingface.co/BAAI/bge-m3
- PatEmbed-large: https://huggingface.co/datalyes/patembed-large
- Snowflake Arctic Embed M v2.0: https://huggingface.co/Snowflake/snowflake-arctic-embed-m-v2.0
- Qwen3-Embedding-0.6B: https://huggingface.co/Qwen/Qwen3-Embedding-0.6B

**Policy implications**

- BGE-M3: MIT; dense/sparse/multi-vector; core arm freezes one mode.
- PatEmbed-large: CC BY-NC-SA 4.0; research/non-commercial boundary.
- Snowflake: Apache-2.0; exact query prefix and remote-code lock.
- Qwen3 Embedding: Apache-2.0; instruction-aware; official last-token pooling; task instruction frozen.

---

## 10. Final synthesis

The weak framing is:

```text
run five models and select the winner
```

The strong framing is:

```text
learn retriever-conditioned representation programs
measure transfer across heterogeneous frozen retrievers
retain arms by unique exposure and frontier value
optimize a deterministic production harness
report quality, latency, cost, and license boundaries
```

This has a stronger causal story, clearer novelty, better production relevance, and more defensible benchmark path than a plain model sweep.
