from __future__ import annotations

import io
import json

import pytest

from myis_research.dapfam_p1_cli import build_parser
from myis_research.kernel.p1 import evaluate_baseline
from myis_research.progress import MAX_ETA_SECONDS, PROGRESS_SCHEMA, ProgressReporter


def test_non_tty_progress_is_structured_bounded_and_identifier_free() -> None:
    stream = io.StringIO()
    ticks = iter((100.0, 100.0, 104.0, 104.0, 108.0, 108.0, 108.0))
    reporter = ProgressReporter(
        stream=stream,
        heartbeat_seconds=120,
        interactive=False,
        clock=lambda: next(ticks),
    )
    with reporter.stage("evaluate_slots", total=2) as progress:
        progress.advance()
        progress.heartbeat()
        progress.advance()

    rows = [json.loads(line) for line in stream.getvalue().splitlines()]
    assert [row["status"] for row in rows] == ["started", "running", "completed"]
    assert all(row["schema_version"] == PROGRESS_SCHEMA for row in rows)
    assert all(set(row) == {
        "elapsed_seconds", "eta_seconds", "processed", "schema_version", "stage", "status", "total"
    } for row in rows)
    assert rows[1]["processed"] == 1
    assert 0 <= rows[1]["eta_seconds"] <= MAX_ETA_SECONDS
    assert rows[-1]["processed"] == rows[-1]["total"] == 2
    assert "query" not in stream.getvalue()
    assert "family" not in stream.getvalue()


def test_tty_progress_uses_stable_single_line_bar() -> None:
    stream = io.StringIO()
    reporter = ProgressReporter(
        stream=stream,
        heartbeat_seconds=120,
        interactive=True,
        tty_render_seconds=0,
    )
    with reporter.stage("load_inputs", total=2) as progress:
        progress.advance()
        progress.advance()
    output = stream.getvalue()
    assert "\rload_inputs" in output
    assert "1/2" in output.replace(" ", "")
    assert "2/2" in output.replace(" ", "")
    assert output.endswith("\n")


def test_progress_stage_rejects_item_identifiers() -> None:
    reporter = ProgressReporter(stream=io.StringIO(), interactive=False)
    with pytest.raises(ValueError, match="safe label"):
        reporter.stage("query/q-123", total=1)


def test_evaluator_reports_every_query_without_exposing_values() -> None:
    calls = 0

    def advance() -> None:
        nonlocal calls
        calls += 1

    evaluate_baseline(
        documents=[{"doc_id": "d1", "family_id": "f1", "text": "alpha"}],
        queries=[
            {"query_id": "q1", "text": "alpha", "split": "train"},
            {"query_id": "q2", "text": "beta", "split": "train"},
        ],
        qrels={"q1": ["f1"]},
        arm_id="R0",
        progress_sink=advance,
    )
    assert calls == 2


def test_p1_cli_defaults_to_120_second_heartbeats() -> None:
    args = build_parser().parse_args([
        "run",
        "--request", "request.json",
        "--cache-root", "cache",
    ])
    assert args.progress_interval_seconds == 120.0
