from __future__ import annotations

import json
from pathlib import Path

import pytest

from myis_research.armindex import a1_2_owner_local_cli_v16 as cli


def test_input_manifest_cli_passes_only_owner_relative_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    owner = tmp_path / "owner"
    owner.mkdir()
    (owner / "gates.json").write_text(json.dumps({"gate": "PASS"}), encoding="ascii")
    (owner / "cells.json").write_text("[]", encoding="ascii")
    (owner / "work.jsonl").write_text("{}\n", encoding="ascii")
    observed: dict[str, object] = {}
    monkeypatch.setattr(cli, "build_input_manifest", lambda **kwargs: observed.update(kwargs) or {"status": "PASS"})
    assert cli.input_manifest_main(["--owner-root", str(owner), "--attempt-id", "a12-cli-test", "--gates-json-relative", "gates.json", "--cells-json-relative", "cells.json", "--work-token-relative", "work.jsonl", "--output-relative", "manifests/input.json"]) == 0
    assert observed["root"] == owner.resolve()
    assert observed["output"] == (owner / "manifests" / "input.json").resolve()


def test_input_manifest_cli_rejects_path_escape(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    owner = tmp_path / "owner"
    owner.mkdir()
    monkeypatch.setattr(cli, "build_input_manifest", lambda **kwargs: {"status": "PASS"})
    with pytest.raises(SystemExit, match="2"):
        cli.input_manifest_main(["--owner-root", str(owner), "--attempt-id", "a12-cli-test", "--gates-json-relative", "../gates.json", "--cells-json-relative", "cells.json", "--work-token-relative", "work.jsonl", "--output-relative", "../input.json"])


def test_evaluator_cli_separates_owner_inputs_and_aggregate_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    owner = tmp_path / "owner"
    owner.mkdir()
    repository = tmp_path / "repository"
    repository.mkdir()
    manifest = owner / "evaluation.json"
    manifest.write_text("{}", encoding="ascii")
    archive = tmp_path / "return.tar.gz"
    archive.write_bytes(b"archive")
    observed: dict[str, object] = {}
    monkeypatch.setattr(cli, "evaluate_safe_return", lambda *args, **kwargs: observed.update({"args": args, **kwargs}) or {"status": "PASS"})
    output = tmp_path / "aggregate"
    assert cli.evaluator_main(["--owner-root", str(owner), "--evaluation-manifest", str(manifest), "--safe-return-archive", str(archive), "--output-root", str(output), "--repository-root", str(repository)]) == 0
    assert observed["args"] == (archive.resolve(), manifest.resolve())
    assert observed["output_root"] == output.resolve()


def test_evaluator_cli_rejects_protected_output_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    owner = tmp_path / "owner"
    owner.mkdir()
    repository = tmp_path / "repository"
    repository.mkdir()
    manifest = owner / "evaluation.json"
    manifest.write_text("{}", encoding="ascii")
    archive = tmp_path / "return.tar.gz"
    archive.write_bytes(b"archive")
    monkeypatch.setattr(cli, "evaluate_safe_return", lambda *args, **kwargs: {"status": "PASS"})
    with pytest.raises(SystemExit, match="2"):
        cli.evaluator_main(["--owner-root", str(owner), "--evaluation-manifest", str(manifest), "--safe-return-archive", str(archive), "--output-root", str(owner / "aggregate"), "--repository-root", str(repository)])
