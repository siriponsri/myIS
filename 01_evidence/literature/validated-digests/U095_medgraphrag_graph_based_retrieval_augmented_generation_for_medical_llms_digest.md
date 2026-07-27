---
paper_id: U095
title: "MedGraphRAG: Graph-based Retrieval-Augmented Generation for Medical LLMs"
pdf_sha256: "75da7f107f4320c00066c50dbc6860c0e4919827cae482d82c217c07b148e58e"
object_path: "01_evidence/B-tier/U095_medgraphrag_graph_based_retrieval_augmented_generation_for_medical_llms.pdf"
legacy_primary_alias: "research/ref-paper/shared/pdfs/16_medgraphrag_graph_based_retrieval_augmented_generation_2025.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: ""
arxiv_source: ""
arxiv_confidence: "not_detected"
page_count: 25
record_type: "paper"
tier: "B"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U095: MedGraphRAG: Graph-based Retrieval-Augmented Generation for Medical LLMs

## Bibliographic Identity

- Verified title source: `acquisition_metadata_verified_in_pdf`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: not detected (source: not detected; confidence: not_detected)
- Pages: 25
- Source collection: `shared`
- Legacy primary alias: `research/ref-paper/shared/pdfs/16_medgraphrag_graph_based_retrieval_augmented_generation_2025.pdf`
- Identity result: `verified` (filename/title token overlap 1.00)

## Classification

**Tier B.** Transferable retrieval, RAG, evaluation, uncertainty, or knowledge-graph method. Relevant surface: C, R.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, benchmark, embedding, contrastive, knowledge graph, graph rag, retrieval-augmented, agent, thai, biomedical, summarization.

Abstract/summary section scan:

> not distort, modify, or introduce creative elements We introduce MedGraphRAG, a novel graph- into the data. Unfortunately, verifying the accuracy based Retrieval-Augmented Generation (RAG) of responses in medicine is particularly challeng- framework designed to enhance LLMs in gen- ing for non-expert users. Therefore, the ability to erating evidence-based medical responses, im- perform complex reasoning using large external proving safety and reliability with private med- datasets, while generating accurate and credible ical data. We introduce Triple Graph Construc- responses backed by verifiable sources, is crucial tion and U-Retrieval to enhance GraphRAG, in medical applications of LLMs. enabling holistic insights and evidence-based Retrieval-augmented generation (RAG) (Lewis response generation for medical applications. Specifically, we connect user documents to et al., 2021) is a technique that answers user queries credible medical sources and integrate Top- using specific and private datasets without requir- down Precise Retrieval with Bottom-up Re- ing further training of the model. However, RAG sponse Refinement for balanced context aware- struggles to synthesize new insights and underper- ness and precise indexing. Validated on 9 med- forms in tasks requiring a holistic understanding ical Q&A benchmarks, 2 health fact-checking across extensive documents. GraphRAG (Hu et al., datasets, and a long-form generation test set, 2024) has been recently introduced to overcome MedGraphRAG outperforms state-of-the-art models while ensuring credible sourcing. Our these limitations. GraphRAG constructs a knowl- code is publicly available. edge graph from raw documents using an LLM, and retrieves knowledge from the graph to enhance re- sponses. By representing clear conceptua

Conclusion/discussion section scan:

> MedGraphRAG improves the reliability of medi- cal response generation with its graph-based RAG framework, using Triple Graph Construction and U-Retrieval to enhance evidence-based, context- Figure 4: The effect of retrieving different number of aware responses. Future work will focus on real- entities and neighbourhoods. Performance evaluated by time data updates and validation on real-world clin- GPT-4 (MedGraphRAG) on MedQA. ical data. Figure 5: The relationship between U-retrieval level and time cost. 28450 6 Limitation a local update strategy. Specifically, we can com- pute the semantic distance between newly inserted Despite the strong capabilities demonstrated by knowledge and existing Meta-Graphs, and apply MedGraphRAG, the graph construction step incurs updates only to relevant subgraphs that exceed a de- significant computational costs. In the retrieval and fined threshold. This selective updating approach response stage, although the costs are lower than balances both efficiency and accuracy. We recog- graph construction, they remain higher than stan- nize these as practical and important limitations, dard large language model (LLM) calls, with each and we plan to supply more detailed discussion on question taking around 70 seconds to process (see them as part of our future work in this research Figure 6 for details). Future efforts should explore direction. methods t

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
