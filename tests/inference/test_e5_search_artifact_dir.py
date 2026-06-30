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


def test_search_parser_accepts_artifact_dir() -> None:
    args = build_search_parser().parse_args(
        [
            "--index",
            "/tmp/corpus.json",
            "--artifact-dir",
            "/tmp/e5-dry-run",
            "query",
        ]
    )

    assert args.artifact_dir == "/tmp/e5-dry-run"


def test_search_artifact_dir_writes_complete_dry_run_files(tmp_path) -> None:
    corpus = tmp_path / "corpus.json"
    artifact_dir = tmp_path / "artifacts"
    _build_index(corpus)

    stdout = StringIO()
    stderr = StringIO()
    code = run_search(
        [
            "--index",
            str(corpus),
            "--limit",
            "1",
            "--artifact-dir",
            str(artifact_dir),
            "--context-max-chars",
            "500",
            "--context-include-scores",
            "je me suis fait baiser",
        ],
        stdout=stdout,
        stderr=stderr,
        builder=fake_builder,
    )

    assert code == 0
    assert stderr.getvalue() == ""
    assert "hit_count: 1" in stdout.getvalue()

    report_payload = json.loads((artifact_dir / "report.json").read_text(encoding="utf-8"))
    context_payload = json.loads((artifact_dir / "context.json").read_text(encoding="utf-8"))
    consumed_payload = json.loads((artifact_dir / "consumed_context.json").read_text(encoding="utf-8"))
    prompt_payload = json.loads((artifact_dir / "prompt.json").read_text(encoding="utf-8"))

    assert report_payload["hit_count"] == 1
    assert context_payload["item_count"] == 1
    assert context_payload["items"][0]["excerpt"] == "arnaque vendeur"
    assert consumed_payload["selected_item_count"] == 1
    assert "score: 1.00000000" in consumed_payload["context_text"]
    assert prompt_payload["selected_item_count"] == 1
    assert "[QUESTION]\nje me suis fait baiser" in prompt_payload["prompt_text"]
    assert "arnaque vendeur" in prompt_payload["prompt_text"]


def test_search_artifact_dir_keeps_explicit_report_override(tmp_path) -> None:
    corpus = tmp_path / "corpus.json"
    artifact_dir = tmp_path / "artifacts"
    explicit_report = tmp_path / "custom_report.json"
    _build_index(corpus)

    code = run_search(
        [
            "--index",
            str(corpus),
            "--limit",
            "1",
            "--artifact-dir",
            str(artifact_dir),
            "--report-file",
            str(explicit_report),
            "je me suis fait baiser",
        ],
        stdout=StringIO(),
        stderr=StringIO(),
        builder=fake_builder,
    )

    assert code == 0
    assert explicit_report.exists()
    assert not (artifact_dir / "report.json").exists()
    assert (artifact_dir / "context.json").exists()
    assert (artifact_dir / "consumed_context.json").exists()
    assert (artifact_dir / "prompt.json").exists()


def test_search_artifact_dir_failure_returns_error(tmp_path) -> None:
    corpus = tmp_path / "corpus.json"
    artifact_dir = tmp_path / "not-a-directory"
    artifact_dir.write_text("file", encoding="utf-8")
    _build_index(corpus)

    stderr = StringIO()
    code = run_search(
        ["--index", str(corpus), "--artifact-dir", str(artifact_dir), "je me suis fait baiser"],
        stdout=StringIO(),
        stderr=stderr,
        builder=fake_builder,
    )

    assert code == 1
    assert "failed to prepare artifact directory" in stderr.getvalue()
