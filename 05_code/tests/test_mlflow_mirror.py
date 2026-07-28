import json
import tempfile
import unittest
from pathlib import Path

from myis_research.mlflow_mirror import (
    EXPERIMENTS,
    MLflowMirror,
    MirrorArtifact,
    MirrorKind,
    MirrorSpec,
    MirrorStage,
    MirrorValidationError,
    rebuild_plan,
    _assert_store_outside_git,
)


SHA = "a" * 64


class FakeBackend:
    def __init__(self, *, fail: bool = False):
        self.fail = fail
        self.experiments = []
        self.logged = []
        self.runs = {}
        self.closed = 0

    def ensure_experiments(self, names, artifact_root):
        if self.fail:
            raise RuntimeError("fixture backend failure with sensitive details")
        self.experiments = list(names)

    def find_run(self, experiment_name, mirror_key):
        return self.runs.get((experiment_name, mirror_key))

    def log_run(self, **values):
        self.logged.append(values)
        run_id = f"run-{len(self.logged)}"
        key = (values["experiment_name"], values["tags"]["mirror_key"])
        self.runs[key] = run_id
        return run_id

    def close(self):
        self.closed += 1


def make_file(root: Path, name: str, value: object) -> Path:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(value, str):
        path.write_text(value, encoding="utf-8")
    else:
        path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")
    return path


class MLflowMirrorTests(unittest.TestCase):
    def test_store_guard_distinguishes_placeholder_from_git_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            placeholder = root / ".git"
            placeholder.mkdir()
            store = root / "store"
            self.assertEqual(_assert_store_outside_git(store), store)
            (placeholder / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
            with self.assertRaises(MirrorValidationError):
                _assert_store_outside_git(store)

    def test_catalog_sync_is_file_scoped_and_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            canonical = root / "repo"
            store = root / "store"
            doc = make_file(canonical, "README.md", "Canonical overview\n")
            skill = make_file(canonical, "skills/review/SKILL.md", "Review rules\n")
            artifacts = (
                MirrorArtifact.from_path(doc, kind=MirrorKind.DOC, canonical_root=canonical),
                MirrorArtifact.from_path(skill, kind=MirrorKind.SKILL, canonical_root=canonical),
            )
            backend = FakeBackend()
            mirror = MLflowMirror(store, backend=backend)
            spec = MirrorSpec(
                stage=MirrorStage.CATALOG,
                run_name="catalog-fixture",
                git_commit="f85404a",
                canonical_source_sha256=SHA,
            )

            first = mirror.sync(spec, artifacts)
            second = mirror.sync(spec, artifacts)

            self.assertEqual(first.status, "synced")
            self.assertEqual(first.as_dict(), second.as_dict())
            self.assertEqual(backend.experiments, list(EXPERIMENTS))
            self.assertEqual(len(backend.logged), 1)
            self.assertEqual([item.path for item in backend.logged[0]["artifacts"]], [doc.resolve(), skill.resolve()])
            self.assertEqual(backend.logged[0]["tags"]["canonical_authority"], "git-and-validated-artifacts")

    def test_scientific_projection_rejects_protected_data_and_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            protected_path = make_file(root, "confirmation-outcomes.json", {"score": 1})
            per_query = make_file(root, "metrics.json", {"per_query": [{"query_id": "q1"}]})
            pdf = root / "paper.pdf"
            pdf.write_bytes(b"%PDF-fixture")

            for artifact in (
                MirrorArtifact.from_path(protected_path, kind=MirrorKind.RESULT, canonical_root=root),
                MirrorArtifact.from_path(per_query, kind=MirrorKind.METRIC, canonical_root=root),
                MirrorArtifact.from_path(pdf, kind=MirrorKind.DOC, canonical_root=root),
            ):
                with self.subTest(path=artifact.path.name), self.assertRaises(MirrorValidationError):
                    artifact.validate()

    def test_scientific_projection_accepts_commitment_hashes_not_membership(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = make_file(
                root,
                "manifest.json",
                {"split_query_ids_hash": SHA, "metrics": {"out_recall_at_100": 0.2}},
            )
            artifact = MirrorArtifact.from_path(manifest, kind=MirrorKind.RESULT, canonical_root=root)
            artifact.validate()

    def test_bootstrap_has_zero_artifacts_and_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            backend = FakeBackend()
            mirror = MLflowMirror(root / "store", backend=backend)
            valid = MirrorSpec(
                stage=MirrorStage.BOOTSTRAP,
                run_name="bootstrap",
                git_commit="f85404a",
                canonical_source_sha256=SHA,
                parameters={"artifact_count": 0, "scientific_metric_count": 0},
            )
            receipt = mirror.sync(valid)
            self.assertEqual(receipt.status, "synced")
            self.assertEqual(backend.logged[0]["artifacts"], ())
            self.assertEqual(backend.logged[0]["metrics"], {})

            invalid = MirrorSpec(
                stage=MirrorStage.BOOTSTRAP,
                run_name="bad-bootstrap",
                git_commit="f85404a",
                canonical_source_sha256=SHA,
                metrics={"score": 1.0},
            )
            with self.assertRaises(MirrorValidationError):
                mirror.sync(invalid)

    def test_reserved_lineage_tags_and_secret_metadata_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            mirror = MLflowMirror(Path(temp) / "store", backend=FakeBackend())
            for tags in (
                {"mirror_key": "caller-controlled"},
                {"note": "api_key=not-a-real-but-forbidden-secret"},
            ):
                spec = MirrorSpec(
                    stage=MirrorStage.CATALOG,
                    run_name="bad-metadata",
                    git_commit="f85404a",
                    canonical_source_sha256=SHA,
                    tags=tags,
                )
                with self.subTest(tags=tags), self.assertRaises(MirrorValidationError):
                    mirror.sync(spec)

    def test_failure_writes_one_deferred_receipt_without_error_text(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            backend = FakeBackend(fail=True)
            mirror = MLflowMirror(root / "store", backend=backend)
            spec = MirrorSpec(
                stage=MirrorStage.CATALOG,
                run_name="catalog-failure",
                git_commit="f85404a",
                canonical_source_sha256=SHA,
            )
            first = mirror.sync(spec)
            second = mirror.sync(spec)
            receipts = list((root / "store" / "receipts" / "mlflow").glob("*.json"))
            self.assertEqual(first.status, "sync_deferred")
            self.assertEqual(first.as_dict(), second.as_dict())
            self.assertEqual(len(receipts), 1)
            body = receipts[0].read_text(encoding="utf-8")
            self.assertNotIn("sensitive details", body)
            self.assertIsNotNone(first.error_hash)

    def test_rebuild_plan_uses_canonical_hashes_and_never_auto_repairs(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            doc = make_file(root, "rules.md", "Canonical rules\n")
            artifact = MirrorArtifact.from_path(doc, kind=MirrorKind.RULE, canonical_root=root)
            plan = rebuild_plan((artifact,), store_root=root / "corrupt-store")
            self.assertEqual(plan["authority"], "git-and-validated-artifacts")
            self.assertFalse(plan["automatic_repair"])
            self.assertEqual(plan["artifact_hashes"]["rules/rules.md"], artifact.sha256)


if __name__ == "__main__":
    unittest.main()
