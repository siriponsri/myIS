---
paper_id: U143
title: "Beyond Keywords: Optimizing Legal Information Retrieval through Embeddings, Cross-Encoders, and Large Language Models"
pdf_sha256: "dcdca487711eb62d7968a9a4165c51185f9881115d18ff0c2f9047f1f8b8665d"
object_path: "01_evidence/B-tier/U143_beyond_keywords_optimizing_legal_information_retrieval_through_embedding.pdf"
legacy_primary_alias: "research/ref-paper/is2/pdfs/51_optimizing_legal_information_retrieval_via_cross_2024.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: ""
arxiv_source: ""
arxiv_confidence: "not_detected"
page_count: 65
record_type: "paper"
tier: "B"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U143: Beyond Keywords: Optimizing Legal Information Retrieval through Embeddings, Cross-Encoders, and Large Language Models

## Bibliographic Identity

- Verified title source: `rendered_title_page_visual_review`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: not detected (source: not detected; confidence: not_detected)
- Pages: 65
- Source collection: `is2`
- Legacy primary alias: `research/ref-paper/is2/pdfs/51_optimizing_legal_information_retrieval_via_cross_2024.pdf`
- Identity result: `verified` (filename/title token overlap 0.71)

## Classification

**Tier B.** Transferable retrieval, RAG, evaluation, uncertainty, or knowledge-graph method. Relevant surface: C, R, IS2-adjacent.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, reranking, ranking, benchmark, embedding, contrastive, retrieval-augmented, agent, cross-lingual, legal, classification, summarization.

Abstract/summary section scan:

> Legal Information Retrieval (LIR) is a specialized field focused on accessing legal texts, including legislation, case law, and scholarly works. Traditional keyword-based search methods often exhibit limitations due to challenges such as synonymy, polysemy, and the complex nature of legal language, leading to reduced recall and precision rates. To address these issues, this thesis aims to optimize the retrieval component within Retrieval-Augmented Generation (RAG) pipelines, ensuring that Large Language Models (LLMs) receive the most pertinent documents to accurately respond to user queries. We explore various methodologies, including embedding techniques, cross-encoders, and LLMs, to enhance the retrieval process. Embedding techniques involve transforming text into dense vector representations, facilitating efficient similarity searches. Cross- encoders jointly encode query-document pairs to assess relevance more precisely, albeit at a higher computational cost. By integrating these approaches, we aim to improve the selection of relevant documents, thereby enhancing the overall performance of RAG systems in the legal domain. Abstract Juridisk informationssökning är ett specialiserat område som fokuserar på att ge tillgång till juridiska texter, inklusive lagstiftning, rättspraxis och akademiska verk. Traditionella sökmetoder baserade på nyckelord uppvisar ofta begrän- sningar på grund av utmaningar som synonymi, polysemi och det komplexa juridiska språket, vilket leder till minskad täckning och precision. För att hantera dessa problem syftar denna avhandling till att förbättra täckningen inom Retrieval-Augmented Generation (RAG)-ramverk, för att säkerställa att stora språkmodeller (LLM) får de mest relevanta dokumenten för att exakt besvara användarfrågor. Vi utforskar

Conclusion/discussion section scan:

> 5.1 Summary of the Work This thesis has thoroughly investigated methods for optimizing the retrieval component of Retrieval-Augmented Generation (RAG) systems, specifically tai- lored to the Italian legal context. Recognizing the shortcomings of traditional keyword-based search techniques (e.g., BM25) in handling the semantic com- plexities of legal queries and documents, the research systematically explored advanced retrieval approaches, including embedding-based techniques, hybrid models, cross-encoder re-ranking, LoRA-based fine-tuning, and Hypothetical Document Embeddings (HyDE). To rigorously evaluate these approaches, the thesis combined both large-scale synthetic datasets and carefully annotated human-generated data, providing a comprehensive analysis of retrieval effectiveness using industry-standard metrics such as precision, recall, F1 score, Discounted Cumulative Gain (DCG), and Normalized Discounted Cumulative Gain (nDCG). The experimental results consistently underscored the significant advantages of semantic embeddings over traditional keyword search, especially when leveraging domain-specific models trained explicitly on legal data, such as voyage-law2 embeddings. Furthermore, the research demonstrated the effectiveness of hybrid retrieval strategies, notably Reciprocal Rank Fusion (RRF), which successfully integrated sparse retrieval (BM25) with dense embeddings

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
