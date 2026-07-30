---
paper_id: U034
title: "A Survey on Patent Analysis: From NLP to Multimodal AI"
authors: "Homaira Huda Shomee, Zhu Wang, Sathya N. Ravi, Sourav Medya"
year: 2024
venue: "arXiv preprint (arXiv:2404.08668)"
affiliation: "Department of Computer Science, University of Illinois Chicago"
pdf_sha256: "94b2ef789464ff2c35599f0cc8399d4710dc8697317fc068723f9841f1676f17"
eb_status: "ingest_new"
tier: "A"
extraction_cache: "extraction-cache/U034.md"
digest_created: "2026-07-25"
schema_version: "PDF_DIGEST_SCHEMA_V1"
---

# U034: A Survey on Patent Analysis: From NLP to Multimodal AI

## Bibliographic Identity
Shomee, Wang, Ravi & Medya 2024, arXiv:2404.08668, University of Illinois Chicago (Dept. of Computer Science). Maintains a companion GitHub repo ("AI4Patents-survey"). SHA-256 verified against manifest (exact match).

## Classification
**Tier A.** A comprehensive, recent (2024) survey introducing a novel task-based taxonomy (patent classification, retrieval, quality analysis, generation) spanning traditional ML through PLMs/LLMs/multimodal models, with dedicated comparison tables per task and explicit coverage of patent retrieval methods (Table 2/9) including several already-encountered papers in this literature set (Siddharth et al. 2022 = U018; multimodal image+text retrieval). Directly on-topic connective/taxonomic infrastructure for interpreting the whole literature review, comparable in role to U033 — placed at Tier A for its breadth, recency, and explicit organization of the retrieval-methods landscape rather than for presenting new experiments of its own.

## Research Problem / Method
Argues existing patent surveys (Gomez & Moens 2014; Krestel et al. 2021; Hanbury et al. 2011; Casola & Lavelli 2022) are outdated and lack task-specific organization, especially missing recent LLM/multimodal trends. Proposes a new taxonomy organizing patent-analysis literature into four tasks — **Patent Classification** (multi-label IPC/CPC classification), **Patent Retrieval** (text + image retrieval for novelty/infringement checks), **Patent Quality Analysis** (citation/claim-count-based value prediction), **Patent Generation** (LLM-based drafting of claims/abstracts/specifications) — further subdividing each by method family (traditional neural networks, ensemble models, PLMs, multimodal models, LLMs). Surveys ~40+ individual studies per category with comparison tables (Tables 1-5) summarizing embeddings/methods/components per paper, and appendix tables (6-11, not individually transcribed in this digest) reporting quantitative evaluation metrics per study.

## Main Findings
For **Patent Retrieval** (Sec 3.2, Table 2): organizes studies by traditional ML (Setchi et al. 2021 — SVM/NaiveBayes/RF/MLP prior-art retrieval), traditional neural networks (Kravets et al. 2017 CNN; Jiang et al. 2021 DUAL-VGG; Kucer et al. 2022 ResNet50 — all image retrieval on DeepPatent), and PLMs/multimodal models (Kang et al. 2020 BERT; Siddharth et al. 2022 = **U018 in this batch** — Sentence-BERT+TransE citation/inventor-KG fusion; Pustu-Iren et al. 2021 — CLIP+RoBERTa multimodal, reported to achieve the **highest mean average precision** among surveyed multimodal approaches; Lo et al. 2024 — BLIP-2+GPT-4V with distribution-aware contrastive loss for tail-class robustness). For **Patent Classification** (Table 1): traces evolution from single-layer LSTM/Word2Vec (Grawe et al. 2017) through BERT/XLNet/RoBERTa (Roudsari et al. 2022, reported as new SOTA, precision up to 0.82 vs. early work's 0.53) to SciBERT domain-adaptive pretraining (Althammer et al. 2021) and Sentence-BERT+KNN (Bekamiri et al. 2024). For **Patent Generation** (Table 4/5): documents the shift from GPT-2 fine-tuning (Lee & Hsiang 2020a; Christofidellis et al. 2022's "PatentGenerativeTransformer") to large-scale patent-specific LLMs (Bai et al. 2024's 240B-token IP-focused LLaMA2/Mixtral fine-tune; Ren & Ma 2024's Qwen2-based drafting agent; Wang et al. 2024b's multi-agent plan-write-review framework) — with the notable finding that **general-purpose LLMs (Llama-3, GPT-4, Mistral) outperform patent-specific fine-tuned models (PatentGPT-J)** on claim generation (Jiang et al. 2024), attributed to stronger generalization/linguistic capacity of larger open models.

## Limitations
Acknowledged (Sec 6, partially read): patent lifecycle length and multi-iteration review process complicate longitudinal evaluation (truncated in extraction at the point of reading). Cross-cutting discussion notes: no universally accepted "gold standard" for patent quality metrics; classification methods show a persistent domain gap between simple architectures (LSTM/BERT, precision ≤0.82) and advanced general LLMs (GPT/LLaMA) not yet systematically applied to classification; generation methods lack rigorous evaluation (BLEU/ROUGE deemed insufficient for legal/factual correctness); direct performance comparisons across retrieval/classification studies are explicitly flagged as unreliable due to differing dataset subsets, class hierarchies, and evaluation metrics.

## Track C/R/S Relevance (proposed, NOT AUTHORIZED / execution-closed)
Track C: HIGH — the retrieval-methods taxonomy (traditional ML → neural → PLM → multimodal) and its explicit note that multimodal (image+text) fusion achieved the highest MAP among surveyed approaches (Pustu-Iren et al. 2021) is directly informative for Track C design choices; independently corroborates U018 (Siddharth et al., already digested) as a recognized citation-KG+SBERT retrieval approach. Track R: LOW — no dedicated reranking taxonomy; citation-based re-ranking is mentioned only as a component of retrieval pipelines, not analyzed as its own category. Track S: NOT RELEVANT — the survey's "Future Directions" (cross-jurisdictional retrieval, foundation models for patents, RAG for patent generation) are forward-looking research suggestions, not this project's roadmap.

## Relationship to Papers A–D
No direct connection. This survey's cited studies use heterogeneous, non-family-level datasets (WIPS, USPTO, DeepPatent, EPO) and metrics not comparable to DAPFAM/Papers A–D's family-level cross-domain framework; no metric cross-comparison is made (per schema §15). Notably corroborates U018 (already in this batch) as an externally-recognized citation-KG+SBERT patent-retrieval method, providing independent confirmation of that paper's placement in the literature.

## Verification Warnings
Non-blocking. Extraction (~1235 lines) was read in full through the core body (Sections 1-6 including all four task sections, discussion/suggestion subsections, future directions, and the start of limitations) — this covers all headline claims in this digest. Detailed quantitative appendix tables (Tables 6-11, reporting per-study evaluation-metric values referenced generically in-text, e.g. "highest accuracy... 0.74," "precision of 0.53," "improved... to 0.82") were confirmed present via in-text citations but not independently re-transcribed from the appendix; the specific numeric values quoted in this digest's Main Findings section were read directly from the main-body discussion text (not the appendix tables) and are therefore reliable without further visual verification.

## EB Cross-Check
Query: "survey patent analysis NLP multimodal AI taxonomy classification retrieval quality generation Shomee Wang Ravi Medya University Illinois Chicago" (narrow SHA/title/arXiv-ID-scoped check; arXiv:2404.08668). Result: NO_MATCH (returned only unrelated IS1 literature-matrix/research-gaps records and two distinct other papers — U079-equivalent novelty-prediction paper and PatenTEB; no record for this SHA, title, or arXiv ID). → **ingest_new**.

---
**Digest Author:** Batch 2A Processing Agent · **Batch ID:** BATCH_2A · **Processing Status:** ✅ COMPLETED · **Content Coverage:** Full core-body read (~600 of 1235 extraction lines: intro, background/taxonomy, all four task method sections with discussion/suggestion subsections, future directions, conclusions, start of limitations); appendix quantitative tables (6-11) confirmed present but not individually transcribed.

**END OF DIGEST**
