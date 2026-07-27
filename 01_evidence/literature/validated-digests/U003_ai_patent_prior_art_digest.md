---
unique_id: U003
priority_tier: A
sha256: 260940c71aeaf5d091fdf06d5739a2ab7c84f39e47c454787e8a55fe672983c1
canonical_path: research/ref-paper/is1/pdfs/03_artificial_intelligence_for_patent_prior_art_2021.pdf
size_bytes: 5220231
title: "Artificial intelligence for patent prior art searching"
authors: "Rossitza Setchi; Irena Spasić; Jeffrey Morgan; Christopher Harrison; Richard Corken"
year: 2021
venue: "World Patent Information 64 (2021) 102021"
doi: "10.1016/j.wpi.2021.102021"
arxiv: null
extraction_cache: source-packet/03-priority-papers/extraction-cache/U003.md
experience_brain_match: no
recommended_ingestion_action: ingest_new
digest_status: completed
digest_prepared: 2026-07-24
pass_type: "Unique-PDF digestion Batch 1 (token-efficient two-stage protocol)"
authority: "External Knowledge (not Grounded Experience, not Paper D evidence)"
---

# U003: Artificial Intelligence for Patent Prior Art Searching

**Unique ID:** U003 · **Priority tier:** A · **SHA-256:** `260940c7…672983c1`
**Canonical path:** `research/ref-paper/is1/pdfs/03_artificial_intelligence_for_patent_prior_art_2021.pdf`

## Bibliographic Identity

- **Title:** Artificial intelligence for patent prior art searching
- **Authors:** Rossitza Setchi (Cardiff University, School of Engineering), Irena Spasić & Jeffrey Morgan (Cardiff University, School of Computer Science and Informatics), Christopher Harrison & Richard Corken (UK Intellectual Property Office)
- **Year:** 2021 (received 2020-04-13; accepted 2021-01-28; online 2021-02-18)
- **Venue:** *World Patent Information*, vol. 64, art. 102021 (Elsevier, peer-reviewed journal)
- **DOI:** https://doi.org/10.1016/j.wpi.2021.102021

## Research Problem

The study asks whether AI can assist patent examiners in the prior art search process — a needle-in-a-haystack task across 100M+ published applications worldwide. It decomposes examiner search into sub-processes (identifying keywords, forming a search statement, selecting classifications, expanding queries, retrieving, sifting/ranking, visualising) and asks which are amenable to AI support. The framing is explicitly **human-machine systems / human-in-the-loop**, not full automation.

## Dataset and Evaluation Setting

- **Training data (UK IPO-supplied, publication dates ≤ 2018-12-31):** PATSTAT bibliographic database (Autumn 2018), GB full-text patents (1979–2018), EP full-text (1978–2018), US full-text (1976–2018). **Examiner search statements were withheld for data-security reasons** — a key constraint on the study design.
- **Test data:** patents published since 2019-01-01 in three technology sectors (Civil Engineering, Computing, Transporting). For each sector, 10 test patents were used as queries; each retrieved up to 30 candidates, blended with 30 random patents and shuffled (blinded), giving ≤60 per working list.
- **Evaluators:** two IPO patent examiners per sector (six total) annotated relevance on a 3-point Likert scale (Yes/Maybe/No) via an EpoqueNet working list; ranks hidden but preserved for Precision@k.
- **Measures:** classification → F-measure (precision/recall); IR & ranking → Precision@k (k=10/20/30); topic modelling → interpretability via inter-examiner agreement (weighted Cohen's κ); usability → focus group. **Recall is explicitly declared unmeasurable** in patent search (a single novelty-destroying citation can end a search).

## Method

A proof-of-concept experimental platform mapping AI techniques to examiner sub-tasks:
- **Classification** into IPC/technology domain: linear **SVM** trained with SGD (scikit-learn), input = title + first 2000 words of description; 75/25 train/test split. SVMs chosen over neural nets (which scored best but risked overfitting on small per-domain data — invoking the "no free lunch" theorem).
- **Query expansion / synonym suggestion:** **WordNet** (lexical ontology), **word2vec** (domain-specific embeddings).
- **Topic modelling / clustering:** **Latent Dirichlet Allocation (LDA)**, 10 topics × 15 keywords.
- **Retrieval:** **Elasticsearch** over the patent corpus.
- **Pipeline:** examiner defines search statement → system classifies → extracts keywords → suggests expansions → examiner curates → system retrieves → assorts into topics → ranks → colour-codes content.

## Main Findings

1. **Classification is near-perfect but on an easy 3-class split:** SVM reached 100% precision/recall/F-measure across all three domains (support 33,097). Framed as due-diligence potential for pre-filing, but the three-domain task is coarse (see warnings).
2. **Retrieval/ranking precision is modest:** across six examiners, precision varied 34–50% (overall average ~38%); **Precision@10 ranged 30–50%**, i.e. the first page held ~3–5 relevant documents.
3. **AI is less effective at formulating search queries** — the single most important, knowledge-intensive step. The paper concludes search-statement construction "will remain a human task" and that no current AI can process an application and generate a usable search statement.
4. **Topic modelling shows promise for visualisation:** moderate examiner confidence (~2.95–3.10 on a 5-pt scale) and variable similarity/interpretability; strongest in Transporting.
5. **Human variability dominates:** examiners formulating queries independently produced significantly different result sets; inter-annotator agreement (Cohen's κ) was fair in Civil Engineering/Computing, unexpectedly low in Transporting.
6. **Overall verdict:** AI can reduce time/cost of *sifting/ranking* retrieved patents, but full automation of the filing/search process is not feasible; the human-in-the-loop and better decision-support tooling are emphasised.

## Limitations

1. **Search and retrieval could not be cleanly separated** — because IPO withheld examiner search statements, the study could not isolate retrieval/ranking quality from query-formulation quality (authors note a better design would have fixed examiner statements and evaluated retrieval only).
2. **Tiny evaluation scale:** 3 sectors × 10 query patents × 6 examiners; qualitative focus group; results are preliminary.
3. **Recall not measurable** by design; precision-only IR evaluation.
4. **Classification task is coarse** (3 broad domains) — 100% accuracy does not transfer to fine-grained IPC/CPC subclass routing.
5. **No neural dense retrieval / rerankers / LLMs** — classical ML stack (SVM, WordNet, word2vec, LDA, Elasticsearch); predates transformer retrieval.
6. **UK-IPO-specific** data and examiner workflow; generalisation to EPO/USPTO/pharma unknown.

## Track C Relevance (candidate-exposure headroom — proposed, NOT AUTHORIZED)

**High.** The paper is squarely a candidate-exposure / query-formulation study. Its central result — *AI is less effective at formulating search queries*, with query-statement construction remaining a human task — is direct external evidence bearing on Track C's premise that candidate exposure is the binding constraint. WordNet/word2vec query expansion is exactly the class of candidate-expansion technique Track C would investigate; this paper reports it as helpful-but-insufficient without human curation. Precision@10 of 30–50% under a manual+AI hybrid provides a real-world reference point for how hard OUT-of-domain exposure is.

## Track R Relevance (fixed-pool ranking headroom — proposed, NOT AUTHORIZED)

**Moderate.** Ranking is one of the sub-tasks (documents ranked within retrieved topics, evaluated via Precision@k). But ranking here is classical similarity ordering over an Elasticsearch pool, not instruction-optimized reranking on a frozen top-K (Paper D's surface). It supports the general claim that ranking-stage gains exist but are modest, without testing prompt/instruction optimization.

## Track S Relevance (SkillOpt / prompt evolution — revision-stage, EXECUTION CLOSED)

**None/negligible.** No prompt optimization, no self-evolving skills, no LLM instruction tuning. Classical ML only. Not relevant to Track S beyond the generic observation that the knowledge-intensive query step resists automation.

## Relationship to Papers A–D

- **Strong thematic corroboration of Paper A (pilot provenance, query rewriting = NULL):** Setchi et al. independently conclude AI cannot reliably formulate search statements and that query construction stays human — consistent with Paper A's finding that label-informed query rewriting gained +0.000702 (CI crosses 0, not confirmed). Frame as *convergent external evidence*, NOT as Paper A/Paper D evidence.
- **Adjacent to Paper D (frozen, fixed-pool scalar reranking):** both touch ranking, but Paper D tests Qwen3-Reranker-0.6B scalar-instruction optimization on DAPFAM family-level frozen top-100; U003 uses classical retrieval on UK-IPO documents. Different corpus, granularity, and method — not closest prior art to Paper D's channel.
- **Not DAPFAM-based;** no overlap with the DAPFAM benchmark, GEPA, or MIPROv2.
- **Citation discipline:** cite U003 as published external literature; do NOT conflate its query-formulation finding with Paper A's internal diagnostic (Paper A is pilot provenance, not Paper D evidence).

## Verification Warnings

1. **100% classification accuracy is on a 3-domain split** — do not cite as evidence that patent classification is "solved"; it does not reflect fine-grained IPC routing.
2. **Precision figures (30–50% @10, ~38% avg)** come from 6 examiners over 30 query patents total — small-n, preliminary; treat as indicative, not benchmark-grade.
3. **Retrieval and query formulation are confounded** (examiner statements withheld) — the "AI less effective at query formulation" conclusion is partly a study-design artifact the authors themselves flag.
4. **Recall unmeasured by design** — comparisons to recall-based benchmarks (e.g., DAPFAM Recall@100) are not apples-to-apples.
5. No numeric table values beyond those quoted were transcribed; consult the cached extraction (`extraction-cache/U003.md`, Tables 5–14) if exact per-examiner figures are needed.

## Experience Brain Cross-Check (READ-ONLY)

- **experience_brain_match:** no
- **matched_knowledge_ids:** none specific to Setchi 2021; nearest returns were KNO-5449A7642CF9 (IS1 literature matrix — DAPFAM/PatenTEB), KNO-528A290EA2E4 (PatenTEB), KNO-20DDBF1D30A0 (candidate-exposure synthesis), plus governance records (KNO-C9CC57A8EC35, KNO-6BC9B4ED3BC2).
- **memory_conflict:** none
- **query mode:** read-only; no record created or modified.
- **recommended_ingestion_action:** ingest_new (if the corpus later ingests query-formulation / human-in-the-loop prior-art evidence). The candidate-exposure synthesis (KNO-20DDBF1D30A0) H2 hypothesis on traceable query expansion is thematically supported by this paper.

## Status

✅ **completed** — Token-efficient two-stage protocol: extracted once to `extraction-cache/U003.md` (12 pages, 8,459 words); targeted reads of title/abstract/intro, methods §3.1–3.3, results §4.1–4.4, conclusions §5, and Tables 4/6/9. Full markdown not loaded wholesale.

---
*Digest prepared 2026-07-24. Source repository unmodified. Experience Brain queried read-only.*
