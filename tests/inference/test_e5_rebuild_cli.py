from __future__ import annotations

import json
from io import StringIO
from types import SimpleNamespace

from inference.e5_rebuild_cli import rebuild_staging_path, run_rebuild


class FakePipeline:
    async def embed_text(self, text: str) -> object:
        if "arnaque" in text or "baiser" in text:
            values = (1.0, 0.0)
        else:
            values = (0.0, 1.0)
        return SimpleNamespace(
            model="fake-e5",
            backend="fake-backend",
            tokenizer_name="fake-tokenizer",
            vector=SimpleNamespace(values=values, dimension=2, normalized=True, l2_norm=1.0),
        )


class FakeBundle:
    def __init__(self) -> None:
        self.pipeline = FakePipeline()


def fake_builder(_config) -> FakeBundle:
    return FakeBundle()


def test_rebuild_staging_path_is_hidden_neighbor(tmp_path) -> None:
    assert rebuild_staging_path(tmp_path / "corpus.json") == tmp_path / ".corpus.json.rebuild.json"


def test_rebuild_cli_builds_validates_and_promotes(tmp_path) -> None:
    corpus = tmp_path / "corpus.json"
    out = StringIO()
    err = StringIO()

    code = run_rebuild(
        [
            "--index",
            str(corpus),
            "--passage",
            "arnaque vendeur",
            "--passage",
            "moteur diesel",
            "--validation-query",
            "je me suis fait baiser",
        ],
        stdout=out,
        stderr=err,
        builder=fake_builder,
    )

    assert code == 0
    assert err.getvalue() == ""
    assert corpus.exists()
    assert not rebuild_staging_path(corpus).exists()
    text = out.getvalue()
    assert "promoted: True" in text
    assert "size: 2" in text
    assert "validation_search: True" in text
    assert "validation_hit_count: 1" in text
    assert "validation_best_score: 1.00000000" in text
    assert "lock_path: " in text


def test_rebuild_cli_reuses_existing_index(tmp_path) -> None:
    corpus = tmp_path / "corpus.json"
    assert run_rebuild(
        ["--index", str(corpus), "--passage", "arnaque vendeur", "--passage", "moteur diesel"],
        stdout=StringIO(),
        stderr=StringIO(),
        builder=fake_builder,
    ) == 0
    out = StringIO()

    code = run_rebuild(
        ["--index", str(corpus), "--passage", "arnaque vendeur", "--passage", "moteur diesel"],
        stdout=out,
        stderr=StringIO(),
        builder=fake_builder,
    )

    assert code == 0
    text = out.getvalue()
    assert "reused_count: 2" in text
    assert "embedded_count: 0" in text
    assert "removed_count: 0" in text
    assert "embedding_reused" in corpus.read_text(encoding="utf-8")


def test_rebuild_cli_dry_run_can_keep_staging_without_promoting(tmp_path) -> None:
    corpus = tmp_path / "corpus.json"
    staging = tmp_path / "candidate.json"
    corpus.write_text("old\n", encoding="utf-8")
    out = StringIO()

    code = run_rebuild(
        [
            "--index",
            str(corpus),
            "--staging",
            str(staging),
            "--dry-run",
            "--keep-staging",
            "--passage",
            "arnaque vendeur",
        ],
        stdout=out,
        stderr=StringIO(),
        builder=fake_builder,
    )

    assert code == 1
    # L'ancien index est volontairement invalide, donc le rebuild échoue avant promotion.
    assert corpus.read_text(encoding="utf-8") == "old\n"
    assert not staging.exists()


def test_rebuild_cli_dry_run_with_valid_previous_keeps_candidate(tmp_path) -> None:
    corpus = tmp_path / "corpus.json"
    staging = tmp_path / "candidate.json"
    assert run_rebuild(
        ["--index", str(corpus), "--passage", "arnaque vendeur"],
        stdout=StringIO(),
        stderr=StringIO(),
        builder=fake_builder,
    ) == 0
    before = corpus.read_text(encoding="utf-8")

    code = run_rebuild(
        [
            "--index",
            str(corpus),
            "--staging",
            str(staging),
            "--dry-run",
            "--keep-staging",
            "--passage",
            "arnaque vendeur",
            "--passage",
            "moteur diesel",
        ],
        stdout=StringIO(),
        stderr=StringIO(),
        builder=fake_builder,
    )

    assert code == 0
    assert corpus.read_text(encoding="utf-8") == before
    assert staging.exists()
    assert "moteur diesel" in staging.read_text(encoding="utf-8")


def test_rebuild_cli_json_output(tmp_path) -> None:
    corpus = tmp_path / "corpus.json"
    out = StringIO()

    code = run_rebuild(
        [
            "--index",
            str(corpus),
            "--format",
            "json",
            "--validation-query",
            "je me suis fait baiser",
            "--passage",
            "arnaque vendeur",
        ],
        stdout=out,
        stderr=StringIO(),
        builder=fake_builder,
    )

    assert code == 0
    payload = json.loads(out.getvalue())
    assert payload["promoted"] is True
    assert payload["validation"]["search_enabled"] is True
    assert payload["validation"]["hit_count"] == 1


def test_rebuild_cli_rejects_same_staging_and_index(tmp_path) -> None:
    corpus = tmp_path / "corpus.json"
    err = StringIO()

    code = run_rebuild(
        ["--index", str(corpus), "--staging", str(corpus), "--passage", "arnaque vendeur"],
        stdout=StringIO(),
        stderr=err,
        builder=fake_builder,
    )

    assert code == 2
    assert "--staging" in err.getvalue()


def test_rebuild_cli_rejects_existing_lock(tmp_path) -> None:
    corpus = tmp_path / "corpus.json"
    lock = tmp_path / ".corpus.json.lock"
    lock.write_text("busy\n", encoding="utf-8")
    err = StringIO()

    code = run_rebuild(
        ["--index", str(corpus), "--passage", "arnaque vendeur"],
        stdout=StringIO(),
        stderr=err,
        builder=fake_builder,
    )

    assert code == 1
    assert "already locked" in err.getvalue()
    assert not corpus.exists()
    assert lock.exists()


def test_rebuild_cli_rejects_invalid_validation_limit(tmp_path) -> None:
    err = StringIO()

    code = run_rebuild(
        ["--index", str(tmp_path / "corpus.json"), "--validation-limit", "0", "--passage", "arnaque vendeur"],
        stdout=StringIO(),
        stderr=err,
        builder=fake_builder,
    )

    assert code == 2
    assert "--validation-limit" in err.getvalue()
