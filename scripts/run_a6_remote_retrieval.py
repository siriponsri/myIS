"""Build an Owner-Store-only deep family pool from frozen A6 index shards.

This adapter is intentionally a post-materialization operation.  It consumes
only the frozen ARM-03 query view and binary normalized passage shards, applies
the already-bound query prefix and MaxP family aggregation, and writes opaque
rankings.  No qrels, split membership, or per-query evaluation is accepted.
"""

from __future__ import annotations

import argparse
import json
from multiprocessing import get_context
from pathlib import Path
from typing import Any

import numpy as np
import torch
from sentence_transformers import SentenceTransformer


QUERY_PREFIX = "encode query for different document retrieval: "
VECTOR_DIMENSION = 1024
DEFAULT_DEPTHS = (200, 500, 1000, 2000)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"invalid JSONL row in {path}")
            rows.append(row)
    return rows


def load_shard(shard_root: Path) -> tuple[np.memmap, np.ndarray, list[str], list[int]]:
    metadata = read_jsonl(shard_root / "metadata.jsonl")
    family_tokens: list[str] = []
    chunk_counts: list[int] = []
    for row in metadata:
        token = row.get("family_token")
        count = row.get("chunk_count")
        if not isinstance(token, str) or not isinstance(count, int) or count < 1:
            raise ValueError(f"invalid shard metadata in {shard_root}")
        # Remote materialization uses uppercase namespace; normalize the
        # opaque token only.  The token remains non-identifying.
        family_tokens.append(token.lower())
        chunk_counts.append(count)
    total_chunks = sum(chunk_counts)
    vector_path = shard_root / "flat-l2-normalized.index.f32"
    expected_bytes = total_chunks * VECTOR_DIMENSION * 4
    if vector_path.stat().st_size != expected_bytes:
        raise ValueError(f"vector byte count mismatch for {shard_root}: {vector_path.stat().st_size} != {expected_bytes}")
    vectors = np.memmap(vector_path, dtype=np.float32, mode="r", shape=(total_chunks, VECTOR_DIMENSION))
    family_index = np.repeat(np.arange(len(family_tokens), dtype=np.int64), np.asarray(chunk_counts, dtype=np.int64))
    return vectors, family_index, family_tokens, chunk_counts


def rank_shard(
    model_path: str,
    query_rows: list[dict[str, Any]],
    shard_root: str,
    device_id: int,
    depths: tuple[int, ...],
    output_path: str,
) -> dict[str, Any]:
    device = torch.device(f"cuda:{device_id}" if torch.cuda.is_available() else "cpu")
    model = SentenceTransformer(model_path, device=str(device))
    query_texts = [QUERY_PREFIX + str(row["query_text"]) for row in query_rows]
    query_vectors = model.encode(
        query_texts,
        batch_size=16,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=True,
    ).astype(np.float32, copy=False)
    vectors, family_index_np, family_tokens, chunk_counts = load_shard(Path(shard_root))
    family_chunk_counts = dict(zip(family_tokens, chunk_counts, strict=True))
    family_index = torch.from_numpy(family_index_np).to(device=device)
    max_depth = max(depths)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    rows_written = 0
    with output.open("w", encoding="ascii", newline="") as handle:
        for query_row, query_np in zip(query_rows, query_vectors, strict=True):
            query = torch.from_numpy(query_np).to(device=device)
            max_scores = torch.full((len(family_tokens),), -torch.inf, dtype=torch.float32, device=device)
            for start in range(0, vectors.shape[0], 8192):
                block = torch.from_numpy(np.asarray(vectors[start : start + 8192])).to(device=device)
                scores = torch.mv(block, query)
                max_scores.scatter_reduce_(0, family_index[start : start + len(scores)], scores, reduce="amax", include_self=True)
            values, indices = torch.topk(max_scores, k=min(max_depth, len(family_tokens)), largest=True, sorted=False)
            candidates = [(family_tokens[int(index)], float(value)) for index, value in zip(indices.cpu().tolist(), values.cpu().tolist(), strict=True)]
            candidates.sort(key=lambda item: (-item[1], item[0]))
            for rank, (family, score) in enumerate(candidates, start=1):
                if rank > max_depth:
                    break
                handle.write(json.dumps({
                    "opaque_query_token": query_row["opaque_query_token"],
                    "opaque_family_token": family,
                    "rank": rank,
                    "score": score,
                    "pool_depth": max_depth,
                    "shard": Path(shard_root).name,
                    "passage_count": family_chunk_counts[family],
                    "field_provenance": "NOT_AVAILABLE_IN_A6_METADATA",
                }, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n")
                rows_written += 1
    return {"shard": Path(shard_root).name, "query_count": len(query_rows), "rows_written": rows_written, "depth": max_depth}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--shard", action="append", nargs=2, metavar=("DEVICE", "ROOT"), required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--depths", type=int, nargs="+", default=list(DEFAULT_DEPTHS))
    args = parser.parse_args()
    rows = read_jsonl(args.queries)
    if len(rows) != 1247 or any(set(row) != {"opaque_query_token", "query_text", "query_index"} for row in rows):
        raise ValueError("query source must be the committed 1,247-row opaque view")
    if sorted(args.depths) != list(args.depths) or args.depths[-1] < 200:
        raise ValueError("depths must be sorted and include at least 200")
    context = get_context("spawn")
    jobs = []
    for device_text, root_text in args.shard:
        device = int(device_text)
        jobs.append(context.Process(target=rank_shard, args=(args.model, rows, root_text, device, tuple(args.depths), str(args.output_dir / f"rankings-gpu{device}.jsonl"))))
    for job in jobs:
        job.start()
    for job in jobs:
        job.join()
    if any(job.exitcode != 0 for job in jobs):
        raise SystemExit("A6 retrieval shard worker failed")
    print(json.dumps({"status": "PASS_A6_DEEP_RANKING", "query_count": len(rows), "depths": args.depths}, sort_keys=True))


if __name__ == "__main__":
    main()
