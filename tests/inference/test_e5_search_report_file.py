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


def test_search_parser_accepts_report_file() -> None:
    args = build_search_parser().parse_args(
        [
            "--index",
            "/tmp/corpus.json",
            "--report-file",
            "/tmp/search-report.json",
            "query",
        ]
    )

    assert args.report_file == "/tmp/search-report.json"


def test_search_writes_report_file_matching_json_output(tmp_path) -> None:
    corpus = tmp_path / "corpus.json"
    report = tmp_path / "search-report.json"
    _build_index(corpus)

    stdout = StringIO()
    stderr = StringIO()
    code = run_search(
        [
            "--index",
            str(corpus),
            "--limit",
            "1",
            "--format",
            "json",
            "--report-file",
            str(report),
            "je me suis fait baiser",
        ],
        stdout=stdout,
        stderr=stderr,
        builder=fake_builder,
    )

    assert code == 0
    assert stderr.getvalue() == ""
    assert report.exists()
    assert json.loads(report.read_text(encoding="utf-8")) == json.loads(stdout.getvalue())
    assert json.loads(report.read_text(encoding="utf-8"))["hit_count"] == 1


def test_search_writes_report_file_for_text_output(tmp_path) -> None:
    corpus = tmp_path / "corpus.json"
    report = tmp_path / "search-report.json"
    _build_index(corpus)

    stdout = StringIO()
    stderr = StringIO()
    code = run_search(
        [
            "--index",
            str(corpus),
            "--min-score",
            "0.5",
            "--report-file",
            str(report),
            "je me suis fait baiser",
        ],
        stdout=stdout,
        stderr=stderr,
        builder=fake_builder,
    )

    assert code == 0
    assert stderr.getvalue() == ""
    assert "hit_count: 1" in stdout.getvalue()
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["hit_count"] == 1
    assert payload["hits"][0]["excerpt"] == "arnaque vendeur"


def test_search_rejects_report_file_without_filename() -> None:
    stderr = StringIO()
    code = run_search(
        ["--index", "/tmp/corpus.json", "--report-file", "/", "query"],
        stdout=StringIO(),
        stderr=stderr,
        builder=fake_builder,
    )

    assert code == 2
    assert "--report-file must target a filename" in stderr.getvalue()


def test_search_report_file_failure_returns_error(tmp_path) -> None:
    corpus = tmp_path / "corpus.json"
    target_directory = tmp_path / "report.json"
    target_directory.mkdir()
    _build_index(corpus)

    stderr = StringIO()
    code = run_search(
        ["--index", str(corpus), "--report-file", str(target_directory), "je me suis fait baiser"],
        stdout=StringIO(),
        stderr=stderr,
        builder=fake_builder,
    )

    assert code == 1
    assert "failed to write report" in stderr.getvalue()
