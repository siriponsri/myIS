---
paper_id: U038
title: "H-ProtoRAG: A hierarchical prototype-based retrieval-augmented framework for multilingual CPC patent classification and prior-art retrieval"
authors: "Zahra Elmi"
year: 2026
venue: "Information Processing and Management 63 (2026) 104861"
affiliation: "Department of Software Engineering, Beykoz University, Istanbul, Turkey"
pdf_sha256: "ab0a43419308ca9b3b4400888c56daaa81b3c5b9e459af35da20bb10edb434f2"
eb_status: "ingest_new"
tier: "A"
extraction_cache: "extraction-cache/U038.md"
digest_created: "2026-07-25"
schema_version: "PDF_DIGEST_SCHEMA_V1"
---

# U038: H-ProtoRAG — Hierarchical Prototype-Based RAG for Multilingual CPC Classification and Prior-Art Retrieval

## Bibliographic Identity
Elmi 2026, Information Processing and Management 63, 104861 (Elsevier), Beykoz University, Istanbul. DOI: 10.1016/j.ipm.2026.104861. Received Dec 2025, accepted Apr 2026. SHA-256 verified against manifest (exact match).

## Classification
**Tier A.** Single-author paper combining **CPC classification** (primary contribution) with a genuine **prior-art retrieval** component evaluated on CLEF-IP 2010 with clean, extractable retrieval metrics (nDCG@10, Precision@1, Recall@50) against a BM25 baseline, plus zero-shot cross-lingual retrieval (Table 4) and controlled ablation baselines that isolate hierarchy-only vs. retrieval-only contributions (Table 2, Table 7). While the retrieval component is secondary to the classification contribution and uses only ~100 CLEF-IP query topics, the presence of real retrieval metrics with a documented baseline comparison and rigorous ablation methodology places this at Tier A rather than B — consistent with this batch's pattern of classifying methodologically rigorous multi-task papers with genuine (if secondary) retrieval evaluation at Tier A.

## Research Problem / Method
Motivated by three gaps in multilingual patent analytics: (1) CPC/IPC classification is typically treated as flat multi-label prediction, ignoring hierarchical structure so errors aren't penalized by severity (cross-section vs. within-branch); (2) classification and prior-art retrieval are designed/evaluated separately, so retrieved evidence rarely informs classification confidence; (3) few systems jointly handle multilingual transfer with calibrated probabilities. Proposes **H-ProtoRAG**: a dual-encoder (non-shared) architecture with section-wise pooling (separate [CLS] vectors for Title/Abstract/Claims combined via learnable weights) feeding (a) a **prototype-structured CPC embedding space** (500 learnable class prototypes, trained via multi-loss = cross-entropy + supervised contrastive + prototype + hierarchy-distance-penalty), (b) a **hybrid dense (FAISS ANN) + sparse (BM25) retriever** with score fusion (λ≈0.5, tuned on dev only) and optional cross-encoder reranking of top-K=50, and (c) a **claim-evidence NLI head** (three-way entailment/neutral/contradiction) supervised by a fixed multilingual NLI teacher (XLM-R fine-tuned on XNLI) — with token-overlap heuristics retained only as an ablation, explicitly avoiding treating lexical overlap as semantic entailment. Retrieved evidence feeds back into CPC posterior recalibration, not just ranking. Trained/evaluated on 1.2M Turkish/English patents (BigQuery CPC corpus) plus BIGPATENT, PatentMatch, CLEF-IP 2010, MAREC, and PatTR for retrieval/multilingual/distillation components. Controlled baselines: a CSPC-LA-style hierarchy-only classifier and a PAI-NET-style retrieve-and-propagate model, both matched on backbone/splits/granularity, isolating the incremental contribution of the full joint design.

## Main Findings
**In-domain CPC classification (Table 2, Section+subclass granularity, ~420 TR / ~610 EN active labels):** Turkish Micro-F1 45.3% (PatentBERT) → 55.3% (H-ProtoRAG), Hier-F1 55.0%→63.7%; English Micro-F1 52.0-53.8%→58.6%, beating the strongest ablation baseline (PAI-NET-style+reranking, 57.2% EN) by 1.4 points. **Cross-source transfer (Table 3):** TR→EN Micro-F1 47.1% (−14.8% relative drop from in-domain), EN→TR 49.2% (−16.0%); Hier-F1 remains comparatively high (53.4%/55.8%) even as Micro-F1 drops, meaning residual errors mostly stay within the correct CPC section — explicitly flagged as conflating language shift with patent-office/drafting-style shift, not a clean language-only transfer measure. **Prior-art retrieval (CLEF-IP 2010, hybrid dense-sparse + cross-encoder reranking):** nDCG@10 0.212 (BM25) → 0.301; Precision@1 0.41→0.60; Recall@50 maintained at 69.4%. **Zero-shot cross-lingual retrieval (Table 4, Japanese claims → English pool):** Recall@50 45.0%, nDCG@10 0.20 — explicitly framed by the author as "a sanity check... rather than evidence of strong zero-shot Japanese retrieval," given modest ranking quality. **Ablation build-up (Table 7):** baseline BERT+CE 45.2% Micro-F1 → +pooling 46.7 → +hard negatives 48.1 → +SupCon 49.4 → +prototypes 50.6 → +hierarchy 50.8 (Hier-F1 62.0→63.3, showing hierarchy term mainly reduces error severity not flat accuracy) → +RAG fusion+reranker 52.1 → +weak NLI (teacher) 53.2, final full config 55.3. **Calibration:** Expected Calibration Error 12.4%→6.1%; top-5% prediction precision 71%→85%.

## Limitations
Extensively self-acknowledged (dedicated §4.3.3 Limitations + §6 Future Work): evaluation limited to Turkish/English/German/French and specific data sources (results may not generalize to other jurisdictions/CPC adoption practices); CPC label space restricted to section+first-level subclass only (not deeper CPC/IPC levels used in real examination); claim-evidence NLI supervision remains a fixed general-domain teacher (XLM-R/XNLI), not gold patent-domain entailment annotation — explicit domain mismatch risk; main TR-EN cross-source transfer results conflate language shift with patent-office/document-style shift (no within-source cross-lingual control); multi-component training pipeline is complex, may hinder reproducibility/deployment; retrieval+reranking increases end-to-end latency; cross-source multilingual performance uneven across language families. Additional (from digest analysis): retrieval evaluation is limited (~100 CLEF-IP query topics, single dataset); zero-shot JA→EN retrieval is explicitly caveated by the author as not strong evidence; no code/model release confirmed at time of this digest (stated "will be released... upon acceptance").

## Track C/R/S Relevance (proposed, NOT AUTHORIZED / execution-closed)
Track C: HIGH — the hybrid dense(FAISS)+sparse(BM25) score-fusion candidate generator (Eq. 1, λ≈0.5 dev-tuned) directly parallels Track C's candidate-generation design space; the paper's own comparison against graph/GNN-based retrieval alternatives (explicitly rejected due to inconsistent relational-graph availability across patent offices) is a relevant design-rationale precedent. Track R: MODERATE — cross-encoder reranking of top-K=50 candidates is directly analogous to Track R's fixed-pool reranking; the paper's controlled ablation isolating "retrieval fusion+reranking" (52.1) from "weak NLI supervision" (52.9→53.2) gains is a useful methodological template for attributing gains cleanly. Track S: LOW — the evidence-conditioned posterior recalibration (using retrieval signals to adjust classification confidence, not just rank) is a novel fusion-adjacent idea but operates on classification labels, not multi-source retrieval synthesis.

## Relationship to Papers A–D
No direct connection. H-ProtoRAG's CLEF-IP 2010 retrieval metrics (nDCG@10, Precision@1, Recall@50) use a different, smaller collection (~100 query topics) and different relevance construction than DAPFAM/Papers A-D's family-level cross-domain framework; no cross-comparison is made here (per schema §15). The paper's CPC classification task and metrics (Micro/Macro/Hier-F1) are entirely orthogonal to Papers A-D's retrieval/reranking focus.

## Verification Warnings
Non-blocking. Core sections (Introduction, Related Work, Method §3, Results §4 including Tables 2-7, Discussion §4.3, Conclusion §5, Future Work §6, Appendix baseline-implementation detail) read directly; all headline tables extracted cleanly as structured markdown with no OCR/grid-damage. Appendix sections beyond the baseline-implementation detail (C onward — calibration/bootstrap procedure detail, Table 10-13 full contents) were not individually transcribed; no headline claim in this digest depends on those untranscribed appendix subsections, as the corresponding summary numbers (nDCG@10 0.212→0.301, ECE 12.4%→6.1%) were read directly from the abstract and main-body discussion text.

## EB Cross-Check
Query: "H-ProtoRAG hierarchical prototype-based retrieval-augmented multilingual CPC patent classification prior-art retrieval Elmi Information Processing Management 2026" (narrow SHA/title/DOI-scoped check; DOI 10.1016/j.ipm.2026.104861). Result: NO_MATCH (returned only unrelated IS1 literature-matrix/DAPFAM/PatenTEB/plan records; no record for this SHA, title, or DOI). → **ingest_new**.

---
**Digest Author:** Batch 2A Processing Agent · **Batch ID:** BATCH_2A · **Processing Status:** ✅ COMPLETED · **Content Coverage:** Core sections + all main result tables (2-7) read directly (~1080 of 1366 extraction lines); Appendix sections C onward confirmed present but not individually transcribed.

**END OF DIGEST**
