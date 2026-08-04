# AUTOINDEX AND HARNESSOPT CONTRACT — ArmIndex V02 NEW

**Authority:** companion scientific contract for `PLAN_V02_NEW.md`

**Purpose:** separate representation optimization from harness optimization while preserving deterministic execution, protected-data isolation, reproducibility, and production constraints.

---

## 1. Core distinction

```text
AutoIndex
  changes the representation program
  while the retrieval arm is frozen.

HarnessOpt
  changes how frozen arms/programs are composed and executed
  while representations and model adapters are frozen.
```

A candidate that changes both surfaces is invalid.

---

## 2. Canonical artifacts

```text
representation_program.schema.json
compiled_representation_manifest.schema.json
arm_adapter_lock.schema.json
autoindex_feedback.schema.json
autoindex_batch.schema.json
arm_program_freeze.schema.json
cross_arm_transfer.schema.json
arm_complementarity.schema.json
harness_config.schema.json
harness_feedback.schema.json
harness_batch.schema.json
harness_freeze.schema.json
production_profile.schema.json
```

Every artifact carries canonical ID, campaign/phase/task/flow IDs, parent, hashes, Git commit/tree, schema version, timestamps, protected-access declaration, cost/latency envelope, status, and stop reason.

---

## 3. AutoIndex contract

### 3.1 Frozen surfaces

- arm/model;
- model revision/tokenizer;
- adapter;
- query instruction/prefix;
- pooling/normalization;
- dimension;
- precision;
- similarity and ANN;
- query representation;
- evaluator;
- split;
- metric;
- top-k;
- family mapping;
- candidate budget;
- Selection/Final state.

### 3.2 Mutable surfaces

- source fields;
- field order;
- field labels;
- unitization;
- independent-claim extraction;
- passage logical size;
- overlap;
- sentence/section boundaries;
- packing;
- deterministic normalization;
- duplicate handling;
- family aggregation.

### 3.3 Proposer input

Allowed aggregate-safe data:

- incumbent program;
- candidate lineage;
- aggregate REP-DEV metrics;
- deltas;
- failure categories;
- latency/storage/cost;
- field-loss and truncation counts;
- remaining axes;
- budget counters;
- literature-derived design notes.

Forbidden:

- query/family IDs;
- qrels;
- rankings;
- per-query outcomes;
- split membership;
- raw benchmark text;
- Selection/Final data.

### 3.4 Batch structure

Each adaptive batch contains exactly four candidates:

1. exploit;
2. matched ablation;
3. orthogonal hypothesis;
4. diversity candidate.

The complete batch must be schema-valid, compile twice identically, pass independent verification, and be hash-frozen before any member is measured.

### 3.5 Candidate admission

Admit only when:

- hypothesis is falsifiable;
- declared axis is valid;
- scientific payload hash is unique;
- compilation succeeds under frozen adapter;
- unit/storage/cost estimate fits;
- source spans/family IDs remain traceable;
- no hidden model/evaluator change occurs;
- independent verifier accepts it.

### 3.6 Stopping

- minimum two complete batches per promoted arm;
- third batch only after strict improvement and remaining budget;
- stop after two completed batches without strict Recall improvement;
- stop when no grounded axis remains;
- stop at cost/time/integrity boundary;
- exact ties are no improvement.

### 3.7 Arm winner

Freeze:

- program bytes/hash;
- compiled manifest hash;
- adapter hash;
- index hash;
- metrics;
- operational values;
- limitations;
- transfer eligibility.

---

## 4. Cross-arm transfer contract

A logical program transfers only when source fields exist and the target adapter can compile safely.

Classify:

- exact logical transfer;
- adapter-constrained compilation;
- unsupported transfer.

Do not claim adapter-constrained outputs are byte-identical.

Required outputs:

- source-program × target-arm matrix;
- within-arm normalized delta;
- target-arm rank;
- field/unitization interaction;
- truncation/unit count;
- cost;
- unsupported reason;
- statistical diagnostic.

---

## 5. Complementarity contract

At equal candidate depths compute:

- union Recall;
- best-arm Recall;
- unique relevant family-query pairs;
- overlap;
- oracle Recall/nDCG in union;
- incremental cost/latency.

A multi-arm harness is eligible only through the preregistered gate. No arm is retained merely because its model name differs.

---

## 6. HarnessOpt contract

### 6.1 Frozen surfaces

- arm programs;
- model adapters;
- indexes;
- query serialization;
- evaluator;
- data/split;
- metrics;
- final output depth;
- maximum arm set;
- cost ceiling;
- no qrels/domain labels at runtime.

### 6.2 Mutable surfaces

```yaml
arm_subset: [...]
execution: parallel | sequential
initial_depth_by_arm: {...}
maximum_depth_by_arm: {...}
fusion:
  method: rrf | weighted_rrf | normalized_rank_sum
  parameters: {...}
routing:
  rare_term_density: ...
  query_length: ...
  score_margin: ...
  arm_overlap: ...
  rank_stability: ...
  field_presence: ...
early_stop:
  conditions: [...]
cache:
  policy: ...
latency_profile: fast | balanced | deep
```

### 6.3 Forbidden harness features

- qrels;
- IN/OUT label;
- IPC/CPC OUT shortcut;
- per-query correctness history;
- Selection/Final feedback;
- query rewriting;
- LLM reasoning in synchronous runtime;
- model or representation changes;
- arbitrary Python generated by optimizer.

### 6.4 Controls

- best single arm;
- all eligible arms with RRF-60;
- top-two with RRF-60;
- top-three with RRF-60;
- commercial-only fixed union.

### 6.5 Batch

Exactly four:

1. quality exploit;
2. cost/latency matched ablation;
3. routing hypothesis;
4. diversity profile.

### 6.6 Objective

Lexicographic quality rule plus Pareto filtering over:

- OUT Recall@100;
- OUT nDCG@100;
- p95 latency;
- cost/query;
- index size;
- number of arm calls.

### 6.7 Runtime determinism

Same query, indexes, config, and environment class must yield same arm actions, depths, ranking, stop reason, and receipt. Thresholds have explicit numeric tolerances.

---

## 7. Production profiles

### FAST

- max two arms;
- BM25 fallback;
- bounded depth;
- at most one escalation;
- synchronous;
- lowest p95 frontier.

### BALANCED

- two/three commercial arms;
- adaptive escalation allowed;
- fixed latency budget;
- synchronous only when SLO passes.

### DEEP

- research or commercial full harness;
- largest frozen depth;
- asynchronous permitted;
- detailed route diagnostics;
- not default interactive endpoint.

---

## 8. Failure and recovery

| Failure | Classification | Recovery |
|---|---|---|
| OOM | infrastructure | reduce batch size only |
| provider interruption | infrastructure | resume same task |
| corrupt partial index | infrastructure | quarantine/rebuild same hash |
| adapter mismatch | integrity | block arm |
| program nondeterminism | integrity | reject candidate |
| metric mismatch | integrity | block revision |
| candidate timeout | terminal unless infrastructure | preserve failure |
| invalid optimizer batch | proposer failure | bounded retry; no partial batch |
| second Selection exposure | hard safety | fail closed |
| insufficient budget | valid stop | close with current evidence |

No valid measured result is overwritten.

---

## 9. Independent verification

Verifier checks:

- immutable Git bytes;
- schema/hash chain;
- protected boundaries;
- one-axis claims;
- batch completeness;
- evaluator comparability;
- budget counters;
- ranking determinism;
- transfer classification;
- runtime label-free policy;
- profile Pareto status;
- report/read-model consistency.

Maker and verifier use separate fresh contexts.

---

## 10. Terminal receipts

AutoIndex:

- `FREEZE_ARM_PROGRAM`
- `STOP_WITH_EVIDENCE_FLAT_REPRESENTATION_SURFACE`
- `BLOCKED_INVALID_ARM_OR_PROGRAM`

HarnessOpt:

- `FREEZE_HARNESSOPT_CHAMPION`
- `FREEZE_FIXED_UNION`
- `FREEZE_BEST_SINGLE_ARM`
- `STOP_WITH_EVIDENCE_HARNESS_NO_GAIN`
- `BLOCKED_HARNESS_INTEGRITY`

Production:

- `FREEZE_THREE_PROFILES`
- `FREEZE_REDUCED_PROFILE_SET`
- `BLOCKED_PRODUCTION_VALIDATION`

Every terminal state is a reportable research outcome.
