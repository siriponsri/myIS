---
unique_id: U018
priority_tier: B
sha256: 4b1023ef0c1e63256232782d5d72aa189133fd510bf282d21680ebfeb730b9cb
canonical_path: research/ref-paper/is1/pdfs/18_enhancing_patent_retrieval_using_text_and_2022.pdf
size_bytes: 1643712
title: "Enhancing Patent Retrieval using Text and Knowledge Graph Embeddings: A Technical Note"
authors: "L. Siddharth; Guangtong Li; Jianxi Luo"
year: 2022
venue: "Data-Driven Innovation Lab, Singapore Univ. of Technology and Design (SUTD)"
doi: null
arxiv: null
extraction_cache: source-packet/03-priority-papers/extraction-cache/U018.md
experience_brain_match: no
recommended_ingestion_action: ingest_new
digest_status: completed
digest_prepared: 2026-07-24
pass_type: "Unique-PDF digestion Batch 1 (token-efficient two-stage protocol)"
authority: "External Knowledge (not Grounded Experience, not Paper D evidence)"
---

# U018: Enhancing Patent Retrieval using Text and Knowledge Graph Embeddings

**Unique ID:** U018 · **Priority tier:** B · **SHA-256:** `4b1023ef…b9cb`
**Canonical path:** `research/ref-paper/is1/pdfs/18_enhancing_patent_retrieval_using_text_and_2022.pdf`

## Bibliographic Identity
Siddharth, Li, Luo (Data-Driven Innovation Lab, SUTD Singapore), 2022 — a technical note in the engineering-design research tradition (InnoGPS lineage).

## Research Problem
Retrieve patents relevant to an *initial set* of patents by representing multiple facets of a patent — text, citation, inventor — in a single embedding, rather than text alone.

## Method (verified against cache)
- **Text embedding:** Sentence-BERT on titles + abstracts (lines 14–15).
- **Citation + inventor embeddings:** **TransE** trained on the citation KG and inventor KG respectively (lines 15–16, 225).
- **Combination:** concatenation of text+citation+inventor selected via a **classification task** as the preferred representation (lines 16–17, 485–487).
- **Retrieval:** multiple initial patents associated to a target via **mean cosine similarity**, used to rank/retrieve targets (lines 18–20, 487–488). Training split 8:1:1, Adam lr 5e-… (line 254).

## Dataset & Evaluation
Applied to two curated sets — a **product family** and an **inventor's portfolio** (lines 20–21, 489). Evaluation is a classification task (representation choice) + a recall task (association) + **qualitative** design-inspiration analysis. **No standard IR benchmark, no MAP/NDCG.**

## Main Findings
- Concatenating text+citation+inventor embeddings gives the preferred patent representation (classification task).
- Mean cosine similarity over multiple initial patents can rank/retrieve relevant targets; retrieved patents surface useful "distant yet in-domain" concepts for design inspiration (lines 474, 489–491).

## Limitations
Note that original-search mechanisms and citation-sharing bias the neighborhood (lines 451, 474); distant in-domain concepts may be missed when patents don't share citations; qualitative/small-scale evaluation on two hand-picked sets; engineering-design domain, not pharma; no IR-metric benchmarking; best embodied inside a support tool (InnoGPS).

## Track C Relevance (candidate-exposure — proposed, NOT AUTHORIZED)
**Medium.** A concrete **multi-view candidate-generation** design: text (SBERT) + citation + inventor signals fused for retrieval — directly analogous to the project's multi-view union hypothesis (H1 in KNO-20DDBF1D30A0). The citation-sharing limitation echoes the cross-domain OUT gap: citation-based neighborhoods miss distant relevant art.

## Track R Relevance (fixed-pool reranking — proposed, NOT AUTHORIZED)
**Low.** Single-stage cosine ranking; no rerank stage.

## Track S Relevance (SkillOpt — EXECUTION CLOSED)
**None.**

## Relationship to Papers A–D
Methodologically relevant, **not closest prior art**. Complements DAPFAM/PatenTEB by adding **knowledge-graph (citation + inventor) facets** to text embeddings — relevant to IS2's KG direction and to Track-C multi-view candidate generation. But domain (engineering design), scale (two curated sets), and evaluation (qualitative, no MAP/NDCG) keep it a Tier-B analogue rather than a benchmark competitor. Its "relevance" = citation/text/inventor similarity, explicitly not legal/novelty judgment.

## Verification Warnings
- Method (SBERT + TransE + concatenation + mean cosine) verified against Abstract (lines 11–21) and Conclusions (481–493).
- No headline IR metric to transcribe; do not attribute MAP/NDCG numbers to this paper. Related-work figures (2.75M patents, 0.8M patents, lines 91/109) belong to *cited* prior work, not this study's dataset — do not misattribute.
- Year (2022) from filename; venue is a lab technical note — confirm exact publication before citing.

## Experience Brain Cross-Check (READ-ONLY)
- **experience_brain_match:** **no** — no Knowledge record carries U018's hash (`4b1023ef…`); nearest return is U012 PatenTEB (`528a290e…`), a different paper.
- **memory_conflict:** none. **query mode:** read-only; nothing created/modified.
- **recommended_ingestion_action:** **ingest_new** (Tier-B; tag for IS2 KG + Track-C multi-view).

## Status
✅ **completed** — reused pre-extracted `extraction-cache/U018.md` (43,041 B); head + targeted greps + one line-range read (481–500). Full markdown not loaded wholesale.

---
*Digest prepared 2026-07-24. Source repository unmodified. Experience Brain queried read-only.*
