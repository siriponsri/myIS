# WPI_JOURNAL_OUTLINE.md — extended journal version for World Patent Information

Target: World Patent Information (Elsevier, ISSN 0172-2190), ideally the open
call "IP data analytics — adopting state-of-the-art AI and ML approaches".
CHECK the CFP deadline on the journal page before committing to it; if the
special issue has closed, submit as a regular article — the scope fits either
way. Format: elsarticle (NOT IEEEtran); start a fresh project. Length target:
7,000–8,500 words. Review is NOT double-anonymous: real names, real repo link
(github.com/siriponsri/myIS), real artifact links throughout.

## Relationship to the conference paper (state this everywhere it matters)
Extended version of the iSAI-NLP 2026 submission. The cover letter declares it;
Section 1 footnote cites it; the new-material fraction (target 40%+) comes from
the additions below. Conference numbers are immutable and must reproduce
exactly wherever they reappear. This plan is robust to either conference
outcome: accepted -> extended version citing the proceedings paper; rejected ->
the full study debuts here, stronger than the conference draft.

## The reframe: same evidence, different audience
Conference arc = methodology-first, for IR researchers ("freezing a variable
does not neutralize it"). Journal arc = practice-first, for patent-search
professionals. The three results become three lessons a professional searcher
can act on. Signature sentences survive ("A patent retriever never sees a
patent." opens both). Tone: WPI is professional and readable — keep the voice,
lose nothing of the rigor, but every section must answer "what should a
searcher or tool buyer do differently?"

## Title options (keep the brand, add the practice payoff)
1. Beyond the Retriever: Configuration and the Exposure Ceiling in AI-Based
   Cross-Domain Patent Search
2. Beyond the Retriever: Why Candidate Exposure, Not Ranking, Caps AI-Based
   Prior-Art Retrieval Across Technical Domains
3. Model Names Are Not Search Tools: A Controlled Study of Configuration and
   Exposure in Cross-Domain Patent Retrieval

## Section plan

### 1. Introduction (rewrite, practice-first)
Hook: AI patent-search tools are procured and compared by model name; what a
searcher actually receives is a configuration — model + document construction +
depth + fusion — and in recall-critical work (patentability, invalidity,
state-of-the-art) the difference matters. "A patent retriever never sees a
patent." Three questions a search professional should ask of any AI tool, which
map to the three studies. Contributions restated for this audience.

### 2. Background and related work (expand)
Two threads the conference version compressed:
(a) practice: recall-critical search types and why cross-domain prior art is
the hard case (paraphrase WPI's own literature; cite recent WPI work, e.g. the
AI patent-retrieval tools survey, plus CEPIUG-adjacent practitioner material);
(b) research: DAPFAM / PatenTEB / 22-model benchmark / AutoIndex / PHAGE as in
the conference version, lightly de-compressed.

### 3. Study design (reuse + de-anonymize + expand)
Same protocol section, now with real links: repo, preregistration artifact with
freeze chronology (2026-08-12 receipt before 2026-08-16 execution), full config
tables moved from prose to appendix references. Evidence map figure reused.

### 4. Lesson 1 — Construction choices do not pick winners across engines
Transfer matrix as-is + (optional, see prep tasks) the lexical extension rows.
NEW: "what this means when reading vendor claims" paragraph. Lesson box:
compare tools at the configuration level; a construction tuned on one engine
carries no promise on another.

### 5. Lesson 2 — Validate a configuration like a claim, not a demo
Selection-125 -> Final-872 protected confirmation, reused. NEW: short
methods-transfer passage — how a search team can replicate this validation
pattern in-house (frozen comparator, held-out queries, paired differences).
Lesson box: demand held-out evidence; demos are development data.

### 6. Lesson 3 — The exposure ceiling (the journal's center of gravity)
Reuse A7 diagnosis, then the NEW analyses:
- exposure-by-depth curve within the Top-200 pool (free, from artifacts);
  extended to depth 500/1000 IF the gated experiment runs (see prep tasks)
- per-domain exposure breakdown: which technical fields lose the most evidence
  (WPI readers care exactly about this)
- 2–3 concrete case studies: a query family whose relevant art never entered
  the pool — show the title pair, name the failure mode in plain language
Lesson box: for recall-critical work, effort belongs in candidate generation
(multiple formulations, broader pools, iterative search), not in trusting a
polished top-10.

### 7. Implications: report the configuration, not the model
The WPI-native contribution: a proposed one-line "configuration statement" for
AI-assisted search reporting (model+revision; construction incl. fields,
segmentation, aggregation; depth; fusion), analogous to how professional
searchers already document search strategies. One boxed checklist. Connect to
reproducibility expectations in professional search reporting.

### 8. Limitations and scope
Single benchmark; one confirmed configuration; exposure characterized to the
depths actually run; findings are information-retrieval results, not legal
conclusions (expand this for the IP audience — one paragraph, not one line).

### 9. Conclusion
Three lessons, one sentence each, then the closing pair: representation
specifies the evidence; the retriever decides what to do with it — and the
pool decides what either of them ever sees.

## Figures and tables
Reuse (restyle for Elsevier single/1.5-column widths): evidence map, transfer
matrix, Final-872 confirmation, exposure diagnosis.
NEW: F5 per-domain exposure chart; F6 exposure-by-depth curve.
Appendix tables: 5x5 screen, 52-config search with outcomes, Selection-125
profiles, per-domain tables. All sourced from DATA_PACK (see prep tasks).

## Writing sequence
1) Now: run JOURNAL_DATA_PREP tasks (agent) -> DATA_PACK.
2) After the conference submission is in: draft Sections 1, 6, 7 first (the
   new spine), then port 3–5 from the conference text with the audience shift.
3) After the iSAI-NLP decision: finalize the relationship statement + cover
   letter, decide on the gated depth experiment, submit.
