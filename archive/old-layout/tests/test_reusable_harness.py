from __future__ import annotations

import sqlite3
import unittest
from decimal import Decimal

from myis_research.harness.candidate_ledger import RouteHit, build_family_ledger
from myis_research.harness.dapfam_text import (
    compose_independent_claim_view,
    compose_tac,
    compose_title_abstract,
    independent_claims,
    parse_claims,
    whitespace_windows,
)
from myis_research.harness.policy import b1_fusion_contract
from myis_research.harness.reranking import (
    parse_permutation,
    sliding_window_starts,
    strip_closed_thinking_blocks,
)
from myis_research.harness.sparse import (
    APP_DOCUMENT_FTS5,
    APP_PASSAGE_FTS5,
    assert_fts5_compatible,
    build_fts5_match_query,
)
from myis_research.harness.usage import (
    UsageRecord,
    aggregate_usage,
    check_prospective_caps,
)


class DapfamTextTests(unittest.TestCase):
    def test_text_claim_and_window_views(self) -> None:
        row = {
            "title": "  Patent title  ",
            "abstract": "Patent abstract",
            "claims": "1. A widget with a sensor.\n2. The widget according to claim 1 with a cover.",
        }
        self.assertEqual(compose_title_abstract(row), "Patent title\n\nPatent abstract")
        self.assertEqual(
            parse_claims(row["claims"]),
            ("A widget with a sensor.", "The widget according to claim 1 with a cover."),
        )
        self.assertEqual(independent_claims(row["claims"]), ("A widget with a sensor.",))
        self.assertEqual(compose_independent_claim_view(row), "A widget with a sensor.")
        self.assertTrue(compose_tac(row).startswith("Patent title\n\nPatent abstract\n\n"))
        self.assertEqual(
            whitespace_windows("one two three four five", 3),
            ("one two three", "four five"),
        )
        self.assertEqual(
            whitespace_windows("one two three four five", 3, stride_tokens=2),
            ("one two three", "three four five"),
        )

    def test_claim_fallback_and_invalid_windows(self) -> None:
        claims = ["According to claim 1, a cover.", "According to claim 2, a seal."]
        self.assertEqual(independent_claims(claims), (claims[0],))
        with self.assertRaises(ValueError):
            whitespace_windows("text", 0)
        with self.assertRaises(ValueError):
            whitespace_windows("text", 2, stride_tokens=3)


class SparseTests(unittest.TestCase):
    def test_match_query_is_deduplicated_and_bounded(self) -> None:
        self.assertEqual(
            build_fts5_match_query("Alpha alpha beta-gamma x", max_terms=2),
            '"alpha" OR "beta-gamma"',
        )
        self.assertEqual(build_fts5_match_query("x"), '""')

    def test_both_app_fts5_schemas_are_compatible(self) -> None:
        for contract in (APP_PASSAGE_FTS5, APP_DOCUMENT_FTS5):
            connection = sqlite3.connect(":memory:")
            try:
                id_columns = ", ".join(f"{name} UNINDEXED" for name in contract.id_columns)
                connection.execute(
                    f"CREATE VIRTUAL TABLE {contract.table_name} USING "
                    f"fts5({contract.text_column}, {id_columns}, tokenize='unicode61')"
                )
                inspection = assert_fts5_compatible(connection, contract)
                self.assertTrue(inspection.compatible)
            finally:
                connection.close()

    def test_schema_mismatch_fails(self) -> None:
        connection = sqlite3.connect(":memory:")
        try:
            connection.execute(
                "CREATE VIRTUAL TABLE passages USING "
                "fts5(text, patent_id UNINDEXED, chunk_id UNINDEXED, tokenize='unicode61')"
            )
            with self.assertRaises(ValueError):
                assert_fts5_compatible(connection, APP_PASSAGE_FTS5)
        finally:
            connection.close()


class MinMaxFusionTests(unittest.TestCase):
    @staticmethod
    def hit(route: str, family: str, rank: int, score: float, query: str = "q") -> RouteHit:
        return RouteHit(query, route, route, family, f"pub-{family}", rank, score)

    def test_direction_constant_scores_missing_routes_and_order(self) -> None:
        hits = [
            self.hit("dense", "A", 1, 0.9),
            self.hit("dense", "B", 3, 0.5),
            self.hit("dense", "C", 2, 0.7),
            self.hit("bm25", "A", 1, -5.0),
            self.hit("bm25", "B", 2, -1.0),
            self.hit("dense", "D", 1, 1.0, query="constant"),
            self.hit("dense", "E", 2, 1.0, query="constant"),
        ]
        rows = build_family_ledger(
            hits,
            fusion_method="minmax_weighted",
            weights={"dense": 0.7, "bm25": 0.3},
            score_directions={"dense": "higher", "bm25": "lower"},
        )
        by_query = {}
        for row in rows:
            by_query.setdefault(row.query_id, []).append(row)
        self.assertEqual([row.family_id for row in by_query["q"]], ["A", "C", "B"])
        self.assertEqual([row.fused_score for row in by_query["q"]], [1.0, 0.35, 0.0])
        self.assertEqual(
            [row.fused_score for row in by_query["constant"]],
            [0.7, 0.7],
        )

    def test_score_direction_is_explicit(self) -> None:
        with self.assertRaises(ValueError):
            build_family_ledger(
                [self.hit("dense", "A", 1, 0.9)],
                fusion_method="minmax_weighted",
                weights={"dense": 1.0},
            )
        contract = b1_fusion_contract()
        self.assertEqual(contract.weights, {"dense": 0.7, "bm25": 0.3})
        self.assertEqual(contract.score_directions, {"dense": "higher", "bm25": "lower"})


class RerankingTests(unittest.TestCase):
    def test_json_text_thinking_and_identity_fallbacks(self) -> None:
        expected = ["A", "B", "C"]
        self.assertEqual(
            parse_permutation('["C", "A", "B"]', expected).permutation,
            ("C", "A", "B"),
        )
        result = parse_permutation("<think>closed reasoning</think>\nB\nC\nA", expected)
        self.assertTrue(result.valid)
        self.assertEqual(result.permutation, ("B", "C", "A"))
        for invalid in ('["A", "B"]', '["A", "A", "C"]', '["A", "B", "X"]'):
            parsed = parse_permutation(invalid, expected)
            self.assertFalse(parsed.valid)
            self.assertEqual(parsed.permutation, tuple(expected))
        self.assertFalse(parse_permutation("<think>open\nA\nB\nC", expected).valid)
        self.assertEqual(strip_closed_thinking_blocks("<think>x</think> A"), "A")

    def test_sliding_windows_are_stable(self) -> None:
        self.assertEqual(sliding_window_starts(5, window=3, stride=2), (0, 2))
        self.assertEqual(sliding_window_starts(6, window=4, stride=3), (0, 2))
        self.assertEqual(sliding_window_starts(2, window=4, stride=1), (0,))


class UsageTests(unittest.TestCase):
    def test_exact_aggregation(self) -> None:
        records = [
            UsageRecord("A2", 11, input_tokens=10, output_tokens=5, latency_ms=20, retries=1, rollouts=2, usd=Decimal("1.25")),
            UsageRecord("A2", 11, input_tokens=3, output_tokens=2, latency_ms=10, rollouts=1, usd=Decimal("0.75")),
            UsageRecord(None, None, rollouts=0, usd=Decimal("2.00"), shared=True),
        ]
        summary = aggregate_usage(records)
        self.assertEqual(summary.total.usd, Decimal("4.00"))
        self.assertEqual(summary.by_seed[("A2", 11)].rollouts, 3)
        self.assertEqual(summary.shared.usd, Decimal("2.00"))

    def test_all_track_s_caps(self) -> None:
        seed_breach = check_prospective_caps(
            [], [UsageRecord("A2", 11, rollouts=161, usd=Decimal("1"))]
        )
        self.assertFalse(seed_breach.allowed)
        arm_breach = check_prospective_caps(
            [],
            [
                UsageRecord("A2", 11, rollouts=160, usd=Decimal("7")),
                UsageRecord("A2", 23, rollouts=160, usd=Decimal("7")),
                UsageRecord("A2", 47, rollouts=161, usd=Decimal("7")),
            ],
        )
        self.assertFalse(arm_breach.allowed)
        shared_breach = check_prospective_caps(
            [], [UsageRecord(None, None, usd=Decimal("31"), shared=True)]
        )
        self.assertFalse(shared_breach.allowed)
        target = check_prospective_caps(
            [],
            [
                UsageRecord("A2", 11, usd=Decimal("20")),
                UsageRecord("A2L", 11, usd=Decimal("20")),
                UsageRecord("A3", 11, usd=Decimal("20")),
                UsageRecord("AUX", 11, usd=Decimal("20")),
                UsageRecord(None, None, usd=Decimal("11"), shared=True),
            ],
        )
        self.assertTrue(target.allowed)
        self.assertEqual(len(target.warnings), 1)
        hard_stop = check_prospective_caps(
            [],
            [
                UsageRecord("A2", 11, usd=Decimal("20")),
                UsageRecord("A2L", 11, usd=Decimal("20")),
                UsageRecord("A3", 11, usd=Decimal("20")),
                UsageRecord("AUX1", 11, usd=Decimal("20")),
                UsageRecord("AUX2", 11, usd=Decimal("20")),
                UsageRecord(None, None, usd=Decimal("1"), shared=True),
            ],
        )
        self.assertFalse(hard_stop.allowed)
        self.assertTrue(any("hard stop" in breach for breach in hard_stop.breaches))


if __name__ == "__main__":
    unittest.main()
