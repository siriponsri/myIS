# Workflow / method diagrams

For NLP/IR/patent pipelines:
- use left-to-right flow when the method is sequential;
- use vertical swimlanes only when actor/stage separation matters;
- group steps by conceptual stage, not by implementation file;
- distinguish data objects from operations visually;
- use one arrow style for normal flow and a second only for feedback/optional paths;
- minimize crossing arrows;
- place feedback loops outside the main path;
- put internal implementation detail in caption/method text unless essential to novelty.

Good paper workflow diagram:
`Input -> Representation/Transformation -> Retrieval/Scoring -> Aggregation -> Evaluation/Output`

If the study is an evaluation protocol, show split/gate/freeze boundaries explicitly.

Do not make Fig. 1 a software architecture poster unless the architecture is the research contribution.
