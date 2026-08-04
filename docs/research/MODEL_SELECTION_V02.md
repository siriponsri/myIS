# MODEL SELECTION V02 NEW — ArmIndex Frozen Retrieval Arms

**Companion to:** `PLAN_V02_NEW.md`

**Policy:** inference only; no model-weight adaptation

**Measured-use rule:** every model must be resolved to a full immutable repository SHA, tokenizer SHA, configuration hash, software lock, and license snapshot before measured execution.

---

## 1. Decision summary

| Arm | Exact repository / implementation | Core mode | Research role | Commercial status |
|---|---|---|---|---|
| ARM-01 | `bm25s` BM25 | lexical | anchor, rare terms, CPU fallback | MIT; commercial-capable subject to package snapshot |
| ARM-02 | `BAAI/bge-m3` | dense only | multilingual long-context generic dense arm | MIT, commercial-capable |
| ARM-03 | `datalyes/patembed-large` | dense | patent-domain research anchor | CC BY-NC-SA 4.0, non-commercial |
| ARM-04 | `Snowflake/snowflake-arctic-embed-m-v2.0` | dense | DAPFAM-aligned comparator and complement | Apache-2.0, commercial-capable |
| ARM-05 | `Qwen/Qwen3-Embedding-0.6B` | dense, instruction-aware | efficient modern multilingual arm | Apache-2.0, commercial-capable |

No model may be automatically replaced. A mutable alias such as `main` is allowed only during Phase 0 resolution; all measured manifests use the resolved full SHA.

---

## 2. Selection rationale

### ARM-01 BM25

BM25 remains essential because DAPFAM shows that dense retrieval does not uniformly dominate under OUT shift; patents and legal documents contain rare technical/legal terms; and BM25 provides a low-latency CPU fallback.

Frozen:

- package version;
- `k1=1.2`;
- `b=0.75`;
- tokenizer;
- casing, punctuation, stemming, stopwords;
- Unicode normalization;
- family aggregation.

### ARM-02 BGE-M3

Official ID: `BAAI/bge-m3`

- dense, sparse, and multi-vector capabilities;
- more than 100 languages;
- up to 8,192 tokens;
- MIT license;
- 1,024 dimensions.

Core decision:

- ARM-02 is dense-only.
- Sparse and multi-vector modes belong to a bounded Research Flow with distinct IDs and receipts.
- Exact pooling and normalization are frozen from the resolved official implementation.
- The official model guidance does not require a query instruction for standard dense use.

Reason: strong commercial-capable generic arm and useful contrast to patent-specific PatEmbed and instruction-aware Qwen.

Sources:

- https://huggingface.co/BAAI/bge-m3
- https://arxiv.org/abs/2402.03216

### ARM-03 PatEmbed-large

Official ID: `datalyes/patembed-large`

Identity:

- PatenTEB patembed-large release;
- approximately 344M parameters;
- 1,024-dimensional embeddings;
- patent-specific encoder;
- CC BY-NC-SA 4.0.

Frozen query text:

```text
encode query for different document retrieval: {query}
```

Frozen document text:

```text
encode document for different retrieval: {document}
```

Frozen behavior:

- one literal space after prefix;
- resolved tokenizer;
- explicit truncation;
- mean pooling over non-padding tokens;
- L2 normalization;
- cosine similarity;
- current plan uses 512-token passages pending immutable verification;
- BF16/FP16 only after rank parity against FP32.

Reason: strongest directly relevant patent-specific frozen arm in current evidence.

License consequence:

- academic/non-commercial research only;
- attribution/share-alike compliance;
- no automatic commercial product use;
- embeddings/index redistribution requires review;
- paper distinguishes research and commercial champions.

Sources:

- https://huggingface.co/datalyes/patembed-large
- https://arxiv.org/abs/2510.22264

### ARM-04 Snowflake Arctic Embed M v2.0

Official ID: `Snowflake/snowflake-arctic-embed-m-v2.0`

Identity:

- approximately 305M total / 113M non-embedding;
- 768 dimensions;
- 8,192-token maximum context;
- multilingual;
- Apache-2.0;
- custom remote code.

Frozen configuration:

```text
query prefix       = "query: "
document prefix    = none
pooling            = first-token / CLS
normalization      = L2
similarity         = normalized dot product
trust_remote_code  = true
```

Additional locks:

- remote-code file hashes;
- explicit max length;
- MRL truncation off;
- 768 dimensions;
- no mutable framework defaults.

Reason: DAPFAM-aligned dense comparator with commercial-friendly license and distinct failure modes.

Sources:

- https://huggingface.co/Snowflake/snowflake-arctic-embed-m-v2.0
- https://arxiv.org/abs/2412.04506

### ARM-05 Qwen3-Embedding-0.6B

Official ID: `Qwen/Qwen3-Embedding-0.6B`

Identity:

- 0.6B parameters;
- 28 layers;
- 32K declared context;
- up to 1,024 dimensions;
- MRL support;
- instruction-aware;
- 100+ languages;
- Apache-2.0.

Frozen core dimension:

```text
1024
```

Frozen query format:

```text
Instruct: Retrieve patent families containing technical information relevant to prior-art search for the query patent family.
Query:{query}
```

Document text has no instruction.

Frozen behavior:

- last-token pooling;
- left padding;
- L2 normalization;
- normalized dot product;
- explicit measured max length selected before REP-DEV;
- `transformers>=4.51.0`;
- attention implementation/padding side recorded.

Reason: modern instruction-aware arm at practical size and suitable for commercial production.

The official model card says query instructions often help; the campaign freezes one instruction and uses a no-instruction negative diagnostic, not an instruction search.

Sources:

- https://huggingface.co/Qwen/Qwen3-Embedding-0.6B
- https://arxiv.org/abs/2506.05176

---

## 3. Excluded models

The campaign excludes:

- Qwen3-Embedding-4B/8B;
- Qwen rerankers;
- proprietary embedding APIs;
- ColBERT/SPLADE training;
- PHAGE reproduction as a required arm;
- fine-tuned patent adapters;
- additional models selected after Train results.

Reasons:

- larger sweeps dilute the representation/harness contribution;
- larger models increase cost and latency;
- reranking changes the study from candidate recovery to ranking;
- proprietary APIs weaken immutable revision control;
- weight-adapted models are out of scope;
- five arms already span lexical, generic dense, domain-specific dense, multilingual long-context, and instruction-aware retrieval.

A new family requires a versioned plan amendment before Selection.

---

## 4. Precision, quantization, and parity

- BF16 preferred; FP16 otherwise.
- FP32 used for parity fixtures.
- Precision constant inside comparison families.
- Quantization is an operational Research Flow, not a free model variant.
- Quantized artifacts require exact ID/hash, rank parity, Recall tolerance, and material latency/storage gain.
- OOM recovery may reduce batch size only.
- OOM may not alter model, max length, representation, pooling, dimension, precision class, or quantization.

---

## 5. Model-adapter test card

Every arm must pass:

1. official example compatibility;
2. deterministic repeated embedding;
3. batch-size parity;
4. reversed-input-order parity;
5. prompt/prefix test;
6. pooling test;
7. normalization test;
8. dimension test;
9. max-length/truncation test;
10. CPU/GPU numeric tolerance;
11. stable nearest-neighbor fixture;
12. license snapshot;
13. cache/revision integrity;
14. no-network measured mode;
15. throughput/cost pilot.

---

## 6. Commercial product policy

### Research champion

May use all valid arms, including PatEmbed-large.

### Commercial-capable champion

May use:

- BM25;
- BGE-M3;
- Snowflake Arctic Embed M v2.0;
- Qwen3-Embedding-0.6B.

PatEmbed-large requires a separate commercial license decision.

Product reports must state:

- exact license;
- permitted use;
- redistribution restrictions;
- model/index provenance;
- data-boundary design;
- latency/cost profile;
- no legal-decision claim.

---

## 7. Promotion rules

| Decision | Automatic rule |
|---|---|
| Arm enters full AutoIndex | top quality, unique hits, or non-dominated frontier; max three |
| BGE extra mode expands | unique hits or meaningful frontier point |
| PatEmbed enters research champion | valid best/competitive result |
| PatEmbed enters commercial champion | prohibited without license decision |
| Qwen lower dimension enters profile | parity plus meaningful latency/storage benefit |
| Quantized artifact enters profile | quality tolerance plus operational gain |
| New model family | plan amendment required |

---

## 8. Required report fields

Every model result reports:

- arm ID;
- repository ID;
- resolved revision SHA;
- tokenizer SHA;
- parameter count;
- embedding dimension;
- prompt/prefix;
- pooling;
- normalization;
- max input length;
- truncation rate;
- precision/quantization;
- device;
- representation program;
- index;
- software versions;
- latency/throughput;
- charged USD;
- license;
- intended-use boundary;
- primary source links.
