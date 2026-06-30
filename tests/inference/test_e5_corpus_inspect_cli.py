from __future__ import annotations

import io
import json

from inference.e5_corpus import E5CorpusEmbedding, E5CorpusIndex, E5CorpusJsonStore
from inference.e5_corpus_inspect_cli import build_inspect_parser, run_inspect


def _index() -> E5CorpusIndex:
    return E5CorpusIndex(
        model="model",
        backend="backend",
        tokenizer="tokenizer",
        dimension=2,
        embeddings=(
            E5CorpusEmbedding(
                id="one",
                text="One",
                prefixed_text="passage: One",
                vector=(1.0, 0.0),
                dimension=2,
                normalized=True,
                l2_norm=1.0,
                metadata={"source_path": "README.md", "source_extension": ".md", "embedding_reused": True},
            ),
            E5CorpusEmbedding(
                id="two",
                text="Two",
                prefixed_text="passage: Two",
                vector=(0.0, 1.0),
                dimension=2,
                normalized=True,
                l2_norm=1.0,
                metadata={"source_path": "doc/a.txt", "source_extension": ".txt", "embedding_reused": False},
            ),
        ),
    )



def _warning_index() -> E5CorpusIndex:
    return E5CorpusIndex(
        model="model",
        backend="backend",
        tokenizer="tokenizer",
        dimension=2,
        embeddings=(
            E5CorpusEmbedding(
                id="one",
                text="One",
                prefixed_text="passage: One",
                vector=(1.0, 0.0),
                dimension=2,
                normalized=True,
                l2_norm=1.0,
                metadata={},
            ),
        ),
    )


def test_inspect_parser_accepts_index_format_and_gate_options() -> None:
    args = build_inspect_parser().parse_args(
        [
            "--index",
            "/tmp/corpus.json",
            "--format",
            "json",
            "--min-chunks",
            "10",
            "--max-empty-texts",
            "0",
            "--max-missing-source-metadata",
            "0",
            "--max-dimension-mismatches",
            "0",
            "--fail-on-warning",
        ]
    )

    assert args.index == "/tmp/corpus.json"
    assert args.format == "json"
    assert args.min_chunks == 10
    assert args.max_empty_texts == 0
    assert args.max_missing_source_metadata == 0
    assert args.max_dimension_mismatches == 0
    assert args.fail_on_warning is True


def test_inspect_cli_writes_text_report(tmp_path) -> None:
    index_path = tmp_path / "corpus.json"
    E5CorpusJsonStore().write(_index(), index_path)
    stdout = io.StringIO()
    stderr = io.StringIO()

    code = run_inspect(["--index", str(index_path), "--top-sources-limit", "1"], stdout=stdout, stderr=stderr)

    assert code == 0
    assert stderr.getvalue() == ""
    output = stdout.getvalue()
    assert f"index: {index_path}" in output
    assert "chunk_count: 2" in output
    assert "source_count: 2" in output
    assert "README.md: 1 (.md)" in output


def test_inspect_cli_writes_json_report(tmp_path) -> None:
    index_path = tmp_path / "corpus.json"
    E5CorpusJsonStore().write(_index(), index_path)
    stdout = io.StringIO()

    code = run_inspect(["--index", str(index_path), "--format", "json"], stdout=stdout)

    assert code == 0
    payload = json.loads(stdout.getvalue())
    assert payload["index"] == str(index_path)
    assert payload["diagnostics"]["chunk_count"] == 2
    assert payload["diagnostics"]["extension_counts"] == {".md": 1, ".txt": 1}


def test_inspect_cli_rejects_invalid_top_sources_limit(tmp_path) -> None:
    index_path = tmp_path / "corpus.json"
    E5CorpusJsonStore().write(_index(), index_path)
    stdout = io.StringIO()
    stderr = io.StringIO()

    code = run_inspect(["--index", str(index_path), "--top-sources-limit", "0"], stdout=stdout, stderr=stderr)

    assert code == 2
    assert stdout.getvalue() == ""
    assert "--top-sources-limit must be positive" in stderr.getvalue()


def test_inspect_cli_returns_two_when_min_chunks_gate_fails(tmp_path) -> None:
    index_path = tmp_path / "corpus.json"
    E5CorpusJsonStore().write(_index(), index_path)
    stdout = io.StringIO()
    stderr = io.StringIO()

    code = run_inspect(["--index", str(index_path), "--min-chunks", "3"], stdout=stdout, stderr=stderr)

    assert code == 2
    assert stderr.getvalue() == ""
    assert "gate:" in stdout.getvalue()
    assert "chunk_count 2 < min_chunks 3" in stdout.getvalue()


def test_inspect_cli_returns_two_when_fail_on_warning_fails(tmp_path) -> None:
    index_path = tmp_path / "corpus.json"
    E5CorpusJsonStore().write(_warning_index(), index_path)
    stdout = io.StringIO()
    stderr = io.StringIO()

    code = run_inspect(["--index", str(index_path), "--fail-on-warning"], stdout=stdout, stderr=stderr)

    assert code == 2
    assert stderr.getvalue() == ""
    assert "diagnostics has warnings" in stdout.getvalue()


def test_inspect_cli_json_includes_gate_result(tmp_path) -> None:
    index_path = tmp_path / "corpus.json"
    E5CorpusJsonStore().write(_index(), index_path)
    stdout = io.StringIO()

    code = run_inspect(["--index", str(index_path), "--min-chunks", "1", "--format", "json"], stdout=stdout)

    assert code == 0
    payload = json.loads(stdout.getvalue())
    assert payload["gate"]["enabled"] is True
    assert payload["gate"]["passed"] is True


def test_inspect_cli_rejects_negative_gate_threshold(tmp_path) -> None:
    index_path = tmp_path / "corpus.json"
    E5CorpusJsonStore().write(_index(), index_path)
    stdout = io.StringIO()
    stderr = io.StringIO()

    code = run_inspect(["--index", str(index_path), "--max-empty-texts", "-1"], stdout=stdout, stderr=stderr)

    assert code == 2
    assert stdout.getvalue() == ""
    assert "max_empty_texts must not be negative" in stderr.getvalue()
