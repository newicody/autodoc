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


def test_rebuild_parser_accepts_diagnostic_gate_options() -> None:
    args = build_rebuild_parser().parse_args(
        [
            "--index",
            "/tmp/corpus.json",
            "--min-chunks",
            "2",
            "--max-missing-source-metadata",
            "0",
            "--max-empty-texts",
            "0",
            "--max-dimension-mismatches",
            "0",
            "--fail-on-warning",
            "--passage",
            "alpha",
        ]
    )

    assert args.min_chunks == 2
    assert args.max_missing_source_metadata == 0
    assert args.max_empty_texts == 0
    assert args.max_dimension_mismatches == 0
    assert args.fail_on_warning is True


def test_rebuild_diagnostic_gate_blocks_promotion_when_min_chunks_fails(tmp_path) -> None:
    corpus = tmp_path / "corpus.json"
    staging = rebuild_staging_path(corpus)
    stderr = StringIO()

    code = run_rebuild(
        [
            "--index",
            str(corpus),
            "--min-chunks",
            "2",
            "--passage",
            "alpha",
        ],
        stdout=StringIO(),
        stderr=stderr,
        builder=fake_builder,
    )

    assert code == 2
    assert "candidate diagnostic gate failed" in stderr.getvalue()
    assert "chunk_count 1 < min_chunks 2" in stderr.getvalue()
    assert not corpus.exists()
    assert not staging.exists()


def test_rebuild_diagnostic_gate_can_keep_failed_staging(tmp_path) -> None:
    corpus = tmp_path / "corpus.json"
    staging = rebuild_staging_path(corpus)

    code = run_rebuild(
        [
            "--index",
            str(corpus),
            "--min-chunks",
            "2",
            "--keep-staging",
            "--passage",
            "alpha",
        ],
        stdout=StringIO(),
        stderr=StringIO(),
        builder=fake_builder,
    )

    assert code == 2
    assert not corpus.exists()
    assert staging.exists()
    assert "alpha" in staging.read_text(encoding="utf-8")


def test_rebuild_diagnostic_gate_reports_passing_gate_in_json(tmp_path) -> None:
    corpus = tmp_path / "corpus.json"
    stdout = StringIO()

    code = run_rebuild(
        [
            "--index",
            str(corpus),
            "--format",
            "json",
            "--min-chunks",
            "1",
            "--passage",
            "alpha",
        ],
        stdout=stdout,
        stderr=StringIO(),
        builder=fake_builder,
    )

    assert code == 0
    payload = json.loads(stdout.getvalue())
    assert payload["promoted"] is True
    assert payload["diagnostic_gate"]["enabled"] is True
    assert payload["diagnostic_gate"]["passed"] is True
    assert payload["diagnostic_gate"]["violations"] == []


def test_rebuild_diagnostic_gate_fail_on_warning_blocks_plain_passages(tmp_path) -> None:
    corpus = tmp_path / "corpus.json"
    stderr = StringIO()

    code = run_rebuild(
        [
            "--index",
            str(corpus),
            "--fail-on-warning",
            "--passage",
            "alpha",
        ],
        stdout=StringIO(),
        stderr=stderr,
        builder=fake_builder,
    )

    assert code == 2
    assert "diagnostics has warnings" in stderr.getvalue()
    assert not corpus.exists()


def test_rebuild_diagnostic_gate_rejects_negative_threshold(tmp_path) -> None:
    stderr = StringIO()

    code = run_rebuild(
        [
            "--index",
            str(tmp_path / "corpus.json"),
            "--min-chunks",
            "-1",
            "--passage",
            "alpha",
        ],
        stdout=StringIO(),
        stderr=stderr,
        builder=fake_builder,
    )

    assert code == 2
    assert "--min-chunks must not be negative" in stderr.getvalue()
