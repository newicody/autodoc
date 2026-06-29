from __future__ import annotations

from io import StringIO
from pathlib import Path
from types import SimpleNamespace

from inference.e5_pipeline import MultilingualE5SmallPipelineConfig
from inference.e5_rank_cli import E5RankCliOutput, run


class FakePipeline:
    def __init__(self) -> None:
        self.seen: list[str] = []

    async def embed_text(self, text: str) -> object:
        self.seen.append(text)
        if text.startswith("query:"):
            values = (1.0, 0.0, 0.0)
        elif "arnaque" in text or "baiser" in text or "fait avoir" in text:
            values = (1.0, 0.0, 0.0)
        elif "moteur" in text:
            values = (0.0, 1.0, 0.0)
        else:
            values = (0.0, 0.0, 1.0)
        return SimpleNamespace(
            text=text,
            model="fake-e5-model",
            backend="fake-e5-backend",
            tokenizer_name="fake-tokenizer",
            vector=SimpleNamespace(values=values, dimension=len(values), normalized=True, l2_norm=1.0),
        )


def make_builder(pipeline: FakePipeline):
    def builder(config: MultilingualE5SmallPipelineConfig) -> object:
        assert config.local.device == "CPU"
        return SimpleNamespace(
            pipeline=pipeline,
            summary=SimpleNamespace(model_path="/fake/openvino_model.xml", device=config.local.device),
        )

    return builder


def test_rank_cli_text_output_orders_passages() -> None:
    pipeline = FakePipeline()
    stdout = StringIO()
    stderr = StringIO()

    code = run(
        (
            "je me suis fait baiser",
            "--passage",
            "problème moteur diesel",
            "--passage",
            "arnaque vendeur voiture",
        ),
        stdout=stdout,
        stderr=stderr,
        builder=make_builder(pipeline),
    )

    assert code == 0
    assert stderr.getvalue() == ""
    output = stdout.getvalue()
    assert "query: je me suis fait baiser" in output
    assert "prefixed_query: query: je me suis fait baiser" in output
    assert "#1 score=1.00000000" in output
    assert "text: arnaque vendeur voiture" in output
    assert pipeline.seen == [
        "query: je me suis fait baiser",
        "passage: problème moteur diesel",
        "passage: arnaque vendeur voiture",
    ]


def test_rank_cli_json_output_and_limit() -> None:
    stdout = StringIO()
    stderr = StringIO()

    code = run(
        (
            "query: arnaque",
            "--passage",
            "moteur diesel",
            "--passage",
            "je me suis fait avoir",
            "--limit",
            "1",
            "--format",
            "json",
        ),
        stdout=stdout,
        stderr=stderr,
        builder=make_builder(FakePipeline()),
    )

    assert code == 0
    assert '"result_count": 1' in stdout.getvalue()
    assert '"prefixed_query": "query: arnaque"' in stdout.getvalue()
    assert '"prefixed_text": "passage: je me suis fait avoir"' in stdout.getvalue()


def test_rank_cli_reads_passages_file(tmp_path: Path) -> None:
    passages_file = tmp_path / "passages.txt"
    passages_file.write_text("\nproblème moteur\n\narnaque vendeur\n", encoding="utf-8")
    stdout = StringIO()
    stderr = StringIO()

    code = run(
        (
            "arnaque",
            "--passages-file",
            str(passages_file),
        ),
        stdout=stdout,
        stderr=stderr,
        builder=make_builder(FakePipeline()),
    )

    assert code == 0
    assert "result_count: 2" in stdout.getvalue()
    assert "text: arnaque vendeur" in stdout.getvalue()


def test_rank_cli_requires_at_least_one_passage() -> None:
    stdout = StringIO()
    stderr = StringIO()

    code = run(("query",), stdout=stdout, stderr=stderr, builder=make_builder(FakePipeline()))

    assert code == 2
    assert "at least one" in stderr.getvalue()


def test_rank_cli_rejects_invalid_limit() -> None:
    stdout = StringIO()
    stderr = StringIO()

    code = run(
        ("query", "--passage", "passage", "--limit", "0"),
        stdout=stdout,
        stderr=stderr,
        builder=make_builder(FakePipeline()),
    )

    assert code == 2
    assert "--limit" in stderr.getvalue()


def test_rank_cli_output_json_projection() -> None:
    output = E5RankCliOutput(
        query="arnaque",
        prefixed_query="query: arnaque",
        model="model",
        backend="backend",
        tokenizer="tokenizer",
        model_path="/tmp/model.xml",
        device="CPU",
        result_count=0,
        passages=(),
    )

    assert output.to_json_dict()["prefixed_query"] == "query: arnaque"
    assert "result_count: 0" in output.to_text()
