source: https://huggingface.co/datasets/datalyes/DAPFAM_patent; ..\\04_Owner_Stores\\armindex\\a6\\a6-goal001-20260823T052423Z-full09\\deep-rankings\\pool-200.jsonl; ..\\04_Owner_Stores\\armindex\\a6\\a6-goal001-20260823T052423Z-full09\\query-input\\opaque-queries-20260823.jsonl; ..\\04_Owner_Stores\\a1.2-v15-20260809\\protected\\inputs\\corpus.jsonl; ..\\04_Owner_Stores\\a1.2-v15-20260809\\protected\\inputs\\evaluator-relations.arrow

# Task F Case Studies

Status: DONE. The three examples are strict `OUT` relations. Opaque tokens are used as safe identifiers. Titles, first abstract sentences, and IPC 3-character domains are joined from the public DAPFAM release; local Owner Store files are used only for the frozen ranking/relation join.

## Case 1

- Query: `q-efebed9260180a90d67ba901337a3b29f3aac8315dd0d592c3281327a40caac1`
- Query title: “classifying a work machine operation”
- Query abstract first sentence: “A method for analyzing the use of a work machine is disclosed.”
- Absent relevant family: `f-46c02889b12a9f342e987c0f8ae9b8be`
- Absent title: “method of operating industrial plant, and industrial plant control system”
- Target abstract first sentence: “Field: machine building.”
- Query domain / target domain: `D05` / `G05` (IPC 3-character)
- Query/target relation: `OUT`
- Best found relevant rank: 1; the listed target is absent from Top-200.

The query describes neural-network classification of machine operation from load or sensor data. The absent title concerns operation of an industrial plant and plant control. Both descriptions concern monitored or controlled industrial operation, while the relation receipt marks them as strict cross-domain.

## Case 2

- Query: `q-9d455c3f87857eb99bb390dee713832eea1c3c8e0c80aecdb20e96aa71aa764c`
- Query title: “tool drive system”
- Query abstract first sentence: “A tool drive system for transferring rotational power from a rotational tool, such as a drill or ratchet, to at least one input drive shaft which then transfers the power to at least one output drive shaft.”
- Absent relevant family: `f-cf7fdc5d27ab10d96513340c361e380d`
- Absent title: “system for controlling motor velocity of a surgical stapling and cutting instrument according to articulation angle of end effector”
- Target abstract first sentence: “A motorized surgical instrument is disclosed.”
- Query domain / target domain: `B23` / `A61` (IPC 3-character)
- Query/target relation: `OUT`
- Best found relevant rank: 1; the listed target is absent from Top-200.

The query text focuses on shafts, gears, angle setting, and torque transfer. The absent title focuses on motor-velocity control in a surgical stapling and cutting instrument. The overlap is at the level of powered mechanical actuation, but the application descriptions are distinct.

## Case 3

- Query: `q-fce4e6c8fe1f84935f3feb26a5b00e17de6f93c5757af1d6b22acb95ac9f3b50`
- Query title: “bifurcated document relevance scoring”
- Query abstract first sentence: “An information retrieval system uses phrases to index, retrieve, organize and describe documents.”
- Absent relevant family: `f-3bd28a7a890f37f559163fc6b825b5ae`
- Absent title: “image display system and image display device”
- Target abstract first sentence: “Problem to be solved: to provide an image display system capable of sharing a flag added to a certain image between different display terminals.”
- Query domain / target domain: `G60` / `G06` (IPC 3-character)
- Query/target relation: `OUT`
- Best found relevant rank: 1; the listed target is absent from Top-200.

The query describes phrase posting lists and document relevance scoring. The absent title describes sharing image flags between a data server and multiple display terminals. The text shows a retrieval/scoring system paired with an image-display system, with no stronger causal explanation asserted here.
