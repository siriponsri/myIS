---
unique_id: U010
priority_tier: A
sha256: a2d8cf145bb05db89268aaaf47c71c847d990330fa0621ba935bb0e25feb1f33
canonical_path: research/ref-paper/is1/pdfs/10_memgraph_enhancing_patent_matching_capability_of_2025.pdf
size_bytes: 61364
title: "Enhancing the Patent Matching Capability of Large Language Models via the Memory Graph"
authors: "Qiushi Xiong; Zhipeng Xu; Zhenghao Liu; Mengjia Wang; Zulong Chen; Yue Sun; Yu Gu; Xiaohua Li; Ge Yu"
year: 2025
venue: "SIGIR '25 (Padua, Italy); arXiv:2504.14845v1; Northeastern University China + Alibaba Group"
doi: "10.1145/xxxxxxx.xxxxxxx (placeholder in preprint)"
arxiv: "2504.14845"
extraction_cache: source-packet/03-priority-papers/extraction-cache/U010.md
experience_brain_match: no
recommended_ingestion_action: ingest_new
digest_status: completed
digest_prepared: 2026-07-24
pass_type: "Unique-PDF digestion Batch 1 (token-efficient two-stage protocol)"
authority: "External Knowledge (not Grounded Experience, not Paper D evidence)"
---

# U010: MemGraph — Enhancing the Patent Matching Capability of LLMs via the Memory Graph

**Unique ID:** U010 · **Priority tier:** A · **SHA-256:** `a2d8cf14…5feb1f33`
**Canonical path:** `research/ref-paper/is1/pdfs/10_memgraph_enhancing_patent_matching_capability_of_2025.pdf`

## Bibliographic Identity

- **Title:** Enhancing the Patent Matching Capability of Large Language Models via the Memory Graph
- **Authors:** Qiushi Xiong, Zhipeng Xu, Zhenghao Liu (corresp.), Mengjia Wang, Zulong Chen, Yue Sun, Yu Gu, Xiaohua Li, Ge Yu — Northeastern University (Shenyang, China) + Alibaba Group
- **Venue:** SIGIR '25, July 13–18 2025, Padua · **arXiv:** 2504.14845v1 (21 Apr 2025) · **Code/data:** github.com/NEUIR/MemGraph (open)

## Research Problem

LLM-based patent matching relies on emergent LLM capability but **overlooks patents' hierarchical classification and categorical relationships**, and suffers the **vocabulary-mismatch problem** in a specialised domain. MemGraph asks whether prompting an LLM to traverse its own **parametric memory** — extracting technical **entities** and attributing them to **ontologies** — can inject that missing hierarchical/relational structure and improve matching without additional fine-tuning.

## Method

MemGraph is built on a Retrieval-Augmented Generation (RAG) backbone and adds two memory-graph-derived latent variables:

1. **Entity Traversal** — prompt the LLM to extract ≤10 specific technical entities from the query patent abstract (Table 1 template).
2. **Ontology Traversal** — prompt the LLM to assign three-level IPC-style technical classifications (Major > Sub > Specific) to the query and each candidate, using the extracted entities.
3. **Retrieval augmentation (Z_IR):** entities expand the query — `p*₀ = p₀ ⊕ Z_IR` — before dense retrieval with **BGE-Base** over a 300k-patent corpus (Top-3 fed to RAG). This is an explicit **entity-based query-expansion** step.
4. **Generation augmentation (Z_Gen):** entities + ontologies are concatenated into the matching prompt, guiding the LLM to select the identifier (A/B/C/D) whose innovations most align with the query.

Formally the task is a **4-way selection**: given query `p₀` and candidates `{p_A…p_D}`, output the identifier ỹ. No model weights are trained; the whole method is prompt/ontology construction over frozen instruct LLMs.

## Dataset and Evaluation Setting

- **PatentMatch** [Zuo et al. 2024, ref 36] — **1,000** matching questions from authentic patents, evenly split **Chinese / English**, spanning all **8 IPC sections** (HUM 30.4%, OPER 26.4%, PHYS 16%, MECH 10%, CHEM 6%, ELEC 4.6%, CONS 4%, TEXT 2.6%).
- **RAG corpus:** 300,000 patents; retriever BGE-Base; Top-3 retrieved.
- **Metric:** **Accuracy** (primary); significance by permutation test P<0.05.
- **Backbone LLMs:** Llama-3.1-Instruct-8B, Qwen2-Instruct-7B, GLM-4-Chat-9B, Qwen2.5-Instruct-14B.
- **Baselines:** domain-specific fine-tuned LLMs (MoZi-7B, PatentGPT-1.5B, PatentGPT-1.0-Dense-70B), Chain-of-Thought, vanilla RAG.

## Main Findings

- **MemGraph beats vanilla LLM by +17.68% avg accuracy and vanilla RAG by +10.85%** (abstract/intro headline).
- **Overall accuracy, Table 3 (En / Zh / Avg):** best config **GLM-4-Chat-9B + MemGraph = 82.8 / 80.8 / 81.8** — surpassing even the 70B PatentGPT-1.0-Dense (66.2 / 72.0 / 69.1). Qwen2.5-14B MemGraph 75.8/75.0/75.4; Llama-3.1-8B climbs from 47.0 (vanilla) → 65.3 (MemGraph).
- **Consistent gains across all 4 backbones** (in-domain and out-of-domain) → strong generalisation; all MemGraph rows statistically significant over both Vanilla LLM (†) and RAG (‡).
- CoT adds only ~1% over vanilla; **RAG helps but injects noise** (hurts Llama-3.1 and Qwen2.5 on some splits) — MemGraph's entity/ontology hints are what reliably lift performance, by focusing the LLM on ontology-related keywords.

## Limitations

1. **Task framing is 4-option multiple choice**, not open-corpus ranked retrieval — accuracy on A/B/C/D is not Recall@K / MAP over a large candidate pool.
2. **Relies on the LLM's parametric memory** for entities/ontologies → vulnerable to hallucinated or shallow domain knowledge; no external ontology grounding (IPC used only "referentially").
3. English + Chinese only; PatentMatch is abstract-level.
4. Retrieval noise persists (RAG base is imperfect); the 300k corpus and Top-3 cap exposure.
5. No latency/token-cost accounting for the multi-prompt traversal pipeline.

## Track C Relevance (candidate-exposure headroom — proposed, NOT AUTHORIZED)

**High.** The **entity-based query expansion** (`p*₀ = p₀ ⊕ Z_IR`) is a concrete, traceable instance of KNO-20DDBF1D30A0 **H2** (claim-element / formulation-vocabulary query expansion to improve OUT candidate exposure). MemGraph shows LLM-extracted entities improve *retrieval* input, not just generation — directly relevant to a candidate-generation ablation, with the caveat that gains are reported as downstream MCQ accuracy, not exposure@K. Reusable design: expansion terms are human-inspectable entities.

## Track R Relevance (fixed-pool ranking headroom — proposed, NOT AUTHORIZED)

**Medium.** The 4-way A/B/C/D selection is effectively **reranking/selection over a tiny fixed candidate set** via an LLM prompted with ontology hints — conceptually adjacent to Paper D's instruction-aware reranking, but on 4 options rather than a top-K list and scored by selection accuracy, not rank metrics. Use as a comparison for LLM-as-reranker prompting, not as a fixed-pool NDCG result.

## Track S Relevance (SkillOpt / prompt evolution — revision-stage, EXECUTION CLOSED)

**Medium.** MemGraph is a **hand-crafted multi-prompt pipeline** (entity template + ontology template, Table 1). It is a candidate *seed* for GEPA/SkillOpt-style prompt evolution — the entity- and ontology-traversal prompts are exactly the kind of instructions a prompt-optimizer would mutate. Track S execution is closed, so this is background/comparison only.

## Relationship to Papers A–D

- **Complements the dense-encoder line** (PatentSBERTa U005, SEARCHFORMER U008, PaECTER U009): those improve the *embedding*; MemGraph keeps a standard BGE retriever and instead improves the **LLM query-expansion + generation** layers — an orthogonal, stackable intervention.
- **Directly instances H2 query expansion** and touches the reranking-selection surface, so it is closer prior art to the Paper A/C/D prompt-and-retrieval theses than the pure-embedding papers. But **evaluation is MCQ accuracy on PatentMatch, not DAPFAM family-level cross-domain Recall@K** — never cross-compare absolute numbers, and never cite as Paper D outcome evidence (Paper D's frozen P7 boundary result stands independently).
- **Distinct from U008:** U008's "PatentMatch" is Risch et al. (paragraph-level positive/negative); this U010 PatentMatch is a different 1,000-question bilingual MCQ dataset [ref 36]. ⚠️ Two datasets share the name — do not conflate.

## Verification Warnings

1. **PatentMatch name collision** — U010's PatentMatch (Zuo et al., ref 36; 1,000 MCQ, bilingual) ≠ U008's PatentMatch (Risch et al., paragraph pairs). Verified via task definition (4-option selection). ⚠️
2. Table 3 columns are de-gridded in the PDF→text cache (En/Zh/Avg numbers on separate lines) — values here mapped by row order and cross-checked against the §5.1 prose; ⚠️ confirm the grid in the PDF if citing precise cells.
3. DOI is a placeholder (`xxxxxxx`) in the preprint — cite as SIGIR '25 / arXiv:2504.14845.
4. "+17.68% over baseline LLMs" and "+10.85% over RAG" are the authors' averaged deltas; individual backbone deltas vary widely (Llama +18.3, Qwen2.5 +8.5).

## Experience Brain Cross-Check (READ-ONLY)

- **experience_brain_match:** **no** — no MemGraph-specific Knowledge or Grounded Experience record. Nearest matches are the IS1 literature matrix (KNO-5449A7642CF9), the candidate-exposure synthesis (KNO-20DDBF1D30A0, esp. H2 query expansion), and local KM (KNO-3D43C4514725).
- **memory_conflict:** none. MemGraph corroborates H2 (query expansion helps) but on an MCQ metric — does not assert any DAPFAM/Paper-D numerical result.
- **query mode:** read-only; no record created or modified.
- **recommended_ingestion_action:** **ingest_new** — not currently in the vault; add as external Knowledge (LLM query-expansion + ontology-prompting prior art).

## Status

✅ **completed** — Token-efficient two-stage protocol: extracted once to `extraction-cache/U010.md` (11 pages, 8,926 words); targeted reads of abstract, §1 intro, §3 methodology (RAG + entity/ontology latent variables, Eqs. 1–9), §4 experimental methodology (PatentMatch stats Table 2, metrics, baselines, backbones), §5 evaluation results (Table 3, §5.1 overall), §6 conclusion. Full markdown not loaded wholesale.

---
*Digest prepared 2026-07-24. Source repository unmodified. Experience Brain queried read-only.*
