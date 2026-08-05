# A1.2 Model Source Locks

## Scope and Authority

This document records the public model-source metadata frozen for the offline
`A1.2_COMMON_MULTI_ARM_SCREENING` contract scaffold. It is engineering
provenance, not execution authorization or measured evidence. Metadata was
resolved from the public Hugging Face model API on 2026-08-05 with `blobs=true`.
No model, tokenizer, configuration, or remote-code payload bytes were
downloaded into the repository or agent workspace.

The immutable machine records are the five files under
`control/armindex/a1.2/model-locks/` and
`control/armindex/a1.2/model-lockset.v1.json`. This document explains those
records without becoming a second source of numeric results.

## Resolved Sources

| Arm | Public source | Resolved revision | Scaffold state |
|---|---|---|---|
| `ARM-01` | `bm25s==0.3.10` | wheel SHA-256 `d271d4e1ad7ffdacb224f41bc54aba55159438ecf06439ffe929f088efa96858` | offline CPU adapter frozen; synthetic rank parity validated |
| `ARM-02` | `BAAI/bge-m3` | `5617a9f61b028005a4858fdac845db406aefb181` | metadata frozen; Owner artifacts pending |
| `ARM-03` | `datalyes/patembed-large` | `2d5c0f92a3e5dc3d5415c08e612c57543c0e03ad` | metadata frozen; Owner artifacts pending |
| `ARM-04` | `Snowflake/snowflake-arctic-embed-m-v2.0` | `95c2741480856aa9666782eb4afe11959938017f` | metadata and remote-code Git objects frozen; Owner byte hashes pending |
| `ARM-05` | `Qwen/Qwen3-Embedding-0.6B` | `97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3` | metadata frozen; Owner artifacts and measured maximum length pending |

## Public Critical Commitments

| Arm | File | Public commitment type | Commitment |
|---|---|---|---|
| `ARM-02` | `pytorch_model.bin` | LFS SHA-256 | `b5e0ce3470abf5ef3831aa1bd5553b486803e83251590ab7ff35a117cf6aad38` |
| `ARM-02` | `tokenizer.json` | LFS SHA-256 | `21106b6d7dab2952c1d496fb21d5dc9db75c28ed361a05f5020bbba27810dd08` |
| `ARM-03` | `model.safetensors` | LFS SHA-256 | `234ea36a876fe5d5c416c1cbaad6f7221e17861fadd6481f0b96588fdc1ca482` |
| `ARM-03` | `tokenizer.json` | Git object ID, not a byte SHA-256 | `5dff0fb953b220cf9900a811df9ae7798d802fdc` |
| `ARM-04` | `model.safetensors` | LFS SHA-256 | `3d80d4727ac8759fb8624b690697c053a3d1992120111dc4a71178e608c26604` |
| `ARM-04` | `tokenizer.json` | LFS SHA-256 | `f1cc44ad7faaeec47241864835473fd5403f2da94673f3f764a77ebcb0a803ec` |
| `ARM-04` | `configuration_hf_alibaba_nlp_gte.py` | Git object ID, not a byte SHA-256 | `d816ed663a58404f966fe322cd113ac39a957686` |
| `ARM-04` | `modeling_hf_alibaba_nlp_gte.py` | Git object ID, not a byte SHA-256 | `63c0975e09b5631b564170d2ecb7985c5d8dd189` |
| `ARM-05` | `model.safetensors` | LFS SHA-256 | `0437e45c94563b09e13cb7a64478fc406947a93cb34a7e05870fc8dcd48e23fd` |
| `ARM-05` | `tokenizer.json` | LFS SHA-256 | `def76fb086971c7867b829c23a26261e38d9d74e02139253b38aeb9df8b4b50a` |

A Git object ID is not represented as a byte SHA-256. The scaffold deliberately
does not invent missing config, tokenizer, adapter, or remote-code byte hashes.
Before launch, the Owner-local runner must hash every pre-staged runtime file
and provide one complete `SHA256SUMS` manifest per dense arm. The manifest must
match the public LFS SHA-256 values where available and add local byte SHA-256
values for Git-backed files and every other runtime dependency.

## Frozen Adapter Intent

- `ARM-01`: `bm25s` Lucene method, `k1=1.2`, `b=0.75`, NumPy backend,
  Unicode NFKC/casefold tokenizer, no stopwords or stemming, zero-score filter,
  and lexical document-ID tie-break.
- `ARM-02`: dense-only BGE-M3, dimension 1,024, declared 8,192-token maximum;
  pooling and normalization require byte-locked Owner-local parity against the
  resolved official implementation.
- `ARM-03`: fixed query/document prefixes, 512-token passages, mean pooling over
  non-padding tokens, L2 normalization, cosine, research/non-commercial use.
- `ARM-04`: `query: ` prefix, no document prefix, CLS pooling, L2 normalized dot
  product, dimension 768, maximum 8,192 tokens, and byte-locked remote code.
- `ARM-05`: frozen patent retrieval instruction, no document instruction,
  last-token pooling with left padding, L2 normalized dot product, dimension
  1,024, and an Owner-local measured maximum length frozen before REP-DEV.

## Launch Boundary

All four dense locks remain
`metadata_frozen_owner_artifacts_pending`. Public metadata alone cannot make an
arm launch-ready. The Owner must validate local byte manifests, adapter parity,
Qwen maximum length, storage capacity, live provider pricing, and the external
termination/TTL path, then explicitly adopt the unchanged A1.2 execution
contract. GPU reservation and measured retrieval remain prohibited until every
launch checklist item passes.
