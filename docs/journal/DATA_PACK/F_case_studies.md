# source: https://huggingface.co/datasets/datalyes/DAPFAM_patent; ..\04_Owner_Stores\armindex\a6\a6-goal001-20260823T052423Z-full09\deep-rankings\deep-rankings.jsonl; ..\04_Owner_Stores\a1.2-v15-20260809\protected\inputs\evaluator-relations.arrow

# Task F Case Studies

Status: DONE. These two examples are selected from the 219 judged queries with
no relevant family in the retained Top-1000 ranking. Opaque tokens are safe
identifiers. Query text is taken from the A6 opaque-query input; public titles,
first abstract sentences, and IPC labels are joined from the DAPFAM release.
The target family is a strict `OUT` relation. `Best found relevant rank: none in
Top-1000` means that no relevant family for that query occurs at ranks 1--1000;
it is not a claim that the family is absent from the full corpus.

## Case 1

- Query: `q-350820864995bc2cc3153df6f7c4412462c00f930bc19e1372c60ee6a6529a50`
- Query title: `recovering heat energy`
- Query abstract first sentence: `Some embodiments of a generator system can be used with the working fluid in a Rankine cycle.`
- Query domain: `F22` (first public IPC 3-character label)
- Absent relevant family: `f-2ffc84b32901ed265ed5799e7185b996`
- Absent title: `heat exchanger assembly`
- Target abstract first sentence: `A heat exchanger assembly has an elongated shell provided with fluid inlet and fluid outlet openings.`
- Target domain: `F28`
- Query/target relation: `OUT`
- Relevant-family count for query: 2
- Best found relevant rank: none in Top-1000

The query concerns recovering heat for an organic Rankine-cycle generator. The
selected target is a heat-exchanger family in a different IPC 3-character
domain. The example is retained because the target remains unexposed even when
the candidate pool is extended fivefold from 200 to 1000.

## Case 2

- Query: `q-7bcdbd44fd4825bb0d02700f61db2b4f06ab14b85540dfa66358175ad6c8e0b4`
- Query title: `systems for depositing material onto workpieces in reaction chambers and methods for removing byproducts from reaction chambers`
- Query abstract first sentence: `Systems for depositing material onto workpieces in reaction chambers and methods for removing byproducts from reaction chambers are disclosed herein.`
- Query domain: `F17` (first public IPC 3-character label)
- Absent relevant family: `f-bdb1b2d1830c06b91ba52e4b5d936304`
- Absent title: `bright tin electroplating bath`
- Target abstract first sentence: `Improved electrolytic tin deposition from aqueous, acid electroplating baths is achieved by addition of a new formula of brighteners.`
- Target domain: `C25`
- Query/target relation: `OUT`
- Relevant-family count for query: 3
- Best found relevant rank: none in Top-1000

The query describes reaction-chamber exhaust and by-product trapping. The
selected target is an electroplating-bath family in a different IPC domain.
Again, the point is exposure failure: the target is not present in the retained
deep ranking, so no reordering of that ranking can recover it.

## Selection and interpretation rule

Cases were selected after computing the strict-`OUT` Top-1000 exposure table.
Only queries with zero relevant families at every retained rank through 1000
were eligible. The examples are descriptive diagnostics, not estimates of
semantic similarity and not evidence that the benchmark relevance labels are
incorrect. Public text is limited to title and first abstract sentence to keep
the projection aggregate-safe; protected qrels and raw per-query outcomes stay
in Owner Stores.
