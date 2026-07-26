---
paper_id: U036
title: "Towards Automated Patent Workflows: AI-Orchestrated Multi-Agent Framework for Intellectual Property Management and Analysis (PatExpert)"
authors: "Sakhinana Sagar Srinivas, Vijay Sri Vaikunth, Venkataramana Runkana"
year: 2024
venue: "NeurIPS 2024 Workshop on Open-World Agents (OWA-2024)"
affiliation: "TCS Research; IIT-Palakkad"
pdf_sha256: "6840dc1ed45a2865c72748a1779ecc427178acc4ff1a7a713d93c94ee2b48bf2"
eb_status: "ingest_new"
tier: "C"
extraction_cache: "extraction-cache/U036.md"
digest_created: "2026-07-25"
schema_version: "PDF_DIGEST_SCHEMA_V1"
---

# U036: PatExpert — AI-Orchestrated Multi-Agent Framework for Patent Analysis

## Bibliographic Identity
Srinivas, Vaikunth & Runkana 2024, NeurIPS 2024 Workshop on Open-World Agents, TCS Research + IIT-Palakkad. SHA-256 verified against manifest (exact match).

## Classification
**Tier C.** PatExpert is a multi-agent framework for patent **classification, acceptance prediction, abstractive summarization, claim generation, multi-patent comparative analysis (ODQA), and scientific hypothesis extraction** — not a prior-art retrieval/reranking system. Its "multi-patent analysis" ODQA component uses Graph Retrieval-Augmented Generation (GRAG) internally, but this retrieves from a knowledge graph built from a fixed small set of already-identified patents for cross-document Q&A, not prior-art candidate search over a corpus. No Recall@k/MAP/NDCG-style retrieval metric is reported for a patent-retrieval task (the Recall@K/NDCG@K in Table 2 measure tool/agent *selection* by the meta-agent, not document retrieval). Tier C — domain-adjacent, non-retrieval task.

## Research Problem / Method
Proposes an autonomous multi-agent conversational framework: a meta-agent (Meta-Llama-3.1-405B) interprets user queries, decomposes patent workflows into sub-tasks via a Directed Acyclic Graph (DAG), and delegates to fine-tuned expert sub-agents (GPT-4o-mini) specialized per task (classification, acceptance prediction, claim generation, summarization, multi-patent GRAG-based ODQA, SAO-based hypothesis extraction). A critique-agent layer (Gold-LLM-as-a-Judge = GPT-4o; Reward-LLM-as-a-Judge = Nvidia Nemotron-4-340B-Reward) evaluates outputs and triggers iterative revision. For multi-patent analysis, synthetic Retrieval-Augmented Fine-Tuning (RAFT) datasets are generated via a Mixture-of-Agents (MoA) pipeline (LLaMA-3.1-405B + Nemotron-4-340B as proposers, GPT-4-Turbo as aggregator) to fine-tune the expert model, paired with a Neo4j-style knowledge graph (built via chunking → embedding → LLM-extracted subject-predicate-object triples) for semantic retrieval at inference time. Evaluated on the Harvard USPTO Patent Dataset (HUPD, 2015-2017 subset, 80-10-10 split) against six frozen (non-fine-tuned) proprietary baselines: GPT-4, GPT-4-Turbo, Claude 3 Opus, Claude 3 Haiku, Gemini 1.5 Pro, Gemini 1.5 Flash.

## Main Findings
PatExpert reports the top score on every single metric across all nine result tables: task planning (TUA 0.94, Acc 0.91, DGC 0.95 vs. next-best GPT-4's 0.92/0.89/0.93); tool selection (Recall@K 0.95, NDCG@K 0.93); tool calling (PC 0.95, EA 0.96, lowest ER 0.04); classification/acceptance (EM 0.90/0.91, F1 0.95/0.96 vs. GPT-4's 0.80/0.81, 0.87/0.88); abstractive summarization (BLEU 0.85/ROUGE-L 0.83 vs. GPT-4's 0.72/0.70); claim generation (BLEU 0.88/ROUGE-L 0.86); multi-patent analysis (BLEU 0.90/ROUGE-L 0.87); user-centric evaluation (Likert satisfaction 4.8/5); and knowledge-graph quality (Triple Accuracy 94-95%). The claimed mechanism for the gap: baseline models are evaluated **frozen/zero-shot** (no fine-tuning, "given the impracticality... due to their large size"), whereas PatExpert's expert sub-agents are **fine-tuned per task** on HUPD data — meaning the comparison is fine-tuned-vs-zero-shot, not an architecture-vs-architecture comparison.

## Limitations
Acknowledged: framework does not yet handle multilingual patent processing/translation (stated as future work). Not acknowledged but material: (1) **baseline asymmetry** — comparing a task-specifically-fine-tuned system against zero-shot frozen proprietary LLMs conflates "multi-agent orchestration benefit" with "fine-tuning benefit," so the headline gap cannot be attributed to the multi-agent architecture itself; (2) all reported baseline scores across all nine tables follow a suspiciously smooth, near-monotonic ranking (GPT-4 > Claude 3 Opus > Gemini 1.5 Pro > Gemini 1.5 Flash > GPT-4 Turbo > Claude 3 Haiku) with PatExpert always highest by a consistent margin — this pattern warrants independent verification before treating the numbers as an unbiased comparison; (3) evaluation ground truth for hypothesis generation and multi-patent analysis is itself LLM-generated ("Gold-LLMs like GPT-4o"), creating potential circularity (LLM-as-judge evaluating LLM-generated references); (4) small/short 2015-2017 HUPD subset, no reported statistical significance testing; (5) not a prior-art retrieval evaluation at all — no comparison to Papers A-D's task is possible in principle.

## Track C/R/S Relevance (proposed, NOT AUTHORIZED / execution-closed)
Track C: LOW — not a candidate-generation/prior-art-retrieval system; the GRAG knowledge-graph construction technique (chunking → embedding → LLM-extracted triples → semantic-similarity graph traversal) is a tangentially relevant multi-hop retrieval technique but applied to a fixed small patent set, not corpus-scale candidate generation. Track R: NOT RELEVANT. Track S: NOT RELEVANT.

## Relationship to Papers A–D
No direct connection. PatExpert addresses classification/generation/summarization tasks entirely distinct from Papers A-D's prior-art retrieval/reranking focus; no metrics are comparable (EM/F1/BLEU/ROUGE for classification/generation vs. DAPFAM's family-level Recall@100/NDCG@100) and none are cross-compared here.

## Verification Warnings
Non-blocking for the digest's characterization (task/method description), but the **headline superiority claims carry a real reproducibility/bias concern** flagged above (fine-tuned-vs-frozen baseline asymmetry, near-perfectly-ordered baseline rankings, self-generated evaluation ground truth) — any future citation of PatExpert's specific EM/F1/BLEU numbers as "state-of-the-art" should note this caveat rather than treating the comparison as controlled. All tables were extracted cleanly (no OCR/grid-damage) — the concern is about experimental design, not extraction fidelity.

## EB Cross-Check
Query: "PatExpert AI-orchestrated multi-agent framework patent classification claim generation GRAG knowledge graph Sakhinana TCS Research" (narrow SHA/title-scoped check; no DOI/arXiv ID found in paper). Result: NO_MATCH (returned only unrelated IS1 literature-matrix/DAPFAM/PatenTEB/benchmarking-patent-embeddings records; no record for this SHA or title). → **ingest_new**.

---
**Digest Author:** Batch 2A Processing Agent · **Batch ID:** BATCH_2A · **Processing Status:** ✅ COMPLETED · **Content Coverage:** Full paper + appendix read (~16 pages).

**END OF DIGEST**
