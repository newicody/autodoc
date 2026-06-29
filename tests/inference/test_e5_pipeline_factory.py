from __future__ import annotations

import asyncio
import math
from types import MappingProxyType

import pytest

from contracts.inference import InferenceRequest, InferenceResult
from inference.e5_pipeline import (
    MultilingualE5SmallPipelineConfig,
    MultilingualE5SmallPipelineFactory,
    build_multilingual_e5_small_pipeline,
)
from inference.e5_profile import MultilingualE5SmallLocalConfig
from inference.tokenizer_contract import TokenizationRequest, TokenizationResult, TokenizerConfig


class FakeTokenizer:
    def __init__(self, name: str) -> None:
        self.name = name

    def tokenize(
        self,
        request: TokenizationRequest,
        *,
        config: TokenizerConfig,
    ) -> TokenizationResult:
        assert request.texts == ("query: salut",)
        assert config.max_length == 8
        return TokenizationResult(
            tokenizer_name=self.name,
            input_ids=((101, 42, 0, 0),),
            attention_mask=((1, 1, 0, 0),),
            token_type_ids=((0, 0, 0, 0),),
            metadata=MappingProxyType({"fake": True}),
        )


class FakeRuntime:
    def __init__(self) -> None:
        self.requests: list[InferenceRequest] = []

    async def infer(self, request: InferenceRequest, *, config):
        self.requests.append(request)
        return InferenceResult(
            text="fake-openvino",
            confidence=1.0,
            backend=config.backend_name,
            metadata=MappingProxyType(
                {
                    "raw_outputs": {
                        "last_hidden_state": (
                            (
                                (1.0, 0.0, 0.0),
                                (0.0, 1.0, 0.0),
                                (9.0, 9.0, 9.0),
                                (9.0, 9.0, 9.0),
                            ),
                        )
                    }
                }
            ),
        )


def test_factory_builds_registries_without_loading_default_dependencies() -> None:
    fake_runtime = FakeRuntime()
    local = MultilingualE5SmallLocalConfig(
        model_dir="/tmp/missing-e5",
        max_length=8,
    )

    bundle = build_multilingual_e5_small_pipeline(
        MultilingualE5SmallPipelineConfig(local=local),
        runtime_factory=lambda: fake_runtime,
        tokenizer_factory=lambda config: FakeTokenizer(config.name),
    )

    assert bundle.summary.profile_name == local.name
    assert bundle.summary.tokenizer_name == local.tokenizer_name
    assert bundle.summary.backend_name == local.name
    assert bundle.summary.model_exists is False
    assert bundle.summary.backend_registered is True
    assert bundle.summary.tokenizer_registered is True
    assert bundle.backend_registry.default_backend_name == local.name
    assert bundle.tokenizer_registry.snapshot().default_name == local.tokenizer_name


@pytest.mark.asyncio
async def test_factory_pipeline_embeds_text_with_injected_runtime_and_tokenizer() -> None:
    fake_runtime = FakeRuntime()
    local = MultilingualE5SmallLocalConfig(
        model_dir="/tmp/missing-e5",
        max_length=8,
    )
    bundle = MultilingualE5SmallPipelineFactory(
        runtime_factory=lambda: fake_runtime,
        tokenizer_factory=lambda config: FakeTokenizer(config.name),
    ).build(MultilingualE5SmallPipelineConfig(local=local))

    result = await bundle.pipeline.embed_text("query: salut")

    assert result.model == local.name
    assert result.tokenizer_name == local.tokenizer_name
    assert result.vector.dimension == 3
    assert result.vector.pooling == "mean"
    assert result.vector.normalized is True
    assert result.vector.values[0] == pytest.approx(1.0 / math.sqrt(2.0))
    assert result.vector.values[1] == pytest.approx(1.0 / math.sqrt(2.0))
    assert result.vector.values[2] == pytest.approx(0.0)
    assert fake_runtime.requests[0].context["inputs"]["token_type_ids"] == ((0, 0, 0, 0),)


def test_factory_can_require_local_model_presence() -> None:
    local = MultilingualE5SmallLocalConfig(model_dir="/tmp/missing-e5")
    factory = MultilingualE5SmallPipelineFactory(
        runtime_factory=lambda: FakeRuntime(),
        tokenizer_factory=lambda config: FakeTokenizer(config.name),
    )

    with pytest.raises(FileNotFoundError):
        factory.build(MultilingualE5SmallPipelineConfig(local=local, require_model_exists=True))
