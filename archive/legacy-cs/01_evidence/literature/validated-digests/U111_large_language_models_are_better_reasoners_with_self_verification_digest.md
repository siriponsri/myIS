---
paper_id: U111
title: "Large Language Models Are Better Reasoners with Self-Verification"
pdf_sha256: "e85895a3ef23f6685d1831a1dd1dd14efc5c704d7d9bc734216b2318163af340"
object_path: "01_evidence/N-tier/U111_large_language_models_are_better_reasoners_with_self_verification.pdf"
legacy_primary_alias: "research/ref-paper/shared/pdfs/37_e5_mistral_text_embeddings_by_weakly_2024.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: "2212.09561"
arxiv_source: "acquisition_url"
arxiv_confidence: "high"
page_count: 26
record_type: "paper"
tier: "N"
identity_status: "alias_title_mismatch"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U111: Large Language Models Are Better Reasoners with Self-Verification

## Bibliographic Identity

- Verified title source: `rendered_first_page_text`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: 2212.09561 (source: acquisition_url; confidence: high)
- Pages: 26
- Source collection: `shared`
- Legacy primary alias: `research/ref-paper/shared/pdfs/37_e5_mistral_text_embeddings_by_weakly_2024.pdf`
- Identity result: `alias_title_mismatch` (filename/title token overlap 0.10)

## Classification

**Tier N.** Wrong acquisition: reasoning paper under an E5-Mistral embedding alias. Relevant surface: H/S.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, ranking, benchmark, knowledge graph, agent, hallucination.

Abstract/summary section scan:

> a final answer. This approach has been shown the advance performances on several challenging NLP Recently, with the chain of thought (CoT) prompting, large language models (LLMs), tasks, even when using only a few or no training e.g., GPT-3, have shown strong reasoning abil- samples (Madaan et al., 2022; Saparov and He, arXiv:2212.09561v5 [cs.AI] 19 Oct 2023 ity in several natural language processing tasks 2022; Fu et al., 2022; Gu et al., 2023). such as arithmetic, commonsense, and logical Although CoT can enable LLMs to solve com- reasoning. However, LLMs with CoT require plex reasoning tasks, it is highly sensitive to indi- multi-step prompting and multi-token predic- vidual mistakes and vulnerable to error accumula- tion, which is highly sensitive to individual mistakes and vulnerable to error accumulation. tion (Shen et al., 2021). If a tiny mistake occurs, The above issues make the LLMs need the abil- it can change the meaning deviations of the whole ity to verify the answers. In fact, after inferring statement (Xiao et al., 2022), leading to incorrect conclusions in some thinking decision tasks, answers (Cobbe et al., 2021). That is especially people often check them by re-verifying steps problematic in using CoT for addressing multi-step to avoid some mistakes. In this paper, we pro- precise reasoning (such as mathematical calcula- pose and prove that LLMs also have similar tion). Due to the lack of the error correction mech- self-verification abilities. We take the conclu- anism, it is difficult for the LLMs to obtain correct sion obtained by CoT as one of the conditions for solving the original problem. By perform- results from the possible errors in multiple steps ing a backward verification of the answers that reasoning. Detecting and mitigating errors is es

Conclusion/discussion section scan:

> Academy of Sciences (No.XDA27020100), Youth In this study, we show that large language models Innovation Promotion Association CAS, and OPPO have a strong ability to self-verification, allowing Research Fund. References Bing Qin, and Ting Liu. 2023. A survey of chain of thought reasoning: Advances, frontiers and future. Ekin Akyürek, Dale Schuurmans, Jacob Andreas, Tengyu Ma, and Denny Zhou. 2022. What learning Karl Cobbe, Vineet Kosaraju, Mohammad Bavar- algorithm is in-context learning? investigations with ian, Jacob Hilton, Reiichiro Nakano, Christopher linear models. arXiv preprint arXiv:2211.15661. Hesse, and John Schulman. 2021. Training veri- Aida Amini, Saadia Gabriel, Peter Lin, Rik Koncel- fiers to solve math word problems. arXiv preprint Kedziorski, Yejin Choi, and Hannaneh Hajishirzi. arXiv:2110.14168. 2019. Mathqa: Towards interpretable math word problem solving with operation-based formalisms. Xiang Deng, Yu Su, Alyssa Lees, You Wu, Cong Yu, north american chapter of the association for com- and Huan Sun. 2021. Reasonbert: Pre-trained to putational linguistics. reason with distant supervision. empirical methods in natural language processing. Patel Arkil, Bhattamishra Satwik, and Goyal Navin. 2021. Are nlp models really able to solve simple Shehzaad Dhuliawala, Mojtaba Komeili, Jing Xu, math word problems? Roberta Raileanu, Xian Li, Asli Celikyilmaz, and Jason Wes

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
