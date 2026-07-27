---
paper_id: U117
title: "Tree-Based Text Retrieval via Hierarchical Clustering in RAG Frameworks: Application on Taiwanese Regulations"
pdf_sha256: "059fc7565b86ff487669bcab4b5b002076fa8d4e2f6989fb1736520164b6115d"
object_path: "01_evidence/B-tier/U117_tree_based_text_retrieval_via_hierarchical_clustering_in_rag_frameworks.pdf"
legacy_primary_alias: "research/ref-paper/shared/pdfs/51_tree_based_text_retrieval_via_hierarchical_clustering.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: "2506.13607"
arxiv_source: "pdf_front_matter"
arxiv_confidence: "medium"
page_count: 19
record_type: "paper"
tier: "B"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U117: Tree-Based Text Retrieval via Hierarchical Clustering in RAG Frameworks: Application on Taiwanese Regulations

## Bibliographic Identity

- Verified title source: `first_page_text`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: 2506.13607 (source: pdf_front_matter; confidence: medium)
- Pages: 19
- Source collection: `shared`
- Legacy primary alias: `research/ref-paper/shared/pdfs/51_tree_based_text_retrieval_via_hierarchical_clustering.pdf`
- Identity result: `verified` (filename/title token overlap 1.00)

## Classification

**Tier B.** Transferable retrieval, RAG, evaluation, uncertainty, or knowledge-graph method. Relevant surface: C, R, IS2-adjacent.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, retrieval-augmented, legal, hallucination.

Abstract/summary section scan:

> Traditional Retrieval-Augmented Generation (RAG) systems employ brute-force inner product search to retrieve the top-k most similar documents, then combined with the user query and passed to a language model. This allows the model to access external knowledge and reduce hallucinations. However, selecting an appro- priate k value remains a significant challenge in practical applications: a small k may fail to retrieve sufficient information, while a large k can introduce excessive and irrelevant content. To address this, we propose a hierarchical clustering-based retrieval method that eliminates the need to predefine k. Our approach maintains the accuracy and relevance of system responses while adaptively selecting semanti- cally relevant content. In the experiment stage, we applied our method to a Taiwanese legal dataset with expert-graded queries. The results show that our approach achieves superior per- formance in expert evaluations and maintains high precision while eliminating the need to predefine k, demonstrating improved accuracy and interpretability in legal text retrieval tasks. Our framework is simple to implement and easily integrates with existing RAG pipelines, making it a practical solution for real-world applications under limited resources.

Conclusion/discussion section scan:

> ごは づぶちぬふちぴづ ぴとづ ばづひてはひねちのっづ はて はふひ ひづぴひどづぶちぬ びべびぴづね〬 ぷづ っはねばちひづ ぴとづ ぴとひづづ ねづぴとはつび〬 ごとづ brute-force inner product search ぷちび びづぴ ちび ぴとづ baseline (Origin method)〮 ごとづ びづっはのつ ねづぴとはつ づねばぬはべづつ hierarchical clustering tree retrieval (Tree method)〬 ちのつ the hierarchical clustering tree retrieval with query extraction(Tree+QE method) ちび ぴとづ ぴとどひつ ねづぴとはつ〮 しづ づぶちぬふちぴづ ぴとづ ばづひてはひねちのっづ はて ぴとづ ぴとひづづ ねづぴとはつび ぢべ ぴとづ adjusted F1 score ちのつ expert rating〮 ごとづ ひづびふぬぴび ちひづ びとはぷの どの うどでふひづ 〴〮 〸 Figure 4: Average Expert Score, F1 Score, and Total Score for the three retrieval methods. ぉの ちつつどぴどはの ぴは ぴとづ ぁぶづひちでづ こっはひづ はて ぴとづ ぴとひづづ ねづぴとはつび〬 ぷづ ちぬびは づぶちぬふちぴづ ぴとづ つどびぴひどぢふぴどはの はて びっはひづ つど》づひづのっづび ぢづぴぷづづの づちっと ばひはばはびづつ ねづぴとはつ ちのつ ぴとづ ぢちびづぬどのづ〮 Figure 5: Box plot of the score differences between the Tree method and the Tree+Query method relative to the Origin method. ぁび びとはぷの どの うどでふひづ 〵〬 ぴとづ ぢはへ ばぬはぴ ばひづびづのぴび ぴとづ びっはひづ つど》づひづのっづび はて ぢはぴと Tree method ちのつ Tree+Query methods ひづぬちぴどぶづ ぴは ぴとづ くひどでどの ねづぴとはつ〮 しとどぬづ ぴとづ ごひづづ ねづぴとはつ つづねはのびぴひちぴづび とどでとづひ ねづつどちの どねばひはぶづねづのぴ〬 どぴび ばづひてはひねちのっづ ちひづ ねはひづ ぷどつづぬべ〬 ぷどぴと ち でひづちぴづひ びばひづちつ ちのつ ち はふぴぬどづひ〮 ぉの っはのぴひちびぴ〬 ぴとづ ごひづづ〫けふづひべ ねづぴとはつ〬 ち ねはひづ っはのびどびぴづのぴ ひちのでづ はて どねばひはぶづねづのぴび〬 つづびばどぴづ とちぶどので ち びぬどでとぴぬべ ぬはぷづひ ねづつどちの〮 ぁぬびは〬 はふひ びぴちぴどびぴどっちぬ びどでのど「っちのっづ ぴづびぴ ひづびふぬぴび ちひづ びとはぷの どの ごちぢぬづ 〲〮 ごとづ ひづびふぬぴび どのつど〭 っちぴづ ぴとちぴ ぢはぴと ぴとづ ごひづづ ねづぴとはつ ちのつ ぴとづ ごひづづ〫けふづひべ ねづぴとはつ ちひづ びぴちぴどびぴどっちぬぬべ

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
