---
paper_id: U106
title: "Collab-RAG: Boosting Retrieval-Augmented Generation for Complex Question Answering"
pdf_sha256: "999733e5b581b0f95d40638a77b331e4cf88a4e1f794bfbbcd8c25fc4737899f"
object_path: "01_evidence/B-tier/U106_collab_rag_boosting_retrieval_augmented_generation_for_complex_question.pdf"
legacy_primary_alias: "research/ref-paper/shared/pdfs/29_collab_rag_boosting_retrieval_augmented_generation_2025.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: ""
arxiv_source: ""
arxiv_confidence: "not_detected"
page_count: 18
record_type: "paper"
tier: "B"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U106: Collab-RAG: Boosting Retrieval-Augmented Generation for Complex Question Answering

## Bibliographic Identity

- Verified title source: `acquisition_metadata_verified_in_pdf`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: not detected (source: not detected; confidence: not_detected)
- Pages: 18
- Source collection: `shared`
- Legacy primary alias: `research/ref-paper/shared/pdfs/29_collab_rag_boosting_retrieval_augmented_generation_2025.pdf`
- Identity result: `verified` (filename/title token overlap 1.00)

## Classification

**Tier B.** Transferable retrieval, RAG, evaluation, uncertainty, or knowledge-graph method. Relevant surface: C, R.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, reranking, ranking, benchmark, embedding, contrastive, retrieval-augmented, query rewriting, agent, summarization, hallucination.

Abstract/summary section scan:

> Retrieval-Augmented Generation (RAG) systems often struggle to han- dle multi-hop question-answering tasks accurately due to irrelevant con- text retrieval and limited complex reasoning capabilities. We introduce Collab-RAG, a collaborative training framework that leverages mutual en- hancement between a white-box small language model (SLM) and a black- box large language model (LLM) for RAG. Specifically, the SLM decom- poses complex queries into simpler sub-questions, thus enhancing the accu- racy of the retrieval and facilitating more effective reasoning by the black- box LLM. Concurrently, the black-box LLM provides feedback signals to improve the SLM’s decomposition capability. We observe that Collab-RAG relies solely on supervision from an affordable black-box LLM without ad- ditional distillation from frontier LLMs, yet demonstrates strong generaliza- tion across multiple black-box LLMs. Experimental evaluations across five multi-hop QA datasets demonstrate that Collab-RAG substantially outper- forms existing black-box-only and SLM fine-tuning baselines by 1.8%-14.2% on average. In particular, our fine-tuned 3B SLM surpasses a frozen 32B LLM in question decomposition, highlighting the efficiency of Collab-RAG in improving reasoning and retrieval for complex questions. Our imple- mentation is available at https://github.com/ritaranx/Collab-RAG/.

Conclusion/discussion section scan:

> We introduce Collab-RAG, a framework that fosters collaboration between a white-box SLM and a black-box LLM to enhance RAG for multi-hop question-answering. Through iterative DPO guided by supervision signals from an affordable black-box LLM (GPT-4o-mini), Collab-RAG significantly enhances the SLM’s question decomposition capabilities without expensive human annotations or resource-intensive model distillation. Experimental results demonstrate that our training strategy consistently outperforms standard RAG models (14.2%) and strong decomposition-based baselines (1.8%) over 5 multi-hop QA datasets, exhibiting robust generalization across various black-box LLMs. Collab-RAG presents a scalable and efficient solution to improve complex retrieval-augmented question-answering scenarios. An important line of future work is to extend Collab-RAG for online reinforcement learning (Jin et al., 2025).

## Evidence Use

This record is indexed for source discovery and method/background triage. Any
numeric or comparative claim used in a paper, thesis, slide, or experiment
protocol must be checked against the canonical PDF object and cited to the
relevant page; this digest is not a substitute for claim-level verification.

## Limitations And Verification

- Review depth is metadata verification plus a full-text scan for abstract,
  conclusion, and controlled topic signals. Identifiers are recorded only from
  acquisition URLs, PDF metadata, or explicitly labeled first-page front
  matter; bibliographies are excluded from identifier discovery.
- Tables, figures, equations, appendices, and numeric results were not
  independently transcribed in this corpus migration pass.
- Legacy aliases remain in `catalog/legacy_aliases.csv`; misleading aliases do
  not create a second paper identity.
