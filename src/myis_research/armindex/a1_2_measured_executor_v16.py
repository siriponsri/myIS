"""Additive runtime core for the frozen A1.2 common screen.

This module deliberately has no access to protected stores, lifecycle state,
evaluation, or result export.  Its caller supplies already-compiled opaque
logical units and staged model directories.  The only returned identities are
opaque family tokens and deterministic ranks.
"""

from __future__ import annotations

import math
import os
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import numpy as np

from .bm25s_adapter import BM25sAdapter
from .scientific_common_programs_v11 import P04_VIEW_DEPTH, fuse_p04_view_rankings

DENSE_ARM_IDS = frozenset({"ARM-02", "ARM-03", "ARM-04", "ARM-05"})
P04_VIEW_IDS = frozenset({"title", "abstract", "claims"})
L2_NORMALIZATION_ATOL = 1e-3
MAX_INPUT_TOKENS = {"ARM-02": 8192, "ARM-03": 512, "ARM-04": 8192, "ARM-05": 32768}
ARM_CONFIG_OVERRIDES: dict[str, dict[str, Any]] = {
    "ARM-04": {
        "attn_implementation": "sdpa",
        "unpad_inputs": False,
        "use_memory_efficient_attention": False,
    }
}
_OPAQUE_ID_RE = re.compile(r"(?:F|Q)-[a-f0-9]{32}")
_PASSAGE_VIEW_RE = re.compile(r"passage-[0-9]{4}")


class MeasuredExecutorV16Error(ValueError):
    """Fail-closed runtime input or adapter error without payload disclosure."""


def aggregate_physical_window_vectors(
    arm_id: str,
    vectors: Sequence[Sequence[float]],
    source_token_counts: Sequence[int],
) -> tuple[float, ...]:
    """Apply the frozen token-weighted mean and dense-arm L2 normalization.

    This is the pure runtime portion of the v15 compiler contract. Keeping the
    helper in the measured bundle avoids importing the protected compiler
    module, whose broader Owner-local dependencies are intentionally excluded.
    """

    if arm_id not in DENSE_ARM_IDS:
        raise MeasuredExecutorV16Error(
            "weighted composition requires a dense arm"
        )
    if not vectors or len(vectors) != len(source_token_counts):
        raise MeasuredExecutorV16Error(
            "weighted composition inputs are incomplete"
        )
    dimension = len(vectors[0])
    if dimension < 1 or any(len(vector) != dimension for vector in vectors):
        raise MeasuredExecutorV16Error(
            "physical window vector dimensions differ"
        )
    if any(
        not isinstance(count, int) or count < 1
        for count in source_token_counts
    ):
        raise MeasuredExecutorV16Error(
            "physical window source-token weights are invalid"
        )
    if any(
        not math.isfinite(float(value))
        for vector in vectors
        for value in vector
    ):
        raise MeasuredExecutorV16Error(
            "physical window vectors contain non-finite values"
        )
    denominator = sum(source_token_counts)
    weighted = [
        sum(
            float(vector[index]) * count
            for vector, count in zip(
                vectors, source_token_counts, strict=True
            )
        )
        / denominator
        for index in range(dimension)
    ]
    norm = math.sqrt(sum(value * value for value in weighted))
    if not math.isfinite(norm) or norm <= 0:
        raise MeasuredExecutorV16Error(
            "weighted logical vector cannot be L2-normalized"
        )
    return tuple(value / norm for value in weighted)


@dataclass(frozen=True)
class PhysicalInput:
    """One compiler-planned physical input, retained only in Owner-local RAM."""

    text: str
    source_token_count: int
    token_ids: tuple[int, ...] | None = None


@dataclass(frozen=True)
class LogicalInput:
    """A logical corpus/query unit composed from one or more physical inputs."""

    logical_id: str
    family_token: str
    view_id: str | None
    physical_inputs: tuple[PhysicalInput, ...]


@dataclass(frozen=True)
class FamilyRank:
    family_token: str
    rank: int
    score: float


@dataclass(frozen=True)
class DenseIndex:
    arm_id: str
    logical_units: tuple[LogicalInput, ...]
    vectors: np.ndarray


class DenseEmbeddingAdapter(Protocol):
    """Frozen embedding interface used by the executor, never a downloader."""

    def encode(self, inputs: Sequence[str]) -> np.ndarray: ...


def _validate_frozen_depth(limit: int | None) -> None:
    if limit != 100:
        raise MeasuredExecutorV16Error(
            "the frozen common screen requires top-100 ranks"
        )


@dataclass
class SentenceTransformerDenseAdapter:
    """Local-only SentenceTransformer invocation for one already staged model."""

    arm_id: str
    model: Any
    batch_size: int = 1

    @classmethod
    def from_staged_directory(
        cls,
        *,
        arm_id: str,
        model_directory: Path,
        device: str,
        batch_size: int = 1,
        max_input_tokens: int | None = None,
    ) -> SentenceTransformerDenseAdapter:
        """Load exactly one staged model with Hub access disabled."""

        if arm_id not in DENSE_ARM_IDS:
            raise MeasuredExecutorV16Error("unsupported dense arm")
        if batch_size < 1:
            raise MeasuredExecutorV16Error("batch size must be positive")
        directory = model_directory.resolve(strict=True)
        if not directory.is_dir() or directory.is_symlink():
            raise MeasuredExecutorV16Error("staged model directory is invalid")
        if (
            os.environ.get("HF_HUB_OFFLINE") != "1"
            or os.environ.get("TRANSFORMERS_OFFLINE") != "1"
        ):
            raise MeasuredExecutorV16Error("offline model runtime is not enforced")
        try:
            import torch
            from sentence_transformers import SentenceTransformer
        except ImportError as error:
            raise MeasuredExecutorV16Error(
                "frozen dense runtime dependency is unavailable"
            ) from error
        model = SentenceTransformer(
            str(directory),
            device=device,
            trust_remote_code=arm_id == "ARM-04",
            local_files_only=True,
            model_kwargs={"torch_dtype": torch.float16},
            config_kwargs=ARM_CONFIG_OVERRIDES.get(arm_id),
        )
        model.max_seq_length = max_input_tokens or MAX_INPUT_TOKENS[arm_id]
        return cls(arm_id=arm_id, model=model, batch_size=batch_size)

    def encode(self, inputs: Sequence[str]) -> np.ndarray:
        if not inputs or any(not isinstance(item, str) or not item for item in inputs):
            raise MeasuredExecutorV16Error("dense inputs must be nonempty strings")
        values = np.asarray(
            self.model.encode(
                list(inputs),
                batch_size=self.batch_size,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            ),
            dtype=np.float64,
        )
        _validate_embedding_matrix(
            values, expected_rows=len(inputs), require_normalized=True
        )
        return values

    def encode_token_ids(self, inputs: Sequence[Sequence[int]]) -> np.ndarray:
        """Encode compiler-planned IDs without lossy text round-tripping."""

        if not inputs or any(not values for values in inputs):
            raise MeasuredExecutorV16Error("dense token-ID inputs must be nonempty")
        try:
            import torch
        except ImportError as error:
            raise MeasuredExecutorV16Error(
                "dense runtime tensor dependency is unavailable"
            ) from error
        tokenizer = getattr(self.model, "tokenizer", None)
        pad_id = getattr(tokenizer, "pad_token_id", None)
        padding_side = getattr(tokenizer, "padding_side", "right")
        if tokenizer is None or not isinstance(pad_id, int) or pad_id < 0:
            raise MeasuredExecutorV16Error("dense tokenizer padding is unavailable")
        if padding_side not in {"left", "right"}:
            raise MeasuredExecutorV16Error("dense tokenizer padding side is invalid")
        if any(
            any(not isinstance(value, int) or value < 0 for value in row)
            for row in inputs
        ):
            raise MeasuredExecutorV16Error("dense token IDs are invalid")
        try:
            device = next(self.model.parameters()).device
        except (AttributeError, StopIteration):
            # SentenceTransformer has parameters in production.  The CPU
            # fallback makes the exact-ID forward contract testable in isolation.
            device = torch.device("cpu")
        try:
            probe = self.model.tokenize(["probe"])
        except Exception as error:
            raise MeasuredExecutorV16Error(
                "dense tokenizer feature contract is unavailable"
            ) from error
        include_token_type_ids = "token_type_ids" in probe
        self.model.eval()
        encoded_batches: list[np.ndarray] = []
        for batch_start in range(0, len(inputs), self.batch_size):
            batch = inputs[batch_start : batch_start + self.batch_size]
            width = max(len(row) for row in batch)
            input_ids = torch.full(
                (len(batch), width), pad_id, dtype=torch.long, device=device
            )
            attention_mask = torch.zeros(
                (len(batch), width), dtype=torch.long, device=device
            )
            for index, row in enumerate(batch):
                values = torch.as_tensor(row, dtype=torch.long, device=device)
                start = width - len(row) if padding_side == "left" else 0
                input_ids[index, start : start + len(row)] = values
                attention_mask[index, start : start + len(row)] = 1
            features: dict[str, Any] = {
                "input_ids": input_ids,
                "attention_mask": attention_mask,
            }
            if include_token_type_ids:
                features["token_type_ids"] = torch.zeros_like(input_ids)
            try:
                with torch.inference_mode():
                    output = self.model.forward(features)
                batch_values = np.asarray(
                    output["sentence_embedding"].detach().cpu().numpy(),
                    dtype=np.float64,
                )
            except Exception as error:
                raise MeasuredExecutorV16Error(
                    "dense token-ID encoding failed"
                ) from error
            _validate_embedding_matrix(batch_values, expected_rows=len(batch))
            encoded_batches.append(batch_values)
        values = np.concatenate(encoded_batches, axis=0)
        _validate_embedding_matrix(values, expected_rows=len(inputs))
        norms = np.linalg.norm(values, axis=1, keepdims=True)
        values = values / norms
        _validate_embedding_matrix(values, expected_rows=len(inputs), require_normalized=True)
        return values


def _validate_embedding_matrix(
    values: np.ndarray, *, expected_rows: int, require_normalized: bool = False
) -> None:
    if values.ndim != 2 or values.shape[0] != expected_rows or values.shape[1] < 1:
        raise MeasuredExecutorV16Error(
            "dense adapter returned an invalid embedding matrix"
        )
    if not bool(np.isfinite(values).all()):
        raise MeasuredExecutorV16Error("dense adapter returned non-finite embeddings")
    norms = np.linalg.norm(values, axis=1)
    if not bool(np.all(norms > 0.0)):
        raise MeasuredExecutorV16Error("dense adapter returned a zero vector")
    if require_normalized and not bool(
        np.allclose(norms, np.ones(expected_rows), rtol=0.0, atol=L2_NORMALIZATION_ATOL)
    ):
        raise MeasuredExecutorV16Error(
            "dense adapter did not preserve frozen L2 normalization"
        )


def _validate_logical_inputs(
    values: Sequence[LogicalInput],
) -> tuple[LogicalInput, ...]:
    result = tuple(values)
    if not result:
        raise MeasuredExecutorV16Error("logical input set is empty")
    identifiers = [item.logical_id for item in result]
    if len(identifiers) != len(set(identifiers)):
        raise MeasuredExecutorV16Error("logical identifiers must be unique")
    for item in result:
        if (
            not item.logical_id
            or not _OPAQUE_ID_RE.fullmatch(item.family_token)
            or not item.physical_inputs
        ):
            raise MeasuredExecutorV16Error(
                "logical input identity or physical plan is invalid"
            )
        if (
            item.view_id is not None
            and item.view_id not in P04_VIEW_IDS
            and _PASSAGE_VIEW_RE.fullmatch(item.view_id) is None
        ):
            raise MeasuredExecutorV16Error("logical input view is invalid")
        for physical in item.physical_inputs:
            if (
                not physical.text
                or isinstance(physical.source_token_count, bool)
                or not isinstance(physical.source_token_count, int)
                or physical.source_token_count < 1
            ):
                raise MeasuredExecutorV16Error("physical input plan is invalid")
            if physical.token_ids is not None and (
                not physical.token_ids
                or any(
                    not isinstance(value, int) or value < 0
                    for value in physical.token_ids
                )
            ):
                raise MeasuredExecutorV16Error("physical token-ID plan is invalid")
    return result


def encode_logical_inputs(
    *,
    arm_id: str,
    adapter: DenseEmbeddingAdapter,
    logical_inputs: Sequence[LogicalInput],
) -> np.ndarray:
    """Encode physical windows then apply the frozen v14/v15 recomposition."""

    if arm_id not in DENSE_ARM_IDS:
        raise MeasuredExecutorV16Error("weighted dense encoding requires a dense arm")
    units = _validate_logical_inputs(logical_inputs)
    physical = [window for unit in units for window in unit.physical_inputs]
    token_id_windows = [window.token_ids for window in physical]
    if any(values is not None for values in token_id_windows):
        if not all(values is not None for values in token_id_windows):
            raise MeasuredExecutorV16Error("physical token-ID plan is incomplete")
        encoder = getattr(adapter, "encode_token_ids", None)
        if not callable(encoder):
            raise MeasuredExecutorV16Error(
                "adapter cannot consume the frozen physical token-ID plan"
            )
        encoded = np.asarray(encoder(token_id_windows), dtype=np.float64)
    else:
        encoded = np.asarray(
            adapter.encode([window.text for window in physical]), dtype=np.float64
        )
    _validate_embedding_matrix(encoded, expected_rows=len(physical))
    cursor = 0
    logical_vectors: list[tuple[float, ...]] = []
    for unit in units:
        count = len(unit.physical_inputs)
        windows = encoded[cursor : cursor + count]
        weights = [window.source_token_count for window in unit.physical_inputs]
        logical_vectors.append(
            aggregate_physical_window_vectors(
                arm_id, [tuple(vector) for vector in windows], weights
            )
        )
        cursor += count
    result = np.asarray(logical_vectors, dtype=np.float64)
    _validate_embedding_matrix(result, expected_rows=len(units))
    return result


def build_dense_index(
    *, arm_id: str, adapter: DenseEmbeddingAdapter, corpus: Sequence[LogicalInput]
) -> DenseIndex:
    """Build an in-memory dense index; logical units never become retrieval units."""

    units = _validate_logical_inputs(corpus)
    return DenseIndex(
        arm_id=arm_id,
        logical_units=units,
        vectors=encode_logical_inputs(
            arm_id=arm_id, adapter=adapter, logical_inputs=units
        ),
    )


def _family_max_ranks(
    units: Sequence[LogicalInput], scores: Sequence[float], *, limit: int | None
) -> tuple[FamilyRank, ...]:
    if len(units) != len(scores):
        raise MeasuredExecutorV16Error("score cardinality does not match logical units")
    maxima: dict[str, float] = {}
    for unit, value in zip(units, scores, strict=True):
        score = float(value)
        if not math.isfinite(score):
            raise MeasuredExecutorV16Error("similarity score is non-finite")
        maxima[unit.family_token] = max(maxima.get(unit.family_token, -math.inf), score)
    ordered = sorted(maxima.items(), key=lambda item: (-item[1], item[0]))
    if limit is not None:
        ordered = ordered[:limit]
    return tuple(
        FamilyRank(family, position, score)
        for position, (family, score) in enumerate(ordered, 1)
    )


def _p04_ranks(
    units: Sequence[LogicalInput], scores: Sequence[float], *, limit: int | None
) -> tuple[FamilyRank, ...]:
    views: dict[str, list[LogicalInput]] = {view: [] for view in P04_VIEW_IDS}
    view_scores: dict[str, list[float]] = {view: [] for view in P04_VIEW_IDS}
    for unit, score in zip(units, scores, strict=True):
        if unit.view_id not in P04_VIEW_IDS:
            raise MeasuredExecutorV16Error(
                "P04 requires title, abstract, and claims views"
            )
        views[unit.view_id].append(unit)
        view_scores[unit.view_id].append(float(score))
    ranked_views = {
        view: [
            {"family_token": row.family_token, "rank": row.rank}
            for row in _family_max_ranks(
                views[view], view_scores[view], limit=P04_VIEW_DEPTH
            )
        ]
        for view in sorted(P04_VIEW_IDS)
    }
    fused = fuse_p04_view_rankings(ranked_views)
    if limit is not None:
        fused = fused[:limit]
    return tuple(
        FamilyRank(family, rank, score) for rank, (family, score) in enumerate(fused, 1)
    )


def search_dense(
    *,
    index: DenseIndex,
    adapter: DenseEmbeddingAdapter,
    query: LogicalInput,
    program_id: str,
    limit: int | None = 100,
) -> tuple[FamilyRank, ...]:
    """Search a dense logical index with frozen family aggregation and P04 RRF."""

    _validate_frozen_depth(limit)
    if index.arm_id not in DENSE_ARM_IDS:
        raise MeasuredExecutorV16Error("dense index arm is invalid")
    query_vector = encode_logical_inputs(
        arm_id=index.arm_id, adapter=adapter, logical_inputs=(query,)
    )
    if query_vector.shape[1] != index.vectors.shape[1]:
        raise MeasuredExecutorV16Error("query and corpus vector dimensions differ")
    scores = np.matmul(index.vectors, query_vector[0])
    if program_id == "P04-SECTION-MULTIVIEW":
        if {unit.view_id for unit in index.logical_units} != P04_VIEW_IDS:
            raise MeasuredExecutorV16Error("P04 corpus view coverage is incomplete")
        return _p04_ranks(index.logical_units, scores, limit=limit)
    if program_id not in {
        "P00-TAC-DOC",
        "P01-TA-DOC",
        "P02-FIRST-CLAIM",
        "P03-PASSAGE",
    }:
        raise MeasuredExecutorV16Error("unknown frozen common program")
    return _family_max_ranks(index.logical_units, scores, limit=limit)


def search_bm25(
    *,
    corpus: Sequence[LogicalInput],
    query: str,
    program_id: str,
    limit: int | None = 100,
) -> tuple[FamilyRank, ...]:
    """Run frozen bm25s and apply the same family aggregation as dense arms."""

    _validate_frozen_depth(limit)
    units = _validate_logical_inputs(corpus)
    if not isinstance(query, str) or not query:
        raise MeasuredExecutorV16Error("BM25 query must be a nonempty string")
    documents = []
    for unit in units:
        if len(unit.physical_inputs) != 1:
            raise MeasuredExecutorV16Error(
                "ARM-01 must retain one physical input per logical unit"
            )
        documents.append(
            {
                "doc_id": unit.logical_id,
                "family_id": unit.family_token,
                "text": unit.physical_inputs[0].text,
            }
        )
    adapter = BM25sAdapter()
    rows = adapter.search(adapter.build_index(documents), query)
    by_id = {unit.logical_id: unit for unit in units}
    scored_units = [by_id[doc_id] for doc_id, _family, _score in rows]
    scores = [score for _doc_id, _family, score in rows]
    if program_id == "P04-SECTION-MULTIVIEW":
        if {unit.view_id for unit in units} != P04_VIEW_IDS:
            raise MeasuredExecutorV16Error("P04 corpus view coverage is incomplete")
        return _p04_ranks(scored_units, scores, limit=limit)
    if program_id not in {
        "P00-TAC-DOC",
        "P01-TA-DOC",
        "P02-FIRST-CLAIM",
        "P03-PASSAGE",
    }:
        raise MeasuredExecutorV16Error("unknown frozen common program")
    return _family_max_ranks(scored_units, scores, limit=limit)


def execute_program_cell_batch(
    *,
    arm_id: str,
    program_id: str,
    corpus: Sequence[LogicalInput],
    queries: Mapping[str, str | LogicalInput],
    adapter: DenseEmbeddingAdapter | None = None,
) -> dict[str, tuple[FamilyRank, ...]]:
    """Execute one cell for an ordered work-token mapping.

    ``queries`` must be an insertion-ordered mapping of opaque ``Q-`` work
    tokens to query strings (ARM-01) or logical physical plans (dense arms).
    The returned dict preserves that key order.  A dense corpus is encoded
    exactly once and all query physical windows are encoded in one adapter
    call; the BM25 index is built exactly once.  No evaluation or export is
    performed here.
    """

    _validate_frozen_depth(100)
    if not isinstance(queries, Mapping) or not queries:
        raise MeasuredExecutorV16Error("query mapping is empty")
    query_items = tuple(queries.items())
    if any(
        not isinstance(token, str)
        or _OPAQUE_ID_RE.fullmatch(token) is None
        or not token.startswith("Q-")
        for token, _ in query_items
    ):
        raise MeasuredExecutorV16Error("query mapping keys must be opaque Q tokens")
    if len({token for token, _ in query_items}) != len(query_items):
        raise MeasuredExecutorV16Error("query mapping keys must be unique")

    units = _validate_logical_inputs(corpus)
    if arm_id == "ARM-01":
        if adapter is not None or any(
            not isinstance(query, str) for _, query in query_items
        ):
            raise MeasuredExecutorV16Error(
                "ARM-01 batch requires string queries without a dense adapter"
            )
        documents = [
            {
                "doc_id": unit.logical_id,
                "family_id": unit.family_token,
                "text": unit.physical_inputs[0].text,
            }
            for unit in units
            if len(unit.physical_inputs) == 1
        ]
        if len(documents) != len(units):
            raise MeasuredExecutorV16Error(
                "ARM-01 must retain one physical input per logical unit"
            )
        bm25 = BM25sAdapter()
        index = bm25.build_index(documents)
        by_id = {unit.logical_id: unit for unit in units}
        result: dict[str, tuple[FamilyRank, ...]] = {}
        for token, query in query_items:
            rows = bm25.search(index, query)
            scored_units = [by_id[doc_id] for doc_id, _family, _score in rows]
            scores = [score for _doc_id, _family, score in rows]
            if program_id == "P04-SECTION-MULTIVIEW":
                if {unit.view_id for unit in units} != P04_VIEW_IDS:
                    raise MeasuredExecutorV16Error(
                        "P04 corpus view coverage is incomplete"
                    )
                result[token] = _p04_ranks(scored_units, scores, limit=100)
            elif program_id in {
                "P00-TAC-DOC",
                "P01-TA-DOC",
                "P02-FIRST-CLAIM",
                "P03-PASSAGE",
            }:
                result[token] = _family_max_ranks(scored_units, scores, limit=100)
            else:
                raise MeasuredExecutorV16Error("unknown frozen common program")
        return result

    if (
        arm_id not in DENSE_ARM_IDS
        or adapter is None
        or any(not isinstance(query, LogicalInput) for _, query in query_items)
    ):
        raise MeasuredExecutorV16Error(
            "dense batch requires logical queries and a staged adapter"
        )
    index = build_dense_index(arm_id=arm_id, adapter=adapter, corpus=units)
    query_units = tuple(query for _, query in query_items)
    query_vectors = encode_logical_inputs(
        arm_id=arm_id, adapter=adapter, logical_inputs=query_units
    )
    if query_vectors.shape[1] != index.vectors.shape[1]:
        raise MeasuredExecutorV16Error("query and corpus vector dimensions differ")
    if (
        program_id == "P04-SECTION-MULTIVIEW"
        and {unit.view_id for unit in units} != P04_VIEW_IDS
    ):
        raise MeasuredExecutorV16Error("P04 corpus view coverage is incomplete")
    result = {}
    for (token, _query), vector in zip(query_items, query_vectors, strict=True):
        scores = np.matmul(index.vectors, vector)
        if program_id == "P04-SECTION-MULTIVIEW":
            result[token] = _p04_ranks(index.logical_units, scores, limit=100)
        elif program_id in {
            "P00-TAC-DOC",
            "P01-TA-DOC",
            "P02-FIRST-CLAIM",
            "P03-PASSAGE",
        }:
            result[token] = _family_max_ranks(index.logical_units, scores, limit=100)
        else:
            raise MeasuredExecutorV16Error("unknown frozen common program")
    return result


def execute_program_cell(
    *,
    arm_id: str,
    program_id: str,
    corpus: Sequence[LogicalInput],
    query: str | LogicalInput,
    adapter: DenseEmbeddingAdapter | None = None,
) -> tuple[FamilyRank, ...]:
    """Execute one frozen program-arm cell and return exactly top-100 safe ranks.

    Inputs come from the Owner-local protected compiler.  ``corpus`` and a
    dense ``query`` remain in process memory.  The result carries only opaque
    family tokens, rank, and score; callers own checkpoints, evaluation, and
    all aggregate-safe export.
    """

    if arm_id == "ARM-01":
        if adapter is not None or not isinstance(query, str):
            raise MeasuredExecutorV16Error(
                "ARM-01 requires a string query without a dense adapter"
            )
        return search_bm25(corpus=corpus, query=query, program_id=program_id, limit=100)
    if (
        arm_id not in DENSE_ARM_IDS
        or adapter is None
        or not isinstance(query, LogicalInput)
    ):
        raise MeasuredExecutorV16Error(
            "dense arms require a staged adapter and logical query"
        )
    index = build_dense_index(arm_id=arm_id, adapter=adapter, corpus=corpus)
    return search_dense(
        index=index,
        adapter=adapter,
        query=query,
        program_id=program_id,
        limit=100,
    )
