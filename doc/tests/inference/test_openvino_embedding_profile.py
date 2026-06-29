from __future__ import annotations

import pytest

from inference.embedding_profile import (
    DEFAULT_EMBEDDING_INPUT_NAMES,
    DEFAULT_EMBEDDING_OUTPUT_NAMES,
    SUPPORTED_EMBEDDING_POOLING,
    OpenVINOEmbeddingProfileConfig,
    register_openvino_embedding_profile,
)
from inference.model_profile import OpenVINOModelProfileRegistry


def test_embedding_profile_config_builds_openvino_model_profile() -> None:
    config = OpenVINOEmbeddingProfileConfig(
        model_path="/models/emb/openvino_model.xml",
        name="openvino.embedding.local",
        device="GPU",
        dimension=1024,
        input_names=("input_ids", "attention_mask", "token_type_ids"),
        output_names=("sentence_embedding",),
        pooling="model",
        normalize=True,
        metadata={"source": "local"},
    )

    profile = config.to_model_profile()

    assert profile.name == "openvino.embedding.local"
    assert profile.task == "embedding"
    assert profile.model_path == "/models/emb/openvino_model.xml"
    assert profile.device == "GPU"
    assert profile.input_names == ("input_ids", "attention_mask", "token_type_ids")
    assert profile.output_names == ("sentence_embedding",)
    assert profile.metadata["profile_kind"] == "openvino.embedding.configurable"
    assert profile.metadata["embedding_dimension"] == 1024
    assert profile.metadata["embedding_pooling"] == "model"
    assert profile.metadata["embedding_normalize"] is True
    assert profile.metadata["requires_tokenizer"] is True
    assert profile.metadata["tokenizer_bound"] is False
    assert profile.metadata["source"] == "local"

    backend_config = profile.to_backend_config()
    assert backend_config.backend_name == "openvino.embedding.local"
    assert backend_config.metadata["task"] == "embedding"
    assert backend_config.metadata["embedding_dimension"] == 1024


def test_embedding_profile_config_has_safe_defaults_without_model_choice() -> None:
    config = OpenVINOEmbeddingProfileConfig(model_path="models/embedding/openvino_model.xml")

    assert config.name == "openvino.embedding"
    assert config.device == "CPU"
    assert config.input_names == DEFAULT_EMBEDDING_INPUT_NAMES
    assert config.output_names == DEFAULT_EMBEDDING_OUTPUT_NAMES
    assert config.dimension is None
    assert config.pooling == "model"
    assert config.normalize is True


def test_embedding_profile_config_from_mapping_accepts_json_like_values() -> None:
    config = OpenVINOEmbeddingProfileConfig.from_mapping(
        {
            "model_path": "models/e5/openvino_model.xml",
            "name": "openvino.embedding.e5",
            "device": "GPU",
            "input_names": ["input_ids", "attention_mask"],
            "output_names": ["embeddings"],
            "dimension": "768",
            "pooling": "mean",
            "normalize": False,
            "metadata": {"family": "e5"},
        }
    )

    assert config.model_path == "models/e5/openvino_model.xml"
    assert config.name == "openvino.embedding.e5"
    assert config.dimension == 768
    assert config.pooling == "mean"
    assert config.normalize is False
    assert config.metadata["family"] == "e5"


def test_embedding_profile_config_freezes_metadata_copy() -> None:
    source = {"family": "bge"}
    config = OpenVINOEmbeddingProfileConfig(
        model_path="models/bge/openvino_model.xml",
        metadata=source,
    )

    source["family"] = "changed"

    assert config.metadata["family"] == "bge"
    with pytest.raises(TypeError):
        config.metadata["family"] = "mutated"  # type: ignore[index]


def test_embedding_profile_config_rejects_invalid_shape() -> None:
    with pytest.raises(ValueError, match="model_path"):
        OpenVINOEmbeddingProfileConfig(model_path="")

    with pytest.raises(ValueError, match="dimension"):
        OpenVINOEmbeddingProfileConfig(model_path="m.xml", dimension=0)

    with pytest.raises(ValueError, match="Unsupported embedding pooling"):
        OpenVINOEmbeddingProfileConfig(model_path="m.xml", pooling="sum")

    with pytest.raises(ValueError, match="input_names"):
        OpenVINOEmbeddingProfileConfig(model_path="m.xml", input_names=())

    with pytest.raises(TypeError, match="metadata"):
        OpenVINOEmbeddingProfileConfig.from_mapping(
            {"model_path": "m.xml", "metadata": ["not", "mapping"]}
        )


def test_embedding_profile_can_be_registered_explicitly() -> None:
    registry = OpenVINOModelProfileRegistry()
    config = OpenVINOEmbeddingProfileConfig(
        model_path="models/local/openvino_model.xml",
        name="openvino.embedding.local",
    )

    profile = register_openvino_embedding_profile(registry, config)

    assert registry.select("openvino.embedding.local") is profile
    assert registry.by_task("embedding") == (profile,)


def test_supported_embedding_pooling_values_are_declarative_contract() -> None:
    assert SUPPORTED_EMBEDDING_POOLING == frozenset({"model", "cls", "mean", "none"})
