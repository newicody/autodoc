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


def test_search_parser_accepts_prompt_files_and_context_budget() -> None:
    args = build_search_parser().parse_args(
        [
            "--index",
            "/tmp/corpus.json",
            "--consumed-context-file",
            "/tmp/consumed.json",
            "--prompt-file",
            "/tmp/prompt.json",
            "--context-max-chars",
            "500",
            "--context-max-items",
            "2",
            "--context-include-scores",
            "query",
        ]
    )

    assert args.consumed_context_file == "/tmp/consumed.json"
    assert args.prompt_file == "/tmp/prompt.json"
    assert args.context_max_chars == 500
    assert args.context_max_items == 2
    assert args.context_include_scores is True


def test_search_writes_consumed_context_and_prompt_files(tmp_path) -> None:
    corpus = tmp_path / "corpus.json"
    context = tmp_path / "context.json"
    consumed = tmp_path / "consumed.json"
    prompt = tmp_path / "prompt.json"
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
            "--consumed-context-file",
            str(consumed),
            "--prompt-file",
            str(prompt),
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

    context_payload = json.loads(context.read_text(encoding="utf-8"))
    assert context_payload["item_count"] == 1
    assert context_payload["items"][0]["excerpt"] == "arnaque vendeur"

    consumed_payload = json.loads(consumed.read_text(encoding="utf-8"))
    assert consumed_payload["selected_item_count"] == 1
    assert "score: 1.00000000" in consumed_payload["context_text"]
    assert "arnaque vendeur" in consumed_payload["context_text"]

    prompt_payload = json.loads(prompt.read_text(encoding="utf-8"))
    assert prompt_payload["selected_item_count"] == 1
    assert "[QUESTION]\nje me suis fait baiser" in prompt_payload["prompt_text"]
    assert "[CONTEXT]" in prompt_payload["prompt_text"]
    assert "arnaque vendeur" in prompt_payload["prompt_text"]


def test_search_rejects_prompt_file_without_filename() -> None:
    stderr = StringIO()
    code = run_search(
        ["--index", "/tmp/corpus.json", "--prompt-file", "/", "query"],
        stdout=StringIO(),
        stderr=stderr,
        builder=fake_builder,
    )

    assert code == 2
    assert "--prompt-file must target a filename" in stderr.getvalue()


def test_search_rejects_invalid_context_budget_with_cli_message() -> None:
    stderr = StringIO()
    code = run_search(
        ["--index", "/tmp/corpus.json", "--context-max-chars", "0", "query"],
        stdout=StringIO(),
        stderr=stderr,
        builder=fake_builder,
    )

    assert code == 2
    assert "--context-max-chars must be positive" in stderr.getvalue()
