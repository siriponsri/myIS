# Inference Capacity and Batching Plan

## Architecture

```text
versioned query dataset
  -> length buckets
  -> bounded async request queue
  -> one vLLM engine per GPU/model replica
  -> continuous batching
  -> per-query checkpoint and validation
  -> MLflow run, trace, metrics and artifacts
```

Do not start multiple workers that each load the same model on one GPU. Client
workers send concurrent requests to one OpenAI-compatible vLLM endpoint.

## Mini-batch semantics

`client_chunk_size` controls checkpoint and submission units. `concurrency`
controls in-flight requests. vLLM owns the dynamic device batch through
continuous batching. These are distinct settings and both must be logged.

Bucket prompts by measured tokenizer length: <=1024, 1025-2048, 2049-4096, and
>4096 tokens. Preserve `query_id` order in output records even when completion
order differs. Write one durable result per query and make retries idempotent.

## Capacity gate

Benchmark candidate GPUs on an approved performance-tuning set, never DEV or
held-out labels. Select using cost per 1,000 valid completed queries, subject to
latency and failure ceilings. A100 80GB is allowed only after measured evidence
shows it is preferable for the selected model/context/workload.

Required grid and metrics live in
`03_experiments/config/inference/benchmark-matrix.yaml`.
Record at least:

- engine and exact version;
- model ID, revision, dtype, quantization and tensor parallelism;
- concurrency, client chunk size, `max_num_seqs`,
  `max_num_batched_tokens`, context and output limits;
- seed, sampling parameters, batch-invariance mode and retry policy;
- input/output token counts, throughput, p50/p95 latency, peak VRAM, OOMs,
  failures, cost and valid completion count.

## Reproducibility

Before confirmatory use, compare a fixed sample across concurrency and request
order. If outputs or metrics differ materially, either enable a validated
batch-invariance mode and accept its throughput cost, or freeze composition and
report the sensitivity. Do not claim bitwise reproducibility without testing it.

## Vast lifecycle

Use API for low-volume model scouting and a large reflector where appropriate.
Use Vast/vLLM only for a selected local-capable target with enough rollouts to
justify fixed hourly cost. Interruptible instances require per-mini-batch
checkpointing. Record storage, bandwidth, startup, retry and idle cost. Destroy
or retain an instance only under the applicable Owner budget/lifecycle gate.
