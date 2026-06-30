from __future__ import annotations

import json
from io import StringIO
from types import SimpleNamespace

from inference.e5_rebuild_cli import build_rebuild_parser, run_rebuild


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


def test_rebuild_parser_accepts_report_file() -> None:
    args = build_rebuild_parser().parse_args(
        [
            "--index",
            "/tmp/corpus.json",
            "--passage",
            "alpha",
            "--report-file",
            "/tmp/report.json",
        ]
    )

    assert args.report_file == "/tmp/report.json"


def test_rebuild_writes_report_file_matching_json_output(tmp_path) -> None:
    corpus = tmp_path / "corpus.json"
    report = tmp_path / "report.json"
    stdout = StringIO()

    code = run_rebuild(
        [
            "--index",
            str(corpus),
            "--format",
            "json",
            "--passage",
            "alpha document",
            "--validation-query",
            "alpha",
            "--validation-min-score",
            "0.5",
            "--report-file",
            str(report),
        ],
        stdout=stdout,
        stderr=StringIO(),
        builder=fake_builder,
    )

    assert code == 0
    assert corpus.exists()
    assert report.exists()
    stdout_payload = json.loads(stdout.getvalue())
    report_payload = json.loads(report.read_text(encoding="utf-8"))
    assert report_payload == stdout_payload
    assert report_payload["promoted"] is True
    assert report_payload["validation"]["query_count"] == 1


def test_rebuild_report_file_is_written_for_dry_run(tmp_path) -> None:
    corpus = tmp_path / "corpus.json"
    report = tmp_path / "report.json"

    code = run_rebuild(
        [
            "--index",
            str(corpus),
            "--passage",
            "alpha document",
            "--dry-run",
            "--report-file",
            str(report),
        ],
        stdout=StringIO(),
        stderr=StringIO(),
        builder=fake_builder,
    )

    assert code == 0
    assert not corpus.exists()
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["promoted"] is False


def test_rebuild_report_file_failure_returns_error(tmp_path) -> None:
    corpus = tmp_path / "corpus.json"
    stderr = StringIO()

    code = run_rebuild(
        [
            "--index",
            str(corpus),
            "--passage",
            "alpha document",
            "--report-file",
            str(tmp_path / "missing" / "report.json"),
        ],
        stdout=StringIO(),
        stderr=stderr,
        builder=fake_builder,
    )

    assert code == 1
    assert "failed to write report" in stderr.getvalue()
