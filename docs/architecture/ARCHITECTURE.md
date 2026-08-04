# ArmIndex Architecture

ArmIndex is an active subsystem of the existing `myis_research` package. The
stable package name and historical SCOPE modules remain unchanged so prior
manifests, imports, receipts, and evidence hashes keep their original meaning.

```mermaid
flowchart TB
    PD[Owner-local protected data] --> EV[Protected evaluator]
    SD[Repository-safe structured document contract] --> RP[Representation program compiler]
    RP --> A1[ARM-01 BM25]
    RP --> A2[ARM-02 BGE-M3]
    RP --> A3[ARM-03 PatEmbed]
    RP --> A4[ARM-04 Snowflake]
    RP --> A5[ARM-05 Qwen]
    A1 --> T[Transfer and complementarity]
    A2 --> T
    A3 --> T
    A4 --> T
    A5 --> T
    T --> H[Deterministic HarnessOpt]
    H --> EV
    EV --> R[Immutable aggregate receipt]
    R --> RM[Shared read model]
    RM --> M[MLflow safe mirror]
    RM --> B[Research Brain]
    RM --> O[Obsidian]
    RM --> D[Dashboard]
    RM --> P[Paper readiness]
```

The representation compiler may change source fields, order, labels,
unitization, packing, normalization, duplicate handling, and aggregation. It
cannot change the retriever adapter, evaluator, split, model weights, or metric
definition. HarnessOpt operates only on frozen arms and programs.

Historical SCOPE code remains behind explicit compatibility imports and is not
read as active ArmIndex authority. The migration manifest records every
preserved, superseded, or newly introduced path.

## Trust boundaries

1. Owner-local protected data and credentials never enter Git.
2. Canonical repository records store aggregate-safe facts and content hashes.
3. MLflow, Brain, Obsidian, Dashboard, and Paper are reproducible projections.
4. Owner decisions are restricted to D2 and D3.
5. Selection and Final are fail-closed until their frozen prerequisites pass.
