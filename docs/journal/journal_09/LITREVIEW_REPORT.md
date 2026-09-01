# Literature audit for journal_09

Date: 2026-09-01

## Round 2 citation correction

Web records were checked against the linked article or arXiv pages below. The
restored references are used only for the stated related-work and qualitative
motivation claims; none changes an experimental result, figure, table, or
section structure.

| Item | Status | Verified identity and persistent record |
|---|---|---|
| Krestel et al. (2021) | DONE | Ralf Krestel, Renukswamy Chikkamath, Christoph Hewel, and Julian Risch, *A survey on deep learning for patent analysis*, *World Patent Information* 65, 102035. [DOI](https://doi.org/10.1016/j.wpi.2021.102035) |
| Rees and Wirz (2025) | DONE | David Rees and Manuel Wirz, *Evaluating the effectiveness of ranking-based patent search engines for identifying relevant prior art: A comparative study in the area of chemistry*, *World Patent Information* 82, 102358. [DOI](https://doi.org/10.1016/j.wpi.2025.102358); [article page](https://www.sciencedirect.com/science/article/pii/S0172219025000250) |
| Poce and Cerro (2026) | DONE | The PII page confirms that the full author list is exactly Sara Poce and Gianni Cerro: *A survey on automated and AI-based tools for patent retrieval with a special focus on the life sciences domain*, *World Patent Information* 85, 102439. [DOI](https://doi.org/10.1016/j.wpi.2026.102439); [article page](https://www.sciencedirect.com/science/article/pii/S0172219026000141) |
| U002 | DONE | Jieh-Sheng Lee and Jieh Hsiang (2021), *Prior Art Search and Reranking for Generated Patent Text*, PatentSemTech / arXiv:2009.09132. [DOI](https://doi.org/10.48550/arXiv.2009.09132); [arXiv](https://arxiv.org/abs/2009.09132) |
| U064 | DONE | Mandeep Rathee, Sean MacAvaney, and Avishek Anand (2025), *Guiding Retrieval using LLM-based Listwise Rankers*, arXiv:2501.09186. [arXiv](https://arxiv.org/abs/2501.09186) |

## Novelty boundary

U002 notes qualitatively that a relevant candidate filtered out by BM25 cannot
be recovered by embedding reranking. U064 likewise identifies bounded recall
in cascaded retrieval because initially unretrieved documents are excluded.
Neither source reports the paper's quantitative exposure-versus-ordering
decomposition on the same population. Section 2.3 now cites both only for that
qualitative motivation.

## Validation

`pdflatex -> bibtex -> pdflatex -> pdflatex` completed successfully with the
local `elsarticle.cls`. The final log has zero undefined citations or
references. `texcount -inc -sum main.tex` reports 4,753 body-text words, a net
increase of 51 from the prior 4,702-word manuscript and within the 80-word
budget. The resulting `main.pdf` has 21 pages; the retained 2.43pt output-box
warning and underfull boxes are pre-existing layout warnings, not undefined
references.
