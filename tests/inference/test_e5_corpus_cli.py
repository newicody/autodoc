from __future__ import annotations

from io import StringIO
from types import SimpleNamespace

from inference.e5_corpus_cli import run_build, run_search


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


def test_build_e5_corpus_cli_writes_index(tmp_path) -> None:
    out = StringIO()
    err = StringIO()
    path = tmp_path / "corpus.json"

    code = run_build(
        ["--output", str(path), "--passage", "arnaque vendeur", "--passage", "moteur diesel"],
        stdout=out,
        stderr=err,
        builder=fake_builder,
    )

    assert code == 0
    assert err.getvalue() == ""
    assert path.exists()
    assert "size: 2" in out.getvalue()


def test_build_e5_corpus_cli_requires_passages(tmp_path) -> None:
    err = StringIO()

    code = run_build(["--output", str(tmp_path / "corpus.json")], stdout=StringIO(), stderr=err, builder=fake_builder)

    assert code == 2
    assert "at least one" in err.getvalue()


def test_search_e5_corpus_cli_reads_index_and_ranks(tmp_path) -> None:
    corpus = tmp_path / "corpus.json"
    assert run_build(
        ["--output", str(corpus), "--passage", "moteur diesel", "--passage", "arnaque vendeur"],
        stdout=StringIO(),
        stderr=StringIO(),
        builder=fake_builder,
    ) == 0
    out = StringIO()
    err = StringIO()

    code = run_search(
        ["--index", str(corpus), "je me suis fait baiser"],
        stdout=out,
        stderr=err,
        builder=fake_builder,
    )

    assert code == 0
    assert err.getvalue() == ""
    assert "#1 score=1.00000000" in out.getvalue()
    assert "excerpt: arnaque vendeur" in out.getvalue()


def test_search_e5_corpus_cli_json_and_limit(tmp_path) -> None:
    corpus = tmp_path / "corpus.json"
    assert run_build(
        ["--output", str(corpus), "--passage", "moteur diesel", "--passage", "arnaque vendeur"],
        stdout=StringIO(),
        stderr=StringIO(),
        builder=fake_builder,
    ) == 0
    out = StringIO()

    code = run_search(
        ["--index", str(corpus), "--limit", "1", "--format", "json", "je me suis fait baiser"],
        stdout=out,
        stderr=StringIO(),
        builder=fake_builder,
    )

    assert code == 0
    assert '"hits":' in out.getvalue()
    assert '"rank": 1' in out.getvalue()
    assert '"source":' in out.getvalue()


def test_build_e5_corpus_cli_accepts_source_file(tmp_path) -> None:
    source = tmp_path / "notes.md"
    source.write_text("arnaque vendeur\n\nMoteur diesel", encoding="utf-8")
    corpus = tmp_path / "corpus.json"
    out = StringIO()
    err = StringIO()

    code = run_build(
        ["--output", str(corpus), "--source-file", str(source), "--chunk-chars", "20"],
        stdout=out,
        stderr=err,
        builder=fake_builder,
    )

    assert code == 0
    assert err.getvalue() == ""
    assert "size: 2" in out.getvalue()
    data = corpus.read_text(encoding="utf-8")
    assert "source_path" in data
    assert "notes.md" in data


def test_build_e5_corpus_cli_rejects_invalid_chunk_options(tmp_path) -> None:
    err = StringIO()

    code = run_build(
        ["--output", str(tmp_path / "corpus.json"), "--source-dir", str(tmp_path), "--chunk-chars", "0"],
        stdout=StringIO(),
        stderr=err,
        builder=fake_builder,
    )

    assert code == 2
    assert "--chunk-chars" in err.getvalue()


def test_search_e5_corpus_cli_reports_source_context(tmp_path) -> None:
    source = tmp_path / "notes.md"
    source.write_text("arnaque vendeur\n\nMoteur diesel", encoding="utf-8")
    corpus = tmp_path / "corpus.json"
    assert run_build(
        ["--output", str(corpus), "--source-file", str(source), "--chunk-chars", "20"],
        stdout=StringIO(),
        stderr=StringIO(),
        builder=fake_builder,
    ) == 0
    out = StringIO()

    code = run_search(
        ["--index", str(corpus), "--excerpt-chars", "12", "je me suis fait baiser"],
        stdout=out,
        stderr=StringIO(),
        builder=fake_builder,
    )

    assert code == 0
    text = out.getvalue()
    assert "source: " in text
    assert "notes.md" in text
    assert "lines: " in text
    assert "chunk: " in text
    assert "excerpt: arnaque ven…" in text


def test_search_e5_corpus_cli_rejects_invalid_excerpt_chars(tmp_path) -> None:
    corpus = tmp_path / "corpus.json"
    assert run_build(
        ["--output", str(corpus), "--passage", "arnaque vendeur"],
        stdout=StringIO(),
        stderr=StringIO(),
        builder=fake_builder,
    ) == 0
    err = StringIO()

    code = run_search(
        ["--index", str(corpus), "--excerpt-chars", "0", "je me suis fait baiser"],
        stdout=StringIO(),
        stderr=err,
        builder=fake_builder,
    )

    assert code == 2
    assert "--excerpt-chars" in err.getvalue()


def test_build_e5_corpus_cli_reuses_previous_index(tmp_path) -> None:
    corpus = tmp_path / "corpus.json"
    rebuilt = tmp_path / "rebuilt.json"
    assert run_build(
        ["--output", str(corpus), "--passage", "arnaque vendeur", "--passage", "moteur diesel"],
        stdout=StringIO(),
        stderr=StringIO(),
        builder=fake_builder,
    ) == 0
    out = StringIO()
    err = StringIO()

    code = run_build(
        [
            "--output",
            str(rebuilt),
            "--reuse-index",
            str(corpus),
            "--passage",
            "arnaque vendeur",
            "--passage",
            "moteur diesel",
        ],
        stdout=out,
        stderr=err,
        builder=fake_builder,
    )

    assert code == 0
    assert err.getvalue() == ""
    text = out.getvalue()
    assert "reused_count: 2" in text
    assert "embedded_count: 0" in text
    assert "removed_count: 0" in text
    assert "embedding_reused" in rebuilt.read_text(encoding="utf-8")
