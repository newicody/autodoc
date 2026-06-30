from __future__ import annotations

import json
from io import StringIO
from types import SimpleNamespace

from inference.e5_corpus_cli import build_search_parser, run_build, run_search


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


def _build_index(path) -> None:
    assert run_build(
        ["--output", str(path), "--passage", "moteur diesel", "--passage", "arnaque vendeur"],
        stdout=StringIO(),
        stderr=StringIO(),
        builder=fake_builder,
    ) == 0


def test_search_parser_accepts_context_file() -> None:
    args = build_search_parser().parse_args(
        [
            "--index",
            "/tmp/corpus.json",
            "--context-file",
            "/tmp/context.json",
            "query",
        ]
    )

    assert args.context_file == "/tmp/context.json"


def test_search_writes_context_file_from_hits(tmp_path) -> None:
    corpus = tmp_path / "corpus.json"
    context = tmp_path / "context.json"
    _build_index(corpus)

    stdout = StringIO()
    stderr = StringIO()
    code = run_search(
        [
            "--index",
            str(corpus),
            "--limit",
            "1",
            "--context-file",
            str(context),
            "je me suis fait baiser",
        ],
        stdout=stdout,
        stderr=stderr,
        builder=fake_builder,
    )

    assert code == 0
    assert stderr.getvalue() == ""
    assert "hit_count: 1" in stdout.getvalue()
    payload = json.loads(context.read_text(encoding="utf-8"))
    assert payload["item_count"] == 1
    assert payload["items"][0]["excerpt"] == "arnaque vendeur"
    assert payload["items"][0]["rank"] == 1


def test_search_rejects_context_file_without_filename() -> None:
    stderr = StringIO()
    code = run_search(
        ["--index", "/tmp/corpus.json", "--context-file", "/", "query"],
        stdout=StringIO(),
        stderr=stderr,
        builder=fake_builder,
    )

    assert code == 2
    assert "--context-file must target a filename" in stderr.getvalue()
