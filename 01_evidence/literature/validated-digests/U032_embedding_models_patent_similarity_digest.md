---
paper_id: U032
title: "A comparative analysis of embedding models for patent similarity"
authors: "Grazia Sveva Ascione, Valerio Sterzi"
year: 2024
venue: "arXiv preprint (arXiv:2403.16630)"
affiliation: "Bordeaux School of Economics (Université de Bordeaux)"
pdf_sha256: "83e960fef77fcdbff639a21a425095f0f99b6620b48fa7a886170654d602915f"
eb_status: "ingest_new"
tier: "B"
extraction_cache: "extraction-cache/U032.md"
digest_created: "2026-07-25"
schema_version: "PDF_DIGEST_SCHEMA_V1"
---

# U032: A Comparative Analysis of Embedding Models for Patent Similarity

## Bibliographic Identity
Ascione & Sterzi 2024, arXiv:2403.16630, Bordeaux School of Economics. SHA-256 verified against manifest (exact match).

## Classification
**Tier B.** Contains a genuine patent-similarity retrieval-adjacent evaluation (comparing static vs. contextual embeddings via a novel ground-truth from patent interferences), with quantitative results (% of cases assigning max/min cosine similarity correctly). Not a retrieval-metric (Recall@k/MAP/NDCG) benchmark and evaluation set is very small (133 pairs), so it does not reach Tier A; it is a methods-comparison economics paper (patent-to-patent similarity for innovation-economics use), not a prior-art search system.

## Research Problem / Method
Investigates whether static (word2vec/doc2vec) or contextual (SentenceTransformer/SBERT) embeddings better estimate patent-to-patent (p2p) textual similarity, and which SBERT training regime performs best. Novel contribution: uses **patent interferences** (USPTO cases where an examiner found two independent applications' claims covering the same invention) as a small ground-truth benchmark of "maximum similarity" claim pairs (133 pairs, from Ganguli et al. 2020's interference dataset cross-referenced with PatentsView claims data, 2001-2014). Compares 5 models: Word2vec TF-IDF (Hain et al. 2022), Doc2vec (Whalen et al. 2020), augmented SBERT "PatentSBERTa" (Bekamiri et al. 2021), and two original models trained by the authors — **Patent SBERT-ub** (RoBERTa-base fine-tuned via SBERT triplet loss on CPC-class-matched patent abstract triplets from PatentsView) and **Patent SBERT-adapt-ub** (domain-adapted variant of the pretrained SBERT architecture). Evaluation: for each of the 133 interference pairs, checks whether a model assigns the highest cosine similarity to the true (ground-truth-matched) claim pair vs. random same-CPC-class negative pairs, and separately checks minimum-similarity assignment on randomly generated (non-matching) pairs.

## Main Findings
Across all 5 models (Table 3): Patent SBERT-ub-adapt best on both max-similarity (52%) and min-similarity (40%) correctness; Patent SBERT-ub second (32%/26%); Word2vec TF-IDF (11%/15%) and Doc2vec (4%/6%) far behind; PatentSBERTa surprisingly weak (1%/13%). Restricted to SBERT-only comparison (Table 4, apples-to-apples): SBERT-ub-adapt 60%/47%, SBERT-ub 37%/30%, PatentSBERTa 3%/23% — the domain-adapted model is consistently best. Key qualitative conclusion: static embeddings (word2vec) trained on very large corpora (48M abstracts) remain competitive with/superior to some contextual models (PatentSBERTa, trained on only 3,432 claim pairs) — i.e., training-data scale, not architecture alone, drives performance; there is no clear universal superiority of contextual over static embeddings in this task.

## Limitations
Acknowledged: no independently-labeled ground truth for *dissimilar* patents (negatives are only randomly generated, not verified as truly dissimilar); very small evaluation set (133 pairs) limits statistical power; domain-adapted SBERT may be less general-purpose than the base architecture; training data for the two new models used only a 10% random subsample of the triplets dataset (1 epoch). Additional: PatentSBERTa's poor performance here may reflect a mismatch in evaluation setup vs. its original training/eval protocol (not directly reproduced) — an important caveat before treating this as SOTA-overturning by itself.

## Track C/R/S Relevance (proposed, NOT AUTHORIZED / execution-closed)
Track C: MODERATE — the core finding (domain-adapted contextual embeddings > generic pretrained embeddings; training-data scale/domain-adaptation can outweigh raw architecture choice) is directly relevant to embedding-model selection for Track C candidate generation. Track R: NOT RELEVANT. Track S: NOT RELEVANT.

## Relationship to Papers A–D
No direct connection. This is a small-scale, patent-interference-based similarity study distinct from DAPFAM/PatenTEB's family-level cross-domain retrieval framework; its % max/min-similarity-assignment metric is not comparable to Recall@k/MAP/NDCG and must not be cross-compared with Papers A–D or DAPFAM (do-not-cross-compare per schema §15).

## Verification Warnings
Non-blocking. Tables 1-4 extracted with markdown-grid artifacts (column headers split across rows) but all headline percentage values were confirmed readable and consistent with the prose discussion (e.g., "52%"/"40%" for SBERT-ub-adapt matches Table 3's presented figures).

## EB Cross-Check
Query: "comparative analysis embedding models patent similarity Patent SBERT-ub domain adaptation patent interferences Ascione Sterzi" (narrow SHA/title/arXiv-ID check). Result: NO_MATCH (returned only unrelated PatenTEB, DAPFAM, IS1 literature-matrix records; no record for this SHA, title, or arXiv ID 2403.16630). → **ingest_new**.

---
**Digest Author:** Batch 2A Processing Agent · **Batch ID:** BATCH_2A · **Processing Status:** ✅ COMPLETED · **Content Coverage:** Full inline extraction (~8 pages) read.

**END OF DIGEST**
