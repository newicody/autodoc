from __future__ import annotations

import json
from io import StringIO
from types import SimpleNamespace

from inference.e5_rebuild_cli import build_rebuild_parser, rebuild_staging_path, run_rebuild


class FakePipeline:
    async def embed_text(self, text: str) -> object:
        values = (1.0, 0.0) if "alpha" in text else (0.0, 1.0)
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


def test_rebuild_parser_accepts_validation_set_options(tmp_path) -> None:
    queries = tmp_path / "queries.txt"
    args = build_rebuild_parser().parse_args(
        [
            "--index",
            "/tmp/corpus.json",
            "--validation-query",
            "alpha",
            "--validation-query",
            "beta",
            "--validation-queries-file",
            str(queries),
            "--validation-min-score",
            "0.8",
            "--passage",
            "alpha",
        ]
    )

    assert args.validation_query == ["alpha", "beta"]
    assert args.validation_queries_file == [str(queries)]
    assert args.validation_min_score == 0.8


def test_rebuild_validation_set_promotes_when_all_queries_pass(tmp_path) -> None:
    corpus = tmp_path / "corpus.json"
    stdout = StringIO()

    code = run_rebuild(
        [
            "--index",
            str(corpus),
            "--format",
            "json",
            "--passage",
            "alpha document",
            "--passage",
            "beta document",
            "--validation-query",
            "alpha",
            "--validation-query",
            "beta",
            "--validation-min-score",
            "0.5",
        ],
        stdout=stdout,
        stderr=StringIO(),
        builder=fake_builder,
    )

    assert code == 0
    assert corpus.exists()
    payload = json.loads(stdout.getvalue())
    assert payload["validation"]["search_enabled"] is True
    assert payload["validation"]["query_count"] == 2
    assert payload["validation"]["hit_count"] == 2
    assert payload["validation"]["passed"] is True
    assert [item["query"] for item in payload["validation"]["queries"]] == ["alpha", "beta"]


def test_rebuild_validation_queries_file_is_used(tmp_path) -> None:
    corpus = tmp_path / "corpus.json"
    queries = tmp_path / "queries.txt"
    queries.write_text("alpha\nbeta\n", encoding="utf-8")
    stdout = StringIO()

    code = run_rebuild(
        [
            "--index",
            str(corpus),
            "--format",
            "json",
            "--passage",
            "alpha document",
            "--passage",
            "beta document",
            "--validation-queries-file",
            str(queries),
            "--validation-min-score",
            "0.5",
        ],
        stdout=stdout,
        stderr=StringIO(),
        builder=fake_builder,
    )

    assert code == 0
    payload = json.loads(stdout.getvalue())
    assert payload["validation"]["query_count"] == 2


def test_rebuild_validation_set_blocks_promotion_when_query_fails(tmp_path) -> None:
    corpus = tmp_path / "corpus.json"
    staging = rebuild_staging_path(corpus)
    stderr = StringIO()

    code = run_rebuild(
        [
            "--index",
            str(corpus),
            "--passage",
            "alpha document",
            "--validation-query",
            "beta",
            "--validation-min-score",
            "0.5",
        ],
        stdout=StringIO(),
        stderr=stderr,
        builder=fake_builder,
    )

    assert code == 2
    assert "candidate search validation failed" in stderr.getvalue()
    assert "queries returned no hits: beta" in stderr.getvalue()
    assert not corpus.exists()
    assert not staging.exists()


def test_rebuild_validation_set_can_keep_failed_staging(tmp_path) -> None:
    corpus = tmp_path / "corpus.json"
    staging = rebuild_staging_path(corpus)

    code = run_rebuild(
        [
            "--index",
            str(corpus),
            "--passage",
            "alpha document",
            "--validation-query",
            "beta",
            "--validation-min-score",
            "0.5",
            "--keep-staging",
        ],
        stdout=StringIO(),
        stderr=StringIO(),
        builder=fake_builder,
    )

    assert code == 2
    assert not corpus.exists()
    assert staging.exists()


def test_rebuild_validation_set_rejects_invalid_min_score(tmp_path) -> None:
    stderr = StringIO()

    code = run_rebuild(
        [
            "--index",
            str(tmp_path / "corpus.json"),
            "--passage",
            "alpha",
            "--validation-min-score",
            "1.1",
            "--validation-query",
            "alpha",
        ],
        stdout=StringIO(),
        stderr=stderr,
        builder=fake_builder,
    )

    assert code == 2
    assert "--validation-min-score must be between -1.0 and 1.0" in stderr.getvalue()
