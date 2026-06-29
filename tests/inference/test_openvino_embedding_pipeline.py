from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

import pytest

from contracts.inference import InferenceRequest, InferenceResult
from inference.adapter import InferenceAdapter
from inference.embedding_pipeline import (
    OpenVINOEmbeddingPipeline,
    OpenVINOEmbeddingPipelineConfig,
    OpenVINOEmbeddingPipelineResult,
)
from inference.embedding_raw import OpenVINOEmbeddingOutputConfig
from inference.registry import BackendRegistry
from inference.tokenizer_contract import (
    TokenizationRequest,
    TokenizationResult,
    TokenizerConfig,
    TokenizerRegistry,
)


@dataclass(frozen=True)
class FakeTokenizer:
    name: str = "fake.embedding.tokens"

    def tokenize(
        self,
        request: TokenizationRequest,
        *,
        config: TokenizerConfig,
    ) -> TokenizationResult:
        assert config.name == self.name
        return TokenizationResult(
            tokenizer_name=self.name,
            input_ids=tuple((101, len(text), 102) for text in request.texts),
            attention_mask=tuple((1, 1, 0) for _ in request.texts),
            metadata={"tokenizer_config": config.name},
        )


class FakeEmbeddingBackend:
    name = "openvino.embedding.local"

    def __init__(self) -> None:
        self.requests: list[InferenceRequest] = []

    async def infer(self, request: InferenceRequest) -> InferenceResult:
        self.requests.append(request)
        assert request.context["inputs"] == {
            "input_ids": ((101, 5, 102),),
            "attention_mask": ((1, 1, 0),),
        }
        return InferenceResult(
            text="fake embedding raw outputs",
            confidence=1.0,
            backend=self.name,
            metadata=MappingProxyType(
                {
                    "raw_outputs": {
                        "last_hidden_state": [
                            [
                                [1.0, 3.0],
                                [5.0, 7.0],
                                [99.0, 99.0],
                            ]
                        ]
                    }
                }
            ),
        )


class MissingRawOutputsBackend:
    name = "openvino.embedding.missing"

    async def infer(self, request: InferenceRequest) -> InferenceResult:
        del request
        return InferenceResult(text="missing", backend=self.name, metadata=MappingProxyType({}))


def _pipeline(backend: object | None = None) -> tuple[OpenVINOEmbeddingPipeline, object]:
    tokenizer_registry = TokenizerRegistry()
    tokenizer_registry.register(FakeTokenizer(), make_default=True)

    backend_registry = BackendRegistry()
    selected_backend = backend or FakeEmbeddingBackend()
    backend_registry.register(selected_backend, make_default=True)  # type: ignore[arg-type]

    config = OpenVINOEmbeddingPipelineConfig(
        model=selected_backend.name,  # type: ignore[attr-defined]
        tokenizer_config=TokenizerConfig(name="fake.embedding.tokens"),
        output_config=OpenVINOEmbeddingOutputConfig(
            output_names=("last_hidden_state",),
            pooling="mean",
            normalize=False,
        ),
        metadata={"source": "unit"},
    )
    return (
        OpenVINOEmbeddingPipeline(
            tokenizer_registry=tokenizer_registry,
            inference_adapter=InferenceAdapter(backend_registry),
            config=config,
        ),
        selected_backend,
    )


@pytest.mark.asyncio
async def test_embedding_pipeline_assembles_tokenizer_backend_and_output_adapter() -> None:
    pipeline, backend = _pipeline()

    result = await pipeline.embed_text("alpha")

    assert isinstance(result, OpenVINOEmbeddingPipelineResult)
    assert result.text == "alpha"
    assert result.model == "openvino.embedding.local"
    assert result.tokenizer_name == "fake.embedding.tokens"
    assert result.backend == "openvino.embedding.local"
    assert result.vector.values == (3.0, 5.0)
    assert result.vector.pooling == "mean"
    assert result.vector.normalized is False
    assert result.vector.dimension == 2
    assert result.metadata["pipeline"] == "OpenVINOEmbeddingPipeline"
    assert result.metadata["vector_dimension"] == 2
    assert result.raw_inputs.input_ids == ((101, 5, 102),)
    assert result.inference.metadata["raw_outputs"]["last_hidden_state"][0][1] == [5.0, 7.0]
    assert backend.requests[0].prompt == "alpha"  # type: ignore[attr-defined]
    assert backend.requests[0].model == "openvino.embedding.local"  # type: ignore[attr-defined]
    assert backend.requests[0].metadata["embedding_pipeline"] is True  # type: ignore[attr-defined]
    assert backend.requests[0].metadata["source"] == "unit"  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_embedding_pipeline_refuses_batch_until_batch_contract_exists() -> None:
    pipeline, _ = _pipeline()

    with pytest.raises(ValueError, match="one text at a time"):
        await pipeline.embed_request(TokenizationRequest(texts=("alpha", "beta")))


@pytest.mark.asyncio
async def test_embedding_pipeline_requires_raw_outputs_from_backend_result() -> None:
    pipeline, _ = _pipeline(MissingRawOutputsBackend())

    with pytest.raises(KeyError, match="raw outputs"):
        await pipeline.embed_text("alpha")


def test_embedding_pipeline_config_validates_explicit_names() -> None:
    with pytest.raises(ValueError, match="model"):
        OpenVINOEmbeddingPipelineConfig(
            model="",
            tokenizer_config=TokenizerConfig(name="fake.embedding.tokens"),
        )

    with pytest.raises(ValueError, match="input_names"):
        OpenVINOEmbeddingPipelineConfig(
            model="openvino.embedding.local",
            tokenizer_config=TokenizerConfig(name="fake.embedding.tokens"),
            input_names=("input_ids",),
        )

    config = OpenVINOEmbeddingPipelineConfig(
        model="openvino.embedding.local",
        tokenizer_config=TokenizerConfig(name="fake.embedding.tokens"),
        tokenizer_name="custom.tokens",
    )
    assert config.tokenizer_name == "custom.tokens"
