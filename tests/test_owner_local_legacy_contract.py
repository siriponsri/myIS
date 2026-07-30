from __future__ import annotations

import json
from pathlib import Path

import pytest

from myis_research.kernel.canonical import file_sha256
from myis_research.kernel.p1 import evaluate_baseline
from myis_research.legacy_dapfam import build_legacy_p1_request
from myis_research.owner_local import OwnerLocalContractError
from myis_research.owner_local_cli import main as owner_local_main
from myis_research.owner_local_runner import (
    _FTS_TERM_CAP,
    _build_or_reuse_index,
    _load_qrels,
    _load_queries,
    _repeat_equivalent,
    _store_path,
    _sqlite_ranker,
    process,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=True) + "\n" for row in rows), encoding="utf-8")


def _legacy_tree(root: Path) -> None:
    dapfam = root / "processed" / "dapfam"
    tac = root / "processed" / "retrieval" / "dapfam_citation_controlled_tac512"
    _write_jsonl(dapfam / "patents.jsonl", [
        {"publication_id": "pub-a", "family_id": "target-a"},
        {"publication_id": "pub-b", "family_id": "target-b"},
    ])
    _write_jsonl(dapfam / "chunks_doc.jsonl", [
        {"doc_id": "doc-a", "publication_id": "pub-a", "text": "alpha system"},
        {"doc_id": "doc-b", "publication_id": "pub-b", "text": "beta system"},
    ])
    _write_jsonl(tac / "corpus_tac_passages.jsonl", [
        {"passage_id": "tac-a", "publication_id": "pub-a", "text": "alpha system"},
        {"passage_id": "tac-b", "publication_id": "pub-b", "text": "beta system"},
    ])
    _write_jsonl(dapfam / "queries.jsonl", [
        {"query_id": f"q{index}", "family_id": f"query-family-{index}", "text": "alpha"}
        for index in range(375)
    ])
    (dapfam / "qrels.tsv").write_text(
        "".join(f"q{index}\t0\tpub-a\t1\n" for index in range(375)), encoding="utf-8"
    )
    tac.mkdir(parents=True, exist_ok=True)
    (tac / "qrels_domain.tsv").write_text(
        "".join(f"q{index}\t0\tpub-a\t1\tIN\n" for index in range(375)), encoding="utf-8"
    )


def _request(root: Path) -> dict[str, object]:
    _, request = build_legacy_p1_request(root, REPOSITORY_ROOT)
    return request


def test_legacy_owner_local_path_preflights_and_emits_aggregate_only_receipt(tmp_path: Path) -> None:
    legacy_root = tmp_path / "legacy"
    protected_root = tmp_path / "protected"
    store_root = tmp_path / "derived-store"
    legacy_root.mkdir()
    protected_root.mkdir()
    _legacy_tree(legacy_root)
    request_path = tmp_path / "request.json"
    receipt_path = tmp_path / "receipt.json"
    request_path.write_text(json.dumps(_request(legacy_root)), encoding="utf-8")

    process(
        request_path,
        protected_root,
        receipt_path,
        store_root=store_root,
        legacy_root=legacy_root,
        repository_root=REPOSITORY_ROOT,
    )

    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["status"] == "blocked"  # Historical exposure stays non-claimable.
    assert receipt["aggregate_hashes"]["r0_integrity"]
    assert receipt["aggregate_hashes"]["r0w_integrity"]
    assert receipt["aggregate_hashes"]["r0_index"] == file_sha256(next((store_root / "r0").rglob("index.sqlite")))
    assert "query-family-" not in json.dumps(receipt)
    assert "pub-a" not in json.dumps(receipt)


def test_domain_qrels_must_match_base_family_relevance(tmp_path: Path) -> None:
    base = tmp_path / "base.tsv"
    domain = tmp_path / "domain.tsv"
    base.write_text("q\t0\tpub\t1\n", encoding="utf-8")
    domain.write_text("q\t0\tother\t1\tIN\n", encoding="utf-8")
    with pytest.raises(OwnerLocalContractError, match="same positive family"):
        _load_qrels(base, domain, {"pub": "family", "other": "other-family"}, {"family", "other-family"})


def test_query_family_uses_explicit_field_or_publication_mapping(tmp_path: Path) -> None:
    query_path = tmp_path / "queries.jsonl"
    _write_jsonl(query_path, [{"query_id": "publication-id", "text": "query"}])
    assert _load_queries(query_path, {"publication-id": "resolved-family"})[0]["family_id"] == "resolved-family"
    with pytest.raises(OwnerLocalContractError, match="family mapping"):
        _load_queries(query_path, {})


def test_index_reuse_requires_actual_sqlite_hash_and_rebuilds_without_overwrite(tmp_path: Path) -> None:
    source = tmp_path / "source.jsonl"
    source.write_text("{}\n", encoding="utf-8")
    rows = [{"doc_id": "d", "family_id": "f", "text": "alpha beta"}]
    kwargs = {
        "family_map": {"pub": "f"},
        "source_hashes": {"source_sha256": file_sha256(source)},
        "view_revision": "synthetic-view-v1",
    }
    index_path, first_hash = _build_or_reuse_index(rows, source, tmp_path / "store", **kwargs)
    assert first_hash == file_sha256(index_path)
    reused_path, reused_hash = _build_or_reuse_index(rows, source, tmp_path / "store", **kwargs)
    assert (reused_path, reused_hash) == (index_path, first_hash)
    index_path.write_bytes(index_path.read_bytes() + b"tamper")
    corrupted_bytes = index_path.read_bytes()
    rebuilt_path, rebuilt_hash = _build_or_reuse_index(rows, source, tmp_path / "store", **kwargs)
    assert index_path.read_bytes() == corrupted_bytes
    assert rebuilt_path != index_path
    assert rebuilt_hash == file_sha256(rebuilt_path)


def test_fts_ranker_uses_or_semantics_and_rejects_overlong_query(tmp_path: Path) -> None:
    source = tmp_path / "source.jsonl"
    source.write_text("{}\n", encoding="utf-8")
    index_path, _ = _build_or_reuse_index(
        [
            {"doc_id": "d-alpha", "family_id": "f-alpha", "text": "alpha"},
            {"doc_id": "d-beta", "family_id": "f-beta", "text": "beta"},
        ],
        source,
        tmp_path / "store",
        family_map={},
        source_hashes={"source_sha256": file_sha256(source)},
        view_revision="synthetic-view-v1",
    )
    assert {row[0] for row in _sqlite_ranker(index_path)("alpha beta")} == {"d-alpha", "d-beta"}
    too_many_terms = " ".join(f"term{index}" for index in range(_FTS_TERM_CAP + 1))
    with pytest.raises(OwnerLocalContractError, match="term cap"):
        _sqlite_ranker(index_path)(too_many_terms)


def test_tac512_rows_are_not_windowed_again_and_repeat_checks_retrieval_commitments() -> None:
    documents = [{"doc_id": "tac", "family_id": "target", "text": "alpha " * 1025}]
    kwargs = {
        "documents": documents,
        "queries": [{"query_id": "q", "text": "alpha", "split": "train"}],
        "qrels": {"q": ["target"]},
        "qrel_domains": {"q": {"target": "IN"}},
        "arm_id": "R0-W",
        "window_size": 512,
        "split_name": "train",
    }
    prewindowed = evaluate_baseline(**kwargs, documents_are_windowed=True)
    rewound = evaluate_baseline(**kwargs, documents_are_windowed=False)
    assert prewindowed["counts"]["indexed_units"] == 1
    assert rewound["counts"]["indexed_units"] == 3
    assert prewindowed["retrieval"]["documents_are_windowed"] is True
    assert _repeat_equivalent(prewindowed, prewindowed)
    changed = {**prewindowed, "ranking_commitment": "0" * 64}
    assert not _repeat_equivalent(prewindowed, changed)


def test_store_root_inside_legacy_tree_is_rejected(tmp_path: Path) -> None:
    legacy_root = tmp_path / "legacy"
    protected_root = tmp_path / "protected"
    legacy_root.mkdir()
    protected_root.mkdir()
    _legacy_tree(legacy_root)
    request_path = tmp_path / "request.json"
    request_path.write_text(json.dumps(_request(legacy_root)), encoding="utf-8")
    with pytest.raises(OwnerLocalContractError, match="outside"):
        process(
            request_path,
            protected_root,
            tmp_path / "receipt.json",
            store_root=legacy_root / "derived-store",
            legacy_root=legacy_root,
            repository_root=REPOSITORY_ROOT,
        )


def test_legacy_runner_rechecks_request_scope_at_execution(tmp_path: Path) -> None:
    legacy_root = tmp_path / "legacy"
    protected_root = tmp_path / "protected"
    legacy_root.mkdir()
    protected_root.mkdir()
    _legacy_tree(legacy_root)
    request = _request(legacy_root)
    request["scope"] = {"campaign_sha256": "0" * 64}
    request_path = tmp_path / "request.json"
    request_path.write_text(json.dumps(request), encoding="utf-8")
    with pytest.raises(OwnerLocalContractError, match="scope does not match current bindings"):
        process(
            request_path,
            protected_root,
            tmp_path / "receipt.json",
            store_root=tmp_path / "store",
            legacy_root=legacy_root,
            repository_root=REPOSITORY_ROOT,
        )


def test_owner_local_receipt_cannot_be_written_into_git_or_legacy_tree(tmp_path: Path) -> None:
    legacy_root = tmp_path / "legacy"
    protected_root = tmp_path / "protected"
    legacy_root.mkdir()
    protected_root.mkdir()
    _legacy_tree(legacy_root)
    request_path = tmp_path / "request.json"
    request_path.write_text(json.dumps(_request(legacy_root)), encoding="utf-8")
    with pytest.raises(OwnerLocalContractError, match="outside Git"):
        process(
            request_path,
            protected_root,
            REPOSITORY_ROOT / "forbidden-receipt.json",
            store_root=tmp_path / "store",
            legacy_root=legacy_root,
            repository_root=REPOSITORY_ROOT,
        )
    with pytest.raises(OwnerLocalContractError, match="read-only legacy tree"):
        process(
            request_path,
            protected_root,
            legacy_root / "forbidden-receipt.json",
            store_root=tmp_path / "store",
            legacy_root=legacy_root,
            repository_root=REPOSITORY_ROOT,
        )


def test_blocked_owner_local_cli_returns_nonzero_without_claiming_acceptance(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    legacy_root = tmp_path / "legacy"
    protected_root = tmp_path / "protected"
    legacy_root.mkdir()
    protected_root.mkdir()
    _legacy_tree(legacy_root)
    request_path = tmp_path / "request.json"
    receipt_path = tmp_path / "receipt.json"
    request_path.write_text(json.dumps(_request(legacy_root)), encoding="utf-8")

    exit_code = owner_local_main([
        "--repository-root", str(REPOSITORY_ROOT),
        "--request", str(request_path),
        "--protected-root", str(protected_root),
        "--legacy-root", str(legacy_root),
        "--store-root", str(tmp_path / "store"),
        "--receipt", str(receipt_path),
    ])

    captured = capsys.readouterr()
    assert exit_code == 3
    assert captured.out == ""
    assert "P1_BLOCKED_WITH_EVIDENCE" in captured.err
    assert '"accepted"' not in captured.err
    assert json.loads(receipt_path.read_text(encoding="utf-8"))["status"] == "blocked"


def test_store_root_inside_git_worktree_is_rejected() -> None:
    with pytest.raises(OwnerLocalContractError, match="outside Git"):
        _store_path(Path.cwd())
