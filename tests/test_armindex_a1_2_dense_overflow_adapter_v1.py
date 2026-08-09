from __future__ import annotations

from pathlib import Path

from myis_research.armindex.a1_2_dense_overflow_adapter_v1 import (
    fit_plan,
    overflow_plan,
    split_template,
    template_for,
)
from myis_research.armindex.a1_2_dense_overflow_composition_audit_v1 import (
    _batch_plans,
    _validate_contract,
)

ROOT = Path(__file__).resolve().parents[1]


class _Tokenizer:
    def __call__(self, values: list[str], **kwargs: object) -> dict[str, list[list[int]]]:
        rows = [[ord(character) for character in value] for value in values]
        if kwargs.get("add_special_tokens"):
            rows = [self.build_inputs_with_special_tokens(row) for row in rows]
        return {"input_ids": rows}

    def build_inputs_with_special_tokens(self, values: list[int]) -> list[int]:
        return [101, *values, 102]


def test_fit_path_is_single_window_and_unchanged() -> None:
    plan = fit_plan(full_rendered_ids=[101, 7, 8, 102], effective_limit=8)
    assert plan.mode == "EXISTING_FROZEN_ADAPTER_PATH"
    assert len(plan.physical_windows) == 1
    assert plan.source_token_count is None
    assert plan.source_tokens_dropped == 0


def test_overflow_windows_are_longest_contiguous_zero_overlap_partition() -> None:
    tokenizer = _Tokenizer()
    source = tuple(range(10, 20))
    prefix = (1, 2)
    rendered = prefix + source
    full = tuple(tokenizer.build_inputs_with_special_tokens(list(rendered)))
    plan = overflow_plan(
        source_ids=source,
        rendered_without_special_ids=rendered,
        full_rendered_ids=full,
        prefix_ids=prefix,
        suffix_ids=(),
        effective_limit=7,
    )
    assert plan.mode == "DENSE_OVERFLOW_COMPOSED"
    assert [window.source_token_count for window in plan.physical_windows] == [3, 3, 3, 1]
    assert [window.source_start for window in plan.physical_windows] == [0, 3, 6, 9]
    assert [window.source_end for window in plan.physical_windows] == [3, 6, 9, 10]
    assert plan.source_tokens_represented == 10
    assert plan.source_tokens_dropped == 0
    assert plan.source_tokens_overlapped == 0
    assert max(window.rendered_token_count for window in plan.physical_windows) <= 7


def test_templates_are_exact_and_single_slot() -> None:
    assert split_template(template_for("ARM-03", side="corpus")) == (
        "encode document for different retrieval: ",
        "",
    )
    assert "Query:{text}" in template_for("ARM-05", side="rep_dev_queries")


def test_batch_planner_preserves_fit_and_composes_overflow() -> None:
    plans = _batch_plans(
        _Tokenizer(),
        texts=["ab", "abcdefghij"],
        arm_id="ARM-02",
        side="corpus",
        effective_limit=6,
    )
    assert [plan.mode for plan in plans] == [
        "EXISTING_FROZEN_ADAPTER_PATH",
        "DENSE_OVERFLOW_COMPOSED",
    ]
    assert plans[1].source_tokens_represented == 10
    assert max(window.rendered_token_count for window in plans[1].physical_windows) == 6


def test_frozen_repair_contract_binds_current_planner() -> None:
    contract = _validate_contract(ROOT)
    assert contract["requirements"]["compatible_program_arm_cells"] == 25
    assert contract["publication_method_disclosure"]["required"] is True
