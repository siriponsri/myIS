"""Deterministic physical-window planning for additive A1.2 dense overflow.

Logical program and unit identity remain outside this module.  The planner
partitions only the frozen tokenizer's source-token sequence and returns a
hash-only plan; it never embeds, retrieves, truncates, or changes an arm's
pooling and normalization behavior.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from ..kernel.canonical import canonical_sha256

IMPLEMENTATION_VERSION = "a1.2-dense-overflow-composition-v1"


class DenseOverflowAdapterError(ValueError):
    """Fail-closed physical input planning error."""


@dataclass(frozen=True)
class PhysicalWindow:
    source_start: int
    source_end: int
    source_token_count: int
    rendered_token_count: int
    physical_input_sha256: str


@dataclass(frozen=True)
class DenseInputPlan:
    mode: str
    raw_rendered_tokens: int
    source_token_count: int | None
    physical_windows: tuple[PhysicalWindow, ...]
    template_token_parity: bool
    source_tokens_represented: int | None
    source_tokens_dropped: int
    source_tokens_overlapped: int
    plan_sha256: str


def template_for(arm_id: str, *, side: str) -> str:
    if side == "corpus":
        return "encode document for different retrieval: {text}" if arm_id == "ARM-03" else "{text}"
    if side != "rep_dev_queries":
        raise DenseOverflowAdapterError("unsupported dense input side")
    try:
        return {
            "ARM-02": "{text}",
            "ARM-03": "encode query for different document retrieval: {text}",
            "ARM-04": "query: {text}",
            "ARM-05": (
                "Instruct: Retrieve patent families containing technical information relevant "
                "to prior-art search for the query patent family.\nQuery:{text}"
            ),
        }[arm_id]
    except KeyError as error:
        raise DenseOverflowAdapterError("unsupported dense arm") from error


def split_template(template: str) -> tuple[str, str]:
    if template.count("{text}") != 1:
        raise DenseOverflowAdapterError("dense template must contain exactly one text slot")
    prefix, suffix = template.split("{text}")
    return prefix, suffix


def _ids(value: Any, *, role: str, allow_empty: bool = False) -> tuple[int, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise DenseOverflowAdapterError(f"{role} token IDs are invalid")
    result = tuple(value)
    if (not result and not allow_empty) or any(not isinstance(item, int) or item < 0 for item in result):
        raise DenseOverflowAdapterError(f"{role} token IDs are invalid")
    return result


def tokenizer_ids(
    tokenizer: Any,
    texts: Sequence[str],
    *,
    add_special_tokens: bool,
) -> tuple[tuple[int, ...], ...]:
    if not texts or any(not isinstance(text, str) or not text for text in texts):
        raise DenseOverflowAdapterError("dense planner requires nonempty logical texts")
    try:
        encoded = tokenizer(
            list(texts),
            add_special_tokens=add_special_tokens,
            truncation=False,
            padding=False,
            return_attention_mask=False,
            return_token_type_ids=False,
            verbose=False,
        )
        values = encoded.get("input_ids")
    except Exception as error:
        raise DenseOverflowAdapterError("frozen tokenizer could not plan dense inputs") from error
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        raise DenseOverflowAdapterError("frozen tokenizer returned no token-ID batch")
    if len(values) != len(texts):
        raise DenseOverflowAdapterError("frozen tokenizer returned the wrong batch size")
    return tuple(_ids(value, role="logical input") for value in values)


def _special_envelope(
    *, rendered_without_special_ids: Sequence[int], full_rendered_ids: Sequence[int]
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """Recover the exact fast-tokenizer post-processing envelope.

    Some fast tokenizers, notably the frozen Qwen tokenizer, apply a backend
    post-processor in ``__call__`` that is not reproduced by
    ``build_inputs_with_special_tokens``.  Recovering the envelope from the
    actual frozen call preserves that behavior without hard-coding token IDs.
    """

    rendered = tuple(rendered_without_special_ids)
    full = tuple(full_rendered_ids)
    matches = [
        start
        for start in range(len(full) - len(rendered) + 1)
        if full[start : start + len(rendered)] == rendered
    ]
    if len(matches) != 1:
        raise DenseOverflowAdapterError("special-token envelope is not uniquely recoverable")
    start = matches[0]
    return full[:start], full[start + len(rendered) :]


def fit_plan(*, full_rendered_ids: Sequence[int], effective_limit: int) -> DenseInputPlan:
    full = _ids(full_rendered_ids, role="fit input")
    if effective_limit < 1 or len(full) > effective_limit:
        raise DenseOverflowAdapterError("fit plan received an overlength input")
    window = PhysicalWindow(
        source_start=0,
        source_end=0,
        source_token_count=0,
        rendered_token_count=len(full),
        physical_input_sha256=hashlib.sha256(bytes_json(full)).hexdigest(),
    )
    body = {
        "mode": "EXISTING_FROZEN_ADAPTER_PATH",
        "raw_rendered_tokens": len(full),
        "physical_input_sha256": window.physical_input_sha256,
    }
    return DenseInputPlan(
        mode=body["mode"],
        raw_rendered_tokens=len(full),
        source_token_count=None,
        physical_windows=(window,),
        template_token_parity=True,
        source_tokens_represented=None,
        source_tokens_dropped=0,
        source_tokens_overlapped=0,
        plan_sha256=canonical_sha256(body),
    )


def bytes_json(values: Sequence[int]) -> bytes:
    return ("[" + ",".join(str(value) for value in values) + "]").encode("ascii")


def overflow_plan(
    *,
    source_ids: Sequence[int],
    rendered_without_special_ids: Sequence[int],
    full_rendered_ids: Sequence[int],
    prefix_ids: Sequence[int],
    suffix_ids: Sequence[int],
    effective_limit: int,
) -> DenseInputPlan:
    source = _ids(source_ids, role="source")
    rendered = _ids(rendered_without_special_ids, role="rendered input")
    full = _ids(full_rendered_ids, role="full rendered input")
    prefix = _ids(prefix_ids, role="template prefix", allow_empty=True)
    suffix = _ids(suffix_ids, role="template suffix", allow_empty=True)
    if effective_limit < 1 or len(full) <= effective_limit:
        raise DenseOverflowAdapterError("overflow plan requires an overlength input")
    if rendered != prefix + source + suffix:
        raise DenseOverflowAdapterError("template/source token concatenation parity failed")
    leading_special, trailing_special = _special_envelope(
        rendered_without_special_ids=rendered,
        full_rendered_ids=full,
    )
    capacity = effective_limit - len(leading_special + prefix + suffix + trailing_special)
    if capacity < 1:
        raise DenseOverflowAdapterError("frozen template leaves no source-token capacity")

    windows: list[PhysicalWindow] = []
    start = 0
    while start < len(source):
        end = min(len(source), start + capacity)
        physical = leading_special + prefix + source[start:end] + suffix + trailing_special
        while len(physical) > effective_limit and end > start:
            end -= 1
            physical = leading_special + prefix + source[start:end] + suffix + trailing_special
        if end == start or len(physical) > effective_limit:
            raise DenseOverflowAdapterError("a source token cannot fit the frozen effective limit")
        # For standard single-sequence tokenizers, capacity is constant.  This
        # check proves that the chosen window is the longest remaining prefix.
        if end < len(source):
            longer = (
                leading_special + prefix + source[start : end + 1] + suffix + trailing_special
            )
            if len(longer) <= effective_limit:
                raise DenseOverflowAdapterError("physical window is not the longest fitting prefix")
        windows.append(
            PhysicalWindow(
                source_start=start,
                source_end=end,
                source_token_count=end - start,
                rendered_token_count=len(physical),
                physical_input_sha256=hashlib.sha256(bytes_json(physical)).hexdigest(),
            )
        )
        start = end
    represented = sum(window.source_token_count for window in windows)
    if represented != len(source):
        raise DenseOverflowAdapterError("physical windows dropped source tokens")
    body: Mapping[str, Any] = {
        "implementation_version": IMPLEMENTATION_VERSION,
        "mode": "DENSE_OVERFLOW_COMPOSED",
        "raw_rendered_tokens": len(full),
        "source_token_count": len(source),
        "overlap": 0,
        "windows": [
            {
                "source_start": window.source_start,
                "source_end": window.source_end,
                "source_token_count": window.source_token_count,
                "rendered_token_count": window.rendered_token_count,
                "physical_input_sha256": window.physical_input_sha256,
            }
            for window in windows
        ],
        "aggregation": "source_token_count_weighted_mean",
    }
    return DenseInputPlan(
        mode="DENSE_OVERFLOW_COMPOSED",
        raw_rendered_tokens=len(full),
        source_token_count=len(source),
        physical_windows=tuple(windows),
        template_token_parity=True,
        source_tokens_represented=represented,
        source_tokens_dropped=0,
        source_tokens_overlapped=0,
        plan_sha256=canonical_sha256(body),
    )
