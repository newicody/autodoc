from __future__ import annotations

import json
from io import StringIO
from types import SimpleNamespace

from inference.e5_cli import run


class FakePipeline:
    async def embed_text(self, text: str) -> object:
        return SimpleNamespace(
            text=text,
            model="openvino.embedding.e5-small",
            backend="openvino.embedding.e5-small",
            tokenizer_name="transformers.multilingual-e5-small",
            vector=SimpleNamespace(
                values=(0.1, 0.2, 0.3, 0.4),
                dimension=4,
                normalized=True,
                l2_norm=1.0,
            ),
        )


class CaptureBuilder:
    def __init__(self) -> None:
        self.configs: list[object] = []

    def __call__(self, config: object) -> object:
        self.configs.append(config)
        return SimpleNamespace(
            pipeline=FakePipeline(),
            summary=SimpleNamespace(
                model_path="/tmp/model/openvino_model.xml",
                device="CPU",
            ),
        )


def test_e5_cli_text_output_uses_injected_builder() -> None:
    builder = CaptureBuilder()
    stdout = StringIO()
    stderr = StringIO()

    exit_code = run(
        [
            "query: test",
            "--model-dir",
            "/tmp/model",
            "--device",
            "CPU",
            "--max-length",
            "64",
            "--preview",
            "2",
        ],
        stdout=stdout,
        stderr=stderr,
        builder=builder,
    )

    assert exit_code == 0
    assert stderr.getvalue() == ""
    assert "dimension: 4" in stdout.getvalue()
    assert "values_preview: [0.10000000, 0.20000000]" in stdout.getvalue()
    assert len(builder.configs) == 1
    config = builder.configs[0]
    assert config.require_model_exists is True
    assert config.local.model_dir == "/tmp/model"
    assert config.local.max_length == 64


def test_e5_cli_json_output_hides_full_vector_by_default() -> None:
    stdout = StringIO()
    stderr = StringIO()

    exit_code = run(
        ["query: test", "--format", "json", "--preview", "3"],
        stdout=stdout,
        stderr=stderr,
        builder=CaptureBuilder(),
    )

    assert exit_code == 0
    payload = json.loads(stdout.getvalue())
    assert payload["dimension"] == 4
    assert payload["values_preview"] == [0.1, 0.2, 0.3]
    assert "values" not in payload


def test_e5_cli_json_output_can_include_full_vector() -> None:
    stdout = StringIO()
    stderr = StringIO()

    exit_code = run(
        ["query: test", "--format", "json", "--full-vector"],
        stdout=stdout,
        stderr=stderr,
        builder=CaptureBuilder(),
    )

    assert exit_code == 0
    payload = json.loads(stdout.getvalue())
    assert payload["values"] == [0.1, 0.2, 0.3, 0.4]


def test_e5_cli_rejects_invalid_preview_before_building_pipeline() -> None:
    builder = CaptureBuilder()
    stdout = StringIO()
    stderr = StringIO()

    exit_code = run(
        ["query: test", "--preview", "-1"],
        stdout=stdout,
        stderr=stderr,
        builder=builder,
    )

    assert exit_code == 2
    assert stdout.getvalue() == ""
    assert "--preview must be >= 0" in stderr.getvalue()
    assert builder.configs == []


def test_e5_cli_applies_query_role_to_raw_text_by_default() -> None:
    stdout = StringIO()
    stderr = StringIO()

    exit_code = run(
        ["texte brut", "--format", "json"],
        stdout=stdout,
        stderr=stderr,
        builder=CaptureBuilder(),
    )

    assert exit_code == 0
    payload = json.loads(stdout.getvalue())
    assert payload["text"] == "query: texte brut"


def test_e5_cli_can_apply_passage_role_to_raw_text() -> None:
    stdout = StringIO()
    stderr = StringIO()

    exit_code = run(
        ["document à indexer", "--role", "passage", "--format", "json"],
        stdout=stdout,
        stderr=stderr,
        builder=CaptureBuilder(),
    )

    assert exit_code == 0
    payload = json.loads(stdout.getvalue())
    assert payload["text"] == "passage: document à indexer"
