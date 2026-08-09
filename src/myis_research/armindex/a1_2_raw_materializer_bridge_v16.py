"""Raw v15 materializer compatibility for the v16 measured runner.

The protected v15 materializer intentionally stores source publication rows,
not executable units.  This small bridge reconstructs the frozen v11 logical
programs in process memory and, for dense arms, applies the additive v14
physical-window plan without importing the protected compiler.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from collections.abc import Mapping, Sequence
from typing import Any

from .a1_2_dense_overflow_adapter_v1 import (
    bytes_json,
    fit_plan,
    overflow_plan,
    split_template,
    template_for,
    tokenizer_ids,
)
from .a1_2_measured_executor_v16 import (
    DENSE_ARM_IDS,
    LogicalInput,
    PhysicalInput,
)
from .scientific_common_programs_v11 import (
    PublicationRecord,
    compile_common_program,
)

MAX_INPUT_TOKENS = {"ARM-02": 8192, "ARM-03": 512, "ARM-04": 8192, "ARM-05": 32768}
_COMMON_PROGRAMS = {
    "P00-TAC-DOC",
    "P01-TA-DOC",
    "P03-PASSAGE",
    "P04-SECTION-MULTIVIEW",
}
_CLAIM_BOUNDARY_RE = re.compile(
    r"(?:^|\n|;\s*)\s*(?P<number>[0-9]{1,4})(?:\s*[.:\-)\]]\s+|\s{2,})",
    re.MULTILINE,
)


class RawMaterializerBridgeV16Error(ValueError):
    """Fail-closed raw materialization error."""


def first_claim_segment(value: Any) -> str:
    """Return the exact frozen v1 first-boundary segment without inference."""

    text = unicodedata.normalize("NFKC", value).strip() if isinstance(value, str) else ""
    if not text:
        raise RawMaterializerBridgeV16Error("P02 claims_text has no segment")
    matches = list(_CLAIM_BOUNDARY_RE.finditer(text))
    accepted: list[tuple[int, int, int]] = []
    previous = 0
    for match in matches:
        number = int(match.group("number"))
        if number > previous:
            accepted.append((number, match.start(), match.end()))
            previous = number
    if not accepted:
        return text
    _number, _start, body_start = accepted[0]
    body_end = accepted[1][1] if len(accepted) > 1 else len(text)
    body = text[body_start:body_end].strip(" .;\t\r\n")
    if not body:
        raise RawMaterializerBridgeV16Error("P02 claims_text has no segment")
    return body


def _record(row: Mapping[str, Any]) -> PublicationRecord:
    required = {
        "family_token",
        "publication_token",
        "publication_ordinal",
        "title_en",
        "abstract_en",
        "claims_text",
        "claims",
    }
    if set(row) != required:
        raise RawMaterializerBridgeV16Error("raw publication fields are invalid")
    try:
        return PublicationRecord(
            family_token=row["family_token"],
            publication_token=row["publication_token"],
            publication_ordinal=row["publication_ordinal"],
            title_en=row["title_en"],
            abstract_en=row["abstract_en"],
            claims_text=row["claims_text"],
            claims=tuple(row["claims"]),
        )
    except (TypeError, ValueError) as error:
        raise RawMaterializerBridgeV16Error("raw publication record is invalid") from error


def _compile_units(rows: Sequence[Mapping[str, Any]], program_id: str) -> tuple[tuple[str, str, str, str | None], ...]:
    records = tuple(_record(row) for row in rows)
    if not records:
        raise RawMaterializerBridgeV16Error("raw corpus is empty")
    if program_id in _COMMON_PROGRAMS:
        try:
            compiled = compile_common_program(program_id, records)
        except Exception as error:
            raise RawMaterializerBridgeV16Error("frozen common-program compilation failed") from error
        return tuple((unit.unit_id, unit.family_token, unit.text, unit.view_id) for unit in compiled.units)
    if program_id != "P02-FIRST-CLAIM":
        raise RawMaterializerBridgeV16Error("unknown executable program")

    # The v15 successor compiled one P02 unit per source publication row.
    # Preserve that cardinality; family aggregation remains a ranking concern.
    units: list[tuple[str, str, str, str | None]] = []
    for record in records:
        try:
            selected = first_claim_segment(record.claims_text)
        except Exception as error:
            raise RawMaterializerBridgeV16Error("P02 first claim is unavailable") from error
        units.append(
            (
                f"{record.family_token}:{record.publication_token}:p02",
                record.family_token,
                selected,
                None,
            )
        )
    return tuple(units)


def _tokenizer(adapter: Any) -> Any:
    value = getattr(adapter, "tokenizer", None)
    if value is None:
        model = getattr(adapter, "model", None)
        value = getattr(model, "tokenizer", None)
    if value is None or not callable(value):
        raise RawMaterializerBridgeV16Error("dense adapter tokenizer is unavailable")
    return value


def _one_ids(tokenizer: Any, text: str, *, add_special_tokens: bool) -> tuple[int, ...]:
    try:
        return tokenizer_ids(tokenizer, (text,), add_special_tokens=add_special_tokens)[0]
    except Exception as error:
        raise RawMaterializerBridgeV16Error("frozen tokenizer could not materialize input") from error


def _optional_ids(tokenizer: Any, text: str) -> tuple[int, ...]:
    return () if not text else _one_ids(tokenizer, text, add_special_tokens=False)


def _decode(tokenizer: Any, values: Sequence[int]) -> str:
    try:
        if callable(getattr(tokenizer, "decode", None)):
            text = tokenizer.decode(
                list(values), skip_special_tokens=True, clean_up_tokenization_spaces=False
            )
        else:
            tokens = tokenizer.convert_ids_to_tokens(list(values))
            text = tokenizer.convert_tokens_to_string(tokens)
    except Exception as error:
        raise RawMaterializerBridgeV16Error("frozen tokenizer cannot decode a physical window") from error
    if not isinstance(text, str) or not text:
        raise RawMaterializerBridgeV16Error("decoded physical window is empty")
    return text


def _verify_window_ids(
    tokenizer: Any,
    text: str,
    *,
    expected_no_special: Sequence[int],
    planned_hash: str,
    role: str,
) -> None:
    """Prove decoded text re-tokenizes to the exact planned physical IDs."""

    observed_no_special = _one_ids(tokenizer, text, add_special_tokens=False)
    if tuple(observed_no_special) != tuple(expected_no_special):
        raise RawMaterializerBridgeV16Error(
            f"{role} tokenizer round-trip differs from the frozen plan"
        )
    observed_full = _one_ids(tokenizer, text, add_special_tokens=True)
    observed_hash = hashlib.sha256(bytes_json(observed_full)).hexdigest()
    if observed_hash != planned_hash:
        raise RawMaterializerBridgeV16Error(
            f"{role} physical token IDs differ from the frozen plan"
        )


def _physical_texts(*, arm_id: str, text: str, adapter: Any) -> tuple[PhysicalInput, ...]:
    tokenizer = _tokenizer(adapter)
    template = template_for(arm_id, side="corpus")
    prefix, suffix = split_template(template)
    source_ids = _one_ids(tokenizer, text, add_special_tokens=False)
    rendered = template.format(text=text)
    rendered_ids = _one_ids(tokenizer, rendered, add_special_tokens=False)
    full_ids = _one_ids(tokenizer, rendered, add_special_tokens=True)
    # Non-instruction dense arms use an empty template prefix; keep that
    # valid while preserving the frozen token plan for non-empty prefixes.
    prefix_ids = _optional_ids(tokenizer, prefix)
    suffix_ids = _optional_ids(tokenizer, suffix)
    limit = MAX_INPUT_TOKENS[arm_id]
    try:
        if len(full_ids) <= limit:
            plan = fit_plan(full_rendered_ids=full_ids, effective_limit=limit)
        else:
            plan = overflow_plan(
                source_ids=source_ids,
                rendered_without_special_ids=rendered_ids,
                full_rendered_ids=full_ids,
                prefix_ids=prefix_ids,
                suffix_ids=suffix_ids,
                effective_limit=limit,
            )
    except Exception as error:
        raise RawMaterializerBridgeV16Error("frozen physical-window planning failed") from error

    physical: list[PhysicalInput] = []
    for window in plan.physical_windows:
        if plan.mode == "EXISTING_FROZEN_ADAPTER_PATH":
            window_text = rendered
            count = len(source_ids)
            expected_no_special = rendered_ids
        else:
            source_window = source_ids[window.source_start : window.source_end]
            decoded = _decode(tokenizer, source_window)
            if _one_ids(tokenizer, decoded, add_special_tokens=False) != tuple(source_window):
                raise RawMaterializerBridgeV16Error(
                    "corpus source-token decode cannot be verified"
                )
            window_text = template.format(text=decoded)
            count = window.source_token_count
            expected_no_special = prefix_ids + tuple(source_window) + suffix_ids
        if count < 1:
            raise RawMaterializerBridgeV16Error("physical window source-token count is invalid")
        _verify_window_ids(
            tokenizer,
            window_text,
            expected_no_special=expected_no_special,
            planned_hash=window.physical_input_sha256,
            role="corpus",
        )
        if len(_one_ids(tokenizer, window_text, add_special_tokens=True)) > limit:
            raise RawMaterializerBridgeV16Error("physical window exceeds frozen effective limit")
        physical.append(PhysicalInput(window_text, count))
    if not physical or sum(item.source_token_count for item in physical) != len(source_ids):
        raise RawMaterializerBridgeV16Error("physical windows do not cover source tokens exactly")
    return tuple(physical)


def materialize_raw_corpus(
    rows: Sequence[Mapping[str, Any]],
    *,
    arm_id: str,
    program_id: str,
    adapter: Any | None = None,
) -> tuple[LogicalInput, ...]:
    """Convert raw materializer publication rows to opaque logical units."""

    units = _compile_units(rows, program_id)
    if arm_id == "ARM-01":
        return tuple(
            LogicalInput(unit_id, family, view, (PhysicalInput(text, 1),))
            for unit_id, family, text, view in units
        )
    if arm_id not in DENSE_ARM_IDS or adapter is None:
        raise RawMaterializerBridgeV16Error("dense raw materialization requires an adapter")
    records = {row["family_token"] for row in rows}
    result: list[LogicalInput] = []
    for unit_id, family, text, view in units:
        if family not in records:
            raise RawMaterializerBridgeV16Error("compiled unit family binding is invalid")
        result.append(LogicalInput(unit_id, family, view, _physical_texts(arm_id=arm_id, text=text, adapter=adapter)))
    return tuple(result)


def materialize_raw_query(
    row: Mapping[str, Any], *, arm_id: str, adapter: Any | None = None
) -> str | LogicalInput:
    """Convert one raw query row to an ARM-01 string or dense logical unit."""

    token, text = row.get("work_token"), row.get("text")
    if not isinstance(token, str) or not token.startswith("Q-") or not isinstance(text, str) or not text:
        raise RawMaterializerBridgeV16Error("raw query row is invalid")
    if arm_id == "ARM-01":
        return text
    if arm_id not in DENSE_ARM_IDS or adapter is None:
        raise RawMaterializerBridgeV16Error("dense raw query materialization requires an adapter")
    # Query templates are arm-specific and differ from corpus templates.
    tokenizer = _tokenizer(adapter)
    template = template_for(arm_id, side="rep_dev_queries")
    prefix, suffix = split_template(template)
    source_ids = _one_ids(tokenizer, text, add_special_tokens=False)
    rendered = template.format(text=text)
    rendered_ids = _one_ids(tokenizer, rendered, add_special_tokens=False)
    full_ids = _one_ids(tokenizer, rendered, add_special_tokens=True)
    prefix_ids = _one_ids(tokenizer, prefix, add_special_tokens=False)
    suffix_ids = _optional_ids(tokenizer, suffix)
    limit = MAX_INPUT_TOKENS[arm_id]
    try:
        if len(full_ids) <= limit:
            plan = fit_plan(full_rendered_ids=full_ids, effective_limit=limit)
        else:
            plan = overflow_plan(
                source_ids=source_ids,
                rendered_without_special_ids=rendered_ids,
                full_rendered_ids=full_ids,
                prefix_ids=prefix_ids,
                suffix_ids=suffix_ids,
                effective_limit=limit,
            )
    except Exception as error:
        raise RawMaterializerBridgeV16Error("frozen query physical-window planning failed") from error
    physical: list[PhysicalInput] = []
    for window in plan.physical_windows:
        source_window = source_ids[window.source_start : window.source_end]
        if plan.mode == "EXISTING_FROZEN_ADAPTER_PATH":
            piece = rendered
            expected_no_special = rendered_ids
            count = len(source_ids)
        else:
            decoded = _decode(tokenizer, source_window)
            if _one_ids(tokenizer, decoded, add_special_tokens=False) != tuple(source_window):
                raise RawMaterializerBridgeV16Error(
                    "query source-token decode cannot be verified"
                )
            piece = template.format(text=decoded)
            expected_no_special = prefix_ids + tuple(source_window) + suffix_ids
            count = window.source_token_count
        _verify_window_ids(
            tokenizer,
            piece,
            expected_no_special=expected_no_special,
            planned_hash=window.physical_input_sha256,
            role="query",
        )
        if len(_one_ids(tokenizer, piece, add_special_tokens=True)) > limit:
            raise RawMaterializerBridgeV16Error("query physical window exceeds frozen effective limit")
        physical.append(PhysicalInput(piece, count))
    return LogicalInput(token, token, None, tuple(physical))


__all__ = ["RawMaterializerBridgeV16Error", "materialize_raw_corpus", "materialize_raw_query"]
